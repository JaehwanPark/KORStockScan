"""State machine handlers for the sniper engine."""

import json
import re
import time
import math
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np

from src.database.models import HoldingAddHistory, RecommendationHistory
from src.engine import kiwoom_orders
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine.sniper_time import (
    TIME_09_00,
    TIME_09_03,
    TIME_09_05,
    TIME_15_30,
    TIME_SCALPING_OVERNIGHT_DECISION,
    TIME_SCALPING_NEW_BUY_CUTOFF,
)
from src.engine.sniper_condition_handlers_big_bite import (
    build_tick_data_from_ws,
    arm_big_bite_if_triggered,
    confirm_big_bite_follow_through,
)
from src.engine.sniper_scale_in import (
    describe_dynamic_scale_in_qty,
    describe_scale_in_qty,
    evaluate_scalping_pyramid,
    evaluate_swing_avg_down,
    evaluate_swing_pyramid,
    evaluate_scalping_reversal_add,
    resolve_scale_in_order_price,
    resolve_holding_elapsed_sec,
)
from src.engine.sniper_scale_in_utils import record_add_history_event
from src.engine.trade_pause_control import is_buy_side_paused, get_pause_state_label
from src.engine.sniper_entry_latency import (
    clear_signal_reference,
    evaluate_live_buy_entry,
)
from src.engine.sniper_entry_state import ENTRY_LOCK, move_orders_to_terminal
from src.engine.sniper_strength_momentum import evaluate_scalping_strength_momentum
from src.engine.sniper_strength_shadow_feedback import record_shadow_candidate
from src.engine.sniper_gatekeeper_replay import record_gatekeeper_snapshot
from src.engine.sniper_post_sell_feedback import record_sim_post_sell_candidate
from src.engine.holding_exit_matrix_runtime import resolve_holding_exit_matrix_scale_in_bias
from src.engine.lifecycle_decision_matrix_runtime import resolve_lifecycle_decision
from src.engine.sniper_dynamic_thresholds import (
    estimate_turnover_hint,
    get_dynamic_scalp_thresholds,
    get_dynamic_swing_gap_threshold,
)
from src.engine.trade_profit import calculate_net_profit_rate
from src.engine.sniper_position_tags import (
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
)
from src.engine.ai_engine import SCALPING_BUY_RECOVERY_CANARY_PROMPT
from src.engine.ofi_ai_smoothing import (
    NEUTRAL as OFI_NEUTRAL,
    STABLE_BEARISH as OFI_STABLE_BEARISH,
    STABLE_BULLISH as OFI_STABLE_BULLISH,
    OfiSmoothingConfig,
    OfiSmoothingState,
    entry_skip_demotion_allowed,
    evaluate_ofi_smoothing,
    ofi_smoothing_log_fields,
)
from src.trading.entry.orderbook_stability_observer import ORDERBOOK_STABILITY_OBSERVER
from src.trading.order.tick_utils import clamp_price_to_tick


KIWOOM_TOKEN = None
DB = None
EVENT_BUS = None
ACTIVE_TARGETS = None
COOLDOWNS = None
ALERTED_STOCKS = None

# ── 프로세스 레벨 marcap TTL 캐시 (hot path용) ──
_MARCAP_CACHE: dict[str, tuple[int, float]] = {}
_MARCAP_CACHE_TTL: int = 300  # 5분
_MARCAP_CACHE_MAX_SIZE: int = 512


def _resolve_zero_qty_cooldown_sec(deposit: int) -> int:
    """주문가능금액 0원은 일시 조회 실패일 수 있어 짧게 재조회합니다."""
    if _safe_int(deposit, 0) <= 0:
        return _rule_int("ZERO_DEPOSIT_RETRY_COOLDOWN_SEC", 20)
    return 1200


def _prune_marcap_cache(now_ts: float) -> None:
    expired_codes = [
        stock_code
        for stock_code, (_, exp_ts) in list(_MARCAP_CACHE.items())
        if now_ts >= float(exp_ts or 0)
    ]
    for stock_code in expired_codes:
        _MARCAP_CACHE.pop(stock_code, None)

    while len(_MARCAP_CACHE) >= _MARCAP_CACHE_MAX_SIZE:
        oldest_code = next(iter(_MARCAP_CACHE), None)
        if oldest_code is None:
            break
        _MARCAP_CACHE.pop(oldest_code, None)


def _extract_sellable_qty_from_error(err_msg: str):
    """주문 거절 메시지에서 'N주 매도가능' 수량을 추출한다."""
    if not err_msg:
        return None
    match = re.search(r"(\d+)\s*주\s*매도가능", str(err_msg))
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


HIGHEST_PRICES = None
LAST_AI_CALL_TIMES = None
LAST_LOG_TIMES = None
TRADING_RULES = None
PUBLISH_GATEKEEPER_REPORT = None
SHOULD_BLOCK_SWING_ENTRY = None
CONFIRM_CANCEL_OR_RELOAD_REMAINING = None
SEND_EXIT_BEST_IOC = None
DUAL_PERSONA_ENGINE = None
BIG_BITE_STATE = {}
_SAME_SYMBOL_SOFT_STOP_TS: dict[str, float] = {}
_HOLDING_FLOW_OVERRIDE_EXIT_RULES = {
    "scalp_soft_stop_pct",
    "scalp_ai_momentum_decay",
    "scalp_trailing_take_profit",
    "scalp_bad_entry_refined_canary",
}
SCALP_SIMULATION_BOOK = "scalp_ai_buy_all"
SCALP_SIM_PENDING_STATUS = "SCALP_SIM_PENDING_BUY"
SCALP_SIM_STATE_PATH = DATA_DIR / "runtime" / "scalp_live_simulator_state.json"
SWING_INTRADAY_PROBE_BOOK = "swing_intraday_live_equiv_probe"
SWING_INTRADAY_PROBE_STATE_PATH = DATA_DIR / "runtime" / "swing_intraday_probe_state.json"
_SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED: dict[str, int] = {}
_SCALP_SIM_SCALE_IN_WINDOW_DAILY_CREATED: dict[str, int] = {}
_SCALP_SIM_AI_CALL_TIMES: list[float] = []
_SWING_PROBE_DAILY_CREATED: dict[str, int] = {}
_SWING_PROBE_DISCARD_LOG_TS: dict[tuple[str, str, str, str], float] = {}
_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS: dict[str, dict] = {}


def _mutate_stock_state(stock, set_fields: dict | None = None, pop_fields: list | tuple = ()):
    """기본 상태(dict) 변경은 ENTRY_LOCK 하에서 일괄 반영.

    lock ownership:
    - `stock` dict의 runtime truth(status/odno/pending flags/qty 등) 변경은 이 helper 우선
    - `ACTIVE_TARGETS`, `cooldowns`, `highest_prices`, `alerted_stocks` 같은 shared collection은
      `with ENTRY_LOCK:` 블록 안에서 직접 갱신
    """
    if stock is None:
        return
    with ENTRY_LOCK:
        if set_fields:
            for key, value in set_fields.items():
                stock[key] = value
        for key in pop_fields:
            stock.pop(key, None)


def _rule(name, default=None):
    if TRADING_RULES is None:
        return default
    return getattr(TRADING_RULES, name, default)


def _rule_bool(name, default=False):
    return bool(_rule(name, default))


def _rule_int(name, default=0):
    try:
        return int(_rule(name, default) or default)
    except (TypeError, ValueError):
        return int(default)


def _rule_float(name, default=0.0):
    try:
        return float(_rule(name, default) or default)
    except (TypeError, ValueError):
        return float(default)


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().lower() in {"", "nan", "nat", "none", "inf", "+inf", "-inf"}:
            return default
        numeric = float(value)
        if not math.isfinite(numeric):
            return default
        return numeric
    except Exception:
        return default


def _safe_int(value, default=0):
    numeric = _safe_float(value, None)
    if numeric is None:
        return default
    try:
        return int(numeric)
    except Exception:
        return default


def _is_swing_strategy(strategy: str | None) -> bool:
    return str(strategy or "").strip().upper() in {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}


def _is_swing_live_order_dry_run(strategy: str | None) -> bool:
    return _is_swing_strategy(strategy) and _rule_bool("SWING_LIVE_ORDER_DRY_RUN_ENABLED", True)


def _is_swing_orderbook_micro_context_enabled(strategy: str | None) -> bool:
    return _is_swing_strategy(strategy) and _rule_bool("SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED", True)


def _swing_live_order_dry_run_owner() -> str:
    return str(_rule("SWING_LIVE_ORDER_DRY_RUN_OWNER", "SwingLiveOrderDryRunSimulation0511") or "")


def _swing_intraday_probe_owner() -> str:
    return str(_rule("SWING_INTRADAY_PROBE_OWNER", "SwingIntradayLiveEquivalentProbe0511") or "")


def _is_swing_intraday_probe_enabled() -> bool:
    return (
        _rule_bool("SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED", True)
        and _rule_bool("SWING_LIVE_ORDER_DRY_RUN_ENABLED", True)
    )


def _is_swing_intraday_probe_target(stock: dict | None) -> bool:
    if not isinstance(stock, dict):
        return False
    return (
        bool(stock.get("swing_intraday_probe"))
        or str(stock.get("simulation_book") or "") == SWING_INTRADAY_PROBE_BOOK
    )


def _is_swing_simulated_position(stock: dict | None, strategy: str | None = None) -> bool:
    if not isinstance(stock, dict):
        return False
    resolved_strategy = strategy or stock.get("strategy")
    return _is_swing_strategy(resolved_strategy) and bool(stock.get("swing_live_order_dry_run"))


def _swing_scale_in_real_canary_allowed_arms() -> set[str]:
    raw = str(_rule("SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS", "PYRAMID,AVG_DOWN") or "")
    return {part.strip().upper() for part in raw.split(",") if part.strip()}


def _swing_one_share_real_canary_allowed_codes() -> set[str]:
    raw = str(_rule("SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES", "") or "")
    return {part.strip().zfill(6) for part in raw.split(",") if part.strip()}


def _is_swing_one_share_real_canary_position(stock: dict | None, strategy: str | None = None) -> bool:
    if not isinstance(stock, dict):
        return False
    if not _is_swing_strategy(strategy or stock.get("strategy")):
        return False
    return bool(
        stock.get("swing_one_share_real_canary")
        or str(stock.get("cohort") or stock.get("real_canary_cohort") or "").strip() == "swing_one_share_real_canary"
    )


def _swing_one_share_real_canary_daily_key(now_ts: float | None = None) -> str:
    try:
        return datetime.fromtimestamp(float(now_ts or time.time())).date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def _swing_one_share_real_canary_usage(day_key: str) -> tuple[int, int, int]:
    new_entries = 0
    open_positions = 0
    notional = 0
    for target in ACTIVE_TARGETS or []:
        if not isinstance(target, dict):
            continue
        if not _is_swing_one_share_real_canary_position(target, target.get("strategy")):
            continue
        if _active_runtime_status(target):
            open_positions += 1
        if str(target.get("swing_one_share_real_canary_order_date") or "") != day_key:
            continue
        new_entries += int(target.get("swing_one_share_real_canary_order_count", 0) or 0)
        notional += int(target.get("swing_one_share_real_canary_notional_krw", 0) or 0)
    return new_entries, open_positions, notional


def _evaluate_swing_one_share_real_canary(
    stock: dict,
    code: str,
    *,
    request_qty: int,
    request_price: int,
    ws_data: dict,
    submit_revalidation_fields: dict,
    swing_entry_micro_fields: dict,
) -> dict:
    day_key = _swing_one_share_real_canary_daily_key()
    common = {
        "policy_id": "swing_one_share_real_canary_phase0",
        "cohort": "swing_one_share_real_canary",
        "request_price": request_price,
        "source_requested_qty": request_qty,
    }
    if not _rule_bool("SWING_ONE_SHARE_REAL_CANARY_ENABLED", False):
        return {"allowed": False, "reason": "real_canary_disabled", "fields": common}
    if _rule_bool("SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT", True) and not _swing_one_share_real_canary_allowed_codes():
        return {"allowed": False, "reason": "approval_allowed_codes_missing", "fields": common}
    if not _is_swing_strategy(stock.get("strategy")):
        return {"allowed": False, "reason": "not_swing_strategy", "fields": common}
    if _is_any_simulated_position(stock, stock.get("strategy")):
        return {"allowed": False, "reason": "sim_or_probe_real_order_forbidden", "fields": common}
    allowed_codes = _swing_one_share_real_canary_allowed_codes()
    normalized_code = str(code or "").strip().zfill(6)
    if normalized_code not in allowed_codes:
        return {"allowed": False, "reason": "code_not_approved", "fields": {**common, "allowed_codes": ",".join(sorted(allowed_codes))}}
    if request_price <= 0:
        return {"allowed": False, "reason": "invalid_order_price", "fields": common}
    if bool((submit_revalidation_fields or {}).get("entry_submit_revalidation_warning")):
        return {"allowed": False, "reason": "submit_revalidation_warning", "fields": {**common, **(submit_revalidation_fields or {})}}
    if bool((swing_entry_micro_fields or {}).get("swing_micro_stale")):
        return {"allowed": False, "reason": "orderbook_micro_stale", "fields": common}
    if str((swing_entry_micro_fields or {}).get("swing_micro_advice") or "") == "RISK_BEARISH":
        return {"allowed": False, "reason": "ofi_qi_risk_bearish", "fields": common}

    max_qty = min(1, max(1, _rule_int("SWING_ONE_SHARE_REAL_CANARY_MAX_QTY", 1)))
    actual_qty = max(0, min(int(request_qty or 0), max_qty))
    if actual_qty <= 0:
        return {"allowed": False, "reason": "real_canary_qty_zero", "fields": common}
    daily_entries, open_positions, daily_notional = _swing_one_share_real_canary_usage(day_key)
    max_new_entries = min(1, max(1, _rule_int("SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY", 1)))
    if daily_entries >= max_new_entries:
        return {"allowed": False, "reason": "daily_new_entry_cap_reached", "fields": {**common, "daily_entries": daily_entries}}
    max_open_positions = min(3, max(1, _rule_int("SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS", 3)))
    if open_positions >= max_open_positions:
        return {"allowed": False, "reason": "open_position_cap_reached", "fields": {**common, "open_positions": open_positions}}
    if any(
        _is_swing_one_share_real_canary_position(target, target.get("strategy"))
        and _active_runtime_status(target)
        and str(target.get("code") or "").strip().zfill(6) == normalized_code
        for target in ACTIVE_TARGETS or []
        if isinstance(target, dict)
    ):
        return {"allowed": False, "reason": "same_symbol_active_limit_reached", "fields": common}
    max_total_notional = min(300000, max(1, _rule_int("SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW", 300000)))
    order_notional = int(request_price * actual_qty)
    if daily_notional + order_notional > max_total_notional:
        return {
            "allowed": False,
            "reason": "total_notional_cap_reached",
            "fields": {**common, "daily_notional": daily_notional, "order_notional": order_notional},
        }
    return {
        "allowed": True,
        "reason": "swing_one_share_real_canary_allowed",
        "qty": actual_qty,
        "fields": {
            **common,
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            "real_canary_actual_qty": actual_qty,
            "real_canary_qty_cap": max_qty,
            "qty_cap_reason": "swing_one_share_real_canary_phase0",
            "order_notional_krw": order_notional,
            "day_key": day_key,
        },
    }


def _is_swing_scale_in_real_canary_holding(stock: dict | None, strategy: str | None = None) -> bool:
    if not isinstance(stock, dict):
        return False
    if not _is_swing_strategy(strategy or stock.get("strategy")):
        return False
    if stock.get("actual_order_submitted") is not True:
        return False
    if stock.get("simulation_book") or stock.get("simulation_owner") or stock.get("simulated_order"):
        return False
    cohort = str(stock.get("cohort") or stock.get("real_canary_cohort") or "").strip()
    return bool(
        cohort in {"swing_one_share_real_canary", "swing_scale_in_real_canary_phase0"}
        or stock.get("swing_one_share_real_canary")
        or stock.get("swing_real_canary")
    )


def _swing_scale_in_real_canary_daily_key(now_ts: float | None = None) -> str:
    try:
        return datetime.fromtimestamp(float(now_ts or time.time())).date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def _swing_scale_in_real_canary_daily_usage(day_key: str) -> tuple[int, int]:
    count = 0
    notional = 0
    for target in ACTIVE_TARGETS or []:
        if not isinstance(target, dict):
            continue
        if str(target.get("swing_scale_in_real_canary_order_date") or "") != day_key:
            continue
        count += int(target.get("swing_scale_in_real_canary_order_count", 0) or 0)
        notional += int(target.get("swing_scale_in_real_canary_notional_krw", 0) or 0)
    return count, notional


def _evaluate_swing_scale_in_real_canary(
    stock: dict,
    code: str,
    *,
    add_type: str,
    qty: int,
    final_price: int,
    curr_price: int,
    ws_data: dict,
    price_resolution: dict,
    swing_scale_micro_fields: dict,
    template_qty: int,
    would_qty: int,
    effective_qty: int,
    cap_qty: int,
    floor_applied: bool,
    qty_reason: str,
) -> dict:
    day_key = _swing_scale_in_real_canary_daily_key()
    common = {
        "policy_id": "swing_scale_in_real_canary_phase0",
        "cohort": "swing_scale_in_real_canary_phase0",
        "add_type": add_type,
        "curr_price": curr_price,
        "would_qty": would_qty,
        "effective_qty": effective_qty,
        "template_qty": template_qty,
        "cap_qty": cap_qty,
        "floor_applied": floor_applied,
        "qty_reason": qty_reason,
        **(swing_scale_micro_fields or {}),
    }
    if not _rule_bool("SWING_SCALE_IN_REAL_CANARY_ENABLED", False):
        return {"allowed": False, "reason": "real_canary_disabled", "fields": common}
    if _rule_bool("SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT", True) and not _rule_bool(
        "SWING_SCALE_IN_REAL_CANARY_ENABLED", False
    ):
        return {"allowed": False, "reason": "approval_artifact_env_missing", "fields": common}
    if not _is_swing_scale_in_real_canary_holding(stock, stock.get("strategy")):
        return {"allowed": False, "reason": "not_approved_real_canary_holding", "fields": common}
    if add_type not in _swing_scale_in_real_canary_allowed_arms():
        return {"allowed": False, "reason": "arm_not_approved", "fields": common}
    if _is_any_simulated_position(stock, stock.get("strategy")):
        return {"allowed": False, "reason": "sim_or_probe_real_order_forbidden", "fields": common}

    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    ws_age_sec = _get_ws_snapshot_age_sec(ws_data or {})
    max_ws_age_sec = _rule_float("AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC", 2.0)
    if ws_age_sec is not None and ws_age_sec > max_ws_age_sec:
        return {
            "allowed": False,
            "reason": "stale_quote",
            "fields": {**common, "best_bid": best_bid, "best_ask": best_ask, "ws_age_sec": f"{ws_age_sec:.2f}"},
        }
    if best_bid <= 0:
        return {"allowed": False, "reason": "missing_best_bid", "fields": {**common, "best_bid": best_bid, "best_ask": best_ask}}
    if not bool((swing_scale_micro_fields or {}).get("orderbook_micro_ready")):
        return {"allowed": False, "reason": "orderbook_micro_not_ready", "fields": {**common, "best_bid": best_bid, "best_ask": best_ask}}
    if bool((swing_scale_micro_fields or {}).get("swing_micro_stale")):
        return {"allowed": False, "reason": "orderbook_micro_stale", "fields": {**common, "best_bid": best_bid, "best_ask": best_ask}}
    if str((swing_scale_micro_fields or {}).get("swing_micro_advice") or "") == "RISK_BEARISH":
        return {"allowed": False, "reason": "ofi_qi_risk_bearish", "fields": {**common, "best_bid": best_bid, "best_ask": best_ask}}

    max_qty = max(1, _rule_int("SWING_SCALE_IN_REAL_CANARY_MAX_QTY", 1))
    actual_qty = max(0, min(int(qty or 0), int(effective_qty or 0), max_qty))
    if actual_qty <= 0:
        return {"allowed": False, "reason": "real_canary_qty_zero", "fields": {**common, "best_bid": best_bid, "best_ask": best_ask}}

    daily_count, daily_notional = _swing_scale_in_real_canary_daily_usage(day_key)
    max_orders_day = max(1, _rule_int("SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY", 1))
    if daily_count >= max_orders_day:
        return {"allowed": False, "reason": "daily_order_cap_reached", "fields": {**common, "daily_count": daily_count}}
    max_orders_position = max(1, _rule_int("SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION", 1))
    position_count = int(stock.get("swing_scale_in_real_canary_order_count", 0) or 0)
    if position_count >= max_orders_position:
        return {"allowed": False, "reason": "position_order_cap_reached", "fields": {**common, "position_count": position_count}}
    max_daily_notional = max(1, _rule_int("SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW", 100000))
    order_notional = int(best_bid * actual_qty)
    if daily_notional + order_notional > max_daily_notional:
        return {
            "allowed": False,
            "reason": "daily_notional_cap_reached",
            "fields": {**common, "daily_notional": daily_notional, "order_notional": order_notional},
        }
    return {
        "allowed": True,
        "reason": "swing_scale_in_real_canary_allowed",
        "qty": actual_qty,
        "order_price": best_bid,
        "order_type_code": "00",
        "fields": {
            **common,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "source_final_price": final_price,
            "source_price_reason": price_resolution.get("reason"),
            "source_price_policy": price_resolution.get("price_source"),
            "real_canary_actual_qty": actual_qty,
            "real_canary_qty_cap": max_qty,
            "qty_cap_reason": "swing_scale_in_real_canary_phase0",
            "order_notional_krw": order_notional,
            "day_key": day_key,
        },
    }


def _is_scalp_strategy(strategy: str | None) -> bool:
    return str(strategy or "").strip().upper() in {"SCALPING", "SCALP"}


def _is_scalp_live_simulator_enabled() -> bool:
    return _rule_bool("SCALP_LIVE_SIMULATOR_ENABLED", True)


def _scalp_live_simulator_owner() -> str:
    return str(_rule("SCALP_LIVE_SIMULATOR_OWNER", "ScalpAiBuyAllLiveSimulator0511") or "")


def _scalp_live_simulator_fill_policy() -> str:
    return str(
        _rule("SCALP_LIVE_SIMULATOR_FILL_POLICY", "signal_inclusive_best_ask_v1")
        or "signal_inclusive_best_ask_v1"
    )


def _is_scalp_sim_candidate_window_expansion_enabled() -> bool:
    return _rule_bool("SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED", False)


def _is_scalp_simulator_target(stock: dict | None) -> bool:
    if not isinstance(stock, dict):
        return False
    return (
        bool(stock.get("scalp_live_simulator"))
        or str(stock.get("simulation_book") or "") == SCALP_SIMULATION_BOOK
    )


def _is_scalp_simulated_position(stock: dict | None, strategy: str | None = None) -> bool:
    if not isinstance(stock, dict):
        return False
    resolved_strategy = strategy or stock.get("strategy")
    return _is_scalp_strategy(resolved_strategy) and _is_scalp_simulator_target(stock)


def _boolish_true(value) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_scalp_sim_ai_budget_target(stock: dict | None, strategy: str | None = None) -> bool:
    if not _rule_bool("SCALP_SIM_AI_BUDGET_ENABLED", False):
        return False
    if not _is_scalp_simulated_position(stock, strategy):
        return False
    return not _boolish_true((stock or {}).get("actual_order_submitted"))


def _scalp_sim_ai_bucket(value, *, step: float = 0.25) -> int:
    try:
        numeric = _safe_float(value, 0.0)
        if step <= 0:
            return int(round(numeric * 100))
        return int(math.floor(numeric / step))
    except Exception:
        return 0


def _build_scalp_sim_ai_feature_signature(
    stock: dict,
    *,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    market_signature,
    is_critical_zone: bool,
    near_ai_exit_band: bool,
    near_safe_profit_band: bool,
) -> str:
    drawdown = _safe_float(peak_profit, 0.0) - _safe_float(profit_rate, 0.0)
    score_bucket = int(_safe_float(current_ai_score, 0.0) // 5)
    market_hash = str(abs(hash(str(market_signature))) % 100000)
    return "|".join(
        [
            f"p:{_scalp_sim_ai_bucket(profit_rate)}",
            f"pk:{_scalp_sim_ai_bucket(peak_profit)}",
            f"dd:{_scalp_sim_ai_bucket(drawdown)}",
            f"score5:{score_bucket}",
            f"critical:{int(bool(is_critical_zone))}",
            f"near_exit:{int(bool(near_ai_exit_band))}",
            f"near_safe:{int(bool(near_safe_profit_band))}",
            f"ra:{stock.get('reversal_add_state') or '-'}",
            f"ofi:{stock.get('holding_flow_ofi_regime') or stock.get('ofi_regime') or '-'}",
            f"m:{market_hash}",
        ]
    )


def _scalp_sim_ai_budget_usage(now_ts: float | None = None) -> int:
    now = float(now_ts or time.time())
    cutoff = now - 60.0
    with ENTRY_LOCK:
        _SCALP_SIM_AI_CALL_TIMES[:] = [ts for ts in _SCALP_SIM_AI_CALL_TIMES if float(ts or 0) >= cutoff]
        return len(_SCALP_SIM_AI_CALL_TIMES)


def _record_scalp_sim_ai_budget_call(now_ts: float | None = None) -> int:
    now = float(now_ts or time.time())
    with ENTRY_LOCK:
        _SCALP_SIM_AI_CALL_TIMES.append(now)
    return _scalp_sim_ai_budget_usage(now)


def _resolve_scalp_sim_ai_budget_decision(
    stock: dict,
    *,
    strategy: str | None,
    now_ts: float,
    profit_rate: float,
    peak_profit: float,
    held_sec: float,
    current_ai_score: float,
    market_signature,
    is_critical_zone: bool,
    near_ai_exit_band: bool,
    near_safe_profit_band: bool,
) -> dict:
    if not _is_scalp_sim_ai_budget_target(stock, strategy):
        return {"action": "call", "target": False}

    max_calls = max(0, _rule_int("SCALP_SIM_AI_MAX_CALLS_PER_MIN", 10))
    max_cd = max(1, _rule_int("SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC", 180))
    critical = bool(is_critical_zone or near_ai_exit_band or near_safe_profit_band)
    signature = _build_scalp_sim_ai_feature_signature(
        stock,
        profit_rate=profit_rate,
        peak_profit=peak_profit,
        current_ai_score=current_ai_score,
        market_signature=market_signature,
        is_critical_zone=is_critical_zone,
        near_ai_exit_band=near_ai_exit_band,
        near_safe_profit_band=near_safe_profit_band,
    )
    last_signature = str(stock.get("scalp_sim_ai_last_feature_signature") or "")
    last_live_call_at = _safe_float(stock.get("scalp_sim_ai_last_live_call_at"), 0.0)
    elapsed_live_sec = max(0.0, float(now_ts or time.time()) - last_live_call_at) if last_live_call_at > 0 else None
    first_review = last_live_call_at <= 0 or not stock.get("scalp_sim_ai_last_action")
    state_changed = signature != last_signature
    max_cooldown_expired = elapsed_live_sec is None or elapsed_live_sec >= max_cd
    used = _scalp_sim_ai_budget_usage(now_ts)
    common = {
        "target": True,
        "feature_signature": signature,
        "last_feature_signature": last_signature or "-",
        "state_changed": state_changed,
        "first_review": first_review,
        "critical": critical,
        "elapsed_live_sec": None if elapsed_live_sec is None else round(elapsed_live_sec, 2),
        "held_sec": int(_safe_float(held_sec, 0.0)),
        "budget_used_per_min": used,
        "budget_cap_per_min": max_calls,
        "last_ai_action": stock.get("scalp_sim_ai_last_action") or stock.get("last_ai_action") or "-",
        "last_ai_score": stock.get("scalp_sim_ai_last_score") or _safe_int(current_ai_score, 0),
    }

    if not first_review and not state_changed and not critical and not max_cooldown_expired:
        return {
            **common,
            "action": "reuse",
            "reuse_reason": "unchanged_feature_signature",
        }

    if max_calls > 0 and used >= max_calls:
        if critical:
            return {
                **common,
                "action": "call",
                "call_reason": "sim_ai_critical_bypass",
                "critical_bypass": True,
            }
        if _rule_bool("SCALP_SIM_AI_DEFERRED_REVIEW_ENABLED", True):
            return {
                **common,
                "action": "defer",
                "defer_reason": "sim_ai_budget_exhausted",
            }
        return {
            **common,
            "action": "reuse",
            "reuse_reason": "budget_exhausted_deferred_disabled",
        }

    if first_review:
        call_reason = "first_sim_holding_review"
    elif critical:
        call_reason = "critical_zone"
    elif state_changed:
        call_reason = "feature_signature_changed"
    elif max_cooldown_expired:
        call_reason = "max_cooldown_expired"
    else:
        call_reason = "scheduled_review"
    return {**common, "action": "call", "call_reason": call_reason, "critical_bypass": False}


def _is_any_simulated_position(stock: dict | None, strategy: str | None = None) -> bool:
    return _is_swing_simulated_position(stock, strategy) or _is_scalp_simulated_position(stock, strategy)


def _is_simulation_alert_context(stock: dict | None, strategy: str | None = None) -> bool:
    if _is_any_simulated_position(stock, strategy):
        return True
    resolved_strategy = strategy or ((stock or {}).get("strategy") if isinstance(stock, dict) else None)
    return _is_swing_live_order_dry_run(resolved_strategy)


def _resolve_telegram_audience_for_stock(
    stock: dict | None,
    strategy: str | None = None,
    *,
    default: str = "VIP_ALL",
) -> str:
    return "ADMIN_ONLY" if _is_simulation_alert_context(stock, strategy) else default


def _should_publish_watching_buy_analysis_telegram(
    stock: dict | None,
    strategy: str | None,
    ai_score,
    *,
    buy_score_threshold=None,
) -> tuple[bool, str]:
    if _is_simulation_alert_context(stock, strategy):
        return False, "simulation_context"
    if bool((stock or {}).get("scalp_sim_candidate_window_expansion")):
        return False, "scalp_sim_candidate_window_expansion"
    if (
        str((stock or {}).get("wait6579_probe_canary_source") or "") == "score65_74_recovery_probe"
        or _is_score65_74_recovery_probe_entry_unlocked(stock)
    ):
        return False, "score65_74_recovery_probe"
    if _is_scalp_strategy(strategy):
        threshold = _safe_float(
            buy_score_threshold,
            _rule_float("BUY_SCORE_THRESHOLD", 75.0),
        )
        if _safe_float(ai_score, 0.0) < threshold:
            return False, "below_buy_score_threshold"
    return True, "publish_allowed"


def _active_runtime_status(stock: dict | None) -> bool:
    status = str((stock or {}).get("status") or "").strip().upper()
    return bool(status) and status not in {"COMPLETED", "EXPIRED"}


def _price_tracking_key(stock: dict | None, code: str) -> str:
    if _is_swing_intraday_probe_target(stock):
        probe_id = str((stock or {}).get("probe_id") or "").strip()
        if probe_id:
            return f"swing_probe:{probe_id}"
    if _is_scalp_simulator_target(stock):
        sim_id = str((stock or {}).get("sim_record_id") or "").strip()
        if sim_id:
            return f"scalp_sim:{sim_id}"
    return str(code or "").strip()[:6]


def _json_safe_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(v) for v in value]
    return str(value)


def _scalp_simulator_active_targets(targets=None) -> list[dict]:
    source = targets if targets is not None else ACTIVE_TARGETS
    return [
        t for t in (source or [])
        if _is_scalp_simulator_target(t) and _active_runtime_status(t)
    ]


def persist_scalp_simulator_state(targets=None) -> None:
    try:
        active_positions = [
            _json_safe_value(dict(target))
            for target in _scalp_simulator_active_targets(targets)
        ]
        payload = {
            "schema_version": 1,
            "simulation_book": SCALP_SIMULATION_BOOK,
            "owner": _scalp_live_simulator_owner(),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "active_positions": active_positions,
        }
        SCALP_SIM_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = SCALP_SIM_STATE_PATH.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(SCALP_SIM_STATE_PATH)
    except Exception as exc:
        log_error(f"[SCALP_SIM_STATE] persist failed: {exc}")


def restore_scalp_simulator_targets(targets=None) -> int:
    if not _is_scalp_live_simulator_enabled() or not SCALP_SIM_STATE_PATH.exists():
        return 0
    target_list = targets if targets is not None else ACTIVE_TARGETS
    if target_list is None:
        return 0
    try:
        payload = json.loads(SCALP_SIM_STATE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log_error(f"[SCALP_SIM_STATE] restore failed: {exc}")
        return 0
    rows = payload.get("active_positions") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return 0
    restored = 0
    existing_ids = {
        str((t or {}).get("sim_record_id") or "").strip()
        for t in target_list
        if _is_scalp_simulator_target(t)
    }
    for row in rows:
        if not isinstance(row, dict) or not _active_runtime_status(row):
            continue
        sim_id = str(row.get("sim_record_id") or "").strip()
        if sim_id and sim_id in existing_ids:
            continue
        code = str(row.get("code") or "").strip()[:6]
        if not code:
            continue
        name = str(row.get("name") or "").strip().upper()
        if code == "123456" or name in {"TEST", "DUMMY", "MOCK"}:
            log_info(f"[SCALP_SIM_STATE] skipped synthetic simulator target code={code} name={name or '-'}")
            continue
        row["code"] = code
        row["strategy"] = "SCALPING"
        row["simulation_book"] = SCALP_SIMULATION_BOOK
        row["scalp_live_simulator"] = True
        row["simulation_owner"] = row.get("simulation_owner") or _scalp_live_simulator_owner()
        row["actual_order_submitted"] = False
        row["simulated_order"] = True
        target_list.append(row)
        if sim_id:
            existing_ids.add(sim_id)
        restored += 1
    if restored:
        log_info(f"[SCALP_SIM_STATE] restored active simulator targets={restored}")
    return restored


def _swing_probe_active_targets(targets=None) -> list[dict]:
    source = targets if targets is not None else ACTIVE_TARGETS
    return [
        t for t in (source or [])
        if _is_swing_intraday_probe_target(t) and _active_runtime_status(t)
    ]


def _read_swing_intraday_probe_state_active_count() -> int:
    if not SWING_INTRADAY_PROBE_STATE_PATH.exists():
        return 0
    try:
        payload = json.loads(SWING_INTRADAY_PROBE_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return 0
    rows = payload.get("active_positions") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return 0
    return sum(1 for row in rows if isinstance(row, dict) and _active_runtime_status(row))


def _log_swing_probe_state_event(stage: str, **fields) -> None:
    try:
        emit_pipeline_event(
            "ENTRY_PIPELINE",
            "SWING_PROBE_STATE",
            "-",
            stage,
            fields={
                "simulation_book": SWING_INTRADAY_PROBE_BOOK,
                "simulation_owner": _swing_intraday_probe_owner(),
                **fields,
            },
        )
    except Exception as exc:
        log_error(f"[SWING_PROBE_STATE] event emit failed stage={stage}: {exc}")


def persist_swing_intraday_probe_state(targets=None, *, allow_empty_overwrite: bool = False, reason: str = "snapshot") -> None:
    if not _rule_bool("SWING_INTRADAY_PROBE_PERSIST_ENABLED", True):
        return
    try:
        active_positions = [
            _json_safe_value(dict(target))
            for target in _swing_probe_active_targets(targets)
        ]
        existing_active_count = _read_swing_intraday_probe_state_active_count()
        if (
            not active_positions
            and existing_active_count > 0
            and not allow_empty_overwrite
        ):
            _log_swing_probe_state_event(
                "swing_probe_state_empty_overwrite_blocked",
                reason=reason,
                existing_active_count=existing_active_count,
                new_active_count=0,
            )
            return
        payload = {
            "schema_version": 2,
            "simulation_book": SWING_INTRADAY_PROBE_BOOK,
            "owner": _swing_intraday_probe_owner(),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "persist_reason": reason,
            "active_positions": active_positions,
            "same_symbol_loss_reentry_cooldowns": _active_swing_same_symbol_loss_reentry_cooldowns(),
        }
        SWING_INTRADAY_PROBE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = SWING_INTRADAY_PROBE_STATE_PATH.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(SWING_INTRADAY_PROBE_STATE_PATH)
        if reason != "snapshot":
            _log_swing_probe_state_event(
                "swing_probe_state_persisted",
                reason=reason,
                simulation_book=SWING_INTRADAY_PROBE_BOOK,
                simulation_owner=_swing_intraday_probe_owner(),
                active_count=len(active_positions),
                allow_empty_overwrite=allow_empty_overwrite,
                **_build_observation_contract_fields("ops_volume_diagnostic"),
            )
    except Exception as exc:
        log_error(f"[SWING_PROBE_STATE] persist failed: {exc}")


def restore_swing_intraday_probe_targets(targets=None) -> int:
    if (
        not _is_swing_intraday_probe_enabled()
        or not _rule_bool("SWING_INTRADAY_PROBE_PERSIST_ENABLED", True)
        or not SWING_INTRADAY_PROBE_STATE_PATH.exists()
    ):
        return 0
    target_list = targets if targets is not None else ACTIVE_TARGETS
    if target_list is None:
        return 0
    try:
        payload = json.loads(SWING_INTRADAY_PROBE_STATE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log_error(f"[SWING_PROBE_STATE] restore failed: {exc}")
        return 0
    cooldown_rows = payload.get("same_symbol_loss_reentry_cooldowns") if isinstance(payload, dict) else {}
    if isinstance(cooldown_rows, dict):
        now_ts = time.time()
        day_key = _swing_probe_daily_key(now_ts)
        restored_cooldowns = 0
        for key, row in cooldown_rows.items():
            if not isinstance(row, dict):
                continue
            code = str(row.get("code") or "").strip()[:6]
            strategy = normalize_strategy(row.get("strategy") or "")
            if not code or not _is_swing_strategy(strategy):
                continue
            if str(row.get("date") or "") != day_key:
                continue
            resolved_key = _swing_same_symbol_loss_reentry_key(code, strategy, now_ts)
            restored_row = dict(row)
            restored_row["code"] = code
            restored_row["strategy"] = strategy
            restored_row["date"] = day_key
            _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS[resolved_key] = restored_row
            restored_cooldowns += 1
        if restored_cooldowns:
            _log_swing_probe_state_event(
                "swing_same_symbol_loss_reentry_cooldowns_restored",
                restored_count=restored_cooldowns,
            )
    rows = payload.get("active_positions") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return 0
    stored_count = sum(1 for row in rows if isinstance(row, dict) and _active_runtime_status(row))
    restored = 0
    existing_ids = {
        str((t or {}).get("probe_id") or "").strip()
        for t in target_list
        if _is_swing_intraday_probe_target(t)
    }
    for row in rows:
        if not isinstance(row, dict) or not _active_runtime_status(row):
            continue
        probe_id = str(row.get("probe_id") or "").strip()
        if probe_id and probe_id in existing_ids:
            continue
        code = str(row.get("code") or "").strip()[:6]
        if not code:
            continue
        name = str(row.get("name") or "").strip().upper()
        if code == "123456" or name in {"TEST", "DUMMY", "MOCK"}:
            log_info(f"[SWING_PROBE_STATE] skipped synthetic probe target code={code} name={name or '-'}")
            continue
        strategy = normalize_strategy(row.get("strategy") or "KOSPI_ML")
        if not _is_swing_strategy(strategy):
            continue
        row["code"] = code
        row["strategy"] = strategy
        row["simulation_book"] = SWING_INTRADAY_PROBE_BOOK
        row["simulation_owner"] = row.get("simulation_owner") or _swing_intraday_probe_owner()
        row["swing_intraday_probe"] = True
        row["swing_live_order_dry_run"] = True
        row["actual_order_submitted"] = False
        row["simulated_order"] = True
        row["broker_order_forbidden"] = True
        row["msg_audience"] = "ADMIN_ONLY"
        row["added_time"] = _safe_float(row.get("added_time"), time.time())
        target_list.append(row)
        if probe_id:
            existing_ids.add(probe_id)
        restored += 1
    if restored or stored_count:
        log_info(f"[SWING_PROBE_STATE] restored active probe targets={restored}")
        _log_swing_probe_state_event(
            "swing_probe_state_restored",
            restored_count=restored,
            stored_active_count=stored_count,
            target_count_after=len(_swing_probe_active_targets(target_list)),
        )
    return restored


def _simulated_order_no(prefix: str, code: str) -> str:
    return f"{prefix}-{code}-{int(time.time() * 1000)}-{uuid4().hex[:6]}"


def _swing_probe_event_fields(stock: dict | None = None, **extra) -> dict:
    stock = stock or {}
    fields = {
        "simulation_book": SWING_INTRADAY_PROBE_BOOK,
        "simulation_owner": _swing_intraday_probe_owner(),
        "swing_intraday_probe": True,
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": "in_memory_probe_only",
        "probe_id": stock.get("probe_id"),
        "probe_origin_stage": stock.get("probe_origin_stage"),
        "probe_arm": stock.get("probe_arm"),
        "evidence_quality": stock.get("evidence_quality"),
        "evidence_quality_weight": stock.get("evidence_quality_weight"),
        "source_record_id": stock.get("source_record_id"),
    }
    fields.update(extra)
    return fields


def _swing_probe_daily_key(now_ts: float | None = None) -> str:
    try:
        return datetime.fromtimestamp(float(now_ts or time.time())).date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def _swing_same_symbol_loss_reentry_key(code: str, strategy: str | None, now_ts: float | None = None) -> str:
    day_key = _swing_probe_daily_key(now_ts)
    norm_code = str(code or "").strip()[:6]
    strategy_norm = normalize_strategy(strategy or "")
    return f"{day_key}:{strategy_norm}:{norm_code}"


def _is_swing_loss_reentry_stop_rule(exit_rule: str | None) -> bool:
    value = str(exit_rule or "").strip().lower()
    if not value:
        return False
    return any(
        marker in value
        for marker in (
            "stop_loss",
            "stop-loss",
            "hard_stop",
            "protect_stop",
            "protect_hard",
            "emergency_stop",
            "loss_cut",
        )
    )


def _prune_swing_same_symbol_loss_reentry_cooldowns(now_ts: float | None = None) -> None:
    day_key = _swing_probe_daily_key(now_ts)
    stale_keys = [
        key for key, row in _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS.items()
        if not isinstance(row, dict) or str(row.get("date") or "") != day_key
    ]
    for key in stale_keys:
        _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS.pop(key, None)


def _active_swing_same_symbol_loss_reentry_cooldowns(now_ts: float | None = None) -> dict:
    _prune_swing_same_symbol_loss_reentry_cooldowns(now_ts)
    return {
        key: _json_safe_value(dict(row))
        for key, row in _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS.items()
        if isinstance(row, dict)
    }


def evaluate_swing_same_symbol_loss_reentry_guard(
    code: str,
    strategy: str | None,
    now_ts: float | None = None,
    source: str | None = None,
) -> dict:
    now_value = _safe_float(now_ts, time.time())
    strategy_norm = normalize_strategy(strategy or "")
    norm_code = str(code or "").strip()[:6]
    base = {
        "guard_family": "swing_same_symbol_loss_reentry_guard",
        "strategy": strategy_norm,
        "code": norm_code,
        "source": source or "-",
        "enabled": _rule_bool("SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED", True),
        "allowed": True,
        "reason": "allowed",
        "cooldown_remaining_sec": 0,
        "blocked_until_ts": 0.0,
        "last_loss_exit_rule": "-",
        "last_loss_profit_rate": "-",
        "loss_count": 0,
    }
    if not base["enabled"]:
        base["reason"] = "disabled"
        return base
    if not norm_code or not _is_swing_strategy(strategy_norm):
        base["reason"] = "not_applicable"
        return base
    _prune_swing_same_symbol_loss_reentry_cooldowns(now_value)
    key = _swing_same_symbol_loss_reentry_key(norm_code, strategy_norm, now_value)
    row = _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS.get(key) or {}
    blocked_until = _safe_float(row.get("blocked_until_ts"), 0.0)
    remaining = max(0, int(math.ceil(blocked_until - now_value))) if blocked_until > now_value else 0
    base.update(
        {
            "cooldown_key": key,
            "blocked_until_ts": blocked_until,
            "cooldown_remaining_sec": remaining,
            "last_loss_exit_rule": row.get("last_loss_exit_rule") or "-",
            "last_loss_profit_rate": row.get("last_loss_profit_rate", "-"),
            "loss_count": _safe_int(row.get("loss_count"), 0),
            "source_book": row.get("source_book") or "-",
            "source_probe_id": row.get("source_probe_id") or "-",
        }
    )
    if remaining > 0:
        base["allowed"] = False
        base["reason"] = "same_symbol_loss_reentry_cooldown"
    return base


def _swing_loss_reentry_guard_log_fields(decision: dict | None) -> dict:
    decision = decision or {}
    return {
        "guard_family": decision.get("guard_family") or "swing_same_symbol_loss_reentry_guard",
        "guard_allowed": bool(decision.get("allowed", True)),
        "guard_reason": decision.get("reason") or "-",
        "cooldown_key": decision.get("cooldown_key") or "-",
        "cooldown_remaining_sec": _safe_int(decision.get("cooldown_remaining_sec"), 0),
        "blocked_until_ts": decision.get("blocked_until_ts") or 0,
        "last_loss_exit_rule": decision.get("last_loss_exit_rule") or "-",
        "last_loss_profit_rate": decision.get("last_loss_profit_rate", "-"),
        "loss_count": _safe_int(decision.get("loss_count"), 0),
    }


def _emit_swing_reentry_counterfactual_after_loss(
    stock: dict,
    code: str,
    origin_stage: str,
    decision: dict,
    *,
    runtime: dict | None = None,
    ws_data: dict | None = None,
    extra_fields: dict | None = None,
) -> None:
    if not _rule_bool("SWING_SAME_SYMBOL_LOSS_REENTRY_COUNTERFACTUAL_ENABLED", True):
        return
    runtime = runtime or {}
    ws_data = ws_data or {}
    extra_fields = extra_fields or {}
    curr_price = _safe_int(ws_data.get("curr") or runtime.get("curr_price"), 0)
    _log_entry_pipeline(
        stock,
        code,
        "swing_reentry_counterfactual_after_loss",
        **_swing_probe_event_fields(
            stock,
            runtime_effect="counterfactual_only",
            probe_origin_stage=origin_stage,
            discard_reason="same_symbol_loss_reentry_cooldown",
            strategy=decision.get("strategy") or normalize_strategy((runtime or {}).get("strategy") or (stock or {}).get("strategy")),
            curr_price=curr_price,
            actual_order_submitted=False,
            broker_order_forbidden=True,
            counterfactual_in_real_like_ev=False,
            **_swing_loss_reentry_guard_log_fields(decision),
            **extra_fields,
        ),
    )


def _record_swing_same_symbol_loss_reentry_cooldown(
    stock: dict | None,
    code: str,
    strategy: str | None,
    *,
    exit_rule: str | None,
    profit_rate,
    now_ts: float | None = None,
    actual_order_submitted: bool | None = None,
    source_stage: str = "exit",
) -> dict | None:
    if not _rule_bool("SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED", True):
        return None
    strategy_norm = normalize_strategy(strategy or (stock or {}).get("strategy"))
    if not _is_swing_strategy(strategy_norm):
        return None
    norm_code = str(code or (stock or {}).get("code") or "").strip()[:6]
    if not norm_code:
        return None
    now_value = _safe_float(now_ts, time.time())
    profit = _safe_float(profit_rate, 0.0)
    _prune_swing_same_symbol_loss_reentry_cooldowns(now_value)
    key = _swing_same_symbol_loss_reentry_key(norm_code, strategy_norm, now_value)
    existing = _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS.get(key) or {}
    blocked_until_existing = _safe_float(existing.get("blocked_until_ts"), 0.0)
    if profit >= 0:
        if blocked_until_existing <= now_value:
            _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS.pop(key, None)
        return None

    loss_count = _safe_int(existing.get("loss_count"), 0) + 1
    threshold = _rule_float("SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT", -2.5)
    consecutive_trigger = max(1, _rule_int("SWING_SAME_SYMBOL_LOSS_REENTRY_CONSECUTIVE_LOSSES", 2))
    cooldown_sec = max(0, _rule_int("SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC", 3600))
    stop_loss_trigger = _is_swing_loss_reentry_stop_rule(exit_rule) and profit <= threshold
    consecutive_loss_trigger = loss_count >= consecutive_trigger
    should_block = stop_loss_trigger or consecutive_loss_trigger
    blocked_until = max(blocked_until_existing, now_value + cooldown_sec) if should_block and cooldown_sec > 0 else blocked_until_existing
    row = {
        "date": _swing_probe_daily_key(now_value),
        "strategy": strategy_norm,
        "code": norm_code,
        "loss_count": loss_count,
        "blocked_until_ts": blocked_until,
        "last_loss_ts": now_value,
        "last_loss_exit_rule": exit_rule or "-",
        "last_loss_profit_rate": profit,
        "source_stage": source_stage,
        "source_book": (stock or {}).get("simulation_book") or ("real_order" if actual_order_submitted else "swing_dry_run"),
        "source_probe_id": (stock or {}).get("probe_id") or "-",
        "actual_order_submitted": bool(actual_order_submitted),
        "trigger": "stop_loss" if stop_loss_trigger else ("consecutive_losses" if consecutive_loss_trigger else "loss_observed"),
    }
    _SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS[key] = row
    if should_block:
        _log_entry_pipeline(
            stock or {},
            norm_code,
            "swing_same_symbol_loss_reentry_cooldown",
            guard_family="swing_same_symbol_loss_reentry_guard",
            strategy=strategy_norm,
            cooldown_sec=cooldown_sec,
            blocked_until_ts=blocked_until,
            exit_rule=exit_rule or "-",
            profit_rate=f"{profit:+.2f}",
            loss_count=loss_count,
            trigger=row["trigger"],
            source_book=row["source_book"],
            source_probe_id=row["source_probe_id"],
            actual_order_submitted=bool(actual_order_submitted),
            broker_order_forbidden=not bool(actual_order_submitted),
        )
    return row


def _active_swing_probe_count_for_symbol(code: str, strategy: str | None = None) -> int:
    norm = str(code or "").strip()[:6]
    strategy_norm = normalize_strategy(strategy or "")
    return sum(
        1
        for target in (ACTIVE_TARGETS or [])
        if _is_swing_intraday_probe_target(target)
        and _active_runtime_status(target)
        and str((target or {}).get("code") or "").strip()[:6] == norm
        and (not strategy_norm or normalize_strategy((target or {}).get("strategy")) == strategy_norm)
    )


def _active_swing_probe_count_for_origin(origin_stage: str) -> int:
    stage = str(origin_stage or "").strip()
    if not stage:
        return 0
    return sum(
        1
        for target in (ACTIVE_TARGETS or [])
        if _is_swing_intraday_probe_target(target)
        and _active_runtime_status(target)
        and str((target or {}).get("probe_origin_stage") or "").strip() == stage
    )


def _has_duplicate_swing_probe(code: str, strategy: str, origin_stage: str) -> bool:
    norm = str(code or "").strip()[:6]
    stage = str(origin_stage or "").strip()
    strategy_norm = normalize_strategy(strategy)
    return any(
        _is_swing_intraday_probe_target(target)
        and _active_runtime_status(target)
        and str((target or {}).get("code") or "").strip()[:6] == norm
        and normalize_strategy((target or {}).get("strategy")) == strategy_norm
        and str((target or {}).get("probe_origin_stage") or "").strip() == stage
        for target in (ACTIVE_TARGETS or [])
    )


def _log_swing_probe_discard(stock, code, origin_stage: str, reason: str, **fields) -> bool:
    now_ts = _safe_float(fields.pop("_now_ts", None), time.time())
    min_interval = max(0, _rule_int("SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC", 60))
    record_id = str(
        (stock or {}).get("id")
        or (stock or {}).get("source_record_id")
        or fields.get("source_record_id")
        or ""
    )
    key = (str(code or "").strip()[:6], record_id, str(origin_stage or ""), str(reason or ""))
    last_ts = _SWING_PROBE_DISCARD_LOG_TS.get(key)
    if min_interval > 0 and last_ts is not None and (now_ts - last_ts) < min_interval:
        return False
    _SWING_PROBE_DISCARD_LOG_TS[key] = now_ts
    _log_entry_pipeline(
        stock,
        code,
        "swing_probe_discarded",
        **_swing_probe_event_fields(
            stock,
            probe_origin_stage=origin_stage,
            discard_reason=reason,
            **fields,
        ),
    )
    return True


def _sim_virtual_budget_krw() -> int:
    return max(0, _rule_int("SIM_VIRTUAL_BUDGET_KRW", 10_000_000))


def _describe_sim_virtual_buy_capacity(curr_price: int, ratio: float, *, max_budget: int = 0) -> dict:
    virtual_budget = _sim_virtual_budget_krw()
    effective_ratio = float(ratio or 0.0)
    if curr_price <= 0:
        return {
            "qty": 1,
            "target_budget": 0,
            "safe_budget": 0,
            "safety_ratio": 0.0,
            "virtual_budget_krw": virtual_budget,
            "effective_ratio": effective_ratio,
        }
    target_budget, safe_budget, qty, safety_ratio = kiwoom_orders.describe_buy_capacity(
        curr_price,
        virtual_budget,
        effective_ratio,
        max_budget=max_budget,
    )
    return {
        "qty": max(1, _safe_int(qty, 0)),
        "target_budget": target_budget,
        "safe_budget": safe_budget,
        "safety_ratio": safety_ratio,
        "virtual_budget_krw": virtual_budget,
        "effective_ratio": effective_ratio,
    }


def _resolve_swing_probe_qty(stock: dict, curr_price: int, ratio: float) -> dict:
    capacity = _describe_sim_virtual_buy_capacity(curr_price, ratio, max_budget=0)
    qty = _safe_int(capacity.get("qty"), 1)
    if curr_price <= 0:
        return {
            "qty": qty,
            "qty_source": "sim_virtual_budget_dynamic_formula",
            "qty_reason": "missing_curr_price_virtual_min_qty",
            "virtual_budget_override": True,
            "virtual_budget_krw": capacity.get("virtual_budget_krw"),
            "budget_authority": "sim_virtual_not_real_orderable_amount",
            "ratio": f"{float(ratio or 0.0):.4f}",
        }
    return {
        "qty": qty,
        "qty_source": "sim_virtual_budget_dynamic_formula",
        "qty_reason": "probe_uses_sim_virtual_budget_with_live_qty_formula",
        "virtual_budget_override": True,
        "virtual_budget_krw": capacity.get("virtual_budget_krw"),
        "target_budget": capacity.get("target_budget"),
        "safe_budget": capacity.get("safe_budget"),
        "safety_ratio": f"{float(capacity.get('safety_ratio') or 0.0):.4f}",
        "virtual_notional_used_krw": int(curr_price * qty),
        "budget_authority": "sim_virtual_not_real_orderable_amount",
        "ratio": f"{float(capacity.get('effective_ratio') or 0.0):.4f}",
    }


def maybe_start_swing_intraday_probe(
    *,
    stock: dict,
    code: str,
    ws_data: dict,
    origin_stage: str,
    runtime: dict | None = None,
    evidence_quality: str = "blocked_stage_intraday_probe",
    probe_arm: str | None = None,
    extra_fields: dict | None = None,
) -> bool:
    """Create an observe-only swing virtual holding from a blocked live-runtime stage."""
    runtime = runtime or {}
    extra_fields = extra_fields or {}
    strategy = normalize_strategy(runtime.get("strategy") or stock.get("strategy"))
    if not _is_swing_strategy(strategy):
        return False
    if not _is_swing_intraday_probe_enabled():
        return False
    if ACTIVE_TARGETS is None:
        _log_swing_probe_discard(
            stock,
            code,
            origin_stage,
            "active_targets_unbound",
            strategy=strategy,
            _now_ts=runtime.get("now_ts"),
        )
        return False

    norm_code = str(code or stock.get("code") or "").strip()[:6]
    curr_price = _safe_int((ws_data or {}).get("curr") or runtime.get("curr_price"), 0)
    if not norm_code or curr_price <= 0:
        _log_swing_probe_discard(
            stock,
            norm_code or code,
            origin_stage,
            "missing_code_or_price",
            strategy=strategy,
            curr_price=curr_price,
            _now_ts=runtime.get("now_ts"),
        )
        return False

    max_per_symbol = max(0, _rule_int("SWING_INTRADAY_PROBE_MAX_PER_SYMBOL", 1))
    symbol_count = _active_swing_probe_count_for_symbol(norm_code, strategy)
    if max_per_symbol > 0 and symbol_count >= max_per_symbol:
        _log_swing_probe_discard(
            stock,
            norm_code,
            origin_stage,
            "max_per_symbol_reached",
            strategy=strategy,
            active_symbol_probes=symbol_count,
            _now_ts=runtime.get("now_ts"),
        )
        return False

    if _has_duplicate_swing_probe(norm_code, strategy, origin_stage):
        _log_swing_probe_discard(
            stock,
            norm_code,
            origin_stage,
            "duplicate_origin_stage",
            strategy=strategy,
            _now_ts=runtime.get("now_ts"),
        )
        return False

    guard_decision = evaluate_swing_same_symbol_loss_reentry_guard(
        norm_code,
        strategy,
        runtime.get("now_ts"),
        source=f"probe:{origin_stage}",
    )
    if not guard_decision.get("allowed", True):
        logged = _log_swing_probe_discard(
            stock,
            norm_code,
            origin_stage,
            "same_symbol_loss_reentry_cooldown",
            strategy=strategy,
            **_swing_loss_reentry_guard_log_fields(guard_decision),
            _now_ts=runtime.get("now_ts"),
        )
        if logged:
            _emit_swing_reentry_counterfactual_after_loss(
                stock,
                norm_code,
                origin_stage,
                guard_decision,
                runtime=runtime,
                ws_data=ws_data,
                extra_fields={"evidence_quality": evidence_quality, **extra_fields},
            )
        return False

    if str(origin_stage or "").strip() == "blocked_swing_score_vpw":
        score_open_cap = max(0, _rule_int("SWING_INTRADAY_PROBE_SCORE_VPW_MAX_OPEN", 4))
        score_open_count = _active_swing_probe_count_for_origin("blocked_swing_score_vpw")
        if score_open_cap > 0 and score_open_count >= score_open_cap:
            _log_swing_probe_discard(
                stock,
                norm_code,
                origin_stage,
                "origin_quota_reached",
                strategy=strategy,
                origin_open_count=score_open_count,
                origin_open_cap=score_open_cap,
                _now_ts=runtime.get("now_ts"),
            )
            return False

    max_open = max(0, _rule_int("SWING_INTRADAY_PROBE_MAX_OPEN", 10))
    open_count = len(_swing_probe_active_targets())
    if max_open > 0 and open_count >= max_open:
        _log_swing_probe_discard(
            stock,
            norm_code,
            origin_stage,
            "max_open_reached",
            strategy=strategy,
            open_count=open_count,
            _now_ts=runtime.get("now_ts"),
        )
        return False

    day_key = _swing_probe_daily_key(runtime.get("now_ts"))
    restored_today = sum(
        1
        for target in _swing_probe_active_targets()
        if str((target or {}).get("probe_date") or "") == day_key
    )
    created_today = max(int(_SWING_PROBE_DAILY_CREATED.get(day_key, 0) or 0), restored_today)
    max_daily = max(0, _rule_int("SWING_INTRADAY_PROBE_MAX_DAILY", 30))
    if max_daily > 0 and created_today >= max_daily:
        _log_swing_probe_discard(
            stock,
            norm_code,
            origin_stage,
            "max_daily_reached",
            strategy=strategy,
            created_today=created_today,
            _now_ts=runtime.get("now_ts"),
        )
        return False

    ratio = _safe_float(runtime.get("ratio"), 0.0)
    if ratio <= 0:
        if strategy == "KOSDAQ_ML":
            ratio = _rule_float("INVEST_RATIO_KOSDAQ_MIN", 0.05)
        else:
            ratio = _rule_float("INVEST_RATIO_KOSPI_MIN", 0.10)
    qty_details = _resolve_swing_probe_qty(stock, curr_price, ratio)
    qty = max(1, _safe_int(qty_details.get("qty"), 1))
    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    now_ts = _safe_float(runtime.get("now_ts"), time.time())
    probe_id = _simulated_order_no("SWINGPROBE", norm_code)
    source_signal_date = stock.get("date")
    entry_date = datetime.fromtimestamp(now_ts).date().isoformat()
    probe_target = dict(stock)
    probe_target.update(
        {
            "code": norm_code,
            "strategy": strategy,
            "position_tag": normalize_position_tag(strategy, stock.get("position_tag")),
            "status": "HOLDING",
            "date": entry_date,
            "source_signal_date": source_signal_date,
            "entry_mode": f"swing_probe_{origin_stage}",
            "order_time": now_ts,
            "order_price": curr_price,
            "requested_buy_qty": qty,
            "entry_requested_qty": qty,
            "entry_filled_qty": qty,
            "entry_fill_amount": int(curr_price * qty),
            "buy_price": curr_price,
            "buy_qty": qty,
            "buy_time": now_ts,
            "holding_started_at": now_ts,
            "swing_live_order_dry_run": True,
            "swing_intraday_probe": True,
            "simulation_book": SWING_INTRADAY_PROBE_BOOK,
            "simulation_owner": _swing_intraday_probe_owner(),
            "simulated_order": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "probe_id": probe_id,
            "source_record_id": stock.get("id"),
            "probe_origin_stage": origin_stage,
            "probe_arm": probe_arm or origin_stage,
            "evidence_quality": evidence_quality,
            "evidence_quality_weight": _safe_float(extra_fields.get("evidence_quality_weight"), 0.70),
            "probe_date": day_key,
            "msg_audience": "ADMIN_ONLY",
        }
    )
    for key in ("pending_buy_msg", "pending_sell_msg", "pending_entry_orders", "odno", "sell_odno", "add_odno", "pending_add_order"):
        probe_target.pop(key, None)

    with ENTRY_LOCK:
        ACTIVE_TARGETS.append(probe_target)
        if isinstance(HIGHEST_PRICES, dict):
            HIGHEST_PRICES[_price_tracking_key(probe_target, norm_code)] = curr_price
        _SWING_PROBE_DAILY_CREATED[day_key] = created_today + 1
    if EVENT_BUS is not None:
        EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [norm_code], "source": "swing_intraday_probe"})

    common_fields = _swing_probe_event_fields(
        probe_target,
        strategy=strategy,
        position_tag=probe_target.get("position_tag"),
        curr_price=curr_price,
        assumed_fill_price=curr_price,
        best_ask=best_ask,
        best_bid=best_bid,
        would_qty=qty,
        qty=qty,
        qty_source=qty_details.get("qty_source"),
        qty_reason=qty_details.get("qty_reason"),
        gap_pct=extra_fields.get("gap_pct", extra_fields.get("fluctuation", runtime.get("fluctuation"))),
        runtime_score_proxy=extra_fields.get("runtime_score_proxy", runtime.get("current_ai_score")),
        score=extra_fields.get("score"),
        v_pw=extra_fields.get("v_pw", runtime.get("current_vpw")),
        gatekeeper_action=extra_fields.get("gatekeeper_action"),
        gatekeeper_allow_entry=extra_fields.get("gatekeeper_allow_entry"),
        gatekeeper_eval_ms=extra_fields.get("gatekeeper_eval_ms"),
        market_regime=extra_fields.get("market_regime"),
        market_regime_block_reason=extra_fields.get("market_regime_block_reason"),
        counterfactual_after_gap=bool(extra_fields.get("counterfactual_after_gap", False)),
        source_signal_date=source_signal_date,
        entry_date=entry_date,
        **{k: v for k, v in qty_details.items() if k not in {"qty", "qty_source", "qty_reason"}},
    )
    _log_entry_pipeline(stock, norm_code, "swing_probe_entry_candidate", **common_fields)
    _log_entry_pipeline(
        probe_target,
        norm_code,
        "swing_probe_holding_started",
        **common_fields,
    )
    persist_swing_intraday_probe_state(reason="probe_holding_started")
    return True


def _mark_swing_simulated_holding(stock, code, curr_price, requested_qty, entry_mode, entry_orders):
    now_ts = time.time()
    _mutate_stock_state(
        stock,
        set_fields={
            "status": "HOLDING",
            "entry_mode": entry_mode,
            "order_time": now_ts,
            "order_price": curr_price,
            "requested_buy_qty": requested_qty,
            "entry_requested_qty": requested_qty,
            "entry_filled_qty": requested_qty,
            "entry_fill_amount": int(curr_price * requested_qty),
            "buy_price": curr_price,
            "buy_qty": requested_qty,
            "buy_time": now_ts,
            "holding_started_at": now_ts,
            "swing_live_order_dry_run": True,
            "simulation_owner": _swing_live_order_dry_run_owner(),
            "actual_order_submitted": False,
            "simulated_entry_orders": entry_orders,
            "msg_audience": "ADMIN_ONLY",
        },
        pop_fields=[
            "pending_buy_msg",
            "pending_entry_orders",
            "odno",
            "pending_add_order",
        ],
    )
    _log_entry_pipeline(
        stock,
        code,
        "swing_sim_holding_started",
        strategy=stock.get("strategy"),
        entry_mode=entry_mode,
        requested_qty=requested_qty,
        assumed_fill_price=curr_price,
        legs=len(entry_orders or []),
        simulation_owner=_swing_live_order_dry_run_owner(),
        actual_order_submitted=False,
        runtime_effect="in_memory_holding_only",
    )


def _scalp_sim_event_fields(**extra) -> dict:
    fields = {
        "simulation_book": SCALP_SIMULATION_BOOK,
        "simulation_owner": _scalp_live_simulator_owner(),
        "simulation_fill_policy": _scalp_live_simulator_fill_policy(),
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "calibration_authority": "equal_weight",
    }
    fields.update(extra)
    return fields


def _scalp_sim_candidate_window_daily_key(now_ts: float | None = None) -> str:
    try:
        return datetime.fromtimestamp(float(now_ts or time.time())).date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def _scalp_sim_candidate_window_context_fields(source: dict | None) -> dict:
    if not isinstance(source, dict) or not bool(source.get("scalp_sim_candidate_window_expansion")):
        return {}
    keys = (
        "scalp_sim_candidate_window_expansion",
        "scalp_sim_candidate_window_source_stage",
        "scalp_sim_candidate_window_blocked_reason",
        "scalp_sim_candidate_window_original_action",
        "scalp_sim_candidate_window_original_score",
        "scalp_sim_candidate_window_original_reason",
        "scalp_sim_candidate_window_date",
    )
    fields = {key: source.get(key) for key in keys if source.get(key) not in (None, "")}
    fields.update(
        {
            "would_real_submit": False,
            "decision_authority": "sim_observation_only",
        }
    )
    return fields


def _has_active_scalp_simulator_position(code: str) -> bool:
    norm = str(code or "").strip()[:6]
    if not norm:
        return False
    return any(
        str((target or {}).get("code") or "").strip()[:6] == norm
        and _is_scalp_simulator_target(target)
        and _active_runtime_status(target)
        for target in (ACTIVE_TARGETS or [])
    )


def _scalp_sim_buy_quote_touch(ws_data: dict, limit_price: int) -> tuple[bool, int, int, int]:
    limit_price = _safe_int(limit_price, 0)
    curr_price = _safe_int((ws_data or {}).get("curr"), 0)
    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    if limit_price <= 0:
        return False, 0, best_ask, best_bid
    if best_ask > 0 and best_ask <= limit_price:
        return True, best_ask, best_ask, best_bid
    if curr_price > 0 and curr_price <= limit_price:
        return True, curr_price, best_ask, best_bid
    return False, 0, best_ask, best_bid


def _scalp_sim_buy_signal_inclusive_fill(ws_data: dict, limit_price: int) -> dict:
    limit_price = _safe_int(limit_price, 0)
    curr_price = _safe_int((ws_data or {}).get("curr"), 0)
    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    would_limit_fill, limit_fill_price, _, _ = _scalp_sim_buy_quote_touch(ws_data or {}, limit_price)
    if best_ask > 0:
        fill_price = best_ask
        fill_source = "best_ask"
    elif curr_price > 0:
        fill_price = curr_price
        fill_source = "curr"
    elif limit_price > 0:
        fill_price = limit_price
        fill_source = "limit_price_fallback"
    else:
        fill_price = 0
        fill_source = "unpriced"
    return {
        "fill_price": fill_price,
        "fill_source": fill_source,
        "best_ask": best_ask,
        "best_bid": best_bid,
        "curr_price": curr_price,
        "limit_price": limit_price,
        "would_limit_fill": bool(would_limit_fill),
        "limit_fill_price": limit_fill_price,
    }


def _scalp_sim_sell_fill_price(ws_data: dict, curr_price: int) -> tuple[int, int, int]:
    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    fill_price = best_bid if best_bid > 0 else _safe_int(curr_price, 0)
    return fill_price, best_ask, best_bid


def _initialize_scalp_sim_holding_defaults(stock: dict, buy_price: int) -> None:
    strategy = "SCALPING"
    position_tag = normalize_position_tag(strategy, stock.get("position_tag"))
    set_fields = {
        "strategy": strategy,
        "position_tag": position_tag,
        "last_ai_reviewed_at": stock.get("last_ai_reviewed_at"),
        "near_ai_exit_started_at": stock.get("near_ai_exit_started_at"),
        "actual_order_submitted": False,
        "simulated_order": True,
    }
    if is_default_position_tag(strategy, position_tag):
        base_stop = _rule_float("SCALP_PRESET_HARD_STOP_PCT", -0.7)
        base_grace = _rule_int("SCALP_PRESET_HARD_STOP_GRACE_SEC", 0)
        base_emergency = _rule_float("SCALP_PRESET_HARD_STOP_EMERGENCY_PCT", min(base_stop - 0.5, -1.2))
        set_fields.update(
            {
                "exit_mode": "SCALP_PRESET_TP",
                "preset_tp_price": kiwoom_utils.get_target_price_up(int(buy_price), 1.5)
                if buy_price > 0
                else 0,
                "hard_stop_pct": base_stop,
                "hard_stop_grace_sec": base_grace,
                "hard_stop_emergency_pct": base_emergency,
                "protect_profit_pct": None,
                "ai_review_done": False,
                "ai_review_score": None,
                "ai_review_action": None,
                "exit_requested": False,
                "exit_order_type": None,
                "exit_order_time": None,
            }
        )
    _mutate_stock_state(stock, set_fields=set_fields)


def _mark_scalp_simulated_holding(
    stock: dict,
    code: str,
    fill_price: int,
    qty: int,
    *,
    now_ts: float,
    best_ask: int,
    best_bid: int,
    fill_source: str | None = None,
    would_limit_fill: bool | None = None,
    limit_fill_price: int | None = None,
) -> None:
    qty = max(1, _safe_int(qty, 1))
    fill_price = _safe_int(fill_price, 0)
    _initialize_scalp_sim_holding_defaults(stock, fill_price)
    _mutate_stock_state(
        stock,
        set_fields={
            "status": "HOLDING",
            "order_time": now_ts,
            "order_price": fill_price,
            "requested_buy_qty": qty,
            "entry_requested_qty": qty,
            "entry_filled_qty": qty,
            "entry_fill_amount": int(fill_price * qty),
            "entry_fill_quality": "FULL_FILL",
            "buy_price": fill_price,
            "buy_qty": qty,
            "buy_time": now_ts,
            "holding_started_at": now_ts,
            "scalp_sim_filled_at": now_ts,
            "actual_order_submitted": False,
            "simulated_order": True,
        },
        pop_fields=[
            "pending_buy_msg",
            "pending_entry_orders",
            "odno",
            "pending_add_order",
        ],
    )
    price_key = _price_tracking_key(stock, code)
    if isinstance(HIGHEST_PRICES, dict):
        with ENTRY_LOCK:
            HIGHEST_PRICES[price_key] = max(_safe_int(HIGHEST_PRICES.get(price_key), 0), fill_price)
    ord_no = str(stock.get("scalp_sim_pending_ord_no") or _simulated_order_no("SIMBUY", code))
    _log_entry_pipeline(
        stock,
        code,
        "scalp_sim_buy_order_assumed_filled",
        **_scalp_sim_event_fields(
            threshold_family="pre_submit_price_guard",
            entry_adm_candidate_id=stock.get("entry_adm_candidate_id"),
            sim_record_id=stock.get("sim_record_id"),
            sim_parent_record_id=stock.get("sim_parent_record_id"),
            ord_no=ord_no,
            qty=qty,
            limit_price=stock.get("scalp_sim_entry_limit_price"),
            assumed_fill_price=fill_price,
            fill_source=fill_source or "unknown",
            best_ask=best_ask,
            best_bid=best_bid,
            would_limit_fill=bool(would_limit_fill),
            limit_fill_price=limit_fill_price,
            would_submit_stage="order_leg_sent",
            runtime_effect="simulated_holding_only",
            **_scalp_sim_candidate_window_context_fields(stock),
        ),
    )
    _log_entry_pipeline(
        stock,
        code,
        "scalp_sim_holding_started",
        **_scalp_sim_event_fields(
            threshold_family="statistical_action_weight",
            entry_adm_candidate_id=stock.get("entry_adm_candidate_id"),
            sim_record_id=stock.get("sim_record_id"),
            sim_parent_record_id=stock.get("sim_parent_record_id"),
            requested_qty=qty,
            assumed_fill_price=fill_price,
            fill_source=fill_source or "unknown",
            entry_fill_quality="FULL_FILL",
            would_limit_fill=bool(would_limit_fill),
            preset_tp_price=stock.get("preset_tp_price", 0),
            runtime_effect="simulated_holding_only",
            **_scalp_sim_candidate_window_context_fields(stock),
        ),
    )
    persist_scalp_simulator_state()


def handle_scalp_simulator_pending_entry(stock: dict, code: str, ws_data: dict, *, now_ts: float | None = None) -> bool:
    if not _is_scalp_simulator_target(stock):
        return False
    if str(stock.get("status") or "").upper() != SCALP_SIM_PENDING_STATUS:
        return False
    now_ts = now_ts or time.time()
    limit_price = _safe_int(stock.get("scalp_sim_entry_limit_price"), 0)
    qty = _safe_int(stock.get("scalp_sim_entry_qty"), _rule_int("SCALP_LIVE_SIMULATOR_QTY", 1) or 1)
    fill_info = _scalp_sim_buy_signal_inclusive_fill(ws_data or {}, limit_price)
    fill_price = _safe_int(fill_info.get("fill_price"), 0)
    if fill_price <= 0:
        if not stock.get("scalp_sim_unpriced_logged"):
            _mutate_stock_state(stock, set_fields={"scalp_sim_unpriced_logged": True})
            _log_entry_pipeline(
                stock,
                code,
                "scalp_sim_entry_unpriced",
                **_scalp_sim_event_fields(
                    threshold_family="pre_submit_price_guard",
                    sim_record_id=stock.get("sim_record_id"),
                    sim_parent_record_id=stock.get("sim_parent_record_id"),
                    qty=qty,
                    limit_price=limit_price,
                    fill_source=fill_info.get("fill_source"),
                    curr_price=fill_info.get("curr_price"),
                    best_ask=fill_info.get("best_ask"),
                    best_bid=fill_info.get("best_bid"),
                ),
            )
            persist_scalp_simulator_state()
        return True
    _mark_scalp_simulated_holding(
        stock,
        code,
        fill_price,
        qty,
        now_ts=now_ts,
        best_ask=_safe_int(fill_info.get("best_ask"), 0),
        best_bid=_safe_int(fill_info.get("best_bid"), 0),
        fill_source=str(fill_info.get("fill_source") or "unknown"),
        would_limit_fill=bool(fill_info.get("would_limit_fill")),
        limit_fill_price=_safe_int(fill_info.get("limit_fill_price"), 0),
    )
    return True


def _resolve_scalp_sim_entry_qty(stock: dict, ws_data: dict, runtime: dict) -> dict:
    configured_qty = _rule_int("SCALP_LIVE_SIMULATOR_QTY", 0)
    if configured_qty > 0:
        virtual_budget = _sim_virtual_budget_krw()
        return {
            "qty": configured_qty,
            "qty_source": "fixed_config",
            "uncapped_qty": configured_qty,
            "cap_applied": False,
            "qty_reason": "fixed_config",
            "virtual_budget_override": True,
            "virtual_budget_krw": virtual_budget,
            "virtual_notional_used_krw": 0,
            "budget_authority": "sim_virtual_not_real_orderable_amount",
        }

    curr_price = _safe_int(
        (ws_data or {}).get("curr")
        or stock.get("target_buy_price")
        or stock.get("entry_armed_target_buy_price"),
        0,
    )
    ratio = _safe_float((runtime or {}).get("ratio"), 0.0)
    effective_ratio = ratio if ratio > 0 else 1.0
    budget_cap = int(_rule("SCALPING_MAX_BUY_BUDGET_KRW", 0) or 0)
    capacity = _describe_sim_virtual_buy_capacity(curr_price, effective_ratio, max_budget=budget_cap)
    qty = _safe_int(capacity.get("qty"), 1)
    if curr_price <= 0:
        return {
            "qty": qty,
            "qty_source": "sim_virtual_budget_dynamic_formula",
            "uncapped_qty": qty,
            "cap_applied": False,
            "qty_reason": "missing_price",
            "curr_price": curr_price,
            "ratio": f"{effective_ratio:.4f}",
            "virtual_budget_override": True,
            "virtual_budget_krw": capacity.get("virtual_budget_krw"),
            "virtual_notional_used_krw": 0,
            "budget_authority": "sim_virtual_not_real_orderable_amount",
        }

    return {
        "qty": qty,
        "qty_source": "sim_virtual_budget_dynamic_formula",
        "uncapped_qty": qty,
        "cap_applied": False,
        "qty_reason": "sim_uses_virtual_budget_with_live_qty_formula",
        "curr_price": curr_price,
        "ratio": f"{effective_ratio:.4f}",
        "target_budget": capacity.get("target_budget"),
        "safe_budget": capacity.get("safe_budget"),
        "safety_ratio": f"{float(capacity.get('safety_ratio') or 0.0):.4f}",
        "budget_cap": budget_cap if budget_cap > 0 else "-",
        "virtual_budget_override": True,
        "virtual_budget_krw": capacity.get("virtual_budget_krw"),
        "virtual_notional_used_krw": int(curr_price * qty),
        "budget_authority": "sim_virtual_not_real_orderable_amount",
    }


def _maybe_arm_scalp_sim_candidate_window(
    *,
    stock: dict,
    code: str,
    ws_data: dict,
    runtime: dict,
    ai_decision: dict | None = None,
    ai_score=None,
    source_stage: str,
    blocked_reason: str,
    ai_engine=None,
) -> bool:
    if not _is_scalp_sim_candidate_window_expansion_enabled():
        return False
    if not isinstance(stock, dict):
        return False
    strategy = normalize_strategy((runtime or {}).get("strategy") or stock.get("strategy"))
    if strategy != "SCALPING":
        return False
    score_value = _safe_float(ai_score if ai_score is not None else (ai_decision or {}).get("score"), 0.0)
    min_score = _rule_int("SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE", 55)
    max_score = _rule_int("SCALP_SIM_CANDIDATE_WINDOW_MAX_SCORE", 100)
    if score_value < float(min_score or 0) or score_value > float(max_score or 100):
        return False
    now_ts = _safe_float((runtime or {}).get("now_ts"), time.time())
    day_key = _scalp_sim_candidate_window_daily_key(now_ts)
    max_open = max(0, _rule_int("SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN", 20))
    open_count = len(_scalp_simulator_active_targets())
    if max_open > 0 and open_count >= max_open:
        _log_entry_pipeline(
            stock,
            code,
            "scalp_sim_candidate_window_discarded",
            **_scalp_sim_event_fields(
                threshold_family="entry_mechanical_momentum",
                discard_reason="max_open_reached",
                source_stage=source_stage,
                blocked_reason=blocked_reason,
                ai_score=f"{score_value:.1f}",
                open_count=open_count,
                max_open=max_open,
                runtime_effect="sim_observation_skipped",
                decision_authority="sim_observation_only",
            ),
        )
        return False
    restored_today = sum(
        1
        for target in _scalp_simulator_active_targets()
        if str((target or {}).get("scalp_sim_candidate_window_date") or "") == day_key
    )
    created_today = max(int(_SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED.get(day_key, 0) or 0), restored_today)
    max_daily = max(0, _rule_int("SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY", 80))
    if max_daily > 0 and created_today >= max_daily:
        _log_entry_pipeline(
            stock,
            code,
            "scalp_sim_candidate_window_discarded",
            **_scalp_sim_event_fields(
                threshold_family="entry_mechanical_momentum",
                discard_reason="max_daily_reached",
                source_stage=source_stage,
                blocked_reason=blocked_reason,
                ai_score=f"{score_value:.1f}",
                created_today=created_today,
                max_daily=max_daily,
                runtime_effect="sim_observation_skipped",
                decision_authority="sim_observation_only",
            ),
        )
        return False

    action = str((ai_decision or {}).get("action") or stock.get("last_watching_ai_action") or "WAIT").upper()
    reason = str((ai_decision or {}).get("reason") or stock.get("last_watching_ai_reason") or "")[:240]
    _mutate_stock_state(
        stock,
        set_fields={
            "scalp_sim_candidate_window_expansion": True,
            "scalp_sim_candidate_window_source_stage": str(source_stage or "-"),
            "scalp_sim_candidate_window_blocked_reason": str(blocked_reason or "-"),
            "scalp_sim_candidate_window_original_action": action,
            "scalp_sim_candidate_window_original_score": f"{score_value:.1f}",
            "scalp_sim_candidate_window_original_reason": reason,
            "scalp_sim_candidate_window_date": day_key,
        },
    )
    sim_runtime = dict(runtime or {})
    sim_runtime.update(
        {
            "strategy": "SCALPING",
            "is_trigger": True,
            "now_ts": now_ts,
            "current_ai_score": score_value,
            "scalp_sim_candidate_window_expansion": True,
        }
    )
    armed = maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        code,
        ws_data or {},
        sim_runtime,
        ai_engine=ai_engine,
    )
    if armed:
        _SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED[day_key] = created_today + 1
    return bool(armed)


def maybe_arm_scalp_live_simulator_from_buy_signal(
    stock: dict,
    code: str,
    ws_data: dict,
    runtime: dict,
    *,
    ai_engine=None,
) -> bool:
    if not _is_scalp_live_simulator_enabled():
        return False
    strategy = normalize_strategy(runtime.get("strategy") or stock.get("strategy"))
    if strategy != "SCALPING":
        return False
    if not bool(runtime.get("is_trigger")):
        return False
    current_ai_score = _safe_float(runtime.get("current_ai_score"), 0.0)
    now_ts = _safe_float(runtime.get("now_ts"), time.time())
    if _has_active_scalp_simulator_position(code):
        _log_entry_pipeline(
            stock,
            code,
            "scalp_sim_duplicate_buy_signal",
            **_scalp_sim_event_fields(
                threshold_family="entry_mechanical_momentum",
                sim_parent_record_id=stock.get("id"),
                ai_score=f"{current_ai_score:.1f}",
            ),
        )
        return False
    limit_price = _safe_int(
        stock.get("target_buy_price") or stock.get("entry_armed_target_buy_price"),
        0,
    )
    qty_details = _resolve_scalp_sim_entry_qty(stock, ws_data or {}, runtime or {})
    qty = max(1, _safe_int(qty_details.get("qty"), 1))
    qty_log_fields = {k: v for k, v in qty_details.items() if k != "qty"}
    pre_ai_context_fields = _scalp_pre_ai_gate_context_log_fields(
        runtime.get("scalp_pre_ai_gate_context") if isinstance(runtime, dict) else {}
    )
    entry_adm_candidate_id = _entry_adm_candidate_id(stock, code)
    sim_record_id = _simulated_order_no("SCALPSIM", code)
    sim_ord_no = _simulated_order_no("SIMBUY", code)
    sim_target = dict(stock)
    sim_target.update(
        {
            "id": None,
            "code": str(code or "").strip()[:6],
            "strategy": "SCALPING",
            "status": SCALP_SIM_PENDING_STATUS,
            "simulation_book": SCALP_SIMULATION_BOOK,
            "simulation_owner": _scalp_live_simulator_owner(),
            "simulation_fill_policy": _scalp_live_simulator_fill_policy(),
            "scalp_live_simulator": True,
            "simulated_order": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "entry_adm_candidate_id": entry_adm_candidate_id,
            "sim_record_id": sim_record_id,
            "sim_parent_record_id": stock.get("id"),
            "scalp_sim_entry_limit_price": limit_price,
            "scalp_sim_entry_qty": qty,
            "scalp_sim_entry_qty_source": qty_details.get("qty_source"),
            "scalp_sim_entry_uncapped_qty": qty_details.get("uncapped_qty", qty),
            "scalp_sim_entry_qty_reason": qty_details.get("qty_reason"),
            "scalp_sim_entry_armed_at": now_ts,
            "scalp_sim_pending_ord_no": sim_ord_no,
            "order_time": now_ts,
            "order_price": limit_price,
            "requested_buy_qty": qty,
            "entry_requested_qty": qty,
            "entry_filled_qty": 0,
            "entry_fill_amount": 0,
            "buy_price": 0,
            "buy_qty": 0,
            "entry_mode": stock.get("entry_mode") or "scalp_sim_ai_buy_all",
            "rt_ai_prob": current_ai_score / 100.0,
            "msg_audience": "ADMIN_ONLY",
            **_scalp_sim_candidate_window_context_fields(stock),
        }
    )
    planned_orders = [{"price": limit_price, "qty": qty, "tif": "DAY"}]
    curr_price = _safe_int((ws_data or {}).get("curr") or limit_price, 0)
    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    latency_gate = {
        "orders": planned_orders,
        "target_buy_price": limit_price,
        "order_price": limit_price,
        "latency_guarded_order_price": limit_price,
        "normal_defensive_order_price": limit_price,
        "price_resolution_reason": "scalp_sim_initial_limit",
        "latency_state": str((runtime or {}).get("latency_state") or "SIMULATED"),
        "decision": "SIMULATED_BUY_SIGNAL",
        "reason": "scalp_live_simulator",
        "ws_age_ms": 0,
        "ws_jitter_ms": 0,
        "spread_ratio": _spread_bps_from_ws(ws_data or {}, curr_price) or 0.0,
        "quote_stale": False,
    }
    ai_price_canary_touched = False
    if ai_engine is not None and hasattr(ai_engine, "evaluate_scalping_entry_price"):
        planned_orders, ai_price_canary_touched = _apply_entry_ai_price_canary(
            stock=sim_target,
            code=code,
            strategy="SCALPING",
            ws_data=ws_data or {},
            ai_engine=ai_engine,
            latency_gate=latency_gate,
            planned_orders=planned_orders,
            curr_price=curr_price,
            best_bid=best_bid,
            best_ask=best_ask,
        )
    if ai_price_canary_touched:
        if not planned_orders:
            _log_entry_pipeline(
                sim_target,
                code,
                "scalp_sim_entry_ai_price_skip_order",
                **_scalp_sim_event_fields(
                    threshold_family="pre_submit_price_guard",
                    entry_adm_candidate_id=entry_adm_candidate_id,
                    sim_record_id=sim_record_id,
                    sim_parent_record_id=stock.get("id"),
                    ai_entry_price_canary_action=latency_gate.get("ai_entry_price_canary_action"),
                    ai_entry_price_canary_confidence=latency_gate.get("ai_entry_price_canary_confidence"),
                    ai_entry_price_canary_reason=latency_gate.get("ai_entry_price_canary_reason"),
                    runtime_effect="simulated_order_skipped",
                    **_scalp_sim_candidate_window_context_fields(sim_target),
                ),
            )
            persist_scalp_simulator_state()
            return True
        adjusted_limit_price = _safe_int((planned_orders[0] or {}).get("price"), limit_price)
        if adjusted_limit_price > 0:
            limit_price = adjusted_limit_price
            sim_target.update(
                {
                    "scalp_sim_entry_limit_price": limit_price,
                    "order_price": limit_price,
                    "entry_ai_price_canary_applied": True,
                    "entry_ai_price_canary_action": latency_gate.get("ai_entry_price_canary_action"),
                    "entry_ai_price_canary_confidence": latency_gate.get("ai_entry_price_canary_confidence"),
                    "entry_ai_price_canary_reason": latency_gate.get("ai_entry_price_canary_reason"),
                    "entry_price_resolution_reason": latency_gate.get("price_resolution_reason"),
                }
            )
            _log_entry_pipeline(
                sim_target,
                code,
                "scalp_sim_entry_ai_price_applied",
                **_scalp_sim_event_fields(
                    threshold_family="pre_submit_price_guard",
                    entry_adm_candidate_id=entry_adm_candidate_id,
                    sim_record_id=sim_record_id,
                    sim_parent_record_id=stock.get("id"),
                    original_limit_price=stock.get("target_buy_price") or stock.get("entry_armed_target_buy_price"),
                    adjusted_limit_price=limit_price,
                    ai_entry_price_canary_action=latency_gate.get("ai_entry_price_canary_action"),
                    ai_entry_price_canary_confidence=latency_gate.get("ai_entry_price_canary_confidence"),
                    ai_entry_price_canary_reason=latency_gate.get("ai_entry_price_canary_reason"),
                    runtime_effect="simulated_entry_price_only",
                    **_scalp_sim_candidate_window_context_fields(sim_target),
                ),
            )
    sim_submit_revalidation_fields = _build_entry_submit_revalidation_fields(
        ws_data or {},
        latency_gate,
        now_ts=now_ts,
    )
    sim_price_snapshot = _build_entry_price_snapshot_fields(
        latency_gate,
        request_price=limit_price,
        curr_price=curr_price,
        best_bid=best_bid,
        best_ask=best_ask,
    )
    if sim_submit_revalidation_fields.get("entry_submit_revalidation_warning"):
        _log_entry_pipeline(
            sim_target,
            code,
            "scalp_sim_entry_submit_revalidation_warning",
            **_scalp_sim_event_fields(
                threshold_family="pre_submit_price_guard",
                entry_adm_candidate_id=entry_adm_candidate_id,
                sim_record_id=sim_record_id,
                sim_parent_record_id=stock.get("id"),
                **sim_submit_revalidation_fields,
                **sim_price_snapshot,
                **_scalp_sim_candidate_window_context_fields(sim_target),
            ),
        )
    if _is_passive_probe_stale_submit_block(sim_submit_revalidation_fields):
        _log_entry_pipeline(
            sim_target,
            code,
            "scalp_sim_entry_submit_revalidation_block",
            **_scalp_sim_event_fields(
                threshold_family="pre_submit_price_guard",
                entry_adm_candidate_id=entry_adm_candidate_id,
                sim_record_id=sim_record_id,
                sim_parent_record_id=stock.get("id"),
                block_reason="stale_context_or_quote",
                runtime_effect="simulated_order_skipped",
                **sim_submit_revalidation_fields,
                **sim_price_snapshot,
                **_scalp_sim_candidate_window_context_fields(sim_target),
            ),
        )
        _emit_scalp_entry_adm_snapshot(
            sim_target,
            code,
            "scalp_sim_entry_submit_revalidation_block",
            ai_score=current_ai_score,
            chosen_action="SKIP_STALE",
            latency_gate=latency_gate,
            submit_fields=sim_submit_revalidation_fields,
            price_snapshot=sim_price_snapshot,
            actual_order_submitted=False,
            broker_order_forbidden=True,
            extra_fields={"sim_record_id": sim_record_id, "sim_parent_record_id": stock.get("id")},
        )
        persist_scalp_simulator_state()
        return True
    for key in ("pending_buy_msg", "pending_sell_msg", "pending_entry_orders", "odno", "sell_odno", "add_odno"):
        sim_target.pop(key, None)
    with ENTRY_LOCK:
        if ACTIVE_TARGETS is not None:
            ACTIVE_TARGETS.append(sim_target)
    if EVENT_BUS is not None:
        EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [code], "source": "scalp_live_simulator"})
    _log_entry_pipeline(
        stock,
        code,
        "scalp_sim_entry_armed",
        **_scalp_sim_event_fields(
            threshold_family="entry_mechanical_momentum",
            entry_adm_candidate_id=entry_adm_candidate_id,
            sim_record_id=sim_record_id,
            sim_parent_record_id=stock.get("id"),
            ai_score=f"{current_ai_score:.1f}",
            limit_price=limit_price,
            qty=qty,
            **qty_log_fields,
            **pre_ai_context_fields,
            **_scalp_sim_candidate_window_context_fields(sim_target),
        ),
    )
    _emit_scalp_entry_adm_snapshot(
        sim_target,
        code,
        "scalp_sim_entry_armed",
        ai_score=current_ai_score,
        latency_gate=latency_gate,
        submit_fields=sim_submit_revalidation_fields,
        price_snapshot=sim_price_snapshot,
        actual_order_submitted=False,
        broker_order_forbidden=True,
        extra_fields={"sim_record_id": sim_record_id, "sim_parent_record_id": stock.get("id")},
    )
    _log_entry_pipeline(
        stock,
        code,
        "scalp_sim_buy_order_virtual_pending",
        **_scalp_sim_event_fields(
            threshold_family="pre_submit_price_guard",
            entry_adm_candidate_id=entry_adm_candidate_id,
            sim_record_id=sim_record_id,
            sim_parent_record_id=stock.get("id"),
            ord_no=sim_ord_no,
            limit_price=limit_price,
            qty=qty,
            **qty_log_fields,
            **sim_submit_revalidation_fields,
            **sim_price_snapshot,
            **pre_ai_context_fields,
            would_submit_stage="order_leg_sent",
            runtime_effect="pending_virtual_fill",
            **_scalp_sim_candidate_window_context_fields(sim_target),
        ),
    )
    handled = handle_scalp_simulator_pending_entry(sim_target, code, ws_data or {}, now_ts=now_ts)
    persist_scalp_simulator_state()
    return handled


def _complete_scalp_simulated_sell(
    *,
    stock: dict,
    code: str,
    ws_data: dict | None,
    curr_price: int,
    now_ts: float,
    sell_reason_type: str,
    exit_rule: str | None,
    profit_rate: float,
) -> bool:
    if not _is_scalp_simulator_target(stock):
        return False
    buy_qty = _safe_int(stock.get("buy_qty"), 0)
    if buy_qty <= 0:
        _log_holding_pipeline(
            stock,
            code,
            "scalp_sim_sell_blocked_zero_qty",
            **_scalp_sim_event_fields(
                threshold_family="statistical_action_weight",
                entry_adm_candidate_id=stock.get("entry_adm_candidate_id"),
                sim_record_id=stock.get("sim_record_id"),
                sim_parent_record_id=stock.get("sim_parent_record_id"),
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                profit_rate=f"{profit_rate:+.2f}",
            ),
        )
        return True
    fill_price, best_ask, best_bid = _scalp_sim_sell_fill_price(ws_data or {}, curr_price)
    simulated_profit_rate = calculate_net_profit_rate(stock.get("buy_price"), fill_price)
    _mutate_stock_state(
        stock,
        set_fields={
            "status": "COMPLETED",
            "sell_price": fill_price,
            "sell_qty": buy_qty,
            "sell_time": now_ts,
            "profit_rate": simulated_profit_rate,
            "simulated_sell_order": True,
            "actual_order_submitted": False,
        },
    )
    if isinstance(HIGHEST_PRICES, dict):
        with ENTRY_LOCK:
            HIGHEST_PRICES.pop(_price_tracking_key(stock, code), None)
    _log_holding_pipeline(
        stock,
        code,
        "scalp_sim_sell_order_assumed_filled",
        **_scalp_sim_event_fields(
            threshold_family="statistical_action_weight",
            entry_adm_candidate_id=stock.get("entry_adm_candidate_id"),
            sim_record_id=stock.get("sim_record_id"),
            sim_parent_record_id=stock.get("sim_parent_record_id"),
            sell_reason_type=sell_reason_type,
            exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
            exit_decision_source=stock.get("last_exit_decision_source") or "MANUAL",
            qty=buy_qty,
            assumed_fill_price=fill_price,
            best_ask=best_ask,
            best_bid=best_bid,
            buy_price=stock.get("buy_price"),
            profit_rate=f"{simulated_profit_rate:+.2f}",
            trigger_profit_rate=f"{profit_rate:+.2f}",
            would_submit_stage="sell_order_sent",
            runtime_effect="simulated_completed_only",
        ),
    )
    try:
        record_sim_post_sell_candidate(
            sim_record_id=stock.get("sim_record_id"),
            candidate_id=stock.get("entry_adm_candidate_id"),
            sim_parent_record_id=stock.get("sim_parent_record_id"),
            stock=stock,
            code=code,
            sell_time=datetime.fromtimestamp(float(now_ts)),
            buy_price=stock.get("buy_price"),
            sell_price=fill_price,
            profit_rate=simulated_profit_rate,
            buy_qty=buy_qty,
            exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
            sell_reason_type=sell_reason_type,
            trigger_profit_rate=profit_rate,
        )
    except Exception as exc:
        log_error(f"[SCALP_SIM_POST_SELL] candidate record failed: {exc}")
    persist_scalp_simulator_state()
    return True


def _coerce_optional_timestamp(value):
    """런타임/DB 경계 시각값을 epoch 초로 보수 변환한다.

    `None`, 빈 문자열, `NaT` 같은 결측 표기는 0으로 취급한다.
    """
    if value in (None, "", 0, "0"):
        return 0.0

    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() in {"nat", "nan", "none"}:
            return 0.0
        try:
            return datetime.fromisoformat(stripped).timestamp()
        except ValueError:
            return 0.0

    if isinstance(value, datetime):
        try:
            return float(value.timestamp())
        except (TypeError, ValueError, OSError, OverflowError):
            return 0.0

    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        try:
            converted = to_pydatetime()
        except Exception:
            return 0.0
        return _coerce_optional_timestamp(converted)

    timestamp_fn = getattr(value, "timestamp", None)
    if callable(timestamp_fn):
        text = str(value).strip().lower()
        if text in {"nat", "nan", "none"}:
            return 0.0
        try:
            return float(timestamp_fn())
        except (TypeError, ValueError, OSError, OverflowError):
            return 0.0

    return 0.0


def _lookup_latest_add_executed_timestamp(stock):
    if not DB or not stock.get('id'):
        return 0.0
    try:
        with DB.get_session() as session:
            row = (
                session.query(HoldingAddHistory.event_time)
                .filter(
                    HoldingAddHistory.recommendation_id == int(stock.get('id')),
                    HoldingAddHistory.event_type == 'EXECUTED',
                )
                .order_by(HoldingAddHistory.event_time.desc(), HoldingAddHistory.id.desc())
                .first()
            )
    except Exception as exc:
        log_error(
            f"[ADD_HISTORY] latest EXECUTED lookup failed "
            f"(id={stock.get('id')}, code={stock.get('code', '-')}): {exc}"
        )
        return 0.0
    if not row:
        return 0.0
    return _coerce_optional_timestamp(row[0])


def _resolve_last_add_timestamp(stock, *, now_ts=None):
    """Return the effective last scale-in fill timestamp.

    Runtime ``last_add_time`` and DB-backed ``last_add_at`` should normally
    match.  If one is accidentally refreshed later, prefer the older positive
    timestamp so post-add cooldown/grace cannot be extended indefinitely.
    """
    candidates = []
    try:
        last_add_time = float(stock.get('last_add_time', 0) or 0)
    except (TypeError, ValueError):
        last_add_time = 0.0
    if last_add_time > 0:
        candidates.append(last_add_time)
    if stock.get('last_add_at'):
        last_add_at = _coerce_optional_timestamp(stock.get('last_add_at'))
        if last_add_at > 0:
            candidates.append(last_add_at)
    oldest = min(candidates) if candidates else 0.0

    # If runtime state says an add exists but the available timestamp is very
    # recent, verify against persisted fill history.  This catches restart/sync
    # paths that accidentally refresh in-memory last_add_time/last_add_at and
    # would otherwise keep post-add grace active indefinitely.
    has_add_history = (
        str(stock.get('last_add_type') or '').strip()
        or _safe_int(stock.get('add_count'), 0) > 0
        or _safe_int(stock.get('pyramid_count'), 0) > 0
        or _safe_int(stock.get('avg_down_count'), 0) > 0
    )
    current_ts = float(now_ts if now_ts is not None else time.time())
    suspicious_recent = oldest <= 0 or (current_ts - oldest) < 600
    if has_add_history and suspicious_recent:
        history_ts = _lookup_latest_add_executed_timestamp(stock)
        if history_ts > 0:
            candidates.append(history_ts)
    return min(candidates) if candidates else 0.0


def _pyramid_post_add_trailing_grace(stock, now_ts):
    if str(stock.get('last_add_type') or '').upper() != 'PYRAMID':
        return False, 0, 0
    grace_sec = _rule_int('SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC', 0)
    if grace_sec <= 0:
        return False, 0, 0

    last_add = _resolve_last_add_timestamp(stock, now_ts=now_ts)
    if last_add <= 0:
        return False, 0, grace_sec

    elapsed_sec = max(0, int(float(now_ts or time.time()) - last_add))
    return elapsed_sec < grace_sec, elapsed_sec, grace_sec


def _log_pyramid_post_add_trailing_grace(stock, code, *, now_ts, exit_rule_candidate, profit_rate, peak_profit, drawdown):
    last_log = float(stock.get('last_pyramid_post_add_trailing_grace_log_ts', 0) or 0)
    if now_ts - last_log < 15:
        return
    active, elapsed_sec, grace_sec = _pyramid_post_add_trailing_grace(stock, now_ts)
    if not active:
        return
    _mutate_stock_state(stock, set_fields={'last_pyramid_post_add_trailing_grace_log_ts': now_ts})
    _log_holding_pipeline(
        stock,
        code,
        "pyramid_post_add_trailing_grace",
        exit_rule_candidate=exit_rule_candidate,
        profit_rate=f"{profit_rate:+.2f}",
        peak_profit=f"{peak_profit:+.2f}",
        drawdown=f"{drawdown:.2f}",
        elapsed_sec=elapsed_sec,
        grace_sec=grace_sec,
        last_add_type=stock.get('last_add_type', '-'),
    )


def _append_holding_price_sample(stock, *, now_ts, curr_price):
    if curr_price <= 0:
        return list(stock.get('holding_price_samples') or [])
    window_sec = max(1, _rule_int('SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC', 20))
    cutoff_ts = float(now_ts or time.time()) - window_sec
    samples = []
    for item in list(stock.get('holding_price_samples') or []):
        if not isinstance(item, dict):
            continue
        ts = _safe_float(item.get('ts'), 0.0)
        price = _safe_int(item.get('price'), 0)
        if ts >= cutoff_ts and price > 0:
            samples.append({'ts': ts, 'price': price})
    samples.append({'ts': float(now_ts or time.time()), 'price': int(curr_price)})
    samples = samples[-60:]
    _mutate_stock_state(stock, set_fields={'holding_price_samples': samples})
    return samples


def _median_price(values):
    cleaned = sorted(_safe_float(item, 0.0) for item in values if _safe_float(item, 0.0) > 0)
    if not cleaned:
        return 0.0
    mid = len(cleaned) // 2
    if len(cleaned) % 2:
        return cleaned[mid]
    return (cleaned[mid - 1] + cleaned[mid]) / 2.0


def _protect_trailing_break_confirmed(
    stock,
    code,
    *,
    now_ts,
    curr_price,
    trailing_stop_price,
    profit_rate,
    peak_profit,
):
    if not _rule_bool('SCALP_PROTECT_TRAILING_SMOOTH_ENABLED', True):
        return True
    emergency_pct = _rule_float('SCALP_PROTECT_TRAILING_EMERGENCY_PCT', -2.0)
    if profit_rate <= emergency_pct:
        return True

    samples = list(stock.get('holding_price_samples') or [])
    min_samples = max(1, _rule_int('SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES', 3))
    min_span_sec = max(0, _rule_int('SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC', 8))
    below_ratio_min = max(0.0, min(1.0, _rule_float('SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO', 0.67)))
    buffer_pct = max(0.0, _rule_float('SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT', 0.80))
    window_sec = max(1, _rule_int('SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC', 20))
    buffered_stop = float(trailing_stop_price) * (1.0 - (buffer_pct / 100.0))

    usable = [
        item for item in samples
        if isinstance(item, dict) and _safe_int(item.get('price'), 0) > 0
    ]
    prices = [_safe_int(item.get('price'), 0) for item in usable]
    if not usable:
        span_sec = 0
    else:
        ts_values = [_safe_float(item.get('ts'), 0.0) for item in usable]
        span_sec = max(0, int(max(ts_values) - min(ts_values)))
    median_price = _median_price(prices)
    below_count = sum(1 for price in prices if price <= buffered_stop)
    below_ratio = (below_count / len(prices)) if prices else 0.0
    confirmed = (
        len(prices) >= min_samples
        and span_sec >= min_span_sec
        and median_price <= buffered_stop
        and below_ratio >= below_ratio_min
    )
    if confirmed:
        _log_holding_pipeline(
            stock,
            code,
            "protect_trailing_smooth_confirmed",
            threshold_family="protect_trailing_smoothing",
            exit_rule_candidate="protect_trailing_stop",
            curr_price=curr_price,
            trailing_stop_price=f"{float(trailing_stop_price):.0f}",
            buffered_stop_price=f"{buffered_stop:.0f}",
            median_price=f"{median_price:.0f}",
            sample_count=len(prices),
            sample_span_sec=span_sec,
            below_ratio=f"{below_ratio:.2f}",
            min_below_ratio=f"{below_ratio_min:.2f}",
            window_sec=window_sec,
            min_span_sec=min_span_sec,
            min_samples=min_samples,
            buffer_pct=f"{buffer_pct:.2f}",
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            emergency_pct=f"{emergency_pct:+.2f}",
        )
        return True

    last_log = float(stock.get('last_protect_trailing_smooth_hold_log_ts', 0) or 0)
    if float(now_ts or time.time()) - last_log >= 5:
        _mutate_stock_state(stock, set_fields={'last_protect_trailing_smooth_hold_log_ts': float(now_ts or time.time())})
        _log_holding_pipeline(
            stock,
            code,
            "protect_trailing_smooth_hold",
            threshold_family="protect_trailing_smoothing",
            exit_rule_candidate="protect_trailing_stop",
            curr_price=curr_price,
            trailing_stop_price=f"{float(trailing_stop_price):.0f}",
            buffered_stop_price=f"{buffered_stop:.0f}",
            median_price=f"{median_price:.0f}",
            sample_count=len(prices),
            sample_span_sec=span_sec,
            below_ratio=f"{below_ratio:.2f}",
            min_below_ratio=f"{below_ratio_min:.2f}",
            window_sec=window_sec,
            min_span_sec=min_span_sec,
            min_samples=min_samples,
            buffer_pct=f"{buffer_pct:.2f}",
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            emergency_pct=f"{emergency_pct:+.2f}",
        )
    return False


def bind_state_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    event_bus=None,
    active_targets=None,
    cooldowns=None,
    alerted_stocks=None,
    highest_prices=None,
    last_ai_call_times=None,
    last_log_times=None,
    trading_rules=None,
    publish_gatekeeper_report=None,
    should_block_swing_entry=None,
    confirm_cancel_or_reload_remaining=None,
    send_exit_best_ioc=None,
    dual_persona_engine=None,
):
    global KIWOOM_TOKEN, DB, EVENT_BUS, ACTIVE_TARGETS, COOLDOWNS, ALERTED_STOCKS, HIGHEST_PRICES
    global LAST_AI_CALL_TIMES, LAST_LOG_TIMES, TRADING_RULES, PUBLISH_GATEKEEPER_REPORT
    global SHOULD_BLOCK_SWING_ENTRY, CONFIRM_CANCEL_OR_RELOAD_REMAINING, SEND_EXIT_BEST_IOC
    global DUAL_PERSONA_ENGINE

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if event_bus is not None:
        EVENT_BUS = event_bus
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if cooldowns is not None:
        COOLDOWNS = cooldowns
    if alerted_stocks is not None:
        ALERTED_STOCKS = alerted_stocks
    if highest_prices is not None:
        HIGHEST_PRICES = highest_prices
    if last_ai_call_times is not None:
        LAST_AI_CALL_TIMES = last_ai_call_times
    if last_log_times is not None:
        LAST_LOG_TIMES = last_log_times
    if trading_rules is not None:
        TRADING_RULES = trading_rules
    if publish_gatekeeper_report is not None:
        PUBLISH_GATEKEEPER_REPORT = publish_gatekeeper_report
    if should_block_swing_entry is not None:
        SHOULD_BLOCK_SWING_ENTRY = should_block_swing_entry
    if confirm_cancel_or_reload_remaining is not None:
        CONFIRM_CANCEL_OR_RELOAD_REMAINING = confirm_cancel_or_reload_remaining
    if send_exit_best_ioc is not None:
        SEND_EXIT_BEST_IOC = send_exit_best_ioc
    if dual_persona_engine is not None:
        DUAL_PERSONA_ENGINE = dual_persona_engine


def sanitize_pending_add_states(active_targets=None):
    """재시작/복구 시 pending add 정합성을 보수 정리합니다."""
    targets = active_targets if active_targets is not None else ACTIVE_TARGETS
    _sanitize_pending_add_states(targets)


def _publish_gatekeeper_report_proxy(stock, code, gatekeeper, allowed):
    if PUBLISH_GATEKEEPER_REPORT is None:
        return
    PUBLISH_GATEKEEPER_REPORT(stock, code, gatekeeper, allowed)


def _should_block_swing_entry(strategy):
    if SHOULD_BLOCK_SWING_ENTRY is None:
        return False, None
    return SHOULD_BLOCK_SWING_ENTRY(strategy)


def _confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    if CONFIRM_CANCEL_OR_RELOAD_REMAINING is None:
        return 0
    return CONFIRM_CANCEL_OR_RELOAD_REMAINING(code, orig_ord_no, token, expected_qty)


def _send_exit_best_ioc(code, qty, token):
    if SEND_EXIT_BEST_IOC is None:
        return {}
    return SEND_EXIT_BEST_IOC(code, qty, token)


def _format_entry_price_text(value):
    try:
        price = int(float(value))
    except (TypeError, ValueError):
        return "-"
    return f"{price:,}원"


def _translate_latency_state(value):
    return {
        "SAFE": "양호",
        "CAUTION": "주의",
        "DANGER": "위험",
    }.get(str(value or "").upper(), value or "-")


def _translate_entry_decision(value):
    return {
        "ALLOW_NORMAL": "기본 진입 허용",
        "REJECT_DANGER": "진입 보류",
        "REJECT": "진입 보류",
    }.get(str(value or "").upper(), value or "-")


def _translate_order_tag(value):
    return {
        "fallback_scout": "폐기된 탐색 주문",
        "fallback_main": "폐기된 본 주문",
        "fallback_single": "폐기된 fallback 주문",
    }.get(value, value or "주문")


def _translate_tif(value):
    return {
        "IOC": "즉시체결 우선",
        "DAY": "장중 유지",
    }.get(str(value or "").upper(), value or "-")


def _format_entry_order_line(order):
    return (
        f"- {_translate_order_tag(order.get('tag'))}: "
        f"{int(order.get('qty') or 0)}주 / "
        f"{_format_entry_price_text(order.get('price'))} / "
        f"{_translate_tif(order.get('tif'))}"
    )


def _resolve_buy_signal_audience(*, liquidity_value=0, ai_score=0):
    threshold = _rule_float('VIP_LIQUIDITY_THRESHOLD', 1_000_000_000)
    try:
        liquidity = float(liquidity_value or 0)
    except (TypeError, ValueError):
        liquidity = 0.0
    try:
        score = float(ai_score or 0)
    except (TypeError, ValueError):
        score = 0.0
    return 'VIP_ALL' if liquidity >= float(threshold or 0) and score >= 90.0 else 'ADMIN_ONLY'


def _publish_buy_signal_submission_notice(
    stock,
    code,
    *,
    strategy,
    curr_price,
    requested_qty,
    entry_mode,
    latency_gate,
    liquidity_value=0,
    ai_score=0,
):
    if EVENT_BUS is None:
        return

    bundle_id = str(stock.get('entry_bundle_id', '') or '').strip()
    if bundle_id and stock.get('last_buy_signal_telegram_bundle_id') == bundle_id:
        return

    audience = _resolve_telegram_audience_for_stock(
        stock,
        strategy,
        default=_resolve_buy_signal_audience(liquidity_value=liquidity_value, ai_score=ai_score),
    )
    dynamic_reason = (
        stock.get('entry_dynamic_reason')
        or stock.get('entry_armed_dynamic_reason')
        or '-'
    )
    msg = (
        f"🛒 **[BUY 신호/주문 제출] {stock.get('name')} ({code})**\n"
        f"전략: `{strategy}` | 진입모드: `{entry_mode}`\n"
        f"현재가: `{int(curr_price):,}원` | 주문수량: `{int(requested_qty or 0)}주`\n"
        f"진입근거: `{dynamic_reason}`\n"
        f"Latency: `{_translate_latency_state(latency_gate.get('latency_state'))}` / "
        f"`{_translate_entry_decision(latency_gate.get('decision'))}`"
    )
    try:
        EVENT_BUS.publish(
            'TELEGRAM_BROADCAST',
            {'message': msg, 'audience': audience, 'parse_mode': 'Markdown'},
        )
        if bundle_id:
            stock['last_buy_signal_telegram_bundle_id'] = bundle_id
        _log_entry_pipeline(
            stock,
            code,
            "buy_signal_telegram_enqueued",
            audience=audience,
            entry_mode=entry_mode,
            requested_qty=_safe_int(requested_qty, 0),
            liquidity_value=_safe_int(liquidity_value, 0),
            ai_score=f"{float(ai_score or 0):.1f}",
            latency=latency_gate.get('latency_state'),
            decision=latency_gate.get('decision'),
            dynamic_reason=dynamic_reason,
        )
    except Exception as exc:
        log_error(f"🚨 [BUY 신호 알림 실패] {stock.get('name')}({code}): {exc}")
        _log_entry_pipeline(
            stock,
            code,
            "buy_signal_telegram_enqueue_failed",
            audience=audience,
            entry_mode=entry_mode,
            error=str(exc),
        )


def _log_entry_pipeline(stock, code, stage, **fields):
    record_id = stock.get("id") if isinstance(stock, dict) else None
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        stock.get("name"),
        code,
        stage,
        record_id=record_id,
        fields=fields,
    )


def _entry_adm_candidate_id(stock, code) -> str:
    if not isinstance(stock, dict):
        return f"ADM-{code}-{int(time.time() * 1000)}-{uuid4().hex[:6]}"
    existing = str(stock.get("entry_adm_candidate_id") or "").strip()
    if existing:
        return existing
    record_id = stock.get("id") or "noid"
    candidate_id = f"ADM-{code}-{record_id}-{int(time.time() * 1000)}-{uuid4().hex[:6]}"
    _mutate_stock_state(stock, set_fields={"entry_adm_candidate_id": candidate_id})
    return candidate_id


def _entry_adm_action_from_context(stage: str, *, ai_decision=None, ai_score=None, latency_gate=None, submit_fields=None) -> str:
    stage = str(stage or "")
    submit_fields = submit_fields or {}
    if stage in {"pre_submit_liquidity_guard_block", "pre_submit_overbought_pullback_guard_block"}:
        return "SKIP_PRE_SUBMIT_SAFETY"
    if stage == "entry_submit_revalidation_block" or bool(submit_fields.get("entry_submit_revalidation_block")):
        return "SKIP_STALE"
    if stage in {"entry_submit_revalidation_warning", "latency_block"} or bool(submit_fields.get("entry_submit_revalidation_warning")):
        return "WAIT_REQUOTE"
    action = str((ai_decision or {}).get("action") or "").upper()
    score_value = _safe_float(ai_score if ai_score is not None else (ai_decision or {}).get("score"), 0.0)
    if action == "BUY" and score_value >= 75:
        guard = str((latency_gate or {}).get("entry_price_guard") or "").lower()
        canary_action = str((latency_gate or {}).get("ai_entry_price_canary_action") or "").upper()
        if "defensive" in guard or canary_action == "USE_DEFENSIVE":
            return "BUY_DEFENSIVE"
        return "BUY_NOW"
    if stage == "blocked_ai_score":
        reason = str((ai_decision or {}).get("ai_input_source_quality_reason") or "").lower()
        return "SKIP_SOURCE_QUALITY" if "source" in reason or "stale" in reason else "NO_BUY_AI"
    return "NO_BUY_AI"


def _emit_scalp_entry_adm_snapshot(
    stock,
    code,
    stage,
    *,
    ai_decision=None,
    ai_score=None,
    chosen_action=None,
    latency_gate=None,
    submit_fields=None,
    price_snapshot=None,
    orderbook_fields=None,
    actual_order_submitted=False,
    broker_order_forbidden=True,
    extra_fields=None,
):
    if not isinstance(stock, dict) or str(stock.get("strategy") or "SCALPING").upper() not in {"SCALPING", "SCALP"}:
        return
    action = chosen_action or _entry_adm_action_from_context(
        stage,
        ai_decision=ai_decision,
        ai_score=ai_score,
        latency_gate=latency_gate,
        submit_fields=submit_fields,
    )
    candidate_id = _entry_adm_candidate_id(stock, code)
    eligible = {
        "BUY_NOW": "BUY_NOW,BUY_DEFENSIVE,WAIT_REQUOTE,NO_BUY_AI",
        "BUY_DEFENSIVE": "BUY_NOW,BUY_DEFENSIVE,WAIT_REQUOTE,NO_BUY_AI",
        "WAIT_REQUOTE": "WAIT_REQUOTE,SKIP_STALE,NO_BUY_AI",
        "SKIP_STALE": "WAIT_REQUOTE,SKIP_STALE,NO_BUY_AI",
        "SKIP_PRE_SUBMIT_SAFETY": "SKIP_PRE_SUBMIT_SAFETY,NO_BUY_AI",
        "SKIP_SOURCE_QUALITY": "SKIP_SOURCE_QUALITY,NO_BUY_AI",
        "NO_BUY_AI": "NO_BUY_AI",
    }.get(action, "NO_BUY_AI")
    rejected = ",".join(item for item in ("BUY_NOW", "WAIT_REQUOTE", "SKIP_STALE", "BUY_DEFENSIVE", "NO_BUY_AI", "SKIP_SOURCE_QUALITY", "SKIP_PRE_SUBMIT_SAFETY") if item not in eligible)
    fields = {
        "candidate_id": candidate_id,
        "entry_adm_candidate_id": candidate_id,
        "ai_score": f"{_safe_float(ai_score if ai_score is not None else (ai_decision or {}).get('score'), 0.0):.1f}",
        "ai_action": str((ai_decision or {}).get("action") or "-"),
        "chosen_action": action,
        "eligible_actions": eligible,
        "rejected_actions": rejected,
        "metric_role": "action_decision_matrix",
        "decision_authority": "entry_advisory_prompt_context_only",
        "window_policy": "same_day_intraday_events_plus_postclose_sim_post_sell_join",
        "sample_floor": 20,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
        "runtime_effect": False,
        "actual_order_submitted": bool(actual_order_submitted),
        "broker_order_forbidden": bool(broker_order_forbidden),
        "forbidden_uses": "threshold mutation,order guard mutation,provider change,bot restart,broker order submit",
        **_scalp_pre_ai_gate_context_log_fields(stock.get("scalp_pre_ai_gate_context")),
    }
    for payload in (ai_decision or {}, latency_gate or {}, submit_fields or {}, price_snapshot or {}, orderbook_fields or {}, extra_fields or {}):
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key not in fields and value is not None:
                    fields[key] = value
    _log_entry_pipeline(stock, code, "scalp_entry_action_decision_snapshot", source_stage=stage, **fields)


def _log_holding_pipeline(stock, code, stage, **fields):
    record_id = stock.get("id")
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        stock.get("name"),
        code,
        stage,
        record_id=record_id,
        fields=fields,
    )


def _log_watching_state_debug(stock, code, *, radar=None, ai_engine=None):
    if not _rule_bool("WATCHING_STATE_DEBUG_LOG_ENABLED", False):
        return
    log_info(
        f"[DEBUG] handle_watching_state 시작: {stock.get('name')} ({code}), 전략={stock.get('strategy')}, "
        f"위치태그={stock.get('position_tag')}, radar={'있음' if radar else '없음'}, "
        f"ai_engine={'있음' if ai_engine else '없음'}"
    )


def _format_action_list(values):
    cleaned = [str(value).strip() for value in (values or []) if str(value).strip()]
    return "|".join(cleaned) if cleaned else "-"


def _spread_bps_from_ws(ws_data, curr_price):
    orderbook = ws_data.get("orderbook") if isinstance(ws_data, dict) else None
    if not isinstance(orderbook, dict):
        return None
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []
    if not asks or not bids:
        return None
    best_ask = _safe_float((asks[0] or {}).get("price"), 0.0)
    best_bid = _safe_float((bids[0] or {}).get("price"), 0.0)
    ref_price = _safe_float(curr_price, 0.0) or ((best_ask + best_bid) / 2.0)
    if best_ask <= 0 or best_bid <= 0 or ref_price <= 0:
        return None
    return ((best_ask - best_bid) / ref_price) * 10000.0


def _top3_depth_ratio_from_ws(ws_data):
    orderbook = ws_data.get("orderbook") if isinstance(ws_data, dict) else None
    if not isinstance(orderbook, dict):
        return None
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []
    ask_qty = sum(_safe_float((level or {}).get("volume"), 0.0) for level in asks[:3])
    bid_qty = sum(_safe_float((level or {}).get("volume"), 0.0) for level in bids[:3])
    if bid_qty <= 0:
        return None
    return ask_qty / bid_qty


def _emit_stat_action_decision_snapshot(
    *,
    stock,
    code,
    strategy,
    ws_data,
    chosen_action,
    eligible_actions=None,
    rejected_actions=None,
    profit_rate=0.0,
    peak_profit=0.0,
    current_ai_score=0.0,
    held_sec=0,
    curr_price=0,
    buy_price=0,
    exit_rule="-",
    sell_reason_type="-",
    scale_in_gate=None,
    scale_in_action=None,
    reason="-",
    force=False,
):
    if not _rule_bool("STAT_ACTION_DECISION_SNAPSHOT_ENABLED", True):
        return False
    if str(strategy or "").upper() != "SCALPING":
        return False

    now_ts = time.time()
    if not force:
        min_interval = _rule_int("STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC", 30)
        last_ts = _safe_float(stock.get("last_stat_action_snapshot_ts"), 0.0)
        if last_ts > 0 and (now_ts - last_ts) < min_interval:
            return False

    gate = scale_in_gate if isinstance(scale_in_gate, dict) else {}
    action = scale_in_action if isinstance(scale_in_action, dict) else {}
    feat = stock.get("last_reversal_features", {}) if isinstance(stock, dict) else {}
    if not isinstance(feat, dict):
        feat = {}

    drawdown_from_peak = _safe_float(peak_profit, 0.0) - _safe_float(profit_rate, 0.0)
    curr_price_int = _safe_int(curr_price, 0)
    buy_price_float = _safe_float(buy_price, 0.0)
    distance_to_buy_bps = (
        ((curr_price_int - buy_price_float) / buy_price_float) * 10000.0
        if curr_price_int > 0 and buy_price_float > 0
        else None
    )
    fields = {
        "threshold_family": "statistical_action_weight",
        "chosen_action": str(chosen_action or "-"),
        "eligible_actions": _format_action_list(eligible_actions),
        "rejected_actions": _format_action_list(rejected_actions),
        "profit_rate": f"{_safe_float(profit_rate, 0.0):+.2f}",
        "peak_profit": f"{_safe_float(peak_profit, 0.0):+.2f}",
        "drawdown_from_peak": f"{drawdown_from_peak:.2f}",
        "held_sec": _safe_int(held_sec, 0),
        "current_ai_score": f"{_safe_float(current_ai_score, 0.0):.0f}",
        "curr_price": curr_price_int,
        "buy_price": f"{buy_price_float:.2f}",
        "buy_qty": _safe_int(stock.get("buy_qty"), 0),
        "avg_down_count": _safe_int(stock.get("avg_down_count"), 0),
        "pyramid_count": _safe_int(stock.get("pyramid_count"), 0),
        "last_add_type": stock.get("last_add_type") or "-",
        "reversal_add_state": stock.get("reversal_add_state") or "-",
        "reversal_add_used": bool(stock.get("reversal_add_used")),
        "exit_rule_candidate": exit_rule or "-",
        "sell_reason_type": sell_reason_type or "-",
        "scale_in_gate_allowed": bool(gate.get("allowed")),
        "scale_in_gate_reason": gate.get("reason", "-"),
        "scale_in_action_type": action.get("add_type", "-"),
        "scale_in_action_reason": action.get("reason", "-"),
        "reason": str(reason or "-"),
        "spread_bps": "-" if _spread_bps_from_ws(ws_data, curr_price_int) is None else f"{_spread_bps_from_ws(ws_data, curr_price_int):.2f}",
        "top3_depth_ratio": "-" if _top3_depth_ratio_from_ws(ws_data) is None else f"{_top3_depth_ratio_from_ws(ws_data):.4f}",
        "buy_pressure_10t": feat.get("buy_pressure_10t", "-"),
        "tick_acceleration_ratio": feat.get("tick_acceleration_ratio", "-"),
        "large_sell_print_detected": feat.get("large_sell_print_detected", "-"),
        "curr_vs_micro_vwap_bp": feat.get("curr_vs_micro_vwap_bp", "-"),
        "snapshot_observe_only": True,
    }
    if distance_to_buy_bps is not None:
        fields["distance_to_buy_bps"] = f"{distance_to_buy_bps:.2f}"

    _log_holding_pipeline(stock, code, "stat_action_decision_snapshot", **fields)
    _mutate_stock_state(stock, set_fields={"last_stat_action_snapshot_ts": now_ts})
    return True


def _append_reversal_add_probe_fields(fields: dict, probe: dict | None) -> dict:
    merged = dict(fields or {})
    if not isinstance(probe, dict) or not probe:
        return merged
    for key in (
        "pnl_ok",
        "hold_ok",
        "low_floor_ok",
        "ai_score_ok",
        "ai_recover_ok",
        "ai_recovering_delta_ok",
        "ai_recovering_consec_ok",
        "supply_ok",
        "buy_pressure_ok",
        "tick_accel_ok",
        "large_sell_absent_ok",
        "micro_vwap_ok",
        "has_reversal_features",
        "reversal_add_used",
        "large_sell_print_detected",
    ):
        if key in probe:
            merged[key] = bool(probe.get(key))
    for key in (
        "profit_rate",
        "pnl_min",
        "pnl_max",
        "held_sec",
        "min_hold_sec",
        "max_hold_sec",
        "profit_floor",
        "floor_margin",
        "current_ai_score",
        "min_ai_score",
        "ai_bottom",
        "min_ai_recovery_delta",
        "ai_hist_len",
        "buy_pressure_10t",
        "min_buy_pressure",
        "tick_acceleration_ratio",
        "min_tick_accel",
        "curr_vs_micro_vwap_bp",
        "min_micro_vwap_bp",
        "supply_pass_count",
    ):
        if key in probe:
            merged[key] = probe.get(key)
    return merged


def _log_orderbook_stability_observation(stock, code, snapshot):
    if not isinstance(snapshot, dict) or not snapshot:
        return
    micro_fields = _build_orderbook_micro_log_fields(snapshot.get("orderbook_micro"))
    _log_entry_pipeline(
        stock,
        code,
        "orderbook_stability_observed",
        fr_10s=int(snapshot.get("fr_10s", 0) or 0),
        quote_age_p50_ms=snapshot.get("quote_age_p50_ms", "-"),
        quote_age_p90_ms=snapshot.get("quote_age_p90_ms", "-"),
        print_quote_alignment=snapshot.get("print_quote_alignment", "-"),
        unstable_quote_observed=bool(snapshot.get("unstable_quote_observed")),
        unstable_reasons=snapshot.get("unstable_reasons") or "-",
        best_bid=int(snapshot.get("best_bid", 0) or 0),
        best_ask=int(snapshot.get("best_ask", 0) or 0),
        sample_trade_count=int(snapshot.get("sample_trade_count", 0) or 0),
        sample_quote_count=int(snapshot.get("sample_quote_count", 0) or 0),
        **micro_fields,
    )


def _update_boolean_sustain_sec(stock, *, key: str, active: bool, now_ts: float) -> int:
    if active:
        started_at = float(stock.get(key, 0) or 0)
        if started_at <= 0:
            started_at = now_ts
            stock[key] = started_at
        return max(0, int(now_ts - started_at))
    stock.pop(key, None)
    return 0


def _is_non_positive_numeric(value) -> bool:
    try:
        return float(value) <= 0.0
    except (TypeError, ValueError):
        return False


def _resolve_sell_order_sign(sell_reason_type: str, profit_rate) -> str:
    reason_upper = str(sell_reason_type or "").upper()
    is_loss = reason_upper == "LOSS"
    if not is_loss and reason_upper == "TRAILING" and _is_non_positive_numeric(profit_rate):
        is_loss = True
    return "📉 [손절 주문]" if is_loss else "🎊 [익절 주문]"


def _resolve_same_symbol_loss_reentry_cooldown_sec(exit_rule: str | None, profit_rate) -> int:
    if not _rule_bool("SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_ENABLED", True):
        return 0
    if not _is_non_positive_numeric(profit_rate):
        return 0
    loss_exit_rules = {
        "scalp_soft_stop_pct",
        "protect_trailing_stop",
        "scalp_bad_entry_refined_canary",
        "reversal_add_post_eval_fail",
    }
    if str(exit_rule or "").strip() not in loss_exit_rules:
        return 0
    return max(0, _rule_int("SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC", 3600))


def _resolve_exit_decision_source(
    *,
    stock: dict | None,
    exit_rule: str | None,
    reason: str | None = None,
) -> str:
    rule = str(exit_rule or "").strip()
    reason_text = str(reason or "").strip().lower()
    strategy = str((stock or {}).get("strategy") or "").upper()

    if rule.startswith("overnight_") or "overnight_flow" in reason_text:
        return "OVERNIGHT_FLOW"

    if (
        stock
        and _holding_flow_override_applicable(strategy, rule)
        and (
            stock.get("holding_flow_override_candidate_key")
            or _safe_float(stock.get("holding_flow_override_last_review_at"), 0.0) > 0
        )
    ):
        return "HOLDING_FLOW_OVERRIDE"

    if rule == "scalp_preset_hard_stop_pct":
        return "PRESET_HARD_STOP"

    if rule in {"scalp_preset_protect_profit", "protect_hard_stop", "protect_trailing_stop"}:
        return "PRESET_PROTECT"

    if rule == "scalp_preset_ai_review_exit":
        return "AI_REVIEW_EXIT"

    if "trailing" in rule:
        return "TRAILING"

    if "timeout" in rule:
        return "TIMEOUT"

    if rule == "scalp_soft_stop_pct":
        return "SOFT_STOP"

    return "MANUAL"


def _mark_same_symbol_soft_stop(code: str, *, now_ts: float) -> None:
    if not _rule_bool("SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED", False):
        return
    cooldown_sec = _rule_int("SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_SEC", 600)
    if cooldown_sec <= 0:
        return
    _SAME_SYMBOL_SOFT_STOP_TS[code] = now_ts


def _remember_exit_context(
    *,
    stock: dict,
    exit_rule: str | None,
    reason: str | None,
    peak_profit: float,
    held_sec: int,
    current_ai_score: float,
    soft_stop_threshold_pct: float | None = None,
) -> None:
    exit_decision_source = _resolve_exit_decision_source(
        stock=stock,
        exit_rule=exit_rule,
        reason=reason,
    )
    stock["last_exit_rule"] = exit_rule or ""
    stock["last_exit_decision_source"] = exit_decision_source
    stock["last_exit_peak_profit"] = round(float(peak_profit or 0.0), 3)
    stock["last_exit_held_sec"] = max(0, int(held_sec or 0))
    stock["last_exit_current_ai_score"] = round(float(current_ai_score or 0.0), 1)
    if soft_stop_threshold_pct is not None:
        stock["last_exit_soft_stop_threshold_pct"] = round(float(soft_stop_threshold_pct or 0.0), 3)
    else:
        stock.pop("last_exit_soft_stop_threshold_pct", None)

    cooldown_sec = _rule_int("SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_SEC", 600)
    cooldown_enabled = _rule_bool("SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED", False)
    stock["last_exit_same_symbol_soft_stop_cooldown_would_block"] = bool(
        str(exit_rule or "").strip() == "scalp_soft_stop_pct" and cooldown_enabled and cooldown_sec > 0
    )


def _emit_same_symbol_soft_stop_cooldown_shadow(
    *,
    stock: dict,
    code: str,
    now_ts: float,
    runtime_remaining_sec: int,
) -> None:
    enabled = _rule_bool("SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED", False)
    if not enabled:
        return

    marked_at = float(_SAME_SYMBOL_SOFT_STOP_TS.get(code, 0) or 0)
    if marked_at <= 0:
        return

    cooldown_sec = _rule_int("SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_SEC", 600)
    if cooldown_sec <= 0:
        return

    elapsed_sec = max(0, int(now_ts - marked_at))
    if elapsed_sec > cooldown_sec:
        _SAME_SYMBOL_SOFT_STOP_TS.pop(code, None)
        stock.pop("_same_symbol_soft_stop_cooldown_shadow_logged_key", None)
        return

    logged_key = f"{int(marked_at)}:{cooldown_sec}"
    if stock.get("_same_symbol_soft_stop_cooldown_shadow_logged_key") == logged_key:
        return

    _log_entry_pipeline(
        stock,
        code,
        "same_symbol_soft_stop_cooldown_shadow",
        elapsed_sec=elapsed_sec,
        cooldown_sec=cooldown_sec,
        runtime_remaining_sec=max(0, int(runtime_remaining_sec or 0)),
        would_block=True,
        shadow_only=True,
    )
    stock["_same_symbol_soft_stop_cooldown_shadow_logged_key"] = logged_key


def _observe_bad_entry_block_candidate(
    stock,
    code: str,
    *,
    strategy: str,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    held_sec: int,
    now_ts: float,
) -> None:
    if (strategy or "").upper() != "SCALPING":
        return
    if not _rule_bool("SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED", True):
        return

    interval_sec = _rule_int("SCALP_BAD_ENTRY_BLOCK_LOG_INTERVAL_SEC", 30)
    last_logged = float(stock.get("last_bad_entry_block_observed_ts", 0.0) or 0.0)
    if interval_sec > 0 and now_ts - last_logged < interval_sec:
        return

    min_hold_sec = _rule_int("SCALP_BAD_ENTRY_BLOCK_MIN_HOLD_SEC", 60)
    min_loss_pct = _rule_float("SCALP_BAD_ENTRY_BLOCK_MIN_LOSS_PCT", -0.70)
    max_peak_pct = _rule_float("SCALP_BAD_ENTRY_BLOCK_MAX_PEAK_PROFIT_PCT", 0.20)
    ai_limit = _rule_float("SCALP_BAD_ENTRY_BLOCK_AI_SCORE_LIMIT", 45)

    if held_sec < min_hold_sec or profit_rate > min_loss_pct or peak_profit > max_peak_pct:
        return
    if float(current_ai_score or 0.0) > ai_limit:
        return

    feat = stock.get("last_reversal_features") or {}
    if not isinstance(feat, dict):
        feat = {}
    stock["last_bad_entry_block_observed_ts"] = now_ts
    _log_holding_pipeline(
        stock,
        code,
        "bad_entry_block_observed",
        classifier="never_green_ai_fade",
        observe_only=True,
        profit_rate=f"{profit_rate:+.2f}",
        peak_profit=f"{peak_profit:+.2f}",
        current_ai_score=f"{float(current_ai_score or 0.0):.0f}",
        held_sec=int(held_sec or 0),
        min_loss_pct=f"{min_loss_pct:+.2f}",
        max_peak_profit_pct=f"{max_peak_pct:+.2f}",
        ai_score_limit=f"{ai_limit:.0f}",
        buy_pressure_10t=feat.get("buy_pressure_10t", "-"),
        tick_acceleration_ratio=feat.get("tick_acceleration_ratio", "-"),
        large_sell_print_detected=feat.get("large_sell_print_detected", "-"),
        curr_vs_micro_vwap_bp=feat.get("curr_vs_micro_vwap_bp", "-"),
    )


def _emit_partial_only_timeout_shadow(
    *,
    stock: dict,
    code: str,
    held_sec: int,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
) -> None:
    enabled = _rule_bool("SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_ENABLED", False)
    if not enabled:
        return

    timeout_sec = _rule_int("SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_SEC", 180)
    if timeout_sec <= 0 or held_sec < timeout_sec:
        return

    requested_qty = _safe_int(stock.get("entry_requested_qty") or stock.get("requested_buy_qty"), 0)
    buy_qty = _safe_int(stock.get("buy_qty"), 0)
    if requested_qty <= 1 or buy_qty <= 0 or buy_qty > 1 or buy_qty >= requested_qty:
        return

    peak_max_pct = _rule_float("SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_MAX_PEAK_PCT", 0.20)
    if peak_profit > peak_max_pct:
        return

    entry_mode = str(stock.get("entry_mode", "") or "normal").strip().lower() or "normal"
    rebase_count = _safe_int(stock.get("_split_entry_rebase_shadow_count"), 0)
    if rebase_count >= 2:
        return

    logged_key = (
        f"{timeout_sec}:{requested_qty}:{buy_qty}:{entry_mode}:{rebase_count}:"
        f"{peak_max_pct:.2f}"
    )
    if stock.get("_partial_only_timeout_shadow_logged_key") == logged_key:
        return

    _log_holding_pipeline(
        stock,
        code,
        "partial_only_timeout_shadow",
        held_sec=int(held_sec),
        timeout_sec=int(timeout_sec),
        requested_qty=int(requested_qty),
        buy_qty=int(buy_qty),
        entry_mode=entry_mode,
        rebase_count=int(rebase_count),
        peak_profit=f"{peak_profit:+.2f}",
        profit_rate=f"{profit_rate:+.2f}",
        current_ai_score=f"{current_ai_score:.0f}",
        shadow_only=True,
    )
    stock["_partial_only_timeout_shadow_logged_key"] = logged_key


def _soft_stop_feature_float(features: dict, key: str, default: float = 0.0) -> float:
    return _safe_float(features.get(key, default), float(default))


def _soft_stop_feature_int(features: dict, key: str, default: int = 0) -> int:
    return _safe_int(features.get(key, default), int(default))


def _soft_stop_expert_time_gate_active(now_ts: float) -> bool:
    activate_at = str(_rule("SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT", "") or "").strip()
    if not activate_at:
        return True
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return float(now_ts or 0.0) >= datetime.strptime(activate_at, fmt).timestamp()
        except ValueError:
            continue
    return True


def _normalize_soft_stop_expert_features(stock: dict) -> tuple[dict, bool]:
    raw = stock.get("last_reversal_features") or {}
    if not isinstance(raw, dict) or not raw:
        return {}, False
    features = {
        "buy_pressure_10t": _soft_stop_feature_float(raw, "buy_pressure_10t", 50.0),
        "tick_acceleration_ratio": _soft_stop_feature_float(raw, "tick_acceleration_ratio", 0.0),
        "large_sell_print_detected": bool(raw.get("large_sell_print_detected", False)),
        "curr_vs_micro_vwap_bp": _soft_stop_feature_float(raw, "curr_vs_micro_vwap_bp", 0.0),
        "net_aggressive_delta_10t": _soft_stop_feature_int(raw, "net_aggressive_delta_10t", 0),
        "same_price_buy_absorption": _soft_stop_feature_int(raw, "same_price_buy_absorption", 0),
        "microprice_edge_bp": _soft_stop_feature_float(raw, "microprice_edge_bp", 0.0),
        "top3_depth_ratio": _soft_stop_feature_float(raw, "top3_depth_ratio", 999.0),
    }
    return features, True


def _has_active_sell_order_pending(stock: dict) -> bool:
    return (
        str(stock.get("status", "") or "").upper() == "SELL_ORDERED"
        or bool(str(stock.get("sell_odno", "") or "").strip())
        or bool(str(stock.get("sell_ord_no", "") or "").strip())
        or bool(str(stock.get("pending_sell_msg", "") or "").strip())
    )


def _build_bad_entry_refined_decision(
    stock: dict,
    *,
    strategy: str,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    held_sec: int,
    dynamic_stop_pct: float,
    hard_stop_pct: float,
) -> dict:
    features, feature_valid = _normalize_soft_stop_expert_features(stock)
    enabled = _rule_bool("SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED", False)
    observe_enabled = _rule_bool("SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED", True)
    min_hold_sec = _rule_int("SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC", 180)
    min_loss_pct = _rule_float("SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT", -1.16)
    max_peak_pct = _rule_float("SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT", 0.05)
    ai_limit = _rule_float("SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT", 45)
    recovery_prob_max = _rule_float("SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX", 0.30)

    buy_pressure = features.get("buy_pressure_10t", 50.0)
    tick_accel = features.get("tick_acceleration_ratio", 0.0)
    large_sell = bool(features.get("large_sell_print_detected", False))
    micro_vwap_bp = features.get("curr_vs_micro_vwap_bp", 0.0)
    net_delta = features.get("net_aggressive_delta_10t", 0)
    absorption_count = features.get("same_price_buy_absorption", 0)
    microprice_edge_bp = features.get("microprice_edge_bp", 0.0)
    top3_depth_ratio = features.get("top3_depth_ratio", 999.0)

    thesis_tick_min = _rule_float("SCALP_SOFT_STOP_THESIS_TICK_ACCEL_MIN", 0.60)
    thesis_vwap_min = _rule_float("SCALP_SOFT_STOP_THESIS_MICRO_VWAP_BP_MIN", -20.0)
    thesis_invalidated = bool(
        large_sell or (tick_accel < thesis_tick_min and micro_vwap_bp < thesis_vwap_min)
    )
    adverse_fill = bool(
        large_sell
        or buy_pressure < 35.0
        or tick_accel < 0.85
        or micro_vwap_bp < -10.0
        or net_delta < 0
    )
    absorption_score = sum(
        1
        for ok in (
            buy_pressure >= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MIN_BUY_PRESSURE", 55.0),
            net_delta > 0,
            absorption_count >= 2,
            micro_vwap_bp >= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MIN_MICRO_VWAP_BP", -5.0),
            microprice_edge_bp >= 0.0,
            tick_accel >= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MIN_TICK_ACCEL", 0.95),
            top3_depth_ratio <= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MAX_TOP3_DEPTH_RATIO", 1.35),
        )
        if ok
    )
    recovery_prob_shadow = max(
        0.0,
        min(
            1.0,
            0.20
            + (0.08 * absorption_score)
            + (0.05 if current_ai_score >= 55 else 0.0)
            + (0.05 if peak_profit >= 0 else 0.0)
            - (0.20 if thesis_invalidated else 0.0),
        ),
    )
    confirmation = bool(
        thesis_invalidated
        or adverse_fill
        or recovery_prob_shadow <= recovery_prob_max
    )

    exclusion_reason = "-"
    if (strategy or "").upper() != "SCALPING":
        exclusion_reason = "not_scalping"
    elif _has_active_sell_order_pending(stock):
        exclusion_reason = "active_sell_pending"
    elif bool(stock.get("reversal_add_used")):
        exclusion_reason = "reversal_add_used"
    elif str(stock.get("reversal_add_state", "") or "").strip() == "POST_ADD_EVAL":
        exclusion_reason = "reversal_add_post_eval"
    elif profit_rate <= hard_stop_pct:
        exclusion_reason = "hard_stop_zone"
    elif profit_rate <= dynamic_stop_pct:
        exclusion_reason = "soft_stop_zone"
    elif not feature_valid:
        exclusion_reason = "invalid_feature"
    elif held_sec < min_hold_sec:
        exclusion_reason = "hold_too_short"
    elif profit_rate > min_loss_pct:
        exclusion_reason = "loss_too_shallow"
    elif peak_profit > max_peak_pct:
        exclusion_reason = "peak_recovered"
    elif float(current_ai_score or 0.0) > ai_limit:
        exclusion_reason = "ai_recovered"
    elif not confirmation:
        exclusion_reason = "no_confirmation"

    would_exit = exclusion_reason == "-"
    return {
        "enabled": enabled,
        "observe_enabled": observe_enabled,
        "feature_valid": feature_valid,
        "features": features,
        "should_exit": bool(enabled and would_exit),
        "would_exit": bool(would_exit),
        "exclusion_reason": exclusion_reason,
        "thesis_invalidated": thesis_invalidated,
        "adverse_fill": adverse_fill,
        "absorption_score": int(absorption_score),
        "recovery_prob_shadow": round(recovery_prob_shadow, 3),
        "recovery_prob_max": recovery_prob_max,
        "min_hold_sec": min_hold_sec,
        "min_loss_pct": min_loss_pct,
        "max_peak_profit_pct": max_peak_pct,
        "ai_score_limit": ai_limit,
    }


def _emit_bad_entry_refined_candidate(
    stock: dict,
    code: str,
    *,
    decision: dict,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    held_sec: int,
) -> None:
    if not decision.get("enabled") and not decision.get("observe_enabled"):
        return
    bucket = max(0, int(held_sec or 0) // 30)
    logged_key = f"{bucket}:{decision.get('exclusion_reason', '-')}:{bool(decision.get('enabled'))}"
    if stock.get("_bad_entry_refined_candidate_logged_key") == logged_key:
        return

    features = decision.get("features") or {}
    _log_holding_pipeline(
        stock,
        code,
        "bad_entry_refined_candidate",
        decision_source="BAD_ENTRY_REFINED_CANARY",
        threshold_family="bad_entry_refined_canary",
        threshold_version=str(
            _rule("SCALP_BAD_ENTRY_REFINED_THRESHOLD_VERSION", "runtime_default") or "runtime_default"
        ),
        threshold_calibration_state=str(
            _rule("SCALP_BAD_ENTRY_REFINED_CALIBRATION_STATE", "runtime_default") or "runtime_default"
        ),
        threshold_applied_value=(
            f"enabled={bool(decision.get('enabled'))}|min_hold={decision.get('min_hold_sec', '-')}|"
            f"min_loss={decision.get('min_loss_pct', 0.0):+.2f}|"
            f"recovery_max={decision.get('recovery_prob_max', 0.0):.3f}"
        ),
        canary_enabled=bool(decision.get("enabled")),
        should_exit=bool(decision.get("should_exit")),
        would_exit=bool(decision.get("would_exit")),
        observe_only=not bool(decision.get("enabled")),
        exclusion_reason=decision.get("exclusion_reason", "-"),
        classifier="never_green_ai_fade_refined",
        profit_rate=f"{profit_rate:+.2f}",
        peak_profit=f"{peak_profit:+.2f}",
        current_ai_score=f"{current_ai_score:.0f}",
        held_sec=int(held_sec or 0),
        min_hold_sec=decision.get("min_hold_sec", "-"),
        min_loss_pct=f"{decision.get('min_loss_pct', 0.0):+.2f}",
        max_peak_profit_pct=f"{decision.get('max_peak_profit_pct', 0.0):+.2f}",
        ai_score_limit=f"{decision.get('ai_score_limit', 0.0):.0f}",
        thesis_invalidated=bool(decision.get("thesis_invalidated")),
        adverse_fill=bool(decision.get("adverse_fill")),
        absorption_score=decision.get("absorption_score", 0),
        recovery_prob_shadow=f"{decision.get('recovery_prob_shadow', 0.0):.3f}",
        recovery_prob_max=f"{decision.get('recovery_prob_max', 0.0):.3f}",
        buy_pressure_10t=features.get("buy_pressure_10t", "-"),
        tick_acceleration_ratio=features.get("tick_acceleration_ratio", "-"),
        large_sell_print_detected=features.get("large_sell_print_detected", "-"),
        curr_vs_micro_vwap_bp=features.get("curr_vs_micro_vwap_bp", "-"),
    )
    stock["_bad_entry_refined_candidate_logged_key"] = logged_key


def _build_soft_stop_expert_decision(
    stock: dict,
    *,
    now_ts: float,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    held_sec: int,
    curr_price: int,
    dynamic_stop_pct: float,
    emergency_pct: float,
    grace_elapsed_sec: int,
    grace_sec: int,
) -> dict:
    features, feature_valid = _normalize_soft_stop_expert_features(stock)
    enabled = _rule_bool("SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED", False)
    active_after_time_gate = _soft_stop_expert_time_gate_active(now_ts)
    extension_sec = max(0, _rule_int("SCALP_SOFT_STOP_ABSORPTION_EXTENSION_SEC", 0))
    min_score = max(1, _rule_int("SCALP_SOFT_STOP_ABSORPTION_MIN_SCORE", 3))
    max_extensions = max(0, _rule_int("SCALP_SOFT_STOP_ABSORPTION_MAX_EXTENSIONS", 1))

    buy_pressure = features.get("buy_pressure_10t", 50.0)
    tick_accel = features.get("tick_acceleration_ratio", 0.0)
    large_sell = bool(features.get("large_sell_print_detected", False))
    micro_vwap_bp = features.get("curr_vs_micro_vwap_bp", 0.0)
    net_delta = features.get("net_aggressive_delta_10t", 0)
    absorption_count = features.get("same_price_buy_absorption", 0)
    microprice_edge_bp = features.get("microprice_edge_bp", 0.0)
    top3_depth_ratio = features.get("top3_depth_ratio", 999.0)

    thesis_tick_min = _rule_float("SCALP_SOFT_STOP_THESIS_TICK_ACCEL_MIN", 0.60)
    thesis_vwap_min = _rule_float("SCALP_SOFT_STOP_THESIS_MICRO_VWAP_BP_MIN", -20.0)
    thesis_invalidated = bool(
        large_sell or (tick_accel < thesis_tick_min and micro_vwap_bp < thesis_vwap_min)
    )
    thesis_reason = "large_sell_print" if large_sell else "-"
    if thesis_reason == "-" and tick_accel < thesis_tick_min and micro_vwap_bp < thesis_vwap_min:
        thesis_reason = "tick_accel_and_micro_vwap_break"

    checks = {
        "buy_pressure": buy_pressure >= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MIN_BUY_PRESSURE", 55.0),
        "net_aggressive_delta": net_delta > 0,
        "same_price_buy_absorption": absorption_count >= 2,
        "curr_vs_micro_vwap": micro_vwap_bp >= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MIN_MICRO_VWAP_BP", -5.0),
        "microprice_edge": microprice_edge_bp >= 0.0,
        "tick_acceleration": tick_accel >= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MIN_TICK_ACCEL", 0.95),
        "top3_depth": top3_depth_ratio <= _rule_float("SCALP_SOFT_STOP_ABSORPTION_MAX_TOP3_DEPTH_RATIO", 1.35),
    }
    absorption_score = sum(1 for ok in checks.values() if ok)
    recovery_prob_shadow = max(
        0.0,
        min(
            1.0,
            0.20
            + (0.08 * absorption_score)
            + (0.05 if current_ai_score >= 55 else 0.0)
            + (0.05 if peak_profit >= 0 else 0.0)
            - (0.20 if thesis_invalidated else 0.0),
        ),
    )
    buy_qty = max(0, _safe_int(stock.get("buy_qty"), 0))
    extension_count = max(0, _safe_int(stock.get("soft_stop_absorption_extension_count"), 0))
    extension_started_at = _safe_float(stock.get("soft_stop_absorption_extension_started_at"), 0.0)
    extension_active = bool(
        extension_started_at > 0
        and extension_sec > 0
        and (now_ts - extension_started_at) < extension_sec
        and profit_rate > emergency_pct
        and not thesis_invalidated
    )

    exclusion_reason = "-"
    if not enabled:
        exclusion_reason = "disabled"
    elif not active_after_time_gate:
        exclusion_reason = "time_gate"
    elif extension_sec <= 0:
        exclusion_reason = "extension_sec_zero"
    elif profit_rate <= emergency_pct:
        exclusion_reason = "emergency_pct"
    elif bool(stock.get("reversal_add_used")):
        exclusion_reason = "reversal_add_used"
    elif str(stock.get("reversal_add_state", "") or "").strip() == "POST_ADD_EVAL":
        exclusion_reason = "reversal_add_post_eval"
    elif _has_active_sell_order_pending(stock):
        exclusion_reason = "active_sell_pending"
    elif not feature_valid:
        exclusion_reason = "invalid_feature"
    elif grace_elapsed_sec < max(0, _safe_int(grace_sec, 0)):
        exclusion_reason = "base_micro_grace"
    elif thesis_invalidated:
        exclusion_reason = thesis_reason
    elif extension_count >= max_extensions and not extension_active:
        exclusion_reason = "max_extension_used"
    elif absorption_score < min_score:
        exclusion_reason = "absorption_score_low"

    should_extend = (
        exclusion_reason == "-"
        and feature_valid
        and absorption_score >= min_score
        and not thesis_invalidated
        and profit_rate > emergency_pct
    ) or extension_active

    return {
        "enabled": enabled,
        "active_after_time_gate": active_after_time_gate,
        "feature_valid": feature_valid,
        "features": features,
        "checks": checks,
        "absorption_score": int(absorption_score),
        "min_score": int(min_score),
        "thesis_invalidated": thesis_invalidated,
        "thesis_reason": thesis_reason,
        "exclusion_reason": exclusion_reason,
        "should_extend": bool(should_extend),
        "extension_sec": int(extension_sec),
        "extension_count": int(extension_count),
        "extension_started_at": float(extension_started_at),
        "extension_active": bool(extension_active),
        "recovery_prob_shadow": round(recovery_prob_shadow, 3),
        "would_trim_qty": max(0, buy_qty // 2) if buy_qty > 1 else 0,
        "would_trim_price": _safe_int(curr_price, 0),
        "mae_proxy_pct": round(float(profit_rate or 0.0), 3),
        "mfe_proxy_pct": round(float(peak_profit or 0.0), 3),
        "held_sec": _safe_int(held_sec, 0),
    }


def _emit_soft_stop_expert_observations(
    stock: dict,
    code: str,
    *,
    decision: dict,
    profit_rate: float,
    peak_profit: float,
    dynamic_stop_pct: float,
    current_ai_score: float,
    held_sec: int,
) -> None:
    bucket = int(max(0, _safe_int(decision.get("held_sec", held_sec), 0)) // 10)
    started_at = _safe_int(stock.get("soft_stop_micro_grace_started_at"), 0)
    logged_key = f"{started_at}:{bucket}:{decision.get('exclusion_reason', '-')}"
    if stock.get("_soft_stop_expert_shadow_logged_key") == logged_key:
        return

    features = decision.get("features") or {}
    _log_holding_pipeline(
        stock,
        code,
        "soft_stop_expert_shadow",
        **_build_observation_contract_fields("ops_volume_diagnostic"),
        hierarchy="mae_mfe_quantile|recovery_probability|partial_de_risk",
        shadow_only=True,
        profit_rate=f"{profit_rate:+.2f}",
        peak_profit=f"{peak_profit:+.2f}",
        soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
        mae_proxy_pct=f"{decision.get('mae_proxy_pct', 0.0):+.3f}",
        mfe_proxy_pct=f"{decision.get('mfe_proxy_pct', 0.0):+.3f}",
        recovery_prob_shadow=f"{decision.get('recovery_prob_shadow', 0.0):.3f}",
        would_trim_qty=_safe_int(decision.get("would_trim_qty"), 0),
        would_trim_price=_safe_int(decision.get("would_trim_price"), 0),
        current_ai_score=f"{current_ai_score:.0f}",
        held_sec=_safe_int(held_sec, 0),
    )
    _log_holding_pipeline(
        stock,
        code,
        "adverse_fill_observed",
        observe_only=True,
        feature_valid=bool(decision.get("feature_valid")),
        buy_pressure_10t=features.get("buy_pressure_10t", "-"),
        net_aggressive_delta_10t=features.get("net_aggressive_delta_10t", "-"),
        microprice_edge_bp=features.get("microprice_edge_bp", "-"),
        top3_depth_ratio=features.get("top3_depth_ratio", "-"),
        large_sell_print_detected=features.get("large_sell_print_detected", "-"),
    )
    stock["_soft_stop_expert_shadow_logged_key"] = logged_key


def _apply_initial_entry_qty_cap(
    planned_orders: list[dict],
    *,
    max_total_qty: int,
) -> tuple[list[dict], int, int, bool]:
    if not planned_orders:
        return [], 0, 0, False

    qty_cap = max(1, int(max_total_qty or 1))
    updated_orders: list[dict] = []
    original_total = 0
    scaled_total = 0
    remaining_qty = qty_cap

    for order in planned_orders:
        item = dict(order or {})
        qty = max(0, int(item.get("qty") or 0))
        original_total += qty

        if qty <= 0 or remaining_qty <= 0:
            item["qty"] = 0
            updated_orders.append(item)
            continue

        scaled_qty = min(qty, remaining_qty)
        item["qty"] = scaled_qty
        scaled_total += scaled_qty
        remaining_qty -= scaled_qty
        updated_orders.append(item)

    applied = scaled_total != original_total
    return updated_orders, original_total, scaled_total, applied


def _apply_wait6579_probe_canary(
    planned_orders: list[dict],
    *,
    curr_price: int,
    max_budget_krw: int,
    min_qty: int,
    max_qty: int,
) -> tuple[list[dict], int, int, bool]:
    if not planned_orders:
        return [], 0, 0, False

    safe_price = max(1, int(curr_price or 0))
    safe_budget = max(0, int(max_budget_krw or 0))
    safe_min_qty = max(1, int(min_qty or 1))
    configured_max_qty = int(max_qty or 0)
    safe_max_qty = configured_max_qty if configured_max_qty > 0 else 0

    updated_orders: list[dict] = []
    original_total = 0
    scaled_total = 0
    applied = False

    for order in planned_orders:
        item = dict(order or {})
        qty = max(0, int(item.get('qty') or 0))
        price = max(1, int(item.get('price') or safe_price))
        original_total += qty

        if qty <= 0:
            item['qty'] = 0
            updated_orders.append(item)
            continue

        budget_qty_cap = (safe_budget // price) if safe_budget > 0 else qty
        if budget_qty_cap <= 0:
            budget_qty_cap = safe_min_qty
        qty_caps = [qty, budget_qty_cap]
        if safe_max_qty > 0:
            qty_caps.append(safe_max_qty)
        scaled_qty = min(qty_caps)
        scaled_qty = max(1, scaled_qty)
        if scaled_qty != qty:
            applied = True
        item['qty'] = scaled_qty
        scaled_total += scaled_qty
        updated_orders.append(item)

    if scaled_total <= 0 and updated_orders:
        for item in updated_orders:
            if int(item.get('qty') or 0) > 0:
                continue
            item['qty'] = safe_min_qty
            scaled_total += safe_min_qty
            applied = True
            break

    return updated_orders, original_total, scaled_total, applied


def _build_soft_stop_whipsaw_confirmation_decision(
    stock,
    *,
    now_ts: float,
    profit_rate: float,
    dynamic_stop_pct: float,
    emergency_pct: float,
    grace_elapsed_sec: int,
    grace_sec: int,
    curr_price: int,
    buy_price: float,
) -> dict:
    enabled = _rule_bool("SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED", False)
    confirm_sec = max(0, _rule_int("SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC", 0))
    buffer_pct = max(0.0, _rule_float("SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT", 0.0))
    max_worsen_pct = max(0.0, _rule_float("SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT", 0.0))
    used = bool((stock or {}).get("soft_stop_whipsaw_confirmation_used"))
    started_at = _safe_float((stock or {}).get("soft_stop_whipsaw_confirmation_started_at"), 0.0)
    touch_price = _safe_int((stock or {}).get("soft_stop_whipsaw_confirmation_touch_price"), 0)
    if touch_price <= 0:
        touch_price = max(0, int(curr_price or 0))
    elapsed_sec = max(0, int(now_ts - started_at)) if started_at > 0 else 0
    additional_worsen = max(0.0, float(dynamic_stop_pct or 0.0) - float(profit_rate or 0.0))
    rebound_above_sell = int(curr_price or 0) >= touch_price if touch_price > 0 else False
    rebound_above_buy = (
        int(curr_price or 0) >= int(float(buy_price or 0.0))
        if float(buy_price or 0.0) > 0
        else False
    )
    threshold_version = str(
        _rule("SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_THRESHOLD_VERSION", "runtime_default")
        or "runtime_default"
    )
    calibration_state = str(
        _rule("SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_CALIBRATION_STATE", "runtime_default")
        or "runtime_default"
    )
    active = (
        enabled
        and confirm_sec > 0
        and grace_sec >= 0
        and grace_elapsed_sec >= grace_sec
        and not used
        and float(profit_rate or 0.0) > float(emergency_pct or 0.0)
        and float(profit_rate or 0.0) >= (float(dynamic_stop_pct or 0.0) - buffer_pct)
        and additional_worsen <= max_worsen_pct
    )
    expired = False
    if active and started_at > 0 and elapsed_sec >= confirm_sec:
        active = False
        expired = True
    return {
        "enabled": enabled,
        "should_confirm": active,
        "confirm_sec": confirm_sec,
        "buffer_pct": buffer_pct,
        "max_worsen_pct": max_worsen_pct,
        "started_at": started_at,
        "elapsed_sec": elapsed_sec,
        "touch_price": touch_price,
        "additional_worsen": additional_worsen,
        "rebound_above_sell": rebound_above_sell,
        "rebound_above_buy": rebound_above_buy,
        "used": used,
        "expired": expired,
        "threshold_family": "soft_stop_whipsaw_confirmation",
        "threshold_version": threshold_version,
        "threshold_calibration_state": calibration_state,
        "threshold_applied_value": (
            f"enabled={enabled}|confirm_sec={confirm_sec}|buffer_pct={buffer_pct:.2f}|"
            f"max_worsen_pct={max_worsen_pct:.2f}"
        ),
    }


def _emit_scalp_hard_time_stop_shadow(
    *,
    stock: dict,
    code: str,
    held_sec: int,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    ai_exit_min_loss_pct: float,
) -> None:
    if not _rule_bool("SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY", False):
        return
    if _safe_int(stock.get("buy_qty"), 0) <= 0:
        return
    if str(stock.get("status", "") or "").strip().upper() in {"COMPLETED", "SOLD"}:
        return

    raw_candidates = _rule("SCALP_COMMON_HARD_TIME_STOP_SHADOW_MINUTES", (3, 5, 7)) or (3, 5, 7)
    try:
        candidates = sorted({max(1, int(value)) for value in raw_candidates})
    except Exception:
        candidates = [3, 5, 7]

    shadow_min_loss_pct = _rule_float(
        "SCALP_COMMON_HARD_TIME_STOP_SHADOW_MIN_LOSS_PCT", ai_exit_min_loss_pct
    )
    shadow_peak_max_pct = float(
        _rule_float("SCALP_COMMON_HARD_TIME_STOP_SHADOW_MAX_PEAK_PCT", 0.20)
    )
    if profit_rate > shadow_min_loss_pct or peak_profit > shadow_peak_max_pct:
        return

    logged_keys = {
        str(item)
        for item in (stock.get("hard_time_stop_shadow_logged") or [])
        if str(item)
    }
    now_entry_mode = str(stock.get("entry_mode", "")).strip().lower() or "normal"
    pos_tag = normalize_position_tag("SCALPING", stock.get("position_tag"))

    for minute_cut in candidates:
        threshold_sec = minute_cut * 60
        if held_sec < threshold_sec:
            continue
        candidate_key = f"{now_entry_mode}_{minute_cut}m"
        if candidate_key in logged_keys:
            continue
        _log_holding_pipeline(
            stock,
            code,
            "hard_time_stop_shadow",
            candidate=candidate_key,
            threshold_sec=threshold_sec,
            held_sec=held_sec,
            entry_mode=now_entry_mode,
            position_tag=pos_tag,
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            ai_score=f"{current_ai_score:.0f}",
            shadow_only=True,
        )
        logged_keys.add(candidate_key)

    if logged_keys:
        stock["hard_time_stop_shadow_logged"] = sorted(logged_keys)


def _log_dual_persona_shadow_result(stock_name, code, strategy, payload, record_id=None):
    stock_stub = {"name": stock_name, "id": record_id}
    if not isinstance(payload, dict):
        _log_entry_pipeline(
            stock_stub,
            code,
            "dual_persona_shadow_error",
            strategy=strategy,
            decision_type="gatekeeper",
            error="invalid_shadow_payload",
        )
        return

    if payload.get("error"):
        _log_entry_pipeline(
            stock_stub,
            code,
            "dual_persona_shadow_error",
            strategy=strategy,
            decision_type=payload.get("decision_type", "gatekeeper"),
            error=payload.get("error", "unknown"),
            shadow_extra_ms=payload.get("shadow_extra_ms", 0),
        )
        return

    _log_entry_pipeline(
        stock_stub,
        code,
        "dual_persona_shadow",
        strategy=strategy,
        decision_type=payload.get("decision_type", "gatekeeper"),
        dual_mode=payload.get("mode", "shadow"),
        gemini_action=payload.get("gemini_action", ""),
        gemini_score=payload.get("gemini_score", 0),
        aggr_action=payload.get("aggr_action", ""),
        aggr_score=payload.get("aggr_score", 0),
        cons_action=payload.get("cons_action", ""),
        cons_score=payload.get("cons_score", 0),
        cons_veto=str(bool(payload.get("cons_veto", False))).lower(),
        fused_action=payload.get("fused_action", ""),
        fused_score=payload.get("fused_score", 0),
        winner=payload.get("winner", ""),
        agreement_bucket=payload.get("agreement_bucket", ""),
        hard_flags=",".join(payload.get("hard_flags", []) or []) or "-",
        shadow_extra_ms=payload.get("shadow_extra_ms", 0),
    )


def _log_watching_shared_prompt_shadow_result(stock_name, code, payload, record_id=None):
    stock_stub = {"name": stock_name, "id": record_id}
    if not isinstance(payload, dict):
        _log_entry_pipeline(
            stock_stub,
            code,
            "watching_shared_prompt_shadow_error",
            strategy="SCALPING",
            error="invalid_shadow_payload",
        )
        return

    if payload.get("error"):
        _log_entry_pipeline(
            stock_stub,
            code,
            "watching_shared_prompt_shadow_error",
            strategy="SCALPING",
            error=payload.get("error", "unknown"),
            gpt_model=payload.get("gpt_model", "-"),
            shadow_extra_ms=payload.get("shadow_extra_ms", 0),
        )
        return

    _log_entry_pipeline(
        stock_stub,
        code,
        "watching_shared_prompt_shadow",
        strategy="SCALPING",
        gemini_action=payload.get("gemini_action", ""),
        gemini_score=payload.get("gemini_score", 0),
        gpt_action=payload.get("gpt_action", ""),
        gpt_score=payload.get("gpt_score", 0),
        action_diverged=str(bool(payload.get("action_diverged", False))).lower(),
        score_gap=payload.get("score_gap", 0),
        gpt_model=payload.get("gpt_model", "-"),
        shadow_extra_ms=payload.get("shadow_extra_ms", 0),
    )


def _shadow_runtime_enabled() -> bool:
    return _rule_bool("OPENAI_DUAL_PERSONA_ENABLED", False)


def _submit_watching_shared_prompt_shadow(*, stock_name, code, ws_data, recent_ticks, recent_candles, gemini_result, record_id=None):
    if (
        not _shadow_runtime_enabled()
        or DUAL_PERSONA_ENGINE is None
        or not hasattr(DUAL_PERSONA_ENGINE, "submit_watching_shared_prompt_shadow")
    ):
        return
    try:
        DUAL_PERSONA_ENGINE.submit_watching_shared_prompt_shadow(
            stock_name=stock_name,
            stock_code=code,
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            gemini_result=gemini_result,
            callback=lambda payload: _log_watching_shared_prompt_shadow_result(
                stock_name,
                code,
                payload,
                record_id=record_id,
            ),
        )
    except Exception as e:
        log_error(f"🚨 [WATCHING shared prompt shadow 제출 실패] {stock_name}({code}): {e}")


def _submit_gatekeeper_dual_persona_shadow(*, stock_name, code, strategy, realtime_ctx, gatekeeper, record_id=None):
    if not _shadow_runtime_enabled() or DUAL_PERSONA_ENGINE is None:
        return
    try:
        DUAL_PERSONA_ENGINE.submit_gatekeeper_shadow(
            stock_name=stock_name,
            stock_code=code,
            strategy=strategy,
            realtime_ctx=realtime_ctx,
            gemini_result=gatekeeper,
            callback=lambda payload: _log_dual_persona_shadow_result(
                stock_name,
                code,
                strategy,
                payload,
                record_id=record_id,
            ),
        )
    except Exception as e:
        log_error(f"🚨 [Gatekeeper 듀얼 페르소나 shadow 제출 실패] {stock_name}({code}): {e}")


def _reason_codes(**checks) -> str:
    failed = [name for name, allowed in checks.items() if not allowed]
    return ",".join(failed) if failed else "eligible"


def _get_swing_gap_threshold(strategy: str) -> float:
    fallback = _rule_float('MAX_SWING_GAP_UP_PCT', 3.0)
    strategy_upper = str(strategy or '').upper()
    if strategy_upper == 'KOSPI_ML':
        return _rule_float('MAX_SWING_GAP_UP_PCT_KOSPI', fallback)
    return _rule_float('MAX_SWING_GAP_UP_PCT_KOSDAQ', fallback)


def _resolve_gatekeeper_reject_cooldown(action_label: str) -> tuple[int, str]:
    action = str(action_label or '').strip()
    if action == '눌림 대기':
        return (
            _rule_int('ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN', 60 * 20),
            'pullback_wait',
        )
    if action in {'전량 회피', '둘 다 아님'}:
        return (
            _rule_int('ML_GATEKEEPER_REJECT_COOLDOWN', 60 * 60 * 2),
            'hard_reject',
        )
    return (
        _rule_int('ML_GATEKEEPER_NEUTRAL_COOLDOWN', 60 * 30),
        'neutral_hold',
    )


def _resolve_stock_marcap(stock, code) -> int:
    """시가총액 조회 (프로세스 레벨 TTL 캐시 + stock 캐시)."""
    existing = _safe_int(stock.get('marcap'), 0)
    if existing > 0:
        return existing
    now_ts = time.time()
    norm_code = str(code or "").strip()[:6]
    _prune_marcap_cache(now_ts)
    if norm_code:
        cached = _MARCAP_CACHE.get(norm_code)
        if cached is not None:
            val, exp_ts = cached
            if now_ts < exp_ts and val > 0:
                stock['marcap'] = val
                return val
    if DB is None:
        return 0
    try:
        marcap = int(DB.get_latest_marcap(code) or 0)
    except Exception:
        marcap = 0
    if marcap > 0 and norm_code:
        _MARCAP_CACHE[norm_code] = (marcap, now_ts + _MARCAP_CACHE_TTL)
        stock['marcap'] = marcap
    return marcap


def _dispatch_scalp_preset_exit(
    *,
    stock,
    code,
    now_ts,
    curr_p,
    buy_p,
    profit_rate,
    peak_profit,
    strategy,
    sell_reason_type,
    reason,
    exit_rule,
):
    target_id = stock.get('id')
    expected_qty = _safe_int(stock.get('buy_qty'), 0)
    orig_ord_no = stock.get('preset_tp_ord_no', '')
    preset_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
    preset_held_sec = 0
    try:
        if stock.get('order_time'):
            preset_held_sec = max(0, int(now_ts - float(stock.get('order_time') or 0)))
    except Exception as exc:
        log_error(
            f"[SCALP_PRESET_EXIT] order_time 파싱 실패 ({stock.get('code', '-')}, {stock.get('order_time')}): {exc}"
        )
        preset_held_sec = 0

    _remember_exit_context(
        stock=stock,
        exit_rule=exit_rule,
        reason=reason,
        peak_profit=peak_profit,
        held_sec=preset_held_sec,
        current_ai_score=preset_ai_score,
    )
    stock['last_exit_reason'] = reason
    exit_decision_source = str(stock.get("last_exit_decision_source") or "MANUAL")
    _log_holding_pipeline(
        stock,
        code,
        "exit_signal",
        sell_reason_type=sell_reason_type,
        reason=reason,
        exit_rule=exit_rule or "-",
        exit_decision_source=exit_decision_source,
        profit_rate=f"{profit_rate:+.2f}",
        peak_profit=f"{peak_profit:+.2f}",
        current_ai_score=f"{preset_ai_score:.0f}",
        held_sec=preset_held_sec,
        curr_price=curr_p,
        buy_price=buy_p,
        buy_qty=expected_qty,
    )

    if _is_scalp_simulated_position(stock, strategy):
        _complete_scalp_simulated_sell(
            stock=stock,
            code=code,
            ws_data={"curr": curr_p},
            curr_price=curr_p,
            now_ts=now_ts,
            sell_reason_type=sell_reason_type,
            exit_rule=exit_rule,
            profit_rate=profit_rate,
        )
        return

    try:
        if target_id:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "SELL_ORDERED"})
    except Exception as e:
        log_error(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")

    rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
    pending_sell_msg = ""
    set_fields = {
        'last_exit_reason': reason,
    }
    ord_no = ''
    if rem_qty > 0:
        sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
        set_fields.update({
            'exit_requested': True,
            'exit_order_type': '16',
            'exit_order_time': now_ts,
            'sell_order_time': now_ts,
        })
        ord_no = str(sell_res.get('ord_no', '') or '') if isinstance(sell_res, dict) else ''
        if ord_no:
            set_fields['sell_ord_no'] = ord_no
        sign = _resolve_sell_order_sign(sell_reason_type, profit_rate)
        pending_sell_msg = (
            f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n"
            f"사유: `{reason}`\n"
            f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)"
        )
        set_fields['pending_sell_msg'] = pending_sell_msg
        _log_holding_pipeline(
            stock,
            code,
            "sell_order_sent",
            sell_reason_type=sell_reason_type,
            exit_rule=exit_rule or "-",
            exit_decision_source=exit_decision_source,
            qty=rem_qty,
            ord_no=ord_no or "-",
            order_type=set_fields.get("exit_order_type") or stock.get("exit_order_type") or "-",
            profit_rate=f"{profit_rate:+.2f}",
        )

    _mutate_stock_state(
        stock,
        set_fields=set_fields | {
            'status': 'SELL_ORDERED',
            'sell_target_price': curr_p,
        },
    )


def _get_best_levels_from_ws(ws_data):
    orderbook = ws_data.get('orderbook') or {}
    asks = orderbook.get('asks') or []
    bids = orderbook.get('bids') or []
    best_ask = 0
    best_bid = 0
    try:
        if asks:
            best_ask = _safe_int(asks[-1].get('price'), 0)
    except Exception:
        best_ask = 0
    try:
        if bids:
            best_bid = _safe_int(bids[0].get('price'), 0)
    except Exception:
            best_bid = 0
    return best_ask, best_bid


def _compute_price_below_bid_bps(price, best_bid):
    price = _coerce_int_value(price)
    best_bid = _coerce_int_value(best_bid)
    if price <= 0 or best_bid <= 0 or price >= best_bid:
        return 0
    return int(round(((best_bid - price) / best_bid) * 10000))


def _build_entry_price_snapshot_fields(latency_gate, *, request_price, curr_price, best_bid, best_ask):
    submitted_order_price = _coerce_int_value(request_price)
    defensive_order_price = _coerce_int_value(latency_gate.get('latency_guarded_order_price'))
    reference_target_price = _coerce_int_value(latency_gate.get('target_buy_price'))
    price_below_bid_bps = _compute_price_below_bid_bps(submitted_order_price, best_bid)

    resolution_reason = str(
        latency_gate.get('price_resolution_reason')
        or latency_gate.get('entry_price_guard')
        or 'none'
    )
    if reference_target_price > 0 and defensive_order_price > 0:
        if (
            submitted_order_price <= reference_target_price < defensive_order_price
            and not resolution_reason.startswith("ai_tier2_")
        ):
            resolution_reason = 'reference_target_cap'
    if (
        defensive_order_price > 0
        and submitted_order_price == defensive_order_price
        and resolution_reason not in {'scalping_reference_rejected_defensive'}
    ):
        resolution_reason = 'defensive_order_price'

    return {
        'submitted_order_price': submitted_order_price,
        'mark_price_at_submit': _coerce_int_value(curr_price),
        'best_bid_at_submit': _coerce_int_value(best_bid),
        'best_ask_at_submit': _coerce_int_value(best_ask),
        'defensive_order_price': defensive_order_price,
        'reference_target_price': reference_target_price,
        'resolved_order_price': submitted_order_price,
        'resolution_reason': resolution_reason,
        'price_below_bid_bps': price_below_bid_bps,
        'reference_target_applied': bool(latency_gate.get('reference_target_applied')),
        'reference_target_rejected_reason': str(latency_gate.get('reference_target_rejected_reason') or ''),
        'reference_target_below_bid_bps': _coerce_int_value(latency_gate.get('reference_target_below_bid_bps')),
        'reference_target_max_below_bid_bps': _coerce_int_value(
            latency_gate.get('reference_target_max_below_bid_bps')
        ),
        'entry_price_resolver_enabled': bool(latency_gate.get('entry_price_resolver_enabled')),
        'ai_entry_price_canary_applied': bool(latency_gate.get('ai_entry_price_canary_applied')),
        'ai_entry_price_canary_action': str(latency_gate.get('ai_entry_price_canary_action') or ''),
        'ai_entry_price_canary_confidence': _coerce_int_value(
            latency_gate.get('ai_entry_price_canary_confidence')
        ),
        'ai_entry_price_canary_reason': str(latency_gate.get('ai_entry_price_canary_reason') or ''),
        'ai_entry_price_canary_max_wait_sec': _coerce_int_value(
            latency_gate.get('ai_entry_price_canary_max_wait_sec')
        ),
    }


def _build_orderbook_micro_context(
    latency_gate,
    *,
    curr_price,
    best_bid,
    best_ask,
    respect_scalping_flag: bool = True,
):
    if respect_scalping_flag and not bool(_rule("SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED", True)):
        return None
    stability = (latency_gate or {}).get("orderbook_stability") or {}
    micro = stability.get("orderbook_micro") if isinstance(stability, dict) else None
    if not isinstance(micro, dict):
        return {
            "ready": False,
            "reason": "missing_snapshot",
            "micro_state": "insufficient",
            "sample_quote_count": 0,
            "observer_healthy": False,
            "observer_missing_reason": "missing_snapshot",
            "ofi_threshold_source": "fallback",
            "ofi_threshold_fallback_reason": "missing_snapshot",
            "ofi_bucket_key": "spread=unknown|price=unknown|depth=unknown|sample=insufficient",
            "ofi_calibration_bucket": "spread=unknown|price=unknown|depth=unknown|sample=insufficient",
            "ofi_calibration_warning": "missing_snapshot",
        }

    tick_size = 1
    try:
        tick_size = int(kiwoom_utils.get_tick_size(_coerce_int_value(curr_price) or _coerce_int_value(best_bid)) or 1)
    except Exception:
        tick_size = 1
    spread_ticks = 0
    if _coerce_int_value(best_ask) > 0 and _coerce_int_value(best_bid) > 0 and tick_size > 0:
        spread_ticks = max(0, int(round((_coerce_int_value(best_ask) - _coerce_int_value(best_bid)) / tick_size)))

    context = {
        "ready": bool(micro.get("ready")),
        "reason": str(micro.get("reason") or ""),
        "qi": micro.get("qi"),
        "qi_ewma": micro.get("qi_ewma"),
        "ofi_norm": micro.get("ofi_norm"),
        "ofi_z": micro.get("ofi_z"),
        "depth_ewma": micro.get("depth_ewma"),
        "micro_state": str(micro.get("micro_state") or "insufficient"),
        "sample_quote_count": _coerce_int_value(micro.get("sample_quote_count")),
        "spread_ticks": spread_ticks,
    }
    for key in (
        "captured_at_ms",
        "snapshot_age_ms",
        "observer_healthy",
        "observer_missing_reason",
        "observer_last_quote_age_ms",
        "observer_last_trade_age_ms",
        "micro_window_sec",
        "micro_z_min_samples",
        "micro_lambda",
        "ofi_bull_threshold",
        "ofi_bear_threshold",
        "qi_bull_threshold",
        "qi_bear_threshold",
        "ofi_threshold_source",
        "ofi_threshold_bucket_key",
        "ofi_threshold_manifest_id",
        "ofi_threshold_manifest_version",
        "ofi_threshold_fallback_reason",
        "ofi_calibration_bucket",
        "ofi_bucket_key",
        "ofi_symbol_sample_count",
        "ofi_bucket_sample_count",
        "ofi_symbol_bearish_rate",
        "ofi_bucket_bearish_rate",
        "ofi_symbol_bullish_rate",
        "ofi_bucket_bullish_rate",
        "ofi_symbol_bucket_deviation",
        "ofi_calibration_warning",
    ):
        if key in micro:
            context[key] = micro.get(key)
    return context


def _build_orderbook_micro_log_fields(micro):
    if not isinstance(micro, dict):
        return {
            "orderbook_micro_ready": False,
            "orderbook_micro_state": "missing",
            "orderbook_micro_reason": "micro_context_missing",
            "orderbook_micro_snapshot_age_ms": "-",
            "orderbook_micro_observer_healthy": False,
        }
    fields = {
        "orderbook_micro_ready": bool(micro.get("ready")),
        "orderbook_micro_reason": str(micro.get("reason") or ""),
        "orderbook_micro_state": str(micro.get("micro_state") or "insufficient"),
        "orderbook_micro_sample_quote_count": _coerce_int_value(micro.get("sample_quote_count")),
    }
    for key in (
        "qi",
        "qi_ewma",
        "ofi_norm",
        "ofi_z",
        "depth_ewma",
        "spread_ticks",
        "captured_at_ms",
        "snapshot_age_ms",
        "observer_healthy",
        "observer_missing_reason",
        "observer_last_quote_age_ms",
        "observer_last_trade_age_ms",
        "micro_window_sec",
        "micro_z_min_samples",
        "micro_lambda",
        "ofi_bull_threshold",
        "ofi_bear_threshold",
        "qi_bull_threshold",
        "qi_bear_threshold",
        "ofi_threshold_source",
        "ofi_threshold_bucket_key",
        "ofi_threshold_manifest_id",
        "ofi_threshold_manifest_version",
        "ofi_threshold_fallback_reason",
        "ofi_calibration_bucket",
        "ofi_bucket_key",
        "ofi_symbol_sample_count",
        "ofi_bucket_sample_count",
        "ofi_symbol_bearish_rate",
        "ofi_bucket_bearish_rate",
        "ofi_symbol_bullish_rate",
        "ofi_bucket_bullish_rate",
        "ofi_symbol_bucket_deviation",
        "ofi_calibration_warning",
    ):
        value = micro.get(key)
        fields[f"orderbook_micro_{key}"] = "-" if value is None else value
    for key, value in micro.items():
        if not str(key).startswith("wide_") or key == "wide_windows":
            continue
        fields[f"orderbook_micro_{key}"] = "-" if value is None else value
    return fields


def _build_swing_orderbook_micro_context(
    code: str,
    *,
    curr_price: int,
    latency_gate: dict | None = None,
    best_bid: int = 0,
    best_ask: int = 0,
) -> dict | None:
    if isinstance(latency_gate, dict):
        micro = _build_orderbook_micro_context(
            latency_gate,
            curr_price=curr_price,
            best_bid=best_bid,
            best_ask=best_ask,
            respect_scalping_flag=False,
        )
        if isinstance(micro, dict):
            return micro
    return _build_live_orderbook_micro_context(code, curr_price=curr_price)


def _build_swing_ws_quote_quality_fields(ws_data: dict | None) -> dict:
    best_ask, best_bid = _get_best_levels_from_ws(ws_data or {})
    quote_age_sec = _get_ws_snapshot_age_sec(ws_data or {})
    quote_age_ms = "-" if quote_age_sec is None else int(round(quote_age_sec * 1000.0))
    quote_present = bool(best_ask > 0 or best_bid > 0 or _safe_int((ws_data or {}).get("curr"), 0) > 0)
    quote_stale = quote_age_ms != "-" and int(quote_age_ms) > max(1, _rule_int("OFI_AI_SMOOTHING_STALE_THRESHOLD_MS", 700))
    if quote_age_sec is not None:
        source = "last_ws_update_ts"
    elif quote_present:
        source = "ws_quote_without_timestamp"
    else:
        source = "missing"
    return {
        "swing_micro_ws_quote_present": bool(quote_present),
        "swing_micro_ws_quote_source": source,
        "swing_micro_ws_quote_age_ms": quote_age_ms,
        "swing_micro_ws_quote_stale": bool(quote_stale) if quote_age_ms != "-" else "unknown",
        "swing_micro_ws_best_bid": best_bid or "-",
        "swing_micro_ws_best_ask": best_ask or "-",
    }


def _build_swing_micro_log_fields(
    micro: dict | None,
    *,
    phase: str,
    add_type: str | None = None,
    ws_data: dict | None = None,
) -> dict:
    fields = _build_orderbook_micro_log_fields(micro)
    ws_quote_fields = _build_swing_ws_quote_quality_fields(ws_data)
    state = str(fields.get("orderbook_micro_state") or "missing").strip().lower()
    ready = bool(fields.get("orderbook_micro_ready"))
    observer_healthy = fields.get("orderbook_micro_observer_healthy")
    if observer_healthy == "-":
        observer_healthy = False
    observer_unhealthy = observer_healthy is not True
    snapshot_age_ms = _safe_float(fields.get("orderbook_micro_snapshot_age_ms"), None)
    stale_threshold_ms = max(1, _rule_int("OFI_AI_SMOOTHING_STALE_THRESHOLD_MS", 700))
    is_stale = snapshot_age_ms is not None and snapshot_age_ms > stale_threshold_ms
    missing = (
        not isinstance(micro, dict)
        or not ready
        or state in {"", "missing", "insufficient"}
        or observer_unhealthy
        or is_stale
    )
    if missing:
        advice = "MISSING"
        price_action = "NO_CHANGE"
        timeout_sec = 0
        reason = "missing_stale_or_insufficient_orderbook_micro"
        source_quality_status = "source_quality_blocker"
        if (
            observer_unhealthy
            and ws_quote_fields["swing_micro_ws_quote_present"] is True
            and ws_quote_fields["swing_micro_ws_quote_stale"] is False
        ):
            source_quality_status = "observer_gap_with_fresh_ws_quote"
    elif state == "bullish":
        advice = "SUPPORT_ENTRY"
        price_action = "ALLOW_EXISTING_PRICE"
        timeout_sec = 0
        reason = "ofi_qi_bullish_support_observed"
        source_quality_status = "ok"
    elif state == "bearish":
        advice = "RISK_BEARISH"
        price_action = "WAIT_FOR_PULLBACK"
        timeout_sec = 30
        reason = "ofi_qi_bearish_risk_observed"
        source_quality_status = "ok"
    else:
        advice = "WAIT_FOR_PULLBACK"
        price_action = "KEEP_EXISTING_PRICE"
        timeout_sec = 0
        reason = "ofi_qi_neutral_or_mixed_observed"
        source_quality_status = "ok"

    add_label = str(add_type or "").upper()
    micro_support = add_label == "PYRAMID" and advice in {"SUPPORT_ENTRY", "WAIT_FOR_PULLBACK"}
    micro_risk = add_label == "PYRAMID" and state == "bearish" and advice != "MISSING"
    recovery_support_observed = add_label == "AVG_DOWN" and advice == "SUPPORT_ENTRY"
    fields.update(
        {
            "swing_micro_phase": phase,
            "swing_micro_advice": advice,
            "swing_micro_counterfactual_price_action": price_action,
            "swing_micro_counterfactual_timeout_sec": timeout_sec,
            "swing_micro_counterfactual_reason": reason,
            "swing_micro_runtime_effect": False,
            "swing_micro_observe_only": True,
            "swing_micro_source_quality_status": source_quality_status,
            "swing_micro_state": state,
            "swing_micro_stale": bool(is_stale),
            "swing_micro_micro_support": bool(micro_support),
            "swing_micro_micro_risk": bool(micro_risk),
            "swing_micro_support": bool(micro_support),
            "swing_micro_risk": bool(micro_risk),
            "swing_micro_recovery_support_observed": bool(recovery_support_observed),
            "recovery_support_observed": bool(recovery_support_observed),
            **ws_quote_fields,
        }
    )
    return fields


def _ofi_ai_smoothing_config() -> OfiSmoothingConfig:
    return OfiSmoothingConfig(
        raw_weight=_rule_float("OFI_AI_SMOOTHING_RAW_WEIGHT", 0.30),
        bullish_threshold=_rule_float("OFI_AI_SMOOTHING_BULLISH_THRESHOLD", 0.45),
        bearish_threshold=_rule_float("OFI_AI_SMOOTHING_BEARISH_THRESHOLD", -0.45),
        release_threshold=_rule_float("OFI_AI_SMOOTHING_RELEASE_THRESHOLD", 0.15),
        persistence_required=max(1, _rule_int("OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED", 2)),
        stale_threshold_ms=max(1, _rule_int("OFI_AI_SMOOTHING_STALE_THRESHOLD_MS", 700)),
    )


def _load_holding_flow_ofi_state(stock: dict) -> OfiSmoothingState:
    return OfiSmoothingState(
        micro_score_raw=_safe_float(stock.get("holding_flow_ofi_micro_score_raw"), None),
        micro_score_smooth=_safe_float(stock.get("holding_flow_ofi_micro_score_smooth"), 0.0),
        regime=str(stock.get("holding_flow_ofi_regime") or OFI_NEUTRAL),
        bullish_count=_safe_int(stock.get("holding_flow_ofi_bullish_count"), 0),
        bearish_count=_safe_int(stock.get("holding_flow_ofi_bearish_count"), 0),
        snapshot_age_ms=_safe_float(stock.get("holding_flow_ofi_snapshot_age_ms"), None),
        reason=str(stock.get("holding_flow_ofi_reason") or "ready"),
    )


def _store_holding_flow_ofi_state(stock: dict, state: OfiSmoothingState) -> None:
    _mutate_stock_state(
        stock,
        set_fields={
            "holding_flow_ofi_micro_score_raw": state.micro_score_raw,
            "holding_flow_ofi_micro_score_smooth": state.micro_score_smooth,
            "holding_flow_ofi_regime": state.regime,
            "holding_flow_ofi_bullish_count": state.bullish_count,
            "holding_flow_ofi_bearish_count": state.bearish_count,
            "holding_flow_ofi_snapshot_age_ms": state.snapshot_age_ms,
            "holding_flow_ofi_reason": state.reason,
        },
    )


def _evaluate_entry_skip_ofi_smoothing(orderbook_micro: dict | None) -> OfiSmoothingState:
    return evaluate_ofi_smoothing(orderbook_micro, config=_ofi_ai_smoothing_config())


def _should_demote_entry_ai_price_skip(confidence: int, orderbook_micro: dict | None) -> tuple[bool, OfiSmoothingState]:
    state = _evaluate_entry_skip_ofi_smoothing(orderbook_micro)
    if not _rule_bool("SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_ENABLED", True):
        return False, state
    max_confidence = _rule_int("SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE", 90)
    if int(confidence or 0) >= max_confidence:
        return False, state
    return entry_skip_demotion_allowed(orderbook_micro, state), state


def _build_live_orderbook_micro_context(code: str, *, curr_price: int) -> dict | None:
    try:
        snapshot = ORDERBOOK_STABILITY_OBSERVER.snapshot(code)
    except Exception:
        return None
    if not isinstance(snapshot, dict):
        return None
    micro = snapshot.get("orderbook_micro")
    if not isinstance(micro, dict):
        return None
    context = dict(micro)
    best_bid = _coerce_int_value(snapshot.get("best_bid"))
    best_ask = _coerce_int_value(snapshot.get("best_ask"))
    tick_size = 1
    try:
        tick_size = int(kiwoom_utils.get_tick_size(_coerce_int_value(curr_price) or best_bid) or 1)
    except Exception:
        tick_size = 1
    if best_ask > 0 and best_bid > 0 and tick_size > 0:
        context["spread_ticks"] = max(0, int(round((best_ask - best_bid) / tick_size)))
    else:
        context.setdefault("spread_ticks", 0)
    context.setdefault("captured_at_ms", snapshot.get("captured_at_ms"))
    context.setdefault("snapshot_age_ms", snapshot.get("snapshot_age_ms"))
    context.setdefault("observer_healthy", snapshot.get("observer_healthy"))
    context.setdefault("observer_missing_reason", snapshot.get("observer_missing_reason"))
    context.setdefault("observer_last_quote_age_ms", snapshot.get("observer_last_quote_age_ms"))
    context.setdefault("observer_last_trade_age_ms", snapshot.get("observer_last_trade_age_ms"))
    return context


def _evaluate_holding_flow_ofi_state(stock: dict, code: str, *, curr_price: int) -> tuple[dict | None, OfiSmoothingState]:
    micro = _build_live_orderbook_micro_context(code, curr_price=curr_price)
    state = evaluate_ofi_smoothing(
        micro,
        previous=_load_holding_flow_ofi_state(stock),
        config=_ofi_ai_smoothing_config(),
    )
    _store_holding_flow_ofi_state(stock, state)
    return micro, state


def _build_entry_ai_price_skip_policy_fields(orderbook_micro):
    micro = orderbook_micro if isinstance(orderbook_micro, dict) else {}
    state = str(micro.get("micro_state") or "missing").strip().lower()
    ready = bool(micro.get("ready"))
    if ready and state == "bearish":
        return {
            "entry_ai_price_skip_policy_warning": "",
            "entry_ai_price_skip_policy_basis": "ofi_bearish_supported",
        }
    if not ready:
        return {
            "entry_ai_price_skip_policy_warning": "ofi_not_ready",
            "entry_ai_price_skip_policy_basis": state or "missing",
        }
    if state in {"neutral", "insufficient", "missing", ""}:
        return {
            "entry_ai_price_skip_policy_warning": "skip_without_bearish_ofi",
            "entry_ai_price_skip_policy_basis": state or "missing",
        }
    return {
        "entry_ai_price_skip_policy_warning": "skip_without_bearish_ofi",
        "entry_ai_price_skip_policy_basis": state,
    }


def _is_pre_submit_price_guard_block(strategy, price, best_bid):
    if strategy not in ('SCALPING', 'SCALP'):
        return False
    if not bool(_rule("SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED", True)):
        return False
    threshold_bps = int(_rule("SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS", 80) or 80)
    if threshold_bps < 0:
        return False
    return _compute_price_below_bid_bps(price, best_bid) > threshold_bps


def _entry_planned_total_qty(planned_orders) -> int:
    total = 0
    for order in planned_orders or []:
        try:
            total += max(0, int((order or {}).get("qty", 0) or 0))
        except (TypeError, ValueError):
            continue
    return total


def _resolve_passive_probe_candidate_price(*, candidate_price, best_bid, curr_price, max_below_bid_ticks):
    candidate_price = _coerce_int_value(candidate_price)
    best_bid = _coerce_int_value(best_bid)
    if candidate_price <= 0 or best_bid <= 0:
        return candidate_price, 0, 0
    tick_size = int(kiwoom_utils.get_tick_size(_coerce_int_value(curr_price) or best_bid) or 1)
    tick_size = max(1, tick_size)
    max_below_bid_ticks = max(0, int(max_below_bid_ticks or 0))
    floor_price = clamp_price_to_tick(best_bid - (tick_size * max_below_bid_ticks))
    if floor_price <= 0:
        return candidate_price, tick_size, 0
    return max(candidate_price, floor_price), tick_size, floor_price


def _maybe_apply_entry_passive_probe(
    *,
    stock,
    latency_gate,
    planned_orders,
    action,
    candidate_price,
    curr_price,
    best_bid,
    best_ask,
):
    if not bool(_rule("SCALPING_ENTRY_PASSIVE_PROBE_ENABLED", True)):
        return candidate_price, {}
    if str(action or "").strip().upper() != "USE_DEFENSIVE":
        return candidate_price, {}
    latency_state = str((latency_gate or {}).get("latency_state") or "").strip().upper()
    if latency_state != "DANGER":
        return candidate_price, {}
    watching_action = str((stock or {}).get("last_watching_ai_action") or "").strip().upper()
    watching_score = _safe_float((stock or {}).get("last_watching_ai_score"), 0.0)
    min_score = float(_rule("SCALPING_ENTRY_PASSIVE_PROBE_MIN_AI_SCORE", 75) or 75)
    if watching_action != "WAIT" or watching_score < min_score:
        return candidate_price, {}
    max_qty = int(_rule("SCALPING_ENTRY_PASSIVE_PROBE_MAX_QTY", 1) or 1)
    total_qty = _entry_planned_total_qty(planned_orders)
    if total_qty <= 0 or total_qty > max_qty:
        return candidate_price, {}

    max_below_bid_ticks = int(_rule("SCALPING_ENTRY_PASSIVE_PROBE_MAX_BELOW_BID_TICKS", 1) or 1)
    adjusted_price, tick_size, floor_price = _resolve_passive_probe_candidate_price(
        candidate_price=candidate_price,
        best_bid=best_bid,
        curr_price=curr_price,
        max_below_bid_ticks=max_below_bid_ticks,
    )
    if adjusted_price <= 0:
        return candidate_price, {}
    if _coerce_int_value(best_ask) > 0 and adjusted_price > _coerce_int_value(best_ask):
        return candidate_price, {}

    return adjusted_price, {
        "entry_order_lifecycle": "passive_probe",
        "entry_passive_probe_applied": True,
        "entry_passive_probe_reason": "wait_score_danger_defensive_1share",
        "entry_passive_probe_original_price": _coerce_int_value(candidate_price),
        "entry_passive_probe_adjusted_price": _coerce_int_value(adjusted_price),
        "entry_passive_probe_floor_price": _coerce_int_value(floor_price),
        "entry_passive_probe_tick_size": int(tick_size or 0),
        "entry_passive_probe_max_below_bid_ticks": max_below_bid_ticks,
        "entry_passive_probe_ai_action": watching_action,
        "entry_passive_probe_ai_score": f"{watching_score:.1f}",
        "entry_passive_probe_total_qty": total_qty,
    }


def _build_entry_submit_revalidation_fields(ws_data, latency_gate, *, now_ts=None):
    now_ts = float(now_ts or time.time())
    decision_ts = _safe_float((latency_gate or {}).get("ai_entry_price_canary_decision_ts"), 0.0)
    context_age_ms = _coerce_int_value((latency_gate or {}).get("ai_entry_price_canary_context_age_ms"))
    quote_age_sec = _get_ws_snapshot_age_sec(ws_data)
    quote_age_ms = "-" if quote_age_sec is None else int(round(quote_age_sec * 1000.0))
    decision_age_ms = "-" if decision_ts <= 0 else int(round(max(0.0, now_ts - decision_ts) * 1000.0))
    max_context_age_ms = int(_rule("SCALPING_ENTRY_SUBMIT_REVALIDATION_MAX_CONTEXT_AGE_MS", 8000) or 8000)
    max_quote_age_ms = int(_rule("SCALPING_ENTRY_SUBMIT_REVALIDATION_MAX_QUOTE_AGE_MS", 2000) or 2000)
    context_stale = context_age_ms > max_context_age_ms if context_age_ms else False
    quote_stale = quote_age_ms != "-" and int(quote_age_ms) > max_quote_age_ms
    return {
        "entry_submit_revalidation": "checked",
        "price_decision_age_ms": decision_age_ms,
        "price_decision_context_age_ms": context_age_ms or "-",
        "quote_age_at_submit_ms": quote_age_ms,
        "price_context_stale_at_submit": bool(context_stale),
        "quote_stale_at_submit": bool(quote_stale),
        "entry_submit_revalidation_warning": "stale_context_or_quote" if (context_stale or quote_stale) else "",
        "entry_order_lifecycle": str((latency_gate or {}).get("entry_order_lifecycle") or "standard"),
        "entry_passive_probe_applied": bool((latency_gate or {}).get("entry_passive_probe_applied")),
        "entry_passive_probe_reason": str((latency_gate or {}).get("entry_passive_probe_reason") or ""),
    }


def _is_passive_probe_stale_submit_block(submit_revalidation_fields) -> bool:
    if not bool(_rule("SCALPING_ENTRY_PASSIVE_PROBE_STALE_SUBMIT_BLOCK_ENABLED", True)):
        return False
    fields = submit_revalidation_fields or {}
    if str(fields.get("entry_order_lifecycle") or "").strip() != "passive_probe":
        return False
    return bool(fields.get("price_context_stale_at_submit") or fields.get("quote_stale_at_submit"))


def _resolve_buy_order_timeout_sec(stock, strategy):
    normalized_strategy = 'SCALPING' if str(strategy or '').upper() in ('SCALPING', 'SCALP') else str(strategy or '').upper()
    if normalized_strategy != 'SCALPING':
        if _coerce_int_value((stock or {}).get('target_buy_price')) > 0:
            return _rule_int('RESERVE_TIMEOUT_SEC', 1200)
        return _rule_int('ORDER_TIMEOUT_SEC', 30)

    explicit_timeout = _coerce_int_value((stock or {}).get('entry_timeout_sec_override'))
    if explicit_timeout > 0:
        return max(5, min(1200, explicit_timeout))

    profile = str(
        (stock or {}).get('entry_timeout_profile')
        or (stock or {}).get('entry_price_timeout_profile')
        or (stock or {}).get('entry_mode')
        or ''
    ).strip().upper()
    pos_tag = normalize_position_tag('SCALPING', (stock or {}).get('position_tag'))

    if profile in {'RESERVE', 'RESERVED'} or pos_tag in {'RESERVE', 'RESERVED'}:
        return _rule_int('SCALPING_RESERVE_ENTRY_TIMEOUT_SEC', 1200)
    if 'PULLBACK' in profile or 'PULLBACK' in pos_tag:
        return _rule_int('SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC', 600)
    if 'BREAKOUT' in profile or 'BREAKOUT' in pos_tag:
        return _rule_int('SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC', 120)
    return _rule_int('SCALPING_ENTRY_TIMEOUT_SEC', 90)


def _build_entry_ai_price_context(stock, latency_gate, *, curr_price, best_bid, best_ask):
    ctx = {
        "strategy": normalize_strategy((stock or {}).get("strategy")),
        "position_tag": normalize_position_tag("SCALPING", (stock or {}).get("position_tag")),
        "current_price": _coerce_int_value(curr_price),
        "best_bid": _coerce_int_value(best_bid),
        "best_ask": _coerce_int_value(best_ask),
        "reference_target_price": _coerce_int_value((latency_gate or {}).get("target_buy_price")),
        "defensive_order_price": _coerce_int_value((latency_gate or {}).get("latency_guarded_order_price")),
        "normal_defensive_order_price": _coerce_int_value((latency_gate or {}).get("normal_defensive_order_price")),
        "resolved_order_price": _coerce_int_value((latency_gate or {}).get("order_price")),
        "resolution_reason": str((latency_gate or {}).get("price_resolution_reason") or ""),
        "price_below_bid_bps": _compute_price_below_bid_bps(
            _coerce_int_value((latency_gate or {}).get("order_price")),
            best_bid,
        ),
        "reference_target_below_bid_bps": _coerce_int_value((latency_gate or {}).get("reference_target_below_bid_bps")),
        "latency_state": str((latency_gate or {}).get("latency_state") or ""),
        "ws_age_ms": _coerce_int_value((latency_gate or {}).get("ws_age_ms")),
        "ws_jitter_ms": _coerce_int_value((latency_gate or {}).get("ws_jitter_ms")),
        "spread_ratio": float((latency_gate or {}).get("spread_ratio", 0.0) or 0.0),
        "quote_stale": bool((latency_gate or {}).get("quote_stale")),
        "signal_score": round(float((stock or {}).get("rt_ai_prob", (stock or {}).get("prob", 0.0)) or 0.0) * 100.0, 2),
    }
    orderbook_micro = _build_orderbook_micro_context(
        latency_gate,
        curr_price=curr_price,
        best_bid=best_bid,
        best_ask=best_ask,
    )
    if orderbook_micro is not None:
        ctx["orderbook_micro"] = orderbook_micro
    return ctx


def _apply_entry_ai_price_canary(
    *,
    stock,
    code,
    strategy,
    ws_data,
    ai_engine,
    latency_gate,
    planned_orders,
    curr_price,
    best_bid,
    best_ask,
):
    if strategy not in ("SCALPING", "SCALP"):
        return planned_orders, False
    if not bool(_rule("SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED", True)):
        return planned_orders, False
    if ai_engine is None or not hasattr(ai_engine, "evaluate_scalping_entry_price"):
        _log_entry_pipeline(stock, code, "entry_ai_price_canary_fallback", reason="ai_engine_unavailable")
        return planned_orders, False

    current_price = _coerce_int_value(curr_price)
    defensive_price = _coerce_int_value((latency_gate or {}).get("latency_guarded_order_price"))
    reference_price = _coerce_int_value((latency_gate or {}).get("target_buy_price"))
    resolved_price = _coerce_int_value((latency_gate or {}).get("order_price"))
    price_context_started_at = time.time()
    price_ctx = _build_entry_ai_price_context(
        stock,
        latency_gate,
        curr_price=current_price,
        best_bid=best_bid,
        best_ask=best_ask,
    )
    micro_log_fields = _build_orderbook_micro_log_fields(price_ctx.get("orderbook_micro"))

    try:
        tick_limit = int(_rule("SCALPING_ENTRY_AI_PRICE_TICK_LIMIT", 20) or 20)
        candle_limit = int(_rule("SCALPING_ENTRY_AI_PRICE_CANDLE_LIMIT", 20) or 20)
        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=tick_limit) or []
        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=candle_limit) or []
    except Exception as exc:
        _log_entry_pipeline(
            stock,
            code,
            "entry_ai_price_canary_fallback",
            reason="context_fetch_failed",
            error=str(exc)[:160],
            **micro_log_fields,
        )
        return planned_orders, False

    ai_eval_started_at = time.perf_counter()
    result = ai_engine.evaluate_scalping_entry_price(
        stock.get("name"),
        code,
        ws_data or {},
        recent_ticks,
        recent_candles,
        price_ctx,
    )
    ai_eval_ms = int(round((time.perf_counter() - ai_eval_started_at) * 1000.0))
    decision_ts = time.time()
    context_age_ms = int(round(max(0.0, decision_ts - price_context_started_at) * 1000.0))
    action = str((result or {}).get("action") or "USE_DEFENSIVE").strip().upper()
    confidence = _coerce_int_value((result or {}).get("confidence"))
    min_confidence = int(_rule("SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE", 60) or 60)
    skip_min_confidence = int(_rule("SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE", 80) or 80)
    reason = str((result or {}).get("reason") or "")
    parse_ok = bool((result or {}).get("ai_parse_ok", True))
    parse_fail = bool((result or {}).get("ai_parse_fail", False))
    source = str((result or {}).get("ai_result_source") or (result or {}).get("result_source") or "live")
    openai_transport_fields = {
        str(key): value
        for key, value in (result or {}).items()
        if str(key).startswith("openai_")
    }

    if parse_fail or not parse_ok:
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_fallback", reason="parse_or_ai_fail",
            action=action, confidence=confidence, source=source, **openai_transport_fields, **micro_log_fields,
        )
        return planned_orders, False
    if confidence < min_confidence:
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_fallback", reason="low_confidence",
            action=action, confidence=confidence, min_confidence=min_confidence,
            **openai_transport_fields, **micro_log_fields,
        )
        return planned_orders, False

    if action == "SKIP":
        if confidence < skip_min_confidence:
            _log_entry_pipeline(
                stock, code, "entry_ai_price_canary_fallback", reason="skip_low_confidence",
                action=action, confidence=confidence, skip_min_confidence=skip_min_confidence, **micro_log_fields,
            )
            return planned_orders, False
        latency_gate["ai_entry_price_canary_action"] = action
        latency_gate["ai_entry_price_canary_confidence"] = confidence
        latency_gate["ai_entry_price_canary_reason"] = reason
        orderbook_micro = price_ctx.get("orderbook_micro") if isinstance(price_ctx, dict) else {}
        skip_policy_fields = _build_entry_ai_price_skip_policy_fields(orderbook_micro)
        demote_skip, ofi_state = _should_demote_entry_ai_price_skip(confidence, orderbook_micro)
        ofi_log_fields = ofi_smoothing_log_fields(ofi_state, prefix="entry_ai_price_ofi")
        if demote_skip:
            latency_gate["ai_entry_price_canary_raw_action"] = "SKIP"
            latency_gate["ai_entry_price_canary_action"] = "USE_DEFENSIVE"
            latency_gate["ai_entry_price_canary_final_action"] = "USE_DEFENSIVE"
            latency_gate["ai_entry_price_canary_confidence"] = confidence
            latency_gate["ai_entry_price_canary_reason"] = reason
            latency_gate["ai_entry_price_ofi_skip_demoted"] = True
            latency_gate["price_resolution_reason"] = "ai_tier2_skip_demoted_to_p1"
            latency_gate["ai_entry_price_canary_applied"] = True
            _log_entry_pipeline(
                stock,
                code,
                "entry_ai_price_ofi_skip_demoted",
                action="SKIP",
                raw_action="SKIP",
                final_action="USE_DEFENSIVE",
                confidence=confidence,
                reason=reason[:160],
                demotion_path="P1_USE_DEFENSIVE",
                **openai_transport_fields,
                **skip_policy_fields,
                **ofi_log_fields,
                **micro_log_fields,
            )
            return planned_orders, True
        _mutate_stock_state(
            stock,
            set_fields={
                "entry_ai_price_skip_started_at": time.time(),
                "entry_ai_price_skip_mark_price": current_price,
                "entry_ai_price_skip_max_price": current_price,
                "entry_ai_price_skip_min_price": current_price,
                "entry_ai_price_skip_micro_state": str((orderbook_micro or {}).get("micro_state") or ""),
                "entry_ai_price_skip_policy_warning": str(
                    skip_policy_fields.get("entry_ai_price_skip_policy_warning") or ""
                ),
                "entry_ai_price_skip_threshold_source": str((orderbook_micro or {}).get("ofi_threshold_source") or ""),
                "entry_ai_price_skip_bucket_key": str((orderbook_micro or {}).get("ofi_bucket_key") or ""),
                "entry_ai_price_skip_followup_30s": False,
                "entry_ai_price_skip_followup_90s": False,
            },
        )
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_skip_order",
            action=action,
            confidence=confidence,
            reason=reason[:160],
            **openai_transport_fields,
            **skip_policy_fields,
            **ofi_log_fields,
            **micro_log_fields,
        )
        return [], True

    if action == "USE_REFERENCE":
        candidate_price = reference_price
    elif action == "IMPROVE_LIMIT":
        candidate_price = _coerce_int_value((result or {}).get("order_price"))
    else:
        action = "USE_DEFENSIVE"
        candidate_price = defensive_price or resolved_price

    if candidate_price <= 0:
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_fallback", reason="invalid_price", action=action,
            **openai_transport_fields, **micro_log_fields
        )
        return planned_orders, False
    candidate_price = clamp_price_to_tick(candidate_price)
    if candidate_price <= 0:
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_fallback", reason="invalid_price", action=action,
            **openai_transport_fields, **micro_log_fields
        )
        return planned_orders, False
    if best_ask > 0 and candidate_price > best_ask:
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_fallback", reason="above_best_ask",
            action=action, candidate_price=candidate_price, best_ask=best_ask,
            **openai_transport_fields, **micro_log_fields,
        )
        return planned_orders, False
    if _is_pre_submit_price_guard_block(strategy, candidate_price, best_bid):
        _log_entry_pipeline(
            stock, code, "entry_ai_price_canary_fallback", reason="pre_submit_price_guard",
            action=action, candidate_price=candidate_price, best_bid=best_bid,
            **openai_transport_fields, **micro_log_fields,
        )
        return planned_orders, False

    passive_price, passive_fields = _maybe_apply_entry_passive_probe(
        stock=stock,
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        action=action,
        candidate_price=candidate_price,
        curr_price=current_price,
        best_bid=best_bid,
        best_ask=best_ask,
    )
    if passive_fields:
        candidate_price = clamp_price_to_tick(passive_price)
        if _is_pre_submit_price_guard_block(strategy, candidate_price, best_bid):
            _log_entry_pipeline(
                stock,
                code,
                "entry_ai_price_canary_fallback",
                reason="passive_probe_price_guard",
                action=action,
                candidate_price=candidate_price,
                best_bid=best_bid,
                **openai_transport_fields,
                **passive_fields,
                **micro_log_fields,
            )
            return planned_orders, False

    adjusted_orders = []
    for order in planned_orders or []:
        next_order = dict(order)
        if str(next_order.get("tif", "DAY") or "DAY").upper() != "IOC":
            next_order["price"] = candidate_price
        adjusted_orders.append(next_order)

    max_wait_sec = max(5, min(1200, _coerce_int_value((result or {}).get("max_wait_sec"), 90)))
    if passive_fields:
        passive_timeout_sec = int(_rule("SCALPING_ENTRY_PASSIVE_PROBE_TIMEOUT_SEC", 30) or 30)
        max_wait_sec = max(5, min(max_wait_sec, passive_timeout_sec))
    latency_gate["orders"] = adjusted_orders
    latency_gate["order_price"] = candidate_price
    latency_gate["price_resolution_reason"] = f"ai_tier2_{action.lower()}"
    latency_gate["ai_entry_price_canary_applied"] = True
    latency_gate["ai_entry_price_canary_action"] = action
    latency_gate["ai_entry_price_canary_confidence"] = confidence
    latency_gate["ai_entry_price_canary_reason"] = reason
    latency_gate["ai_entry_price_canary_max_wait_sec"] = max_wait_sec
    latency_gate["ai_entry_price_canary_eval_ms"] = ai_eval_ms
    latency_gate["ai_entry_price_canary_decision_ts"] = decision_ts
    latency_gate["ai_entry_price_canary_context_age_ms"] = context_age_ms
    latency_gate["ai_entry_price_canary_context_best_bid"] = _coerce_int_value(best_bid)
    latency_gate["ai_entry_price_canary_context_best_ask"] = _coerce_int_value(best_ask)
    latency_gate.update(openai_transport_fields)
    if passive_fields:
        latency_gate.update(passive_fields)
    _mutate_stock_state(stock, set_fields={"entry_timeout_sec_override": max_wait_sec})
    _log_entry_pipeline(
        stock,
        code,
        "entry_ai_price_canary_applied",
        action=action,
        confidence=confidence,
        reason=reason[:160],
        original_order_price=resolved_price,
        candidate_price=candidate_price,
        reference_target_price=reference_price,
        defensive_order_price=defensive_price,
        max_wait_sec=max_wait_sec,
        ai_eval_ms=ai_eval_ms,
        price_decision_context_age_ms=context_age_ms,
        **openai_transport_fields,
        **passive_fields,
        **micro_log_fields,
    )
    return adjusted_orders, True


def _get_ws_snapshot_age_sec(ws_data):
    raw_ts = (ws_data or {}).get('last_ws_update_ts')
    if raw_ts in (None, '', 0):
        return None
    try:
        age = time.time() - float(raw_ts)
        return max(0.0, float(age))
    except Exception:
        return None


def _resolve_reference_age_sec(primary_ts, *, fallback_ts=None, now_ts=None):
    def _coerce_ts(value):
        if value in (None, "", 0, "0", "None"):
            return None
        try:
            ts = float(value)
        except Exception:
            return None
        return ts if ts > 0 else None

    reference_ts = _coerce_ts(primary_ts)
    if reference_ts is None:
        reference_ts = _coerce_ts(fallback_ts)
    if reference_ts is None:
        return None

    current_ts = time.time() if now_ts is None else float(now_ts)
    return max(0.0, float(current_ts - reference_ts))


def _extract_ai_overlap_snapshot(
    *,
    ws_data,
    recent_ticks=None,
    recent_candles=None,
    ai_engine=None,
):
    snapshot = {
        "latest_strength": float(ws_data.get("v_pw", 0.0) or 0.0),
        "buy_pressure_10t": float(ws_data.get("buy_ratio", 0.0) or 0.0),
        "distance_from_day_high_pct": 0.0,
        "intraday_range_pct": 0.0,
    }

    ticks = list(recent_ticks or [])
    candles = list(recent_candles or [])
    if ticks:
        try:
            snapshot["latest_strength"] = float(ticks[0].get("strength", snapshot["latest_strength"]) or snapshot["latest_strength"])
        except Exception:
            pass
        try:
            buy_vol = sum(_safe_int(tick.get("volume"), 0) for tick in ticks if str(tick.get("dir") or "").upper() == "BUY")
            sell_vol = sum(_safe_int(tick.get("volume"), 0) for tick in ticks if str(tick.get("dir") or "").upper() == "SELL")
            total_vol = buy_vol + sell_vol
            if total_vol > 0:
                snapshot["buy_pressure_10t"] = (buy_vol / total_vol) * 100.0
        except Exception:
            pass

    curr_price = _safe_int(ws_data.get("curr"), 0)
    high_price = _safe_float(
        ws_data.get("high")
        or ws_data.get("high_price")
        or ws_data.get("day_high")
        or ws_data.get("today_high"),
        0.0,
    )
    low_price = _safe_float(
        ws_data.get("low")
        or ws_data.get("low_price")
        or ws_data.get("day_low")
        or ws_data.get("today_low"),
        0.0,
    )
    if curr_price > 0 and high_price and high_price > 0:
        snapshot["distance_from_day_high_pct"] = ((curr_price - high_price) / high_price) * 100.0
    if curr_price > 0 and high_price and low_price and low_price > 0 and high_price >= low_price:
        snapshot["intraday_range_pct"] = ((high_price - low_price) / low_price) * 100.0

    if candles and curr_price > 0:
        highs = []
        lows = []
        for candle in candles:
            try:
                highs.append(float(candle.get("고가", 0) or 0))
                lows.append(float(candle.get("저가", 0) or 0))
            except Exception:
                continue
        candle_high_price = max([value for value in highs if value > 0], default=0.0)
        candle_low_price = min([value for value in lows if value > 0], default=0.0)
        if candle_high_price > 0:
            snapshot["distance_from_day_high_pct"] = ((curr_price - candle_high_price) / candle_high_price) * 100.0
        if candle_low_price > 0 and candle_high_price >= candle_low_price:
            snapshot["intraday_range_pct"] = ((candle_high_price - candle_low_price) / candle_low_price) * 100.0

    if ai_engine and hasattr(ai_engine, "_extract_scalping_features"):
        try:
            feature_map = ai_engine._extract_scalping_features(ws_data, ticks, candles)
            snapshot["latest_strength"] = float(feature_map.get("latest_strength", snapshot["latest_strength"]) or snapshot["latest_strength"])
            snapshot["buy_pressure_10t"] = float(feature_map.get("buy_pressure_10t", snapshot["buy_pressure_10t"]) or snapshot["buy_pressure_10t"])
            snapshot["distance_from_day_high_pct"] = float(
                feature_map.get("distance_from_day_high_pct", snapshot["distance_from_day_high_pct"])
                or snapshot["distance_from_day_high_pct"]
            )
            snapshot["intraday_range_pct"] = float(
                feature_map.get("intraday_range_pct", snapshot["intraday_range_pct"])
                or snapshot["intraday_range_pct"]
            )
        except Exception:
            pass

    return snapshot


def _build_ai_overlap_log_fields(
    *,
    stock,
    ai_score,
    momentum_tag=None,
    threshold_profile=None,
    overbought_blocked=False,
    blocked_stage=None,
    overlap_snapshot=None,
):
    snapshot = overlap_snapshot or (stock.get("last_ai_overlap_snapshot") or {})
    return {
        "ai_score": f"{float(ai_score or 0.0):.1f}",
        "latest_strength": f"{float(snapshot.get('latest_strength', 0.0) or 0.0):.1f}",
        "buy_pressure_10t": f"{float(snapshot.get('buy_pressure_10t', 0.0) or 0.0):.2f}",
        "distance_from_day_high_pct": f"{float(snapshot.get('distance_from_day_high_pct', 0.0) or 0.0):.3f}",
        "intraday_range_pct": f"{float(snapshot.get('intraday_range_pct', 0.0) or 0.0):.3f}",
        "momentum_tag": momentum_tag or stock.get("entry_momentum_tag") or stock.get("position_tag") or "-",
        "threshold_profile": threshold_profile or stock.get("entry_threshold_profile") or "-",
        "overbought_blocked": bool(overbought_blocked),
        "blocked_stage": blocked_stage or "-",
    }


def _build_ai_ops_log_fields(
    ai_decision,
    *,
    ai_score_raw=None,
    ai_score_after_bonus=None,
    entry_score_threshold=None,
    big_bite_bonus_applied=None,
    ai_cooldown_blocked=None,
):
    payload = ai_decision or {}
    out = {
        "ai_parse_ok": bool(payload.get("ai_parse_ok", False)),
        "ai_parse_fail": bool(payload.get("ai_parse_fail", False)),
        "ai_fallback_score_50": bool(payload.get("ai_fallback_score_50", False)),
        "ai_response_ms": int(payload.get("ai_response_ms", 0) or 0),
        "ai_prompt_type": str(payload.get("ai_prompt_type", "-") or "-"),
        "ai_prompt_version": str(payload.get("ai_prompt_version", "-") or "-"),
        "ai_result_source": str(payload.get("ai_result_source", "-") or "-"),
        "ai_model": str(payload.get("ai_model", "-") or "-"),
        "ai_model_tier": str(payload.get("ai_model_tier", "-") or "-"),
        "cache_mode": str(payload.get("cache_mode", "-") or "-"),
    }
    for field_name in (
        "cache_profile",
        "cache_strategy",
        "cache_key_status",
        "holding_cache_ttl_sec",
        "holding_cache_bucket_signature",
        "holding_cache_bucket_changed_fields",
        "holding_exit_matrix_status",
        "holding_exit_matrix_cohort",
        "holding_exit_matrix_version",
        "holding_exit_matrix_source_date",
        "holding_exit_matrix_valid_for_date",
        "holding_exit_matrix_application_mode",
        "holding_exit_matrix_loaded_from",
        "holding_exit_matrix_cache_token",
        "holding_exit_matrix_price_bucket",
        "holding_exit_matrix_volume_bucket",
        "holding_exit_matrix_time_bucket",
        "holding_exit_matrix_recommended_biases",
        "holding_exit_matrix_policy_hints",
        "holding_exit_matrix_decision_alignment",
        "holding_exit_matrix_runtime_effect",
        "holding_exit_matrix_original_action",
        "holding_exit_matrix_forced_action",
        "holding_exit_matrix_runtime_reason",
        "holding_exit_matrix_scale_in_bias",
        "entry_adm_status",
        "entry_adm_version",
        "entry_adm_source_date",
        "entry_adm_application_mode",
        "entry_adm_loaded_from",
        "entry_adm_cache_token",
        "entry_adm_bucket_token",
        "entry_adm_score_bucket",
        "entry_adm_risk_context_bucket",
        "entry_adm_stale_bucket",
        "entry_adm_price_resolution_bucket",
        "entry_adm_liquidity_bucket",
        "entry_adm_overbought_bucket",
        "entry_adm_time_bucket",
        "entry_adm_recommended_action",
        "entry_adm_decision_alignment",
        "entry_adm_runtime_effect",
        "entry_adm_original_action",
        "entry_adm_forced_action",
        "entry_adm_runtime_reason",
        "ai_reason_language_policy",
    ):
        if field_name in payload:
            out[field_name] = str(payload.get(field_name, "-") or "-")
    for field_name in (
        "openai_transport_mode",
        "openai_request_id",
        "openai_endpoint_name",
        "openai_schema_name",
        "openai_ws_error_type",
        "openai_input_tokens",
        "openai_output_tokens",
        "openai_total_tokens",
        "openai_cached_input_tokens",
        "openai_reasoning_tokens",
    ):
        if field_name in payload:
            if field_name.startswith("openai_") and field_name.endswith("_tokens"):
                out[field_name] = int(payload.get(field_name, 0) or 0)
            else:
                out[field_name] = str(payload.get(field_name, "-") or "-")
    for field_name in (
        "openai_ws_queue_wait_ms",
        "openai_ws_roundtrip_ms",
    ):
        if field_name in payload:
            out[field_name] = int(payload.get(field_name, 0) or 0)
    for field_name in (
        "openai_ws_used",
        "openai_ws_http_fallback",
    ):
        if field_name in payload:
            raw_value = payload.get(field_name)
            if isinstance(raw_value, bool):
                out[field_name] = raw_value
            else:
                out[field_name] = str(raw_value).strip().lower() in {"1", "true", "yes", "y"}
    if "holding_exit_matrix_feature_enabled" in payload:
        out["holding_exit_matrix_feature_enabled"] = bool(payload.get("holding_exit_matrix_feature_enabled"))
    if "holding_exit_matrix_applied" in payload:
        out["holding_exit_matrix_applied"] = bool(payload.get("holding_exit_matrix_applied"))
    if "holding_exit_matrix_runtime_bias_enabled" in payload:
        out["holding_exit_matrix_runtime_bias_enabled"] = bool(payload.get("holding_exit_matrix_runtime_bias_enabled"))
    if "holding_exit_matrix_runtime_bias_applied" in payload:
        out["holding_exit_matrix_runtime_bias_applied"] = bool(payload.get("holding_exit_matrix_runtime_bias_applied"))
    if "entry_adm_feature_enabled" in payload:
        out["entry_adm_feature_enabled"] = bool(payload.get("entry_adm_feature_enabled"))
    if "entry_adm_prompt_applied" in payload:
        out["entry_adm_prompt_applied"] = bool(payload.get("entry_adm_prompt_applied"))
    if "entry_adm_runtime_bias_enabled" in payload:
        out["entry_adm_runtime_bias_enabled"] = bool(payload.get("entry_adm_runtime_bias_enabled"))
    if "entry_adm_runtime_bias_applied" in payload:
        out["entry_adm_runtime_bias_applied"] = bool(payload.get("entry_adm_runtime_bias_applied"))
    if "ai_reason_language_violation" in payload:
        out["ai_reason_language_violation"] = bool(payload.get("ai_reason_language_violation"))
    if payload.get("scalp_feature_packet_version"):
        out["scalp_feature_packet_version"] = str(payload.get("scalp_feature_packet_version"))
    for field_name in (
        "tick_acceleration_ratio_sent",
        "same_price_buy_absorption_sent",
        "large_sell_print_detected_sent",
        "ask_depth_ratio_sent",
        "tick_source_quality_fields_sent",
    ):
        if field_name in payload:
            out[field_name] = bool(payload.get(field_name))
    for field_name in (
        "tick_sample_count",
        "tick_window_sample_count",
        "tick_latest_age_ms",
        "tick_window_span_sec",
        "tick_accel_effective_recent_5tick_seconds",
        "tick_acceleration_ratio_raw",
        "quote_age_ms",
    ):
        if field_name in payload:
            raw_value = payload.get(field_name)
            try:
                out[field_name] = int(float(raw_value))
            except Exception:
                out[field_name] = str(raw_value or "-")
    for field_name in (
        "tick_latest_time",
        "tick_accel_source",
        "tick_context_quality",
        "quote_age_source",
        "ai_input_source_quality_status",
        "ai_input_source_quality_reason",
    ):
        if field_name in payload:
            out[field_name] = str(payload.get(field_name, "-") or "-")
    for field_name in (
        "tick_context_stale",
        "quote_stale",
    ):
        if field_name in payload:
            raw_value = payload.get(field_name)
            if isinstance(raw_value, bool):
                out[field_name] = raw_value
            else:
                text_value = str(raw_value or "unknown").strip().lower()
                out[field_name] = (
                    text_value in {"1", "true", "yes", "y"}
                    if text_value not in {"unknown", "-", "none", ""}
                    else "unknown"
                )
    if ai_score_raw is not None:
        out["ai_score_raw"] = f"{float(ai_score_raw or 0.0):.1f}"
    if ai_score_after_bonus is not None:
        out["ai_score_after_bonus"] = f"{float(ai_score_after_bonus or 0.0):.1f}"
    if entry_score_threshold is not None:
        out["entry_score_threshold"] = f"{float(entry_score_threshold or 0.0):.1f}"
    if big_bite_bonus_applied is not None:
        out["big_bite_bonus_applied"] = bool(big_bite_bonus_applied)
    if ai_cooldown_blocked is not None:
        out["ai_cooldown_blocked"] = bool(ai_cooldown_blocked)
    return out


def _build_ai_input_not_evaluated_fields(reason: str) -> dict:
    return {
        "ai_input_source_quality_status": "not_evaluated",
        "ai_input_source_quality_reason": str(reason or "not_evaluated"),
        "tick_source_quality_fields_sent": False,
        "tick_accel_source": "not_evaluated",
        "tick_context_quality": "not_evaluated",
        "quote_age_source": "not_evaluated",
    }


def _ensure_ai_source_quality_fields(fields: dict, stock: dict | None, *, not_evaluated_reason: str) -> dict:
    out = dict(fields or {})
    if "tick_source_quality_fields_sent" not in out and isinstance(stock, dict):
        out.update(dict(stock.get("last_watching_ai_source_quality_fields") or {}))
    if "tick_source_quality_fields_sent" not in out:
        out.update(_build_ai_input_not_evaluated_fields(not_evaluated_reason))
    elif "ai_input_source_quality_status" not in out:
        out["ai_input_source_quality_status"] = "evaluated"
        out["ai_input_source_quality_reason"] = str(out.get("tick_context_quality") or "tick_audit_present")
    return out


def _build_tick_source_quality_log_fields(feature_probe):
    payload = feature_probe or {}
    out = {}
    for field_name in (
        "tick_sample_count",
        "tick_window_sample_count",
        "tick_latest_age_ms",
        "tick_window_span_sec",
        "quote_age_ms",
    ):
        if field_name in payload:
            raw_value = payload.get(field_name)
            try:
                out[field_name] = int(float(raw_value))
            except Exception:
                out[field_name] = str(raw_value or "-")
    for field_name in (
        "tick_latest_time",
        "tick_accel_source",
        "tick_context_quality",
        "quote_age_source",
    ):
        if field_name in payload:
            out[field_name] = str(payload.get(field_name, "-") or "-")
    for field_name in (
        "tick_context_stale",
        "quote_stale",
    ):
        if field_name in payload:
            raw_value = payload.get(field_name)
            if isinstance(raw_value, bool):
                out[field_name] = raw_value
            else:
                text_value = str(raw_value or "unknown").strip().lower()
                out[field_name] = (
                    text_value in {"1", "true", "yes", "y"}
                    if text_value not in {"unknown", "-", "none", ""}
                    else "unknown"
                )
    for field_name in (
        "tick_accel_effective_recent_5tick_seconds",
        "tick_acceleration_ratio_raw",
    ):
        if field_name in payload:
            raw_value = payload.get(field_name)
            try:
                out[field_name] = f"{float(raw_value):.3f}"
            except Exception:
                out[field_name] = str(raw_value or "-")
    if out:
        out["tick_source_quality_fields_sent"] = True
    return out


def _build_observation_contract_fields(metric_role: str) -> dict:
    role = str(metric_role or "ops_volume_diagnostic")
    return {
        "metric_role": role,
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
        "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        "source_quality_route": "source_quality_blocker_or_workorder_only",
    }


def _build_pre_ai_gate_contract_fields(threshold_family: str, *, gate_action: str) -> dict:
    fields = _build_observation_contract_fields("risk_context")
    fields.update(
        {
            "threshold_family": threshold_family,
            "runtime_family_candidate": threshold_family,
            "gate_layer": "pre_ai_risk_context",
            "gate_action": gate_action,
            "allowed_runtime_apply": False,
            "human_approval_required": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": False,
        }
    )
    return fields


def _build_pre_submit_gate_contract_fields(threshold_family: str, *, gate_action: str = "pre_submit_block") -> dict:
    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "order_safety_pre_submit_only",
        "runtime_effect": "pre_submit_block",
        "threshold_family": threshold_family,
        "runtime_family_candidate": threshold_family,
        "gate_layer": "entry_pre_submit_guard",
        "gate_action": gate_action,
        "allowed_runtime_apply": False,
        "human_approval_required": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": "provider_route_change/bot_restart/runtime_threshold_apply_without_approval",
    }


def _reset_scalp_pre_ai_gate_context(stock: dict | None, ws_data: dict | None) -> None:
    if isinstance(ws_data, dict):
        ws_data["scalp_pre_ai_gate_context"] = {}
    _mutate_stock_state(
        stock,
        set_fields={"scalp_pre_ai_gate_context": {}},
        pop_fields=[
            "entry_overbought_risk_state",
            "entry_strength_momentum_risk_state",
            "entry_liquidity_risk_state",
        ],
    )


def _register_scalp_pre_ai_gate_context(stock: dict | None, ws_data: dict | None, gate_key: str, context: dict) -> dict:
    if not isinstance(context, dict):
        context = {}
    gate = str(gate_key or "").strip()
    if not gate:
        return {}
    stock_context = dict((stock or {}).get("scalp_pre_ai_gate_context") or {})
    ws_context = dict((ws_data or {}).get("scalp_pre_ai_gate_context") or {})
    normalized = {
        "gate": gate,
        **context,
    }
    stock_context[gate] = normalized
    ws_context[gate] = normalized
    if isinstance(ws_data, dict):
        ws_data["scalp_pre_ai_gate_context"] = ws_context
        ws_data[f"{gate}_risk_state"] = normalized.get("risk_state") or normalized.get("state") or "-"
    _mutate_stock_state(
        stock,
        set_fields={
            "scalp_pre_ai_gate_context": stock_context,
            f"entry_{gate}_risk_state": normalized.get("risk_state") or normalized.get("state") or "-",
        },
    )
    return normalized


def _scalp_pre_ai_gate_context_log_fields(context: dict | None) -> dict:
    context = context if isinstance(context, dict) else {}
    keys = sorted(str(key) for key in context.keys() if str(key).strip())
    fields = {
        "pre_ai_gate_context_keys": ",".join(keys) if keys else "-",
    }
    for gate in ("strength_momentum", "overbought", "liquidity"):
        gate_context = context.get(gate) if isinstance(context.get(gate), dict) else {}
        if not gate_context:
            continue
        prefix = f"{gate}_"
        for key in ("risk_state", "state", "reason", "gate_action", "threshold_family", "risk_bucket"):
            if key in gate_context:
                fields[f"{prefix}{key}"] = gate_context.get(key)
    return fields


def _strength_momentum_source_quality_block_reason(ws_data: dict | None, result: dict | None) -> str:
    if not _rule_bool("SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED", True):
        return ""
    result = result if isinstance(result, dict) else {}
    reason = str(result.get("reason") or "").strip().lower()
    if reason == "insufficient_history":
        return "insufficient_history"
    quote_age_sec = _get_ws_snapshot_age_sec(ws_data or {})
    max_ws_age_sec = _rule_float("SCALP_PRE_AI_MAX_WS_AGE_SEC", 3.0)
    if quote_age_sec is not None and quote_age_sec > max_ws_age_sec:
        return "stale_ws_snapshot"
    buy_ratio = _safe_float(result.get("window_buy_ratio"), 0.0)
    exec_buy_ratio = _safe_float(result.get("window_exec_buy_ratio"), 0.0)
    net_buy_qty = _safe_int(result.get("window_net_buy_qty"), 0)
    total_value = _safe_int(result.get("window_total_value"), 0)
    if (
        total_value > 0
        and buy_ratio <= _rule_float("SCALP_PRE_AI_EXTREME_SELL_BUY_RATIO_MAX", 0.35)
        and exec_buy_ratio <= _rule_float("SCALP_PRE_AI_EXTREME_SELL_EXEC_BUY_RATIO_MAX", 0.35)
        and net_buy_qty < 0
    ):
        return "extreme_sell_dominant"
    return ""


def _classify_overbought_risk(overlap_snapshot: dict | None, *, intraday_surge: float, max_intraday_surge: float) -> dict:
    snapshot = overlap_snapshot if isinstance(overlap_snapshot, dict) else {}
    distance = _safe_float(snapshot.get("distance_from_day_high_pct"), 0.0)
    strength = _safe_float(snapshot.get("latest_strength"), 0.0)
    buy_pressure = _safe_float(snapshot.get("buy_pressure_10t"), 0.0)
    pullback_min = _rule_float("SCALP_OVERBOUGHT_PULLBACK_MIN_DISTANCE_PCT", -0.35)
    rebreak_strength = _rule_float("SCALP_OVERBOUGHT_REBREAK_MIN_STRENGTH", 120.0)
    rebreak_pressure = _rule_float("SCALP_OVERBOUGHT_REBREAK_MIN_BUY_PRESSURE", 60.0)
    if distance <= pullback_min:
        state = "pullback_observed"
        risk_bucket = "pullback_candidate"
    elif strength >= rebreak_strength and buy_pressure >= rebreak_pressure and intraday_surge <= max_intraday_surge + 1.0:
        state = "rebreak_candidate"
        risk_bucket = "rebreak_candidate"
    else:
        state = "pullback_required"
        risk_bucket = "chase_risk"
    return {
        "risk_state": state,
        "risk_bucket": risk_bucket,
        "distance_from_day_high_pct": f"{distance:.3f}",
        "latest_strength": f"{strength:.1f}",
        "buy_pressure_10t": f"{buy_pressure:.2f}",
        "pullback_min_distance_pct": f"{pullback_min:.2f}",
        "rebreak_min_strength": f"{rebreak_strength:.1f}",
        "rebreak_min_buy_pressure": f"{rebreak_pressure:.2f}",
    }


def _overbought_pre_submit_allowed(context: dict | None) -> bool:
    if not _rule_bool("SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED", True):
        return True
    context = context if isinstance(context, dict) else {}
    overbought = context.get("overbought") if isinstance(context.get("overbought"), dict) else {}
    if not overbought:
        return True
    return str(overbought.get("risk_state") or "").strip() in {"pullback_observed", "rebreak_candidate"}


def _append_holding_flow_history(stock: dict, *, now_ts: float, exit_rule: str, profit_rate: float, flow_result: dict) -> None:
    history = list(stock.get("holding_flow_review_history") or [])
    history.append(
        {
            "time": datetime.fromtimestamp(float(now_ts or time.time())).strftime("%H:%M:%S"),
            "action": str(flow_result.get("action", "-") or "-"),
            "flow_state": str(flow_result.get("flow_state", "-") or "-"),
            "score": _safe_int(flow_result.get("score"), 0),
            "profit_rate": f"{float(profit_rate or 0.0):+.2f}",
            "exit_rule": exit_rule or "-",
            "reason": str(flow_result.get("reason", "-") or "-")[:120],
        }
    )
    _mutate_stock_state(stock, set_fields={"holding_flow_review_history": history[-5:]})


def _flow_evidence_text(flow_result: dict) -> str:
    evidence = flow_result.get("evidence") if isinstance(flow_result, dict) else None
    if isinstance(evidence, list):
        cleaned = [str(item).replace("\n", " ").strip() for item in evidence if str(item).strip()]
        return "|".join(cleaned[:5]) if cleaned else "-"
    return str(evidence or "-").replace("\n", " ")


def _holding_flow_override_applicable(strategy: str, exit_rule: str) -> bool:
    return (
        _rule_bool("HOLDING_FLOW_OVERRIDE_ENABLED", True)
        and str(strategy or "").upper() == "SCALPING"
        and str(exit_rule or "").strip() in _HOLDING_FLOW_OVERRIDE_EXIT_RULES
    )


def _clear_holding_flow_override_candidate(stock: dict, code: str, *, reason: str, profit_rate: float | None = None):
    if not stock.get("holding_flow_override_candidate_key"):
        return
    previous_key = str(stock.get("holding_flow_override_candidate_key") or "-")
    _mutate_stock_state(
        stock,
        pop_fields=(
            "holding_flow_override_candidate_key",
            "holding_flow_override_started_at",
            "holding_flow_override_candidate_profit",
            "holding_flow_override_exit_rule",
            "holding_flow_override_last_review_at",
            "holding_flow_override_last_review_profit",
            "holding_flow_override_last_action",
            "holding_flow_override_last_flow_state",
            "holding_flow_override_last_score",
            "holding_flow_override_last_reason",
            "holding_flow_override_next_review_sec",
        ),
    )
    _log_holding_pipeline(
        stock,
        code,
        "holding_flow_override_candidate_cleared",
        **_build_observation_contract_fields("funnel_count"),
        reason=reason,
        previous_key=previous_key,
        profit_rate=f"{profit_rate:+.2f}" if profit_rate is not None else "-",
    )


def _overnight_flow_override_worsen_from_candidate(stock: dict, profit_rate: float) -> float:
    candidate_profit = _safe_float(stock.get("overnight_flow_override_candidate_profit"), profit_rate)
    return float(candidate_profit or 0.0) - float(profit_rate or 0.0)


def _should_revert_overnight_flow_override_hold(stock: dict, profit_rate: float, now_t) -> bool:
    if not stock.get("overnight_flow_override_hold"):
        return False
    if not (TIME_SCALPING_OVERNIGHT_DECISION <= now_t < TIME_15_30):
        return False
    worsen_pct = max(
        0.0,
        _safe_float(
            stock.get("overnight_flow_override_worsen_pct"),
            _rule_float("HOLDING_FLOW_OVERRIDE_WORSEN_PCT", 0.80),
        ),
    )
    return (_overnight_flow_override_worsen_from_candidate(stock, profit_rate) + 1e-9) >= worsen_pct


def _evaluate_holding_flow_override(
    *,
    stock: dict,
    code: str,
    strategy: str,
    ws_data: dict,
    ai_engine,
    exit_rule: str,
    sell_reason_type: str,
    reason: str,
    profit_rate: float,
    peak_profit: float,
    drawdown: float,
    current_ai_score: float,
    held_sec: int,
    curr_price: int,
    buy_price: float,
    now_ts: float,
) -> bool:
    """Return True when the original exit should proceed."""
    if not _holding_flow_override_applicable(strategy, exit_rule):
        return True

    if ai_engine is None or not hasattr(ai_engine, "evaluate_scalping_holding_flow"):
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="ai_engine_unavailable",
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
        )
        return True

    worsen_pct = max(0.0, _rule_float("HOLDING_FLOW_OVERRIDE_WORSEN_PCT", 0.80))
    max_defer_sec = max(1, _rule_int("HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC", 90))
    min_review_sec = max(1, _rule_int("HOLDING_FLOW_REVIEW_MIN_INTERVAL_SEC", 30))
    max_review_sec = max(min_review_sec, _rule_int("HOLDING_FLOW_REVIEW_MAX_INTERVAL_SEC", 90))
    price_trigger_pct = max(0.0, _rule_float("HOLDING_FLOW_REVIEW_PRICE_TRIGGER_PCT", 0.35))
    max_ws_age = max(0.0, _rule_float("HOLDING_FLOW_REVIEW_MAX_WS_AGE_SEC", 3.0))
    candidate_key = f"{exit_rule}:{sell_reason_type}"
    existing_key = str(stock.get("holding_flow_override_candidate_key", "") or "")
    candidate_started_at = _safe_float(stock.get("holding_flow_override_started_at"), 0.0)
    candidate_profit = _safe_float(stock.get("holding_flow_override_candidate_profit"), profit_rate)

    if existing_key != candidate_key or candidate_started_at <= 0:
        candidate_started_at = now_ts
        candidate_profit = profit_rate
        _mutate_stock_state(
            stock,
            set_fields={
                "holding_flow_override_candidate_key": candidate_key,
                "holding_flow_override_started_at": now_ts,
                "holding_flow_override_candidate_profit": profit_rate,
                "holding_flow_override_exit_rule": exit_rule,
            },
        )

    elapsed_sec = max(0, int(now_ts - candidate_started_at))
    worsen_from_candidate = float(candidate_profit or 0.0) - float(profit_rate or 0.0)
    last_review_at = _safe_float(stock.get("holding_flow_override_last_review_at"), 0.0)
    last_review_profit = _safe_float(stock.get("holding_flow_override_last_review_profit"), profit_rate)
    last_review_action = str(stock.get("holding_flow_override_last_action", "") or "").upper()
    review_elapsed_sec = max(0, int(now_ts - last_review_at)) if last_review_at > 0 else None
    profit_move_since_review = abs(float(profit_rate or 0.0) - float(last_review_profit or 0.0))
    if elapsed_sec >= max_defer_sec:
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="max_defer_sec",
            elapsed_sec=elapsed_sec,
            max_defer_sec=max_defer_sec,
            profit_rate=f"{profit_rate:+.2f}",
            candidate_profit=f"{candidate_profit:+.2f}",
        )
        return True
    if worsen_from_candidate >= worsen_pct:
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="worsen_floor",
            worsen_from_candidate=f"{worsen_from_candidate:.2f}",
            worsen_pct=f"{worsen_pct:.2f}",
            profit_rate=f"{profit_rate:+.2f}",
            candidate_profit=f"{candidate_profit:+.2f}",
        )
        return True

    if (
        last_review_at > 0
        and last_review_action in {"HOLD", "TRIM"}
        and review_elapsed_sec is not None
        and review_elapsed_sec < max_review_sec
        and (review_elapsed_sec < min_review_sec or profit_move_since_review < price_trigger_pct)
    ):
        if _rule_bool("HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED", True):
            orderbook_micro, ofi_state = _evaluate_holding_flow_ofi_state(stock, code, curr_price=curr_price)
            swing_exit_micro_fields = (
                _build_swing_micro_log_fields(orderbook_micro, phase="exit")
                if _is_swing_orderbook_micro_context_enabled(strategy)
                else {}
            )
            orderbook_micro_fields = (
                swing_exit_micro_fields
                if swing_exit_micro_fields
                else _build_orderbook_micro_log_fields(orderbook_micro)
            )
            bearish_confirm_worsen_pct = max(
                0.0,
                _rule_float("HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT", 0.30),
            )
            if ofi_state.regime == OFI_STABLE_BEARISH and worsen_from_candidate + 1e-9 >= bearish_confirm_worsen_pct:
                _log_holding_pipeline(
                    stock,
                    code,
                    "holding_flow_ofi_smoothing_applied",
                    smoothing_action="CONFIRM_EXIT",
                    exit_rule=exit_rule,
                    raw_flow_action=last_review_action,
                    final_flow_action="EXIT",
                    source="review_interval_reuse",
                    profit_rate=f"{profit_rate:+.2f}",
                    candidate_profit=f"{candidate_profit:+.2f}",
                    worsen_from_candidate=f"{worsen_from_candidate:.2f}",
                    bearish_confirm_worsen_pct=f"{bearish_confirm_worsen_pct:.2f}",
                    **ofi_smoothing_log_fields(ofi_state, prefix="holding_flow_ofi"),
                    **orderbook_micro_fields,
                )
                _log_holding_pipeline(
                    stock,
                    code,
                    "holding_flow_override_exit_confirmed",
                    exit_rule=exit_rule,
                    flow_state=stock.get("holding_flow_override_last_flow_state", "-"),
                    flow_score=_safe_int(stock.get("holding_flow_override_last_score"), 0),
                    profit_rate=f"{profit_rate:+.2f}",
                    confirm_reason="ofi_stable_bearish_interval",
                )
                return True
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_defer_exit",
            exit_rule=exit_rule,
            original_sell_reason_type=sell_reason_type,
            flow_action=last_review_action,
            flow_state=stock.get("holding_flow_override_last_flow_state", "-"),
            flow_score=_safe_int(stock.get("holding_flow_override_last_score"), 0),
            flow_reason=stock.get("holding_flow_override_last_reason", "review_interval_hold"),
            profit_rate=f"{profit_rate:+.2f}",
            candidate_profit=f"{candidate_profit:+.2f}",
            worsen_pct=f"{worsen_pct:.2f}",
            elapsed_sec=elapsed_sec,
            review_elapsed_sec=review_elapsed_sec,
            profit_move_since_review=f"{profit_move_since_review:.2f}",
            min_review_sec=min_review_sec,
            max_review_sec=max_review_sec,
            price_trigger_pct=f"{price_trigger_pct:.2f}",
            **_build_observation_contract_fields("ops_volume_diagnostic"),
            **(
                _build_swing_micro_log_fields(
                    _build_live_orderbook_micro_context(code, curr_price=curr_price),
                    phase="exit",
                )
                if _is_swing_orderbook_micro_context_enabled(strategy)
                else {}
            ),
        )
        _emit_stat_action_decision_snapshot(
            stock=stock,
            code=code,
            strategy=strategy,
            ws_data=ws_data,
            chosen_action="hold_wait",
            eligible_actions=["hold_wait", "exit_now"],
            rejected_actions=[f"exit_now:flow_{last_review_action.lower()}_interval"],
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
            curr_price=curr_price,
            buy_price=buy_price,
            exit_rule=exit_rule or "-",
            sell_reason_type=sell_reason_type or "-",
            reason=f"holding_flow_override_interval:{stock.get('holding_flow_override_last_reason', '-')}",
            force=True,
        )
        return False

    ws_age_sec = _get_ws_snapshot_age_sec(ws_data)
    if ws_age_sec is not None and max_ws_age > 0 and ws_age_sec > max_ws_age:
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="ws_stale",
            ws_age_sec=f"{ws_age_sec:.2f}",
            max_ws_age_sec=f"{max_ws_age:.2f}",
            profit_rate=f"{profit_rate:+.2f}",
        )
        return True

    tick_limit = max(1, _rule_int("HOLDING_FLOW_REVIEW_TICK_LIMIT", 30))
    candle_limit = max(1, _rule_int("HOLDING_FLOW_REVIEW_CANDLE_LIMIT", 60))
    try:
        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=tick_limit)
        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=candle_limit)
    except Exception as exc:
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="context_fetch_failed",
            error=str(exc)[:160],
            profit_rate=f"{profit_rate:+.2f}",
        )
        return True

    if not recent_ticks:
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="no_recent_ticks",
            profit_rate=f"{profit_rate:+.2f}",
        )
        return True

    position_ctx = {
        "exit_rule": exit_rule,
        "sell_reason_type": sell_reason_type,
        "reason": reason,
        "buy_price": buy_price,
        "curr_price": curr_price,
        "profit_rate": profit_rate,
        "peak_profit": peak_profit,
        "drawdown": drawdown,
        "held_sec": held_sec,
        "current_ai_score": current_ai_score,
        "worsen_pct": worsen_pct,
    }
    flow_result = ai_engine.evaluate_scalping_holding_flow(
        stock.get("name", code),
        code,
        ws_data,
        recent_ticks,
        recent_candles,
        position_ctx,
        flow_history=stock.get("holding_flow_review_history") or [],
        decision_kind="intraday_exit",
    )
    _mutate_stock_state(
        stock,
        set_fields={
            "holding_flow_override_last_review_at": now_ts,
            "holding_flow_override_last_review_profit": profit_rate,
            "holding_flow_override_last_action": str(flow_result.get("action", "EXIT") or "EXIT").upper(),
            "holding_flow_override_last_flow_state": str(flow_result.get("flow_state", "-") or "-"),
            "holding_flow_override_last_score": _safe_int(flow_result.get("score"), 0),
            "holding_flow_override_last_reason": str(flow_result.get("reason", "-") or "-")[:160],
            "holding_flow_override_next_review_sec": _safe_int(flow_result.get("next_review_sec"), min_review_sec),
        },
    )
    _append_holding_flow_history(
        stock,
        now_ts=now_ts,
        exit_rule=exit_rule,
        profit_rate=profit_rate,
        flow_result=flow_result,
    )
    flow_action = str(flow_result.get("action", "EXIT") or "EXIT").upper()
    parse_failed = bool(flow_result.get("ai_parse_fail")) or flow_action not in {"HOLD", "TRIM", "EXIT"}
    orderbook_micro = None
    ofi_state = None
    ofi_log_fields = {}
    micro_log_fields = {}
    swing_exit_micro_fields = {}
    if _rule_bool("HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED", True):
        orderbook_micro, ofi_state = _evaluate_holding_flow_ofi_state(stock, code, curr_price=curr_price)
        ofi_log_fields = ofi_smoothing_log_fields(ofi_state, prefix="holding_flow_ofi")
        micro_log_fields = _build_orderbook_micro_log_fields(orderbook_micro)
    elif _is_swing_orderbook_micro_context_enabled(strategy):
        orderbook_micro = _build_live_orderbook_micro_context(code, curr_price=curr_price)
        micro_log_fields = _build_orderbook_micro_log_fields(orderbook_micro)
    if _is_swing_orderbook_micro_context_enabled(strategy):
        swing_exit_micro_fields = _build_swing_micro_log_fields(orderbook_micro, phase="exit")
        _log_holding_pipeline(
            stock,
            code,
            "swing_exit_micro_context_observed",
            exit_rule=exit_rule,
            raw_flow_action=flow_action,
            **swing_exit_micro_fields,
        )
    micro_log_fields_for_smoothing = {} if swing_exit_micro_fields else micro_log_fields
    _log_holding_pipeline(
        stock,
        code,
        "holding_flow_override_review",
        exit_rule=exit_rule,
        candidate_reason=reason,
        flow_action=flow_action,
        flow_state=flow_result.get("flow_state", "-"),
        flow_score=_safe_int(flow_result.get("score"), 0),
        flow_reason=flow_result.get("reason", "-"),
        flow_evidence=_flow_evidence_text(flow_result),
        profit_rate=f"{profit_rate:+.2f}",
        peak_profit=f"{peak_profit:+.2f}",
        held_sec=held_sec,
        elapsed_sec=elapsed_sec,
        worsen_from_candidate=f"{worsen_from_candidate:.2f}",
        **_build_ai_ops_log_fields(flow_result),
        **swing_exit_micro_fields,
    )
    if parse_failed:
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_force_exit",
            exit_rule=exit_rule,
            force_reason="parse_fail",
            profit_rate=f"{profit_rate:+.2f}",
        )
        return True
    if _rule_bool("HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED", True) and ofi_state is not None:
        bearish_confirm_worsen_pct = max(
            0.0,
            _rule_float("HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT", 0.30),
        )
        if flow_action == "EXIT" and ofi_state.regime == OFI_STABLE_BULLISH:
            _log_holding_pipeline(
                stock,
                code,
                "holding_flow_ofi_smoothing_applied",
                smoothing_action="DEBOUNCE_EXIT",
                exit_rule=exit_rule,
                raw_flow_action="EXIT",
                final_flow_action="HOLD",
                source="holding_flow_review",
                profit_rate=f"{profit_rate:+.2f}",
                candidate_profit=f"{candidate_profit:+.2f}",
                worsen_from_candidate=f"{worsen_from_candidate:.2f}",
                max_defer_sec=max_defer_sec,
                worsen_pct=f"{worsen_pct:.2f}",
                **ofi_log_fields,
                **micro_log_fields_for_smoothing,
                **swing_exit_micro_fields,
            )
            _log_holding_pipeline(
                stock,
                code,
                "holding_flow_override_defer_exit",
                exit_rule=exit_rule,
                original_sell_reason_type=sell_reason_type,
                flow_action="EXIT",
                flow_state=flow_result.get("flow_state", "-"),
                flow_score=_safe_int(flow_result.get("score"), 0),
                flow_reason=flow_result.get("reason", "-"),
                flow_evidence=_flow_evidence_text(flow_result),
                profit_rate=f"{profit_rate:+.2f}",
                candidate_profit=f"{candidate_profit:+.2f}",
                worsen_pct=f"{worsen_pct:.2f}",
                elapsed_sec=elapsed_sec,
                defer_reason="ofi_stable_bullish_debounce",
                **_build_observation_contract_fields("ops_volume_diagnostic"),
                **swing_exit_micro_fields,
            )
            _emit_stat_action_decision_snapshot(
                stock=stock,
                code=code,
                strategy=strategy,
                ws_data=ws_data,
                chosen_action="hold_wait",
                eligible_actions=["hold_wait", "exit_now"],
                rejected_actions=["exit_now:ofi_stable_bullish_debounce"],
                profit_rate=profit_rate,
                peak_profit=peak_profit,
                current_ai_score=current_ai_score,
                held_sec=held_sec,
                curr_price=curr_price,
                buy_price=buy_price,
                exit_rule=exit_rule or "-",
                sell_reason_type=sell_reason_type or "-",
                reason=f"holding_flow_ofi_smoothing:{flow_result.get('reason', '-')}",
                force=True,
            )
            return False
        if (
            flow_action in {"HOLD", "TRIM"}
            and ofi_state.regime == OFI_STABLE_BEARISH
            and worsen_from_candidate + 1e-9 >= bearish_confirm_worsen_pct
        ):
            _log_holding_pipeline(
                stock,
                code,
                "holding_flow_ofi_smoothing_applied",
                smoothing_action="CONFIRM_EXIT",
                exit_rule=exit_rule,
                raw_flow_action=flow_action,
                final_flow_action="EXIT",
                source="holding_flow_review",
                profit_rate=f"{profit_rate:+.2f}",
                candidate_profit=f"{candidate_profit:+.2f}",
                worsen_from_candidate=f"{worsen_from_candidate:.2f}",
                bearish_confirm_worsen_pct=f"{bearish_confirm_worsen_pct:.2f}",
                **ofi_log_fields,
                **micro_log_fields_for_smoothing,
                **swing_exit_micro_fields,
            )
            _log_holding_pipeline(
                stock,
                code,
                "holding_flow_override_exit_confirmed",
                exit_rule=exit_rule,
                flow_state=flow_result.get("flow_state", "-"),
                flow_score=_safe_int(flow_result.get("score"), 0),
                profit_rate=f"{profit_rate:+.2f}",
                confirm_reason="ofi_stable_bearish",
            )
            return True
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_ofi_smoothing_applied",
            smoothing_action="NO_CHANGE",
            exit_rule=exit_rule,
            raw_flow_action=flow_action,
            final_flow_action=flow_action,
            source="holding_flow_review",
            profit_rate=f"{profit_rate:+.2f}",
            **ofi_log_fields,
            **micro_log_fields_for_smoothing,
            **swing_exit_micro_fields,
        )
    if flow_action == "EXIT":
        _log_holding_pipeline(
            stock,
            code,
            "holding_flow_override_exit_confirmed",
            exit_rule=exit_rule,
            flow_state=flow_result.get("flow_state", "-"),
            flow_score=_safe_int(flow_result.get("score"), 0),
            profit_rate=f"{profit_rate:+.2f}",
        )
        return True

    _log_holding_pipeline(
        stock,
        code,
        "holding_flow_override_defer_exit",
        exit_rule=exit_rule,
        original_sell_reason_type=sell_reason_type,
        flow_action=flow_action,
        flow_state=flow_result.get("flow_state", "-"),
        flow_score=_safe_int(flow_result.get("score"), 0),
        flow_reason=flow_result.get("reason", "-"),
        flow_evidence=_flow_evidence_text(flow_result),
        profit_rate=f"{profit_rate:+.2f}",
        candidate_profit=f"{candidate_profit:+.2f}",
        worsen_pct=f"{worsen_pct:.2f}",
        elapsed_sec=elapsed_sec,
        **_build_observation_contract_fields("ops_volume_diagnostic"),
        **swing_exit_micro_fields,
    )
    _emit_stat_action_decision_snapshot(
        stock=stock,
        code=code,
        strategy=strategy,
        ws_data=ws_data,
        chosen_action="hold_wait",
        eligible_actions=["hold_wait", "exit_now"],
        rejected_actions=[f"exit_now:flow_{flow_action.lower()}"],
        profit_rate=profit_rate,
        peak_profit=peak_profit,
        current_ai_score=current_ai_score,
        held_sec=held_sec,
        curr_price=curr_price,
        buy_price=buy_price,
        exit_rule=exit_rule or "-",
        sell_reason_type=sell_reason_type or "-",
        reason=f"holding_flow_override:{flow_result.get('reason', '-')}",
        force=True,
    )
    return False


def _extract_buy_recovery_probe_features(ai_engine, ws_data, recent_ticks, recent_candles):
    if ai_engine is None or not hasattr(ai_engine, "_extract_scalping_features"):
        return None
    try:
        features = ai_engine._extract_scalping_features(ws_data or {}, recent_ticks or [], recent_candles or []) or {}
    except Exception:
        return None
    return {
        "buy_pressure": float(features.get("buy_pressure_10t", 0.0) or 0.0),
        "tick_accel": float(features.get("tick_acceleration_ratio", 0.0) or 0.0),
        "micro_vwap_bp": float(features.get("curr_vs_micro_vwap_bp", 0.0) or 0.0),
        "large_sell_print": bool(features.get("large_sell_print_detected", False)),
        "tick_sample_count": features.get("tick_sample_count", "-"),
        "tick_window_sample_count": features.get("tick_window_sample_count", "-"),
        "tick_latest_time": features.get("tick_latest_time", "-"),
        "tick_latest_age_ms": features.get("tick_latest_age_ms", "-"),
        "tick_window_span_sec": features.get("tick_window_span_sec", "-"),
        "tick_accel_effective_recent_5tick_seconds": features.get("tick_accel_effective_recent_5tick_seconds", "-"),
        "tick_acceleration_ratio_raw": features.get("tick_acceleration_ratio_raw", "-"),
        "tick_accel_source": features.get("tick_accel_source", "-"),
        "tick_context_stale": features.get("tick_context_stale", "unknown"),
        "tick_context_quality": features.get("tick_context_quality", "unknown"),
        "quote_age_ms": features.get("quote_age_ms", "-"),
        "quote_age_source": features.get("quote_age_source", "missing"),
        "quote_stale": features.get("quote_stale", "unknown"),
    }


def _is_wait65_79_candidate(action, ai_score) -> bool:
    if str(action or "WAIT").upper() == "BUY":
        return False
    try:
        score = float(ai_score or 0.0)
    except Exception:
        return False
    min_score = float(_rule("AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE", 65) or 65)
    max_score = float(_rule("AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE", 79) or 79)
    return min_score <= score <= max_score


def _log_wait65_79_ev_candidate(
    *,
    stock,
    code,
    action,
    ai_score,
    ai_decision,
    ws_data,
    feature_probe,
):
    probe = feature_probe or {}
    latency_state = str((ws_data or {}).get("latency_state", "") or "").strip().upper() or "-"
    source_quality_fields = _ensure_ai_source_quality_fields(
        _build_tick_source_quality_log_fields(probe),
        stock,
        not_evaluated_reason="wait65_79_ev_candidate_no_tick_audit",
    )
    _log_entry_pipeline(
        stock,
        code,
        "wait65_79_ev_candidate",
        action=str(action or "WAIT").upper(),
        ai_score=f"{float(ai_score or 0.0):.1f}",
        buy_pressure=f"{float(probe.get('buy_pressure', 0.0) or 0.0):.2f}",
        tick_accel=f"{float(probe.get('tick_accel', 0.0) or 0.0):.3f}",
        micro_vwap_bp=f"{float(probe.get('micro_vwap_bp', 0.0) or 0.0):.2f}",
        latency_state=latency_state,
        **source_quality_fields,
        parse_ok=bool((ai_decision or {}).get("ai_parse_ok", False)),
        ai_response_ms=int((ai_decision or {}).get("ai_response_ms", 0) or 0),
        terminal_blocker="-",
        **_build_observation_contract_fields("source_quality_gate"),
    )


def _should_run_main_buy_recovery_canary(
    ai_decision,
    ai_score,
    ws_data,
    recent_ticks,
    recent_candles,
    ai_engine,
    *,
    feature_probe=None,
):
    if not _rule_bool("AI_MAIN_BUY_RECOVERY_CANARY_ENABLED", False):
        return False
    if bool((ai_decision or {}).get("ai_fallback_score_50", False)):
        return False
    if str((ai_decision or {}).get("action", "WAIT") or "WAIT").upper() == "BUY":
        return False

    try:
        score = float(ai_score or 0.0)
    except Exception:
        return False
    min_score = _rule_float("AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE", 65)
    max_score = _rule_float("AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE", 79)
    if score < min_score or score > max_score:
        return False

    # DANGER latency 표본은 기회 회복 canary 대상에서 제외한다.
    latency_state = str((ws_data or {}).get("latency_state", "") or "").strip().upper()
    if latency_state == "DANGER":
        return False

    probe = feature_probe or _extract_buy_recovery_probe_features(
        ai_engine,
        ws_data,
        recent_ticks,
        recent_candles,
    )
    if not isinstance(probe, dict):
        return False

    min_buy_pressure = _rule_float("AI_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE", 65.0)
    min_tick_accel = _rule_float("AI_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL", 1.20)
    min_micro_vwap_bp = _rule_float("AI_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP", 0.0)

    buy_pressure = float(probe.get("buy_pressure", 0.0) or 0.0)
    tick_accel = float(probe.get("tick_accel", 0.0) or 0.0)
    micro_vwap_bp = float(probe.get("micro_vwap_bp", 0.0) or 0.0)
    large_sell_print = bool(probe.get("large_sell_print", False))

    if large_sell_print:
        return False
    if buy_pressure < min_buy_pressure:
        return False
    if tick_accel < min_tick_accel:
        return False
    if micro_vwap_bp < min_micro_vwap_bp:
        return False
    return True


def _should_run_score65_74_recovery_probe(
    ai_decision,
    ai_score,
    ws_data,
    recent_ticks,
    recent_candles,
    ai_engine,
    *,
    feature_probe=None,
):
    if not _rule_bool("AI_SCORE65_74_RECOVERY_PROBE_ENABLED", False):
        return False
    if bool((ai_decision or {}).get("ai_fallback_score_50", False)):
        return False
    if str((ai_decision or {}).get("action", "WAIT") or "WAIT").upper() == "BUY":
        return False

    try:
        score = float(ai_score or 0.0)
    except Exception:
        return False
    min_score = _rule_float("AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE", 65)
    max_score = _rule_float("AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE", 74)
    if score < min_score or score > max_score:
        return False

    latency_state = str((ws_data or {}).get("latency_state", "") or "").strip().upper()
    if latency_state == "DANGER":
        return False

    probe = feature_probe or _extract_buy_recovery_probe_features(
        ai_engine,
        ws_data,
        recent_ticks,
        recent_candles,
    )
    if not isinstance(probe, dict):
        return False

    if bool(probe.get("large_sell_print", False)):
        return False
    if float(probe.get("buy_pressure", 0.0) or 0.0) < _rule_float("AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE", 65.0):
        return False
    if float(probe.get("tick_accel", 0.0) or 0.0) < _rule_float("AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL", 1.20):
        return False
    if float(probe.get("micro_vwap_bp", 0.0) or 0.0) < _rule_float("AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP", 0.0):
        return False
    return True


def _resolve_wait6579_probe_entry_unlock(stock) -> dict:
    if not bool((stock or {}).get("wait6579_probe_canary_armed")):
        return {"unlocked": False, "source": "", "event_stage": ""}
    source = str((stock or {}).get("wait6579_probe_canary_source") or "")
    if source == "score65_74_recovery_probe":
        return {
            "unlocked": _rule_bool("AI_SCORE65_74_RECOVERY_PROBE_ENABLED", False),
            "source": source,
            "event_stage": "score65_74_recovery_probe_entry_unlocked",
            "decision_source": "BUY_SCORE65_74_RECOVERY_PROBE",
        }
    if source == "buy_recovery_canary_promoted":
        return {
            "unlocked": _rule_bool("AI_MAIN_BUY_RECOVERY_CANARY_ENABLED", False),
            "source": source,
            "event_stage": "buy_recovery_canary_entry_unlocked",
            "decision_source": "BUY_RECOVERY_CANARY_PROMOTED",
        }
    return {"unlocked": False, "source": source, "event_stage": ""}


def _is_score65_74_recovery_probe_entry_unlocked(stock) -> bool:
    unlock = _resolve_wait6579_probe_entry_unlock(stock)
    return bool(unlock.get("unlocked")) and unlock.get("source") == "score65_74_recovery_probe"


def _should_apply_ai_score_50_buy_hold_override(ai_score, ai_decision=None) -> bool:
    if not _rule_bool("AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED", True):
        return False
    if bool((ai_decision or {}).get("ai_fallback_score_50", False)):
        return True
    try:
        return abs(float(ai_score or 0.0) - 50.0) < 1e-9
    except Exception:
        return False


def _block_ai_score_50_buy_hold_override_if_needed(
    *,
    stock,
    code,
    current_ai_score,
    ai_decision,
    config,
    cooldowns,
    now_ts,
) -> bool:
    if not _should_apply_ai_score_50_buy_hold_override(current_ai_score, ai_decision):
        return False
    cooldown_time = config["AI_WAIT_DROP_COOLDOWN"]
    with ENTRY_LOCK:
        cooldowns[code] = now_ts + cooldown_time
    ai_ops_fields = _build_ai_ops_log_fields(
        ai_decision,
        ai_score_raw=current_ai_score,
        ai_score_after_bonus=current_ai_score,
        entry_score_threshold=75,
        big_bite_bonus_applied=False,
        ai_cooldown_blocked=False,
    )
    ai_ops_fields = _ensure_ai_source_quality_fields(
        ai_ops_fields,
        stock,
        not_evaluated_reason="ai_score_50_buy_hold_override_no_tick_audit",
    )
    _log_entry_pipeline(
        stock,
        code,
        "blocked_ai_score",
        threshold=75,
        cooldown_sec=cooldown_time,
        blocked_reason="ai_score_50_buy_hold_override",
        ai_score_50_buy_hold_override=True,
        **_build_ai_overlap_log_fields(
            stock=stock,
            ai_score=current_ai_score,
            momentum_tag=stock.get("entry_momentum_tag"),
            threshold_profile=stock.get("entry_threshold_profile"),
            overbought_blocked=False,
            blocked_stage="blocked_ai_score",
        ),
        **ai_ops_fields,
    )
    return True


def _resolve_holding_elapsed_sec(stock):
    return resolve_holding_elapsed_sec(stock)


def _bucket_int(value, bucket):
    try:
        bucket = max(1, int(bucket))
        return int(_safe_float(value, 0.0) // bucket)
    except Exception:
        return 0


def _bucket_int_with_deadband(value, bucket, *, zero_band=1.0):
    try:
        bucket = max(1, int(bucket))
        numeric = float(value or 0)
        if abs(numeric) < (bucket * float(zero_band or 0.0)):
            return 0
        return int(numeric // bucket)
    except Exception:
        return 0


def _handle_watching_strategy_branch(stock, code, ws_data, radar, ai_engine, runtime, config):
    strategy = runtime["strategy"]
    pos_tag = runtime["pos_tag"]
    now_ts = runtime["now_ts"]
    curr_price = runtime["curr_price"]
    current_vpw = runtime["current_vpw"]
    fluctuation = runtime["fluctuation"]
    cooldowns = runtime["cooldowns"]
    event_bus = runtime["event_bus"]

    is_trigger = runtime["is_trigger"]
    msg = runtime["msg"]
    ratio = runtime["ratio"]
    liquidity_value = runtime["liquidity_value"]

    current_ai_score = runtime["current_ai_score"]
    ai_decision = {}
    ai_prob = runtime["ai_prob"]
    buy_threshold = runtime["buy_threshold"]
    strong_vpw = runtime["strong_vpw"]

    if strategy == 'SCALPING':
        if pos_tag == 'VCP_CANDID':
            return False

        current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        min_ratio = config["INVEST_RATIO_SCALPING_MIN"]
        max_ratio = config["INVEST_RATIO_SCALPING_MAX"]
        ratio = min_ratio + (current_ai_score / 100.0) * (max_ratio - min_ratio)

        ask_tot = _safe_int(ws_data.get('ask_tot'), 0)
        bid_tot = _safe_int(ws_data.get('bid_tot'), 0)
        open_price = float(ws_data.get('open', curr_price) or curr_price)
        marcap = _resolve_stock_marcap(stock, code)
        turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
        scalp_limits = get_dynamic_scalp_thresholds(marcap, turnover_hint=turnover_hint)

        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price
        max_surge = float(scalp_limits.get('max_surge', config["MAX_SCALP_SURGE_PCT"]) or config["MAX_SCALP_SURGE_PCT"])
        max_intraday_surge = float(
            scalp_limits.get('max_intraday_surge', config["MAX_INTRADAY_SURGE"]) or config["MAX_INTRADAY_SURGE"]
        )
        min_liquidity = int(scalp_limits.get('min_liquidity', config["MIN_SCALP_LIQUIDITY"]) or config["MIN_SCALP_LIQUIDITY"])
        big_bite_hit = False
        big_bite_armed = False
        big_bite_confirmed = False
        big_bite_info = {}
        entry_arm = _get_live_entry_arm(stock, code)

        if entry_arm:
            current_ai_score = float(entry_arm.get('ai_score', current_ai_score) or current_ai_score)
            ratio = float(entry_arm.get('ratio', ratio) or ratio)
            _mutate_stock_state(
                stock,
                set_fields={
                    'rt_ai_prob': current_ai_score / 100.0,
                    'target_buy_price': int(entry_arm.get('target_buy_price') or curr_price),
                    'entry_armed_resume_count': int(stock.get('entry_armed_resume_count', 0) or 0) + 1,
                },
            )
            _log_entry_pipeline(
                stock,
                code,
                "entry_armed_resume",
                ai_score=f"{current_ai_score:.1f}",
                ratio=f"{ratio:.4f}",
                remaining_sec=f"{float(entry_arm.get('remaining_sec', 0.0) or 0.0):.1f}",
                armed_reason=entry_arm.get('reason'),
                dynamic_reason=entry_arm.get('dynamic_reason'),
                **_build_observation_contract_fields("funnel_count"),
            )
            is_trigger = True
        else:
            _reset_scalp_pre_ai_gate_context(stock, ws_data)
            if fluctuation >= max_surge or intraday_surge >= max_intraday_surge:
                overlap_snapshot = _extract_ai_overlap_snapshot(ws_data=ws_data)
                overbought_risk = _classify_overbought_risk(
                    overlap_snapshot,
                    intraday_surge=intraday_surge,
                    max_intraday_surge=max_intraday_surge,
                )
                overbought_context = _register_scalp_pre_ai_gate_context(
                    stock,
                    ws_data,
                    "overbought",
                    {
                        **overbought_risk,
                        "threshold_family": "overbought_pullback_guard_p1",
                        "gate_action": "risk_context_only",
                        "legacy_blocked_stage": "blocked_overbought",
                        "fluctuation": f"{fluctuation:.2f}",
                        "intraday_surge": f"{intraday_surge:.2f}",
                        "max_surge": f"{max_surge:.2f}",
                        "max_intraday_surge": f"{max_intraday_surge:.2f}",
                    },
                )
                _mutate_stock_state(stock, set_fields={'last_ai_overlap_snapshot': overlap_snapshot})
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_overbought",
                    **_build_pre_ai_gate_contract_fields(
                        "overbought_pullback_guard_p1",
                        gate_action="risk_context_only",
                    ),
                    fluctuation=f"{fluctuation:.2f}",
                    intraday_surge=f"{intraday_surge:.2f}",
                    max_surge=f"{max_surge:.2f}",
                    max_intraday_surge=f"{max_intraday_surge:.2f}",
                    marcap=marcap,
                    cap_bucket=scalp_limits.get('bucket_label'),
                    risk_state=overbought_context.get("risk_state"),
                    risk_bucket=overbought_context.get("risk_bucket"),
                    **_build_ai_overlap_log_fields(
                        stock=stock,
                        ai_score=current_ai_score,
                        momentum_tag=stock.get("entry_momentum_tag"),
                        threshold_profile=stock.get("entry_threshold_profile"),
                        overbought_blocked=True,
                        blocked_stage="blocked_overbought",
                        overlap_snapshot=overlap_snapshot,
                    ),
                )
                if not _rule_bool("SCALP_PRE_AI_SOFT_GATE_ENABLED", True):
                    return False

            try:
                tick_data = build_tick_data_from_ws(ws_data)
                big_bite_armed, big_bite_info = arm_big_bite_if_triggered(
                    stock=stock,
                    code=code,
                    ws_data=ws_data,
                    tick_data=tick_data,
                    runtime_state=BIG_BITE_STATE,
                )
                big_bite_confirmed, confirm_info = confirm_big_bite_follow_through(
                    stock=stock,
                    code=code,
                    ws_data=ws_data,
                    runtime_state=BIG_BITE_STATE,
                )
                big_bite_hit = bool(big_bite_confirmed)
                big_bite_info = {**(big_bite_info or {}), **(confirm_info or {})}
            except Exception as exc:
                log_error(f"⚠️ [Big-Bite] 보조 신호 계산 실패 ({code}): {exc}")

            _mutate_stock_state(
                stock,
                set_fields={
                    'big_bite_confirmed': bool(big_bite_confirmed),
                    'big_bite_info': big_bite_info or {},
                    'big_bite_triggered': bool(big_bite_armed),
                },
            )

            gate_tags = config["BIG_BITE_HARD_GATE_TAGS_SCALPING"]
            hard_gate_required = bool(
                config["BIG_BITE_HARD_GATE_ENABLED"]
                and gate_tags
                and any(tag in pos_tag for tag in gate_tags)
            )
            _mutate_stock_state(
                stock,
                set_fields={
                    'big_bite_hard_gate_required': hard_gate_required,
                    'big_bite_hard_gate_blocked': bool(hard_gate_required and not big_bite_confirmed),
                    'big_bite_hard_gate_tags': gate_tags,
                },
            )

            if hard_gate_required and not big_bite_confirmed:
                _mutate_stock_state(stock, set_fields={'big_bite_block_reason': 'hard_gate'})
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_big_bite_hard_gate",
                    required=hard_gate_required,
                    triggered=big_bite_armed,
                    confirmed=big_bite_confirmed,
                    position_tag=pos_tag,
                )
                return False

            if pos_tag == 'VCP_NEXT':
                _mutate_stock_state(
                    stock,
                    set_fields={
                        'target_buy_price': curr_price,
                        'msg_audience': 'ADMIN_ONLY',
                    },
                )
                is_trigger = True
                msg = (
                    f"🚀 **{stock['name']} ({code}) VCP 시초가 예약 매수!**\n"
                    f"현재가: `{curr_price:,}원` (전일 VCP NEXT 달성)"
                )
            else:
                if radar is None:
                    _log_entry_pipeline(stock, code, "blocked_missing_radar", strategy=strategy)
                    return False

                observe_only = bool(_rule("SCALP_DYNAMIC_VPW_OBSERVE_ONLY", True))
                momentum_ws_data = dict(ws_data or {})
                momentum_ws_data["_position_tag"] = pos_tag
                momentum_gate = evaluate_scalping_strength_momentum(momentum_ws_data)
                _mutate_stock_state(
                    stock,
                    set_fields={
                        'entry_momentum_tag': momentum_gate.get("position_tag"),
                        'entry_threshold_profile': momentum_gate.get("threshold_profile"),
                    },
                )
                if momentum_gate.get("enabled"):
                    _log_strength_momentum_observation(stock, code, momentum_gate)
                    if not momentum_gate.get("allowed"):
                        source_quality_block_reason = _strength_momentum_source_quality_block_reason(ws_data, momentum_gate)
                        overlap_snapshot = _extract_ai_overlap_snapshot(ws_data=ws_data)
                        _mutate_stock_state(stock, set_fields={'last_ai_overlap_snapshot': overlap_snapshot})
                        gate_action = "source_quality_block" if source_quality_block_reason else "risk_context_only"
                        strength_context = _register_scalp_pre_ai_gate_context(
                            stock,
                            ws_data,
                            "strength_momentum",
                            {
                                "risk_state": source_quality_block_reason or "weak_momentum_context",
                                "reason": momentum_gate.get("reason"),
                                "threshold_family": "strength_momentum_soft_gate_p1",
                                "gate_action": gate_action,
                                "legacy_blocked_stage": "blocked_strength_momentum",
                                "vpw_delta": f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                                "window_buy_value": int(momentum_gate.get("window_buy_value", 0) or 0),
                                "window_buy_ratio": f"{float(momentum_gate.get('window_buy_ratio', 0.0) or 0.0):.2f}",
                                "window_exec_buy_ratio": f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                                "window_net_buy_qty": int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                            },
                        )
                        _log_entry_pipeline(
                            stock,
                            code,
                            "blocked_strength_momentum",
                            **_build_pre_ai_gate_contract_fields(
                                "strength_momentum_soft_gate_p1",
                                gate_action=gate_action,
                            ),
                            reason=momentum_gate.get("reason"),
                            source_quality_block_reason=source_quality_block_reason or "-",
                            risk_state=strength_context.get("risk_state"),
                            delta=f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                            buy_value=int(momentum_gate.get("window_buy_value", 0) or 0),
                            buy_ratio=f"{float(momentum_gate.get('window_buy_ratio', 0.0) or 0.0):.2f}",
                            exec_buy_ratio=f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                            net_buy_qty=int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                            **_build_ai_overlap_log_fields(
                                stock=stock,
                                ai_score=current_ai_score,
                                momentum_tag=momentum_gate.get("position_tag"),
                                threshold_profile=momentum_gate.get("threshold_profile"),
                                overbought_blocked=False,
                                blocked_stage="blocked_strength_momentum",
                                overlap_snapshot=overlap_snapshot,
                            ),
                        )
                        if source_quality_block_reason or (not observe_only and not _rule_bool("SCALP_PRE_AI_SOFT_GATE_ENABLED", True)):
                            return False

                if current_vpw < config["VPW_SCALP_LIMIT"]:
                    shadow_candidate = None
                    if momentum_gate.get("allowed"):
                        if observe_only:
                            shadow_candidate = record_shadow_candidate(stock, code, ws_data, momentum_gate)
                            if shadow_candidate:
                                _log_entry_pipeline(
                                    stock,
                                    code,
                                    "shadow_candidate_recorded",
                                    shadow_id=shadow_candidate.get("shadow_id"),
                                    signal_price=shadow_candidate.get("signal_price"),
                                    dynamic_delta=f"{float(shadow_candidate.get('dynamic_delta', 0.0) or 0.0):.1f}",
                                    dynamic_buy_value=int(shadow_candidate.get("dynamic_window_buy_value", 0) or 0),
                                    dynamic_buy_ratio=f"{float(shadow_candidate.get('dynamic_window_buy_ratio', 0.0) or 0.0):.2f}",
                                )
                        else:
                            _log_entry_pipeline(
                                stock,
                                code,
                                "dynamic_vpw_override_pass",
                                **_build_observation_contract_fields("ops_volume_diagnostic"),
                                current_vpw=f"{current_vpw:.1f}",
                                threshold=config["VPW_SCALP_LIMIT"],
                                dynamic_reason=momentum_gate.get("reason"),
                                dynamic_delta=f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                                dynamic_buy_value=int(momentum_gate.get("window_buy_value", 0) or 0),
                                dynamic_buy_ratio=f"{float(momentum_gate.get('window_buy_ratio', 0.0) or 0.0):.2f}",
                                dynamic_exec_buy_ratio=f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                                dynamic_net_buy_qty=int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                                dynamic_profile=momentum_gate.get("threshold_profile"),
                            )
                            shadow_candidate = None
                    if not (momentum_gate.get("allowed") and not observe_only):
                        overlap_snapshot = _extract_ai_overlap_snapshot(ws_data=ws_data)
                        _mutate_stock_state(stock, set_fields={'last_ai_overlap_snapshot': overlap_snapshot})
                        vpw_context = _register_scalp_pre_ai_gate_context(
                            stock,
                            ws_data,
                            "strength_momentum",
                            {
                                "risk_state": "below_static_vpw_context",
                                "reason": momentum_gate.get("reason"),
                                "threshold_family": "strength_momentum_soft_gate_p1",
                                "gate_action": "risk_context_only",
                                "legacy_blocked_stage": "blocked_vpw",
                                "current_vpw": f"{current_vpw:.1f}",
                                "vpw_threshold": config["VPW_SCALP_LIMIT"],
                            },
                        )
                        _log_entry_pipeline(
                            stock,
                            code,
                            "blocked_vpw",
                            **_build_pre_ai_gate_contract_fields(
                                "strength_momentum_soft_gate_p1",
                                gate_action="risk_context_only",
                            ),
                            current_vpw=f"{current_vpw:.1f}",
                            threshold=config["VPW_SCALP_LIMIT"],
                            dynamic_allowed=momentum_gate.get("allowed"),
                            dynamic_reason=momentum_gate.get("reason"),
                            risk_state=vpw_context.get("risk_state"),
                            dynamic_delta=f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                            dynamic_buy_value=int(momentum_gate.get("window_buy_value", 0) or 0),
                            dynamic_exec_buy_ratio=f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                            dynamic_net_buy_qty=int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                            shadow_recorded=bool(shadow_candidate),
                            **_build_ai_overlap_log_fields(
                                stock=stock,
                                ai_score=current_ai_score,
                                momentum_tag=momentum_gate.get("position_tag"),
                                threshold_profile=momentum_gate.get("threshold_profile"),
                                overbought_blocked=False,
                                blocked_stage="blocked_vpw",
                                overlap_snapshot=overlap_snapshot,
                            ),
                        )
                        if not _rule_bool("SCALP_PRE_AI_SOFT_GATE_ENABLED", True):
                            return False

                if liquidity_value < min_liquidity:
                    liquidity_context = _register_scalp_pre_ai_gate_context(
                        stock,
                        ws_data,
                        "liquidity",
                        {
                            "risk_state": "below_min_liquidity",
                            "reason": "below_min_liquidity",
                            "threshold_family": "liquidity_pre_submit_guard_p1",
                            "gate_action": "risk_context_only",
                            "legacy_blocked_stage": "blocked_liquidity",
                            "liquidity_value": int(liquidity_value),
                            "min_liquidity": min_liquidity,
                        },
                    )
                    _log_entry_pipeline(
                        stock,
                        code,
                        "blocked_liquidity",
                        **_build_pre_ai_gate_contract_fields(
                            "liquidity_pre_submit_guard_p1",
                            gate_action="risk_context_only",
                        ),
                        liquidity_value=int(liquidity_value),
                        min_liquidity=min_liquidity,
                        marcap=marcap,
                        cap_bucket=scalp_limits.get('bucket_label'),
                        risk_state=liquidity_context.get("risk_state"),
                    )
                    if not _rule_bool("SCALP_PRE_AI_SOFT_GATE_ENABLED", True):
                        return False

                scanner_price = stock.get('buy_price') or 0
                if scanner_price > 0:
                    gap_pct = (curr_price - scanner_price) / scanner_price * 100
                    if gap_pct >= 1.5:
                        if code not in cooldowns:
                            with ENTRY_LOCK:
                                cooldowns[code] = now_ts + 1200
                        _log_entry_pipeline(
                            stock,
                            code,
                            "blocked_gap_from_scan",
                            gap_pct=f"{gap_pct:.1f}",
                            scanner_price=int(scanner_price),
                            curr_price=curr_price,
                        )
                        return False

                current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
                target_buy_price, used_drop_pct = radar.get_smart_target_price(
                    curr_price,
                    v_pw=current_vpw,
                    ai_score=current_ai_score,
                    ask_tot=ask_tot,
                    bid_tot=bid_tot,
                )

                last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
                time_elapsed = now_ts - last_ai_time
                is_vip_target = (target_buy_price > 0) and (curr_price <= target_buy_price * 1.015)

                if is_vip_target and last_ai_time == 0:
                    log_info(f"⏳ [{stock['name']}] 첫 AI 분석을 시작합니다... (기계적 매수 일시 보류)")

                if ai_engine and is_vip_target and (time_elapsed > config["AI_WATCHING_COOLDOWN"] or last_ai_time == 0):
                    ai_call_executed = False
                    try:
                        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)
                        if ws_data.get('orderbook') and recent_ticks:
                            ai_decision = ai_engine.analyze_target(
                                stock['name'],
                                ws_data,
                                recent_ticks,
                                recent_candles,
                                prompt_profile="watching",
                            )
                            ai_call_executed = True
                            _mutate_stock_state(
                                stock,
                                pop_fields=[
                                    'wait6579_probe_canary_armed',
                                    'wait6579_probe_canary_source',
                                    'wait6579_probe_canary_score',
                                ],
                            )

                            action = ai_decision.get('action', 'WAIT')
                            ai_score = ai_decision.get('score', 50)
                            reason = ai_decision.get('reason', '사유 없음')
                            ai_source_quality_fields = _build_tick_source_quality_log_fields(ai_decision)
                            _mutate_stock_state(
                                stock,
                                set_fields={
                                    'last_watching_ai_action': str(action or 'WAIT').upper(),
                                    'last_watching_ai_score': float(ai_score or 0.0),
                                    'last_watching_ai_reason': str(reason or '')[:240],
                                    'last_watching_ai_confirmed_at': now_ts,
                                    'last_watching_ai_source_quality_fields': ai_source_quality_fields,
                                },
                            )
                            feature_probe = _extract_buy_recovery_probe_features(
                                ai_engine,
                                ws_data,
                                recent_ticks,
                                recent_candles,
                            ) or {
                                "buy_pressure": 0.0,
                                "tick_accel": 0.0,
                                "micro_vwap_bp": 0.0,
                                "large_sell_print": False,
                            }
                            latency_state = str((ws_data or {}).get("latency_state", "") or "").strip().upper() or "-"
                            overlap_snapshot = _extract_ai_overlap_snapshot(
                                ws_data=ws_data,
                                recent_ticks=recent_ticks,
                                recent_candles=recent_candles,
                                ai_engine=ai_engine,
                            )
                            _mutate_stock_state(stock, set_fields={'last_ai_overlap_snapshot': overlap_snapshot})
                            _log_entry_pipeline(
                                stock,
                                code,
                                "ai_confirmed",
                                action=action,
                                vip_target=is_vip_target,
                                buy_pressure=f"{float(feature_probe.get('buy_pressure', 0.0) or 0.0):.2f}",
                                tick_accel=f"{float(feature_probe.get('tick_accel', 0.0) or 0.0):.3f}",
                                micro_vwap_bp=f"{float(feature_probe.get('micro_vwap_bp', 0.0) or 0.0):.2f}",
                                large_sell_print_detected=bool(feature_probe.get("large_sell_print", False)),
                                latency_state=latency_state,
                                **_scalp_pre_ai_gate_context_log_fields(stock.get("scalp_pre_ai_gate_context")),
                                **_build_ai_overlap_log_fields(
                                    stock=stock,
                                    ai_score=ai_score,
                                    momentum_tag=stock.get("entry_momentum_tag"),
                                    threshold_profile=stock.get("entry_threshold_profile"),
                                    overbought_blocked=False,
                                    blocked_stage="-",
                                    overlap_snapshot=overlap_snapshot,
                                ),
                                **_build_ai_ops_log_fields(
                                    ai_decision,
                                    ai_score_raw=ai_score,
                                    ai_score_after_bonus=ai_score,
                                    entry_score_threshold=75,
                                    big_bite_bonus_applied=False,
                                    ai_cooldown_blocked=False,
                                ),
                            )
                            _emit_scalp_entry_adm_snapshot(
                                stock,
                                code,
                                "ai_confirmed",
                                ai_decision=ai_decision,
                                ai_score=ai_score,
                                chosen_action="BUY_NOW" if str(action or "").upper() == "BUY" and _safe_float(ai_score, 0.0) >= 75 else "NO_BUY_AI",
                                actual_order_submitted=False,
                                broker_order_forbidden=True,
                            )
                            if _is_wait65_79_candidate(action, ai_score):
                                _log_wait65_79_ev_candidate(
                                    stock=stock,
                                    code=code,
                                    action=action,
                                    ai_score=ai_score,
                                    ai_decision=ai_decision,
                                    ws_data=ws_data,
                                    feature_probe=feature_probe,
                                )
                            if _should_run_score65_74_recovery_probe(
                                ai_decision,
                                ai_score,
                                ws_data,
                                recent_ticks,
                                recent_candles,
                                ai_engine,
                                feature_probe=feature_probe,
                            ):
                                action = "BUY"
                                reason = (
                                    f"{reason} | score65_74_recovery_probe:{float(ai_score or 0.0):.0f}"
                                    if reason
                                    else f"score65_74_recovery_probe:{float(ai_score or 0.0):.0f}"
                                )
                                ai_decision = dict(ai_decision or {})
                                ai_decision["action"] = action
                                ai_decision["score"] = ai_score
                                ai_decision["reason"] = reason
                                _mutate_stock_state(
                                    stock,
                                    set_fields={
                                        'wait6579_probe_canary_armed': True,
                                        'wait6579_probe_canary_source': "score65_74_recovery_probe",
                                        'wait6579_probe_canary_score': f"{float(ai_score):.1f}",
                                    },
                                )
                                _log_entry_pipeline(
                                    stock,
                                    code,
                                    "score65_74_recovery_probe",
                                    applied=True,
                                    decision_source="BUY_SCORE65_74_RECOVERY_PROBE",
                                    threshold_family="score65_74_recovery_probe",
                                    threshold_version=str(
                                        _rule("AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION", "runtime_default")
                                        or "runtime_default"
                                    ),
                                    threshold_calibration_state=str(
                                        _rule("AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE", "runtime_default")
                                        or "runtime_default"
                                    ),
                                    threshold_applied_value=(
                                        f"enabled=True|score={int(_rule('AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE', 65) or 65)}-"
                                        f"{int(_rule('AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE', 74) or 74)}|"
                                        f"budget={int(_rule('AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW', 50_000) or 50_000)}|qty=1"
                                    ),
                                    ai_score=f"{float(ai_score or 0.0):.1f}",
                                    buy_pressure=f"{float(feature_probe.get('buy_pressure', 0.0) or 0.0):.2f}",
                                    tick_accel=f"{float(feature_probe.get('tick_accel', 0.0) or 0.0):.3f}",
                                    micro_vwap_bp=f"{float(feature_probe.get('micro_vwap_bp', 0.0) or 0.0):.2f}",
                                    latency_state=str((ws_data or {}).get("latency_state", "") or "").strip().upper() or "-",
                                    **_build_tick_source_quality_log_fields(feature_probe),
                                    qty_cap=1,
                                    budget_cap_krw=int(_rule("AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW", 50_000) or 50_000),
                                )
                            _submit_watching_shared_prompt_shadow(
                                stock_name=stock['name'],
                                code=code,
                                ws_data=ws_data,
                                recent_ticks=recent_ticks,
                                recent_candles=recent_candles,
                                gemini_result=ai_decision,
                                record_id=stock.get("id"),
                            )

                            if _should_run_main_buy_recovery_canary(
                                ai_decision,
                                ai_score,
                                ws_data,
                                recent_ticks,
                                recent_candles,
                                ai_engine,
                                feature_probe=feature_probe,
                            ):
                                recovery_decision = ai_engine.analyze_target_shadow_prompt(
                                    stock['name'],
                                    ws_data,
                                    recent_ticks,
                                    recent_candles,
                                    strategy="SCALPING",
                                    prompt_override=SCALPING_BUY_RECOVERY_CANARY_PROMPT,
                                    prompt_type="scalping_buy_recovery_canary",
                                    cache_profile="watching_buy_recovery_canary",
                                )
                                recovery_action = str(recovery_decision.get("action", "WAIT") or "WAIT").upper()
                                recovery_score = float(recovery_decision.get("score", 50) or 50)
                                promote_threshold = float(_rule("AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE", 75) or 75)
                                can_promote = (
                                    str(action or "WAIT").upper() != "BUY"
                                    and recovery_action == "BUY"
                                    and recovery_score >= promote_threshold
                                )
                                _log_entry_pipeline(
                                    stock,
                                    code,
                                    "watching_buy_recovery_canary",
                                    main_action=str(action or "WAIT").upper(),
                                    main_score=f"{float(ai_score or 0.0):.1f}",
                                    recovery_action=recovery_action,
                                    recovery_score=f"{recovery_score:.1f}",
                                    promoted=str(can_promote).lower(),
                                    promote_threshold=f"{promote_threshold:.1f}",
                                    **_build_ai_ops_log_fields(
                                        recovery_decision,
                                        ai_score_raw=recovery_score,
                                        ai_score_after_bonus=recovery_score,
                                        entry_score_threshold=promote_threshold,
                                        big_bite_bonus_applied=False,
                                        ai_cooldown_blocked=False,
                                    ),
                                )
                                if can_promote:
                                    action = "BUY"
                                    ai_score = recovery_score
                                    reason = (
                                        f"{reason} | buy_recovery_canary:{recovery_score:.0f}"
                                        if reason
                                        else f"buy_recovery_canary:{recovery_score:.0f}"
                                    )
                                ai_decision = dict(ai_decision or {})
                                ai_decision["action"] = action
                                ai_decision["score"] = ai_score
                                ai_decision["reason"] = reason
                                if can_promote:
                                    _mutate_stock_state(
                                        stock,
                                        set_fields={
                                            'wait6579_probe_canary_armed': True,
                                            'wait6579_probe_canary_source': "buy_recovery_canary_promoted",
                                            'wait6579_probe_canary_score': f"{float(recovery_score):.1f}",
                                        },
                                    )

                            if ai_score != 50:
                                _mutate_stock_state(stock, set_fields={'rt_ai_prob': ai_score / 100.0})
                                current_ai_score = ai_score
                                log_info(f"💎 [VIP AI 확답 완료: {stock['name']}] {action} | 점수: {ai_score}점 | {reason}")
                                if action == "BUY":
                                    publish_ai_buy_alert, publish_skip_reason = _should_publish_watching_buy_analysis_telegram(
                                        stock,
                                        strategy,
                                        current_ai_score,
                                        buy_score_threshold=config.get("BUY_SCORE_THRESHOLD", 75)
                                        if isinstance(config, dict)
                                        else 75,
                                    )
                                    if publish_ai_buy_alert:
                                        ai_msg = (
                                            f"🤖 <b>[VIP 종목 실시간 분석]</b>\n"
                                            f"🎯 종목: {stock['name']}\n"
                                            f"⚡ 행동: <b>{action} ({ai_score}점)</b>\n"
                                            f"🧠 사유: {reason}"
                                        )
                                        target_audience = (
                                            'VIP_ALL'
                                            if liquidity_value >= config["VIP_LIQUIDITY_THRESHOLD"] and current_ai_score >= 90
                                            else 'ADMIN_ONLY'
                                        )
                                        target_audience = _resolve_telegram_audience_for_stock(
                                            stock,
                                            strategy,
                                            default=target_audience,
                                        )
                                        event_bus.publish(
                                            'TELEGRAM_BROADCAST',
                                            {'message': ai_msg, 'audience': target_audience, 'parse_mode': 'HTML'},
                                        )
                                    else:
                                        _log_entry_pipeline(
                                            stock,
                                            code,
                                            "buy_analysis_telegram_suppressed",
                                            action=action,
                                            ai_score=f"{float(current_ai_score or 0.0):.1f}",
                                            reason=publish_skip_reason,
                                            actual_order_submitted=False,
                                            broker_order_forbidden=True,
                                            decision_authority="sim_or_pre_submit_observation_only",
                                        )
                            else:
                                log_info(f"⚠️ [{stock['name']}] AI 판단 보류(Score 50). 매수보류 override를 적용합니다.")
                                current_ai_score = 50
                    except Exception as e:
                        log_error(
                            f"🚨 [AI 엔진 오류] {stock['name']}({code}): {e} | "
                            "Score 50 매수보류 override로 처리합니다."
                        )
                        current_ai_score = 50

                    if ai_call_executed:
                        with ENTRY_LOCK:
                            LAST_AI_CALL_TIMES[code] = now_ts

                    if _block_ai_score_50_buy_hold_override_if_needed(
                        stock=stock,
                        code=code,
                        current_ai_score=current_ai_score,
                        ai_decision=ai_decision,
                        config=config,
                        cooldowns=cooldowns,
                        now_ts=now_ts,
                    ):
                        return False

                    if ai_call_executed and last_ai_time == 0:
                        if not big_bite_confirmed:
                            _log_entry_pipeline(
                                stock,
                                code,
                                "first_ai_wait",
                                **_build_observation_contract_fields("funnel_count"),
                                ai_score=f"{current_ai_score:.1f}",
                                big_bite_confirmed=big_bite_confirmed,
                                vip_target=is_vip_target,
                            )
                            _maybe_arm_scalp_sim_candidate_window(
                                stock=stock,
                                code=code,
                                ws_data=ws_data,
                                runtime=runtime,
                                ai_decision=ai_decision,
                                ai_score=current_ai_score,
                                source_stage="first_ai_wait",
                                blocked_reason="big_bite_not_confirmed",
                                ai_engine=ai_engine,
                            )
                            return False

                if _block_ai_score_50_buy_hold_override_if_needed(
                    stock=stock,
                    code=code,
                    current_ai_score=current_ai_score,
                    ai_decision=ai_decision,
                    config=config,
                    cooldowns=cooldowns,
                    now_ts=now_ts,
                ):
                    return False

                boost_applied_value = 0
                if big_bite_confirmed:
                    boost_applied_value = config["BIG_BITE_BOOST_SCORE"]
                elif big_bite_armed:
                    boost_applied_value = config["BIG_BITE_ARMED_ENTRY_BONUS"]

                if boost_applied_value:
                    current_ai_score = min(100.0, current_ai_score + boost_applied_value)
                    _mutate_stock_state(
                        stock,
                        set_fields={
                            'big_bite_boosted': bool(big_bite_confirmed),
                            'big_bite_boost_value': boost_applied_value,
                        },
                    )
                else:
                    _mutate_stock_state(
                        stock,
                        set_fields={
                            'big_bite_boosted': False,
                            'big_bite_boost_value': 0,
                        },
                    )

                if ai_engine and is_vip_target and last_ai_time > 0 and time_elapsed <= config["AI_WATCHING_COOLDOWN"]:
                    _log_entry_pipeline(
                        stock,
                        code,
                        "ai_cooldown_blocked",
                        cooldown_elapsed_sec=int(time_elapsed),
                        cooldown_threshold_sec=config["AI_WATCHING_COOLDOWN"],
                        **_build_ai_input_not_evaluated_fields("watching_ai_cooldown_active"),
                        **_build_ai_ops_log_fields(
                            {
                                "ai_parse_ok": False,
                                "ai_parse_fail": False,
                                "ai_fallback_score_50": False,
                                "ai_response_ms": 0,
                                "ai_prompt_type": "scalping_watch_cooldown_blocked",
                                "ai_result_source": "watching_cooldown",
                            },
                            ai_score_raw=current_ai_score,
                            ai_score_after_bonus=current_ai_score,
                            entry_score_threshold=75,
                            big_bite_bonus_applied=bool(boost_applied_value),
                            ai_cooldown_blocked=True,
                        ),
                    )

                wait6579_probe_entry_unlock = _resolve_wait6579_probe_entry_unlock(stock)
                wait6579_probe_entry_unlocked = bool(wait6579_probe_entry_unlock.get("unlocked"))
                if current_ai_score < 75 and current_ai_score != 50 and not wait6579_probe_entry_unlocked:
                    cooldown_time = config["AI_WAIT_DROP_COOLDOWN"]
                    with ENTRY_LOCK:
                        cooldowns[code] = now_ts + cooldown_time
                    ai_ops_fields = _build_ai_ops_log_fields(
                        ai_decision,
                        ai_score_raw=current_ai_score,
                        ai_score_after_bonus=current_ai_score,
                        entry_score_threshold=75,
                        big_bite_bonus_applied=bool(boost_applied_value),
                        ai_cooldown_blocked=False,
                    )
                    ai_ops_fields = _ensure_ai_source_quality_fields(
                        ai_ops_fields,
                        stock,
                        not_evaluated_reason="blocked_ai_score_no_tick_audit",
                    )
                    _log_entry_pipeline(
                        stock,
                        code,
                        "blocked_ai_score",
                        threshold=75,
                        cooldown_sec=cooldown_time,
                        **_build_ai_overlap_log_fields(
                            stock=stock,
                            ai_score=current_ai_score,
                            momentum_tag=stock.get("entry_momentum_tag"),
                            threshold_profile=stock.get("entry_threshold_profile"),
                            overbought_blocked=False,
                            blocked_stage="blocked_ai_score",
                        ),
                        **ai_ops_fields,
                    )
                    _emit_scalp_entry_adm_snapshot(
                        stock,
                        code,
                        "blocked_ai_score",
                        ai_decision=ai_decision,
                        ai_score=current_ai_score,
                        chosen_action="NO_BUY_AI",
                        actual_order_submitted=False,
                        broker_order_forbidden=True,
                    )
                    _maybe_arm_scalp_sim_candidate_window(
                        stock=stock,
                        code=code,
                        ws_data=ws_data,
                        runtime=runtime,
                        ai_decision=ai_decision,
                        ai_score=current_ai_score,
                        source_stage="blocked_ai_score",
                        blocked_reason="below_buy_score_threshold",
                        ai_engine=ai_engine,
                    )
                    return False
                if wait6579_probe_entry_unlocked and current_ai_score < 75:
                    _log_entry_pipeline(
                        stock,
                        code,
                        wait6579_probe_entry_unlock.get("event_stage") or "wait6579_probe_canary_entry_unlocked",
                        decision_source=wait6579_probe_entry_unlock.get("decision_source") or "WAIT6579_PROBE_CANARY",
                        ai_score=f"{current_ai_score:.1f}",
                        entry_score_threshold=75,
                        source=wait6579_probe_entry_unlock.get("source") or stock.get("wait6579_probe_canary_source", "-"),
                        qty_cap=1,
                        budget_cap_krw=int(_rule("AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW", 50_000) or 50_000),
                    )

                final_target_buy_price, final_used_drop_pct = radar.get_smart_target_price(
                    curr_price,
                    v_pw=current_vpw,
                    ai_score=current_ai_score,
                    ask_tot=ask_tot,
                    bid_tot=bid_tot,
                )
                _mutate_stock_state(stock, set_fields={'target_buy_price': final_target_buy_price})
                _activate_entry_arm(
                    stock,
                    code,
                    ai_score=current_ai_score,
                    ratio=ratio,
                    target_buy_price=final_target_buy_price,
                    current_vpw=current_vpw,
                    reason='qualification_passed',
                    dynamic_reason=momentum_gate.get('reason'),
                )
                _emit_scalp_entry_adm_snapshot(
                    stock,
                    code,
                    "entry_armed",
                    ai_decision=ai_decision,
                    ai_score=current_ai_score,
                    chosen_action="BUY_NOW",
                    actual_order_submitted=False,
                    broker_order_forbidden=False,
                    extra_fields={"target_buy_price": final_target_buy_price},
                )
                is_trigger = True
                if big_bite_confirmed:
                    _mutate_stock_state(stock, set_fields={'big_bite_boosted': True})

    elif strategy in ['KOSDAQ_ML', 'KOSPI_ML']:
        if radar is None:
            _log_entry_pipeline(stock, code, "blocked_missing_radar", strategy=strategy)
            return False

        if strategy == 'KOSDAQ_ML':
            marcap = _resolve_stock_marcap(stock, code)
            turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
            swing_gap = get_dynamic_swing_gap_threshold(strategy, marcap, turnover_hint=turnover_hint)
            max_gap = float(
                swing_gap.get('threshold', _get_swing_gap_threshold(strategy)) or _get_swing_gap_threshold(strategy)
            )
            if fluctuation >= max_gap:
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_swing_gap",
                    **_build_observation_contract_fields("funnel_count"),
                    strategy=strategy,
                    fluctuation=f"{fluctuation:.2f}",
                    threshold=f"{max_gap:.2f}",
                    marcap=marcap,
                    cap_bucket=swing_gap.get('bucket_label'),
                )
                if _rule_bool("SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED", True):
                    maybe_start_swing_intraday_probe(
                        stock=stock,
                        code=code,
                        ws_data=ws_data,
                        origin_stage="blocked_swing_gap",
                        runtime=runtime,
                        evidence_quality="counterfactual_after_gap",
                        probe_arm="counterfactual_after_gap",
                        extra_fields={
                            "fluctuation": f"{fluctuation:.2f}",
                            "gap_pct": f"{fluctuation:.2f}",
                            "threshold": f"{max_gap:.2f}",
                            "marcap": marcap,
                            "cap_bucket": swing_gap.get('bucket_label'),
                            "counterfactual_after_gap": True,
                            "evidence_quality_weight": 0.60,
                        },
                    )
                return False

            vpw_limit_base = int(config["VPW_KOSDAQ_LIMIT"])
            strong_vpw = int(config["VPW_STRONG_KOSDAQ_LIMIT"])
            buy_threshold = int(config["BUY_SCORE_KOSDAQ_THRESHOLD"])
            vpw_condition = current_vpw >= vpw_limit_base
            ratio_min = float(config["INVEST_RATIO_KOSDAQ_MIN"])
            ratio_max = float(config["INVEST_RATIO_KOSDAQ_MAX"])
            ai_score_threshold = int(config["AI_SCORE_THRESHOLD_KOSDAQ"])
            ai_prob = stock.get('prob', config["SNIPER_AGGRESSIVE_PROB"])
            v_pw_limit = vpw_limit_base if ai_prob >= 0.70 else strong_vpw
        else:
            marcap = _resolve_stock_marcap(stock, code)
            turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
            swing_gap = get_dynamic_swing_gap_threshold(strategy, marcap, turnover_hint=turnover_hint)
            max_gap = float(
                swing_gap.get('threshold', _get_swing_gap_threshold(strategy)) or _get_swing_gap_threshold(strategy)
            )
            if fluctuation >= max_gap:
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_swing_gap",
                    **_build_observation_contract_fields("funnel_count"),
                    strategy=strategy,
                    fluctuation=f"{fluctuation:.2f}",
                    threshold=f"{max_gap:.2f}",
                    marcap=marcap,
                    cap_bucket=swing_gap.get('bucket_label'),
                )
                if _rule_bool("SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED", True):
                    maybe_start_swing_intraday_probe(
                        stock=stock,
                        code=code,
                        ws_data=ws_data,
                        origin_stage="blocked_swing_gap",
                        runtime=runtime,
                        evidence_quality="counterfactual_after_gap",
                        probe_arm="counterfactual_after_gap",
                        extra_fields={
                            "fluctuation": f"{fluctuation:.2f}",
                            "gap_pct": f"{fluctuation:.2f}",
                            "threshold": f"{max_gap:.2f}",
                            "marcap": marcap,
                            "cap_bucket": swing_gap.get('bucket_label'),
                            "counterfactual_after_gap": True,
                            "evidence_quality_weight": 0.60,
                        },
                    )
                return False

            vpw_limit_base = 100
            strong_vpw = int(config["VPW_STRONG_LIMIT"])
            buy_threshold = int(config["BUY_SCORE_THRESHOLD"])
            vpw_condition = current_vpw >= 103
            ratio_min = float(config["INVEST_RATIO_KOSPI_MIN"])
            ratio_max = float(config["INVEST_RATIO_KOSPI_MAX"])
            ai_score_threshold = int(config["AI_SCORE_THRESHOLD_KOSPI"])
            ai_prob = stock.get('prob', config["SNIPER_AGGRESSIVE_PROB"])
            v_pw_limit = vpw_limit_base if ai_prob >= 0.70 else strong_vpw

        score, prices, conclusion, checklist, metrics = radar.analyze_signal_integrated(ws_data, ai_prob)
        is_shooting = current_vpw >= v_pw_limit
        if (score >= buy_threshold or is_shooting) and vpw_condition:
            gatekeeper_error_cd = int(_rule('ML_GATEKEEPER_ERROR_COOLDOWN', 60 * 10))
            gatekeeper = None
            gatekeeper_allow = False
            action_label = 'UNKNOWN'
            gatekeeper_eval_ms = 0

            if not ai_engine:
                log_error(f"🚨 [{strategy} Gatekeeper 미초기화] {stock['name']}({code})")
                with ENTRY_LOCK:
                    cooldowns[code] = now_ts + gatekeeper_error_cd
                _log_entry_pipeline(stock, code, "blocked_gatekeeper_missing", strategy=strategy)
                return False

            realtime_ctx = None
            gatekeeper_fast_sig = _build_gatekeeper_fast_signature(stock, ws_data, strategy, score)
            gatekeeper_fast_snapshot = _build_gatekeeper_fast_snapshot(stock, ws_data, strategy, score)
            gatekeeper_fast_reuse_sec = _resolve_gatekeeper_fast_reuse_sec()
            gatekeeper_fast_max_ws_age = float(_rule('AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC', 2.0) or 2.0)
            gatekeeper_ws_age_sec = _get_ws_snapshot_age_sec(ws_data)
            fast_sig_matches = gatekeeper_fast_sig == stock.get('last_gatekeeper_fast_signature')
            fast_sig_age = _resolve_reference_age_sec(
                stock.get('last_gatekeeper_fast_at'),
                fallback_ts=stock.get('last_gatekeeper_action_at'),
                now_ts=now_ts,
            )
            fast_sig_age_str = "-" if fast_sig_age is None else f"{fast_sig_age:.1f}"
            near_score_boundary = abs(float(score) - float(buy_threshold)) <= 3.0
            fast_sig_fresh = fast_sig_age is not None and fast_sig_age < gatekeeper_fast_reuse_sec
            ws_fresh = gatekeeper_ws_age_sec is None or gatekeeper_ws_age_sec <= gatekeeper_fast_max_ws_age
            has_last_action = bool(str(stock.get('last_gatekeeper_action', '') or '').strip())
            has_last_allow_flag = 'last_gatekeeper_allow_entry' in stock
            can_fast_reuse = (
                fast_sig_matches and fast_sig_fresh and ws_fresh and not near_score_boundary and has_last_action and has_last_allow_flag
            )

            if can_fast_reuse:
                gatekeeper = {
                    'allow_entry': bool(stock.get('last_gatekeeper_allow_entry', False)),
                    'action_label': stock.get('last_gatekeeper_action', 'UNKNOWN'),
                    'report': stock.get('last_gatekeeper_report', ''),
                    'eval_ms': 0,
                    'lock_wait_ms': 0,
                    'packet_build_ms': 0,
                    'model_call_ms': 0,
                    'total_internal_ms': 0,
                    'cache_hit': True,
                    'cache_mode': 'fast_reuse',
                }
                gatekeeper_eval_ms = 0
                _log_entry_pipeline(
                    stock,
                    code,
                    "gatekeeper_fast_reuse",
                    strategy=strategy,
                    action=gatekeeper.get('action_label', 'UNKNOWN'),
                    age_sec=fast_sig_age_str,
                    ws_age_sec="-" if gatekeeper_ws_age_sec is None else f"{gatekeeper_ws_age_sec:.2f}",
                )
                is_new_evaluation = False
            else:
                action_age_sec = _resolve_reference_age_sec(stock.get('last_gatekeeper_action_at'), now_ts=now_ts)
                allow_age_sec = _resolve_reference_age_sec(stock.get('last_gatekeeper_allow_entry_at'), now_ts=now_ts)
                action_age_sec_str = "-" if action_age_sec is None else f"{action_age_sec:.2f}"
                allow_age_sec_str = "-" if allow_age_sec is None else f"{allow_age_sec:.2f}"
                sig_delta = _describe_snapshot_deltas(stock.get('last_gatekeeper_fast_snapshot', {}), gatekeeper_fast_snapshot, limit=5) or "-"
                _log_entry_pipeline(
                    stock,
                    code,
                    "gatekeeper_fast_reuse_bypass",
                    strategy=strategy,
                    score=round(float(score), 2),
                    age_sec=fast_sig_age_str,
                    ws_age_sec="-" if gatekeeper_ws_age_sec is None else f"{gatekeeper_ws_age_sec:.2f}",
                    action_age_sec=action_age_sec_str,
                    allow_entry_age_sec=allow_age_sec_str,
                    sig_delta=sig_delta,
                    reason_codes=_reason_codes(
                        sig_changed=fast_sig_matches,
                        age_expired=fast_sig_fresh,
                        ws_stale=ws_fresh,
                        score_boundary=not near_score_boundary,
                        missing_action=has_last_action,
                        missing_allow_flag=has_last_allow_flag,
                    ),
                )
                try:
                    realtime_ctx = kiwoom_utils.build_realtime_analysis_context(
                        token=KIWOOM_TOKEN,
                        code=code,
                        ws_data=ws_data,
                        market_cap=_resolve_stock_marcap(stock, code),
                        strat_label=strategy,
                        position_status='NONE',
                        avg_price=0,
                        pnl_pct=0.0,
                        trailing_pct=0.0,
                        stop_pct=0.0,
                        target_price=curr_price,
                        target_reason='WATCHING 최종 진입 Gatekeeper 검증',
                        score=float(score),
                        conclusion=conclusion,
                        quant_metrics=metrics,
                    )
                    gatekeeper_started_at = time.perf_counter()
                    gatekeeper = ai_engine.evaluate_realtime_gatekeeper(
                        stock_name=stock['name'],
                        stock_code=code,
                        realtime_ctx=realtime_ctx,
                        analysis_mode='SWING',
                    )
                    gatekeeper_eval_ms = int((time.perf_counter() - gatekeeper_started_at) * 1000)
                    gatekeeper['eval_ms'] = gatekeeper_eval_ms
                    record_gatekeeper_snapshot(stock=stock, code=code, strategy=strategy, realtime_ctx=realtime_ctx, gatekeeper=gatekeeper)
                    is_new_evaluation = True
                    _mutate_stock_state(
                        stock,
                        set_fields={
                            'last_gatekeeper_action_at': now_ts,
                            'last_gatekeeper_allow_entry_at': now_ts,
                            'last_gatekeeper_fast_snapshot': gatekeeper_fast_snapshot,
                            'last_gatekeeper_fast_at': now_ts,
                        },
                    )
                    with ENTRY_LOCK:
                        LAST_AI_CALL_TIMES[code] = now_ts
                    action_label = gatekeeper.get('action_label', 'UNKNOWN')
                    gatekeeper_allow = bool(gatekeeper.get('allow_entry', False))
                    gatekeeper_cache_mode = str(gatekeeper.get('cache_mode', 'hit' if gatekeeper.get('cache_hit') else 'miss'))
                    _mutate_stock_state(
                        stock,
                        set_fields={
                            'last_gatekeeper_action': action_label,
                            'last_gatekeeper_report': gatekeeper.get('report', ''),
                            'last_gatekeeper_eval_ms': gatekeeper_eval_ms,
                            'last_gatekeeper_allow_entry': gatekeeper_allow,
                            'last_gatekeeper_cache_mode': gatekeeper_cache_mode,
                            'last_gatekeeper_lock_wait_ms': int(gatekeeper.get('lock_wait_ms', 0) or 0),
                            'last_gatekeeper_packet_build_ms': int(gatekeeper.get('packet_build_ms', 0) or 0),
                            'last_gatekeeper_model_call_ms': int(gatekeeper.get('model_call_ms', 0) or 0),
                            'last_gatekeeper_total_internal_ms': int(gatekeeper.get('total_internal_ms', 0) or 0),
                            'last_gatekeeper_fast_signature': gatekeeper_fast_sig,
                        },
                    )
                    if is_new_evaluation and realtime_ctx is not None:
                        _submit_gatekeeper_dual_persona_shadow(
                            stock_name=stock['name'],
                            code=code,
                            strategy=strategy,
                            realtime_ctx=realtime_ctx,
                            gatekeeper=gatekeeper,
                            record_id=stock.get('id'),
                        )
                except Exception as e:
                    log_error(f"🚨 [{strategy} Gatekeeper 오류] {stock['name']}({code}): {e}")
                    with ENTRY_LOCK:
                        cooldowns[code] = now_ts + gatekeeper_error_cd
                    _log_entry_pipeline(
                        stock, code, "blocked_gatekeeper_error", strategy=strategy, cooldown_sec=gatekeeper_error_cd,
                        gatekeeper_eval_ms=gatekeeper_eval_ms,
                        gatekeeper_lock_wait_ms=stock.get('last_gatekeeper_lock_wait_ms', 0),
                        gatekeeper_packet_build_ms=stock.get('last_gatekeeper_packet_build_ms', 0),
                        gatekeeper_model_call_ms=stock.get('last_gatekeeper_model_call_ms', 0),
                        gatekeeper_total_internal_ms=stock.get('last_gatekeeper_total_internal_ms', 0),
                    )
                    return False

            if not gatekeeper_allow:
                gatekeeper_reject_cd, gatekeeper_cd_policy = _resolve_gatekeeper_reject_cooldown(action_label)
                log_info(f"🚫 [{strategy} Gatekeeper 거부] {stock['name']} ({action_label})")
                with ENTRY_LOCK:
                    cooldowns[code] = now_ts + gatekeeper_reject_cd
                _log_entry_pipeline(
                    stock, code, "blocked_gatekeeper_reject", strategy=strategy, action=action_label,
                    cooldown_sec=gatekeeper_reject_cd, cooldown_policy=gatekeeper_cd_policy,
                    gatekeeper_eval_ms=gatekeeper_eval_ms, gatekeeper_cache=stock.get('last_gatekeeper_cache_mode', 'miss'),
                    gatekeeper_lock_wait_ms=stock.get('last_gatekeeper_lock_wait_ms', 0),
                    gatekeeper_packet_build_ms=stock.get('last_gatekeeper_packet_build_ms', 0),
                    gatekeeper_model_call_ms=stock.get('last_gatekeeper_model_call_ms', 0),
                    gatekeeper_total_internal_ms=stock.get('last_gatekeeper_total_internal_ms', 0),
                    **_build_observation_contract_fields("funnel_count"),
                )
                maybe_start_swing_intraday_probe(
                    stock=stock,
                    code=code,
                    ws_data=ws_data,
                    origin_stage="blocked_gatekeeper_reject",
                    runtime=runtime,
                    evidence_quality="blocked_stage_intraday_probe",
                    extra_fields={
                        "score": round(float(score), 2),
                        "runtime_score_proxy": round(float(score), 2),
                        "gatekeeper_action": action_label,
                        "gatekeeper_allow_entry": False,
                        "gatekeeper_eval_ms": gatekeeper_eval_ms,
                        "gatekeeper_cache": stock.get('last_gatekeeper_cache_mode', 'miss'),
                        "cooldown_sec": gatekeeper_reject_cd,
                        "cooldown_policy": gatekeeper_cd_policy,
                    },
                )
                return False

            blocked, block_reason = _should_block_swing_entry(stock.get('strategy', ''))
            swing_regime_micro_fields = {}
            if _is_swing_orderbook_micro_context_enabled(strategy):
                swing_regime_micro_fields = _build_swing_micro_log_fields(
                    _build_live_orderbook_micro_context(code, curr_price=curr_price),
                    phase="entry",
                )
            if blocked:
                log_info(f"⛔ [시장환경필터] {stock['name']}({code}) 스윙 진입 보류 - {block_reason}")
                _log_entry_pipeline(
                    stock,
                    code,
                    "market_regime_block",
                    strategy=strategy,
                    market_regime_block_reason=block_reason,
                    **swing_regime_micro_fields,
                )
                maybe_start_swing_intraday_probe(
                    stock=stock,
                    code=code,
                    ws_data=ws_data,
                    origin_stage="market_regime_block",
                    runtime=runtime,
                    evidence_quality="blocked_stage_intraday_probe",
                    extra_fields={
                        "score": round(float(score), 2),
                        "runtime_score_proxy": round(float(score), 2),
                        "gatekeeper_action": action_label,
                        "gatekeeper_allow_entry": True,
                        "gatekeeper_eval_ms": gatekeeper_eval_ms,
                        "market_regime_block_reason": block_reason,
                        **swing_regime_micro_fields,
                    },
                )
                return False

            _log_entry_pipeline(
                stock, code, "market_regime_pass", strategy=strategy, gatekeeper=action_label,
                score=round(float(score), 2), gatekeeper_eval_ms=gatekeeper_eval_ms,
                gatekeeper_cache=stock.get('last_gatekeeper_cache_mode', 'miss'),
                gatekeeper_lock_wait_ms=stock.get('last_gatekeeper_lock_wait_ms', 0),
                gatekeeper_packet_build_ms=stock.get('last_gatekeeper_packet_build_ms', 0),
                gatekeeper_model_call_ms=stock.get('last_gatekeeper_model_call_ms', 0),
                gatekeeper_total_internal_ms=stock.get('last_gatekeeper_total_internal_ms', 0),
                **swing_regime_micro_fields,
            )
            score_weight = max(0.0, min(1.0, (float(score) - buy_threshold) / max(1.0, (100 - buy_threshold))))
            ratio = ratio_min + (score_weight * (ratio_max - ratio_min))
            if is_shooting and ratio < ((ratio_min + ratio_max) / 2):
                ratio = (ratio_min + ratio_max) / 2

            is_trigger = True
            _mutate_stock_state(
                stock,
                set_fields={
                    'target_buy_price': curr_price,
                    'msg_audience': _resolve_telegram_audience_for_stock(stock, strategy),
                },
            )
            _publish_gatekeeper_report_proxy(stock, code, gatekeeper, allowed=True)
        else:
            _log_entry_pipeline(
                stock,
                code,
                "blocked_swing_score_vpw",
                **_build_observation_contract_fields("funnel_count"),
                strategy=strategy,
                score=round(float(score), 2),
                buy_threshold=buy_threshold,
                current_vpw=f"{current_vpw:.1f}",
                vpw_condition=bool(vpw_condition),
                v_pw_limit=v_pw_limit,
                is_shooting=bool(is_shooting),
                ai_prob=f"{float(ai_prob or 0.0):.4f}",
                conclusion=conclusion,
            )
            maybe_start_swing_intraday_probe(
                stock=stock,
                code=code,
                ws_data=ws_data,
                origin_stage="blocked_swing_score_vpw",
                runtime=runtime,
                evidence_quality="blocked_stage_intraday_probe",
                extra_fields={
                    "score": round(float(score), 2),
                    "runtime_score_proxy": round(float(score), 2),
                    "buy_threshold": buy_threshold,
                    "current_vpw": f"{current_vpw:.1f}",
                    "v_pw": f"{current_vpw:.1f}",
                    "vpw_condition": bool(vpw_condition),
                    "v_pw_limit": v_pw_limit,
                    "is_shooting": bool(is_shooting),
                },
            )

    runtime.update(
        {
            "is_trigger": is_trigger,
            "msg": msg,
            "ratio": ratio,
            "liquidity_value": liquidity_value,
            "current_ai_score": current_ai_score,
            "scalp_min_liquidity": min_liquidity if strategy == "SCALPING" else 0,
            "scalp_pre_ai_gate_context": stock.get("scalp_pre_ai_gate_context") or {},
        }
    )
    return True


def _submit_watching_triggered_entry(stock, code, ws_data, admin_id, runtime):
    strategy = runtime["strategy"]
    ratio = runtime["ratio"]
    curr_price = runtime["curr_price"]
    liquidity_value = runtime["liquidity_value"]
    msg = runtime["msg"]
    now_ts = runtime["now_ts"]
    cooldowns = runtime["cooldowns"]
    alerted_stocks = runtime["alerted_stocks"]
    ai_engine = runtime.get("ai_engine")

    if not admin_id:
        log_info(f"⚠️ [매수보류] {stock['name']}: 관리자 ID가 없습니다.")
        _log_entry_pipeline(stock, code, "blocked_no_admin")
        if _is_swing_strategy(strategy):
            maybe_start_swing_intraday_probe(
                stock=stock,
                code=code,
                ws_data=ws_data,
                origin_stage="blocked_no_admin",
                runtime=runtime,
                evidence_quality="blocked_stage_intraday_probe",
                extra_fields={"block_reason": "no_admin"},
            )
        return False

    deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
    uncapped_target_budget = int(max(float(deposit) * float(ratio), 0.0))
    budget_cap = 0
    if strategy == 'SCALPING':
        budget_cap = int(_rule('SCALPING_MAX_BUY_BUDGET_KRW', 0) or 0)
    target_budget, safe_budget, real_buy_qty, used_safety_ratio = kiwoom_orders.describe_buy_capacity(
        curr_price, deposit, ratio, max_budget=budget_cap
    )
    budget_cap_applied = budget_cap > 0 and target_budget < uncapped_target_budget
    budget_cap_msg = f", 절대한도 {budget_cap:,}원 적용" if budget_cap_applied else ""

    if real_buy_qty <= 0:
        zero_qty_cooldown_sec = _resolve_zero_qty_cooldown_sec(deposit)
        is_zero_deposit = _safe_int(deposit, 0) <= 0
        deposit_errors = kiwoom_orders.get_last_deposit_errors()
        auth_failure = next((err for err in deposit_errors if kiwoom_orders.is_auth_failure_error(err)), None)
        zero_qty_stage = "auth_zero_qty" if is_zero_deposit and auth_failure else "blocked_zero_qty"
        if is_zero_deposit:
            log_info(
                f"⚠️ [매수보류] {stock['name']}: 주문가능금액 조회가 0원으로 반환되어 재조회 대기합니다. "
                f"(주문가능금액 {deposit:,}원, 전략비중 {ratio:.1%}, 안전계수 {used_safety_ratio:.0%}, "
                f"실사용예산 {safe_budget:,}원, 현재가 {curr_price:,}원, 재조회대기 {zero_qty_cooldown_sec}초)"
            )
        else:
            log_info(
                f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다. "
                f"(주문가능금액 {deposit:,}원, 전략비중 {ratio:.1%}, 안전계수 {used_safety_ratio:.0%}, "
                f"실사용예산 {safe_budget:,}원, 현재가 {curr_price:,}원{budget_cap_msg})"
            )
        log_info(
            f"[DEBUG] {code} 매수 수량 0주 "
            f"(deposit={deposit}, ratio={ratio:.4f}, uncapped_target_budget={uncapped_target_budget}, "
            f"target_budget={target_budget}, safe_budget={safe_budget}, safety_ratio={used_safety_ratio:.4f}, "
            f"curr_price={curr_price}, retry_cooldown_sec={zero_qty_cooldown_sec})"
        )
        with ENTRY_LOCK:
            cooldowns[code] = now_ts + zero_qty_cooldown_sec
        _log_entry_pipeline(
            stock, code, zero_qty_stage, deposit=deposit, ratio=f"{ratio:.4f}", target_budget=target_budget,
            safe_budget=safe_budget, safety_ratio=f"{used_safety_ratio:.4f}", curr_price=curr_price,
            budget_cap=budget_cap if budget_cap_applied else "-", cooldown_sec=zero_qty_cooldown_sec,
            auth_return_code=(auth_failure or {}).get("return_code", "-"),
            auth_return_msg=(auth_failure or {}).get("return_msg", "-"),
        )
        if _is_swing_strategy(strategy):
            maybe_start_swing_intraday_probe(
                stock=stock,
                code=code,
                ws_data=ws_data,
                origin_stage=zero_qty_stage,
                runtime=runtime,
                evidence_quality="blocked_stage_intraday_probe",
                extra_fields={
                    "deposit": deposit,
                    "ratio": f"{ratio:.4f}",
                    "target_budget": target_budget,
                    "safe_budget": safe_budget,
                    "safety_ratio": f"{used_safety_ratio:.4f}",
                    "curr_price": curr_price,
                    "budget_cap": budget_cap if budget_cap_applied else "-",
                },
            )
        return False

    _log_entry_pipeline(
        stock, code, "budget_pass", deposit=deposit, ratio=f"{ratio:.4f}", target_budget=target_budget,
        safe_budget=safe_budget, safety_ratio=f"{used_safety_ratio:.4f}",
        budget_cap=budget_cap if budget_cap_applied else "-", qty=real_buy_qty,
        **_scalp_pre_ai_gate_context_log_fields(runtime.get("scalp_pre_ai_gate_context")),
        **_build_observation_contract_fields("funnel_count"),
    )

    if _is_swing_strategy(strategy):
        guard_decision = evaluate_swing_same_symbol_loss_reentry_guard(
            code,
            strategy,
            now_ts,
            source="pre_submit",
        )
        if not guard_decision.get("allowed", True):
            remaining = max(1, _safe_int(guard_decision.get("cooldown_remaining_sec"), 1))
            with ENTRY_LOCK:
                cooldowns[code] = now_ts + remaining
                alerted_stocks.discard(code)
            clear_signal_reference(stock)
            log_info(
                f"[SWING_REENTRY_GUARD_BLOCK] {stock.get('name')}({code}) "
                f"reason={guard_decision.get('reason')} remaining={remaining}s"
            )
            _log_entry_pipeline(
                stock,
                code,
                "swing_same_symbol_loss_reentry_blocked",
                strategy=strategy,
                deposit=deposit,
                ratio=f"{ratio:.4f}",
                target_budget=target_budget,
                safe_budget=safe_budget,
                safety_ratio=f"{used_safety_ratio:.4f}",
                qty=real_buy_qty,
                actual_order_submitted=False,
                broker_order_forbidden=True,
                runtime_effect="pre_submit_block",
                **_swing_loss_reentry_guard_log_fields(guard_decision),
            )
            _emit_swing_reentry_counterfactual_after_loss(
                stock,
                code,
                "pre_submit",
                guard_decision,
                runtime=runtime,
                ws_data=ws_data,
                extra_fields={
                    "deposit": deposit,
                    "ratio": f"{ratio:.4f}",
                    "target_budget": target_budget,
                    "safe_budget": safe_budget,
                    "safety_ratio": f"{used_safety_ratio:.4f}",
                    "would_qty": real_buy_qty,
                },
            )
            return False

    if strategy == 'SCALPING':
        order_type_code = "00"
        final_price = int(float(stock.get('target_buy_price', curr_price) or curr_price))
    else:
        order_type_code = "6"
        final_price = 0

    latency_signal_strength = float(stock.get('rt_ai_prob', stock.get('prob', 0.0)) or 0.0)
    latency_signal_score = latency_signal_strength * 100.0
    latency_gate = evaluate_live_buy_entry(
        stock=stock, code=code, ws_data=ws_data, strategy_id=strategy, planned_qty=real_buy_qty,
        signal_price=curr_price, signal_strength=latency_signal_strength,
        target_buy_price=final_price if strategy == 'SCALPING' else 0,
    )
    _mutate_stock_state(
        stock,
        set_fields={
            'latency_entry_state': latency_gate.get('latency_state'),
            'latency_entry_decision': latency_gate.get('decision'),
            'latency_entry_reason': latency_gate.get('reason'),
        },
    )
    _log_orderbook_stability_observation(stock, code, latency_gate.get('orderbook_stability'))
    best_ask_at_submit, best_bid_at_submit = _get_best_levels_from_ws(ws_data)
    latency_price_snapshot = _build_entry_price_snapshot_fields(
        latency_gate, request_price=latency_gate.get('order_price', 0), curr_price=curr_price,
        best_bid=best_bid_at_submit, best_ask=best_ask_at_submit,
    )
    swing_entry_micro_fields = {}
    if _is_swing_orderbook_micro_context_enabled(strategy):
        swing_entry_micro = _build_swing_orderbook_micro_context(
            code,
            curr_price=curr_price,
            latency_gate=latency_gate,
            best_bid=best_bid_at_submit,
            best_ask=best_ask_at_submit,
        )
        swing_entry_micro_fields = _build_swing_micro_log_fields(swing_entry_micro, phase="entry")
        _log_entry_pipeline(
            stock,
            code,
            "swing_entry_micro_context_observed",
            strategy=strategy,
            **swing_entry_micro_fields,
        )
    entry_orderbook_micro_fields = (
        {}
        if swing_entry_micro_fields
        else _build_orderbook_micro_log_fields(
            _build_orderbook_micro_context(
                latency_gate,
                curr_price=curr_price,
                best_bid=best_bid_at_submit,
                best_ask=best_ask_at_submit,
            )
        )
    )

    entry_mode = latency_gate.get('mode', 'reject')
    log_info(
        f"[LATENCY_ENTRY_DECISION] {stock.get('name')}({code}) "
        f"mode={entry_mode} decision={latency_gate.get('decision')} latency={latency_gate.get('latency_state')} "
        f"signal={latency_gate.get('signal_price')} latest={latency_gate.get('latest_price')} "
        f"allowed_slippage={latency_gate.get('computed_allowed_slippage')} orders={len(latency_gate.get('orders') or [])}"
    )
    if not latency_gate.get('allowed') or entry_mode == 'reject':
        log_info(
            f"[LATENCY_ENTRY_BLOCK] {stock.get('name')}({code}) decision={latency_gate.get('decision')} "
            f"latency={latency_gate.get('latency_state')} reason={latency_gate.get('reason')} "
            f"signal={latency_gate.get('signal_price')} latest={latency_gate.get('latest_price')} "
            f"ws_age_ms={latency_gate.get('ws_age_ms')} ws_jitter_ms={latency_gate.get('ws_jitter_ms')} "
            f"spread_ratio={latency_gate.get('spread_ratio')} quote_stale={latency_gate.get('quote_stale')}"
        )
        clear_signal_reference(stock)
        _log_entry_pipeline(
            stock, code, "latency_block", decision=latency_gate.get('decision'), latency=latency_gate.get('latency_state'),
            reason=latency_gate.get('reason'), ws_age_ms=latency_gate.get('ws_age_ms'),
            ws_jitter_ms=latency_gate.get('ws_jitter_ms'),
            spread_ratio=f"{float(latency_gate.get('spread_ratio', 0.0) or 0.0):.6f}",
            quote_stale=bool(latency_gate.get('quote_stale')),
            latency_danger_reasons=latency_gate.get('latency_danger_reasons'),
            signal_price=int(latency_gate.get('signal_price', 0) or 0),
            latest_price=int(latency_gate.get('latest_price', 0) or 0),
            computed_allowed_slippage=int(latency_gate.get('computed_allowed_slippage', 0) or 0),
            latency_canary_applied=bool(latency_gate.get('latency_canary_applied')),
            latency_canary_reason=latency_gate.get('latency_canary_reason'),
            **_build_ai_overlap_log_fields(
                stock=stock, ai_score=latency_signal_score, momentum_tag=stock.get("entry_momentum_tag"),
                threshold_profile=stock.get("entry_threshold_profile"), overbought_blocked=False,
                blocked_stage="latency_block",
            ),
            **swing_entry_micro_fields,
        )
        _emit_scalp_entry_adm_snapshot(
            stock,
            code,
            "latency_block",
            ai_score=latency_signal_score,
            chosen_action="WAIT_REQUOTE" if not bool(latency_gate.get("quote_stale")) else "SKIP_STALE",
            latency_gate=latency_gate,
            orderbook_fields=entry_orderbook_micro_fields,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        )
        if _is_swing_strategy(strategy):
            maybe_start_swing_intraday_probe(
                stock=stock,
                code=code,
                ws_data=ws_data,
                origin_stage="latency_block",
                runtime=runtime,
                evidence_quality="blocked_stage_intraday_probe",
                extra_fields={
                    "decision": latency_gate.get('decision'),
                    "latency_state": latency_gate.get('latency_state'),
                    "latency_reason": latency_gate.get('reason'),
                    "ws_age_ms": latency_gate.get('ws_age_ms'),
                    "ws_jitter_ms": latency_gate.get('ws_jitter_ms'),
                    "spread_ratio": f"{float(latency_gate.get('spread_ratio', 0.0) or 0.0):.6f}",
                    "quote_stale": bool(latency_gate.get('quote_stale')),
                    "signal_price": int(latency_gate.get('signal_price', 0) or 0),
                    "latest_price": int(latency_gate.get('latest_price', 0) or 0),
                    **swing_entry_micro_fields,
                },
            )
        return False

    requested_qty = int(real_buy_qty or 0)
    planned_orders = latency_gate.get('orders') or []
    wait6579_probe_applied = False
    wait6579_cap_enabled = (
        bool(_rule("AI_WAIT6579_PROBE_CANARY_ENABLED", False))
        or bool(_rule("AI_SCORE65_74_RECOVERY_PROBE_ENABLED", False))
        or bool(_rule("AI_MAIN_BUY_RECOVERY_CANARY_ENABLED", False))
    )
    if strategy == 'SCALPING' and wait6579_cap_enabled and bool(stock.get('wait6579_probe_canary_armed')):
        probe_max_budget = int(_rule("AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW", 50_000) or 50_000)
        probe_min_qty = int(_rule("AI_WAIT6579_PROBE_CANARY_MIN_QTY", 1) or 1)
        probe_max_qty = int(_rule("AI_WAIT6579_PROBE_CANARY_MAX_QTY", 0) or 0)
        adjusted_orders, original_qty, scaled_qty, applied = _apply_wait6579_probe_canary(
            planned_orders, curr_price=curr_price, max_budget_krw=probe_max_budget,
            min_qty=probe_min_qty, max_qty=probe_max_qty,
        )
        if adjusted_orders:
            planned_orders = adjusted_orders
            latency_gate["orders"] = planned_orders
        if scaled_qty > 0:
            requested_qty = scaled_qty
        wait6579_probe_applied = bool(applied)
        _log_entry_pipeline(
            stock, code, "wait6579_probe_canary_applied", source=stock.get('wait6579_probe_canary_source', '-'),
            ai_score=stock.get('wait6579_probe_canary_score', '-'), max_budget_krw=probe_max_budget,
            min_qty=probe_min_qty, max_qty=probe_max_qty, original_qty=original_qty, scaled_qty=scaled_qty,
            legs=len(planned_orders), applied=wait6579_probe_applied,
        )
        log_info(
            f"[WAIT6579_PROBE_CANARY] {stock.get('name')}({code}) "
            f"qty={original_qty}->{scaled_qty} max_budget={probe_max_budget} applied={wait6579_probe_applied}"
        )
        _mutate_stock_state(
            stock,
            pop_fields=['wait6579_probe_canary_armed', 'wait6579_probe_canary_source', 'wait6579_probe_canary_score'],
        )

    if strategy == "SCALPING" and bool(_rule("SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED", False)):
        initial_entry_qty_cap = int(_rule("SCALPING_INITIAL_ENTRY_MAX_QTY", 1) or 1)
        adjusted_orders, original_qty, scaled_qty, applied = _apply_initial_entry_qty_cap(planned_orders, max_total_qty=initial_entry_qty_cap)
        if adjusted_orders:
            planned_orders = adjusted_orders
            latency_gate["orders"] = planned_orders
        if scaled_qty > 0:
            requested_qty = scaled_qty
        _log_entry_pipeline(
            stock, code, "initial_entry_qty_cap_applied", enabled=True, cap_qty=initial_entry_qty_cap,
            original_qty=original_qty, scaled_qty=scaled_qty, applied=bool(applied),
            entry_mode=entry_mode, legs=len(planned_orders),
        )
        if applied:
            log_info(
                f"[INITIAL_ENTRY_QTY_CAP] {stock.get('name')}({code}) "
                f"qty={original_qty}->{scaled_qty} cap={initial_entry_qty_cap} entry_mode={entry_mode}"
            )

    planned_orders, ai_price_canary_touched = _apply_entry_ai_price_canary(
        stock=stock,
        code=code,
        strategy=strategy,
        ws_data=ws_data,
        ai_engine=ai_engine,
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        curr_price=curr_price,
        best_bid=best_bid_at_submit,
        best_ask=best_ask_at_submit,
    )
    if ai_price_canary_touched:
        latency_gate["orders"] = planned_orders
        latency_price_snapshot = _build_entry_price_snapshot_fields(
            latency_gate, request_price=latency_gate.get('order_price', 0), curr_price=curr_price,
            best_bid=best_bid_at_submit, best_ask=best_ask_at_submit,
        )
    submit_revalidation_fields = _build_entry_submit_revalidation_fields(ws_data, latency_gate, now_ts=time.time())
    if submit_revalidation_fields.get("entry_submit_revalidation_warning"):
        _log_entry_pipeline(
            stock,
            code,
            "entry_submit_revalidation_warning",
            **submit_revalidation_fields,
        )
        _emit_scalp_entry_adm_snapshot(
            stock,
            code,
            "entry_submit_revalidation_warning",
            ai_score=latency_signal_score,
            chosen_action="WAIT_REQUOTE",
            latency_gate=latency_gate,
            submit_fields=submit_revalidation_fields,
            price_snapshot=latency_price_snapshot,
            orderbook_fields=entry_orderbook_micro_fields,
            actual_order_submitted=False,
            broker_order_forbidden=False,
        )

    _log_entry_pipeline(
        stock, code, "latency_pass", mode=entry_mode, decision=latency_gate.get('decision'),
        latency=latency_gate.get('latency_state'), orders=len(planned_orders), reason=latency_gate.get('reason'),
        ws_age_ms=latency_gate.get('ws_age_ms'), ws_jitter_ms=latency_gate.get('ws_jitter_ms'),
        spread_ratio=f"{float(latency_gate.get('spread_ratio', 0.0) or 0.0):.6f}",
        quote_stale=bool(latency_gate.get('quote_stale')), latency_danger_reasons=latency_gate.get('latency_danger_reasons'),
        signal_price=int(latency_gate.get('signal_price', 0) or 0), latest_price=int(latency_gate.get('latest_price', 0) or 0),
        computed_allowed_slippage=int(latency_gate.get('computed_allowed_slippage', 0) or 0),
        latency_canary_applied=bool(latency_gate.get('latency_canary_applied')),
        latency_canary_reason=latency_gate.get('latency_canary_reason'), entry_price_guard=latency_gate.get('entry_price_guard'),
        entry_price_defensive_ticks=int(latency_gate.get('entry_price_defensive_ticks', 0) or 0),
        normal_defensive_order_price=int(latency_gate.get('normal_defensive_order_price', 0) or 0),
        latency_guarded_order_price=int(latency_gate.get('latency_guarded_order_price', 0) or 0),
        counterfactual_order_price_1tick=int(latency_gate.get('counterfactual_order_price_1tick', 0) or 0),
        order_price=int(latency_gate.get('order_price', 0) or 0),
        ai_entry_price_canary_eval_ms=int(latency_gate.get('ai_entry_price_canary_eval_ms', 0) or 0),
        **_scalp_pre_ai_gate_context_log_fields(runtime.get("scalp_pre_ai_gate_context")),
        **submit_revalidation_fields,
        **latency_price_snapshot,
        **entry_orderbook_micro_fields,
        **_build_ai_overlap_log_fields(
            stock=stock, ai_score=latency_signal_score, momentum_tag=stock.get("entry_momentum_tag"),
            threshold_profile=stock.get("entry_threshold_profile"), overbought_blocked=False, blocked_stage="-",
        ),
        **swing_entry_micro_fields,
    )
    _emit_scalp_entry_adm_snapshot(
        stock,
        code,
        "latency_pass",
        ai_score=latency_signal_score,
        latency_gate=latency_gate,
        submit_fields=submit_revalidation_fields,
        price_snapshot=latency_price_snapshot,
        orderbook_fields=entry_orderbook_micro_fields,
        actual_order_submitted=False,
        broker_order_forbidden=False,
    )

    if _is_passive_probe_stale_submit_block(submit_revalidation_fields):
        log_info(
            f"[ENTRY_SUBMIT_REVALIDATION_BLOCK] {stock.get('name')}({code}) "
            f"lifecycle=passive_probe warning={submit_revalidation_fields.get('entry_submit_revalidation_warning')}"
        )
        clear_signal_reference(stock)
        _log_entry_pipeline(
            stock,
            code,
            "entry_submit_revalidation_block",
            block_reason="stale_context_or_quote",
            actual_order_submitted=False,
            threshold_family="pre_submit_price_guard",
            **submit_revalidation_fields,
            **latency_price_snapshot,
            **entry_orderbook_micro_fields,
            **swing_entry_micro_fields,
        )
        _emit_scalp_entry_adm_snapshot(
            stock,
            code,
            "entry_submit_revalidation_block",
            ai_score=latency_signal_score,
            chosen_action="SKIP_STALE",
            latency_gate=latency_gate,
            submit_fields=submit_revalidation_fields,
            price_snapshot=latency_price_snapshot,
            orderbook_fields=entry_orderbook_micro_fields,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        )
        return False

    if is_buy_side_paused():
        log_info(
            f"[TRADING_PAUSED_BLOCK] buy order blocked "
            f"{stock.get('name')}({code}) strategy={strategy} state={get_pause_state_label()}"
        )
        clear_signal_reference(stock)
        _log_entry_pipeline(stock, code, "blocked_pause", strategy=strategy)
        if _is_swing_strategy(strategy):
            maybe_start_swing_intraday_probe(
                stock=stock,
                code=code,
                ws_data=ws_data,
                origin_stage="blocked_pause",
                runtime=runtime,
                evidence_quality="blocked_stage_intraday_probe",
                extra_fields={"pause_state": get_pause_state_label()},
            )
        return False

    scalp_pre_ai_gate_context = runtime.get("scalp_pre_ai_gate_context") if isinstance(runtime.get("scalp_pre_ai_gate_context"), dict) else {}
    if strategy == "SCALPING" and _rule_bool("SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED", True):
        min_liquidity = _safe_int(runtime.get("scalp_min_liquidity"), _rule_int("MIN_SCALP_LIQUIDITY", 500_000_000))
        if liquidity_value < min_liquidity:
            log_info(
                f"[PRE_SUBMIT_LIQUIDITY_GUARD_BLOCK] {stock.get('name')}({code}) "
                f"liquidity={int(liquidity_value)} min={min_liquidity}"
            )
            clear_signal_reference(stock)
            _log_entry_pipeline(
                stock,
                code,
                "pre_submit_liquidity_guard_block",
                **_build_pre_submit_gate_contract_fields("liquidity_pre_submit_guard_p1"),
                liquidity_value=int(liquidity_value),
                min_liquidity=min_liquidity,
                block_reason="below_min_liquidity",
                **submit_revalidation_fields,
                **latency_price_snapshot,
                **entry_orderbook_micro_fields,
                **_scalp_pre_ai_gate_context_log_fields(scalp_pre_ai_gate_context),
            )
            _emit_scalp_entry_adm_snapshot(
                stock,
                code,
                "pre_submit_liquidity_guard_block",
                ai_score=latency_signal_score,
                chosen_action="SKIP_PRE_SUBMIT_SAFETY",
                latency_gate=latency_gate,
                submit_fields=submit_revalidation_fields,
                price_snapshot=latency_price_snapshot,
                orderbook_fields=entry_orderbook_micro_fields,
                actual_order_submitted=False,
                broker_order_forbidden=True,
                extra_fields={"liquidity_value": int(liquidity_value), "min_liquidity": min_liquidity},
            )
            return False

    if strategy == "SCALPING" and not _overbought_pre_submit_allowed(scalp_pre_ai_gate_context):
        overbought_context = scalp_pre_ai_gate_context.get("overbought") if isinstance(scalp_pre_ai_gate_context.get("overbought"), dict) else {}
        log_info(
            f"[PRE_SUBMIT_OVERBOUGHT_PULLBACK_GUARD_BLOCK] {stock.get('name')}({code}) "
            f"state={overbought_context.get('risk_state')} bucket={overbought_context.get('risk_bucket')}"
        )
        clear_signal_reference(stock)
        _log_entry_pipeline(
            stock,
            code,
            "pre_submit_overbought_pullback_guard_block",
            **_build_pre_submit_gate_contract_fields("overbought_pullback_guard_p1"),
            block_reason="pullback_or_rebreak_not_confirmed",
            risk_state=overbought_context.get("risk_state") or "-",
            risk_bucket=overbought_context.get("risk_bucket") or "-",
            **submit_revalidation_fields,
            **latency_price_snapshot,
            **entry_orderbook_micro_fields,
            **_scalp_pre_ai_gate_context_log_fields(scalp_pre_ai_gate_context),
        )
        _emit_scalp_entry_adm_snapshot(
            stock,
            code,
            "pre_submit_overbought_pullback_guard_block",
            ai_score=latency_signal_score,
            chosen_action="SKIP_PRE_SUBMIT_SAFETY",
            latency_gate=latency_gate,
            submit_fields=submit_revalidation_fields,
            price_snapshot=latency_price_snapshot,
            orderbook_fields=entry_orderbook_micro_fields,
            actual_order_submitted=False,
            broker_order_forbidden=True,
            extra_fields={
                "block_reason": "pullback_or_rebreak_not_confirmed",
                "risk_state": overbought_context.get("risk_state") or "-",
                "risk_bucket": overbought_context.get("risk_bucket") or "-",
            },
        )
        return False

    lifecycle_submit_decision = resolve_lifecycle_decision(
        stage="submit",
        original_action="ALLOW_SUBMIT",
        context={
            **submit_revalidation_fields,
            **latency_price_snapshot,
            **entry_orderbook_micro_fields,
            "ai_score": latency_signal_score,
            "liquidity_value": int(liquidity_value),
            "stale_quote_submit_block": False,
            "broker_submit_blocked": False,
        },
    )
    submit_revalidation_fields.update(lifecycle_submit_decision)
    if lifecycle_submit_decision.get("lifecycle_matrix_enabled"):
        lifecycle_submit_log_fields = {
            **submit_revalidation_fields,
            **latency_price_snapshot,
            **entry_orderbook_micro_fields,
        }
        _log_entry_pipeline(
            stock,
            code,
            "lifecycle_decision_matrix_runtime_policy",
            **lifecycle_submit_log_fields,
        )

    big_bite_summary = ""
    if stock.get('big_bite_triggered') or stock.get('big_bite_confirmed'):
        info = stock.get('big_bite_info') or {}
        big_bite_summary = (
            f"\n🧪 Big-Bite: T={stock.get('big_bite_triggered')} / C={stock.get('big_bite_confirmed')} / "
            f"Boost=+{stock.get('big_bite_boost_value', 0)}"
            f"\n└ agg={info.get('agg_value')} impact={info.get('impact_ratio')} chase={info.get('chase_pct')}"
        )
        _mutate_stock_state(stock, set_fields={'msg_audience': 'ADMIN_ONLY'})

    swing_one_share_real_canary_fields = None
    if _is_swing_strategy(strategy) and _is_swing_live_order_dry_run(strategy):
        one_share_eval = _evaluate_swing_one_share_real_canary(
            stock,
            code,
            request_qty=requested_qty,
            request_price=int(final_price or latency_gate.get('order_price', 0) or 0),
            ws_data=ws_data,
            submit_revalidation_fields=submit_revalidation_fields,
            swing_entry_micro_fields=swing_entry_micro_fields,
        )
        if one_share_eval.get("allowed"):
            swing_one_share_real_canary_fields = one_share_eval.get("fields") or {}
            requested_qty = int(one_share_eval.get("qty") or 1)
            log_info(
                f"[SWING_ONE_SHARE_REAL_CANARY] {stock.get('name')}({code}) "
                f"approved qty={requested_qty} price={final_price} global_dry_run_kept=true"
            )
        elif _rule_bool("SWING_ONE_SHARE_REAL_CANARY_ENABLED", False):
            _log_entry_pipeline(
                stock,
                code,
                "swing_one_share_real_canary_blocked",
                block_reason=one_share_eval.get("reason"),
                actual_order_submitted=False,
                broker_order_forbidden=True,
                **(one_share_eval.get("fields") or {}),
            )

    msg = msg or (
        f"✅ **{stock['name']} ({code}) 진입 주문 전송!**\n전략: `{strategy}`\n현재가: `{curr_price:,}원`\n주문 수량: `{requested_qty}주`"
        f"{big_bite_summary}"
    )

    successful_orders = []
    swing_order_dry_run = _is_swing_live_order_dry_run(strategy) and swing_one_share_real_canary_fields is None
    for planned_order in planned_orders:
        request = _resolve_live_entry_order_request(
            strategy=strategy, entry_mode=entry_mode, planned_order=planned_order,
            default_order_type_code=order_type_code, default_price=final_price,
        )
        qty = request['qty']
        price = request['price']
        if swing_one_share_real_canary_fields is not None:
            if successful_orders:
                _log_entry_pipeline(
                    stock,
                    code,
                    "swing_one_share_real_canary_extra_leg_skipped",
                    tag=request['tag'],
                    actual_order_submitted=False,
                    broker_order_forbidden=True,
                    **swing_one_share_real_canary_fields,
                )
                continue
            qty = min(qty, int(swing_one_share_real_canary_fields.get("real_canary_actual_qty") or 1))
            request = {**request, "qty": qty}
        if qty <= 0:
            _log_entry_pipeline(stock, code, "skip_order_leg_zero_qty", tag=request['tag'])
            continue
        price_snapshot = _build_entry_price_snapshot_fields(
            latency_gate, request_price=price, curr_price=curr_price,
            best_bid=best_bid_at_submit, best_ask=best_ask_at_submit,
        )
        if _is_pre_submit_price_guard_block(strategy, price, best_bid_at_submit):
            max_below_bid_bps = int(_rule('SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS', 80) or 80)
            _log_entry_pipeline(
                stock, code, "pre_submit_price_guard_block", tag=request['tag'], qty=qty, price=price,
                order_type=request['order_type_code'], tif=request['tif'],
                max_below_bid_bps=max_below_bid_bps, **price_snapshot,
            )
            log_info(
                f"[PRE_SUBMIT_PRICE_GUARD_BLOCK] {stock.get('name')}({code}) "
                f"price={price} best_bid={best_bid_at_submit} "
                f"below_bid_bps={price_snapshot['price_below_bid_bps']} threshold_bps={max_below_bid_bps}"
            )
            continue
        _log_entry_pipeline(
            stock, code, "order_leg_request", tag=request['tag'], qty=qty, price=price,
            order_type=request['order_type_code'], tif=request['tif'],
            entry_price_guard=latency_gate.get('entry_price_guard'),
            entry_price_defensive_ticks=int(latency_gate.get('entry_price_defensive_ticks', 0) or 0),
            normal_defensive_order_price=int(latency_gate.get('normal_defensive_order_price', 0) or 0),
            latency_guarded_order_price=int(latency_gate.get('latency_guarded_order_price', 0) or 0),
            counterfactual_order_price_1tick=int(latency_gate.get('counterfactual_order_price_1tick', 0) or 0),
            **submit_revalidation_fields,
            **price_snapshot,
            **swing_entry_micro_fields,
            **(swing_one_share_real_canary_fields or {}),
        )
        if swing_order_dry_run:
            ord_no = _simulated_order_no("SIMBUY", code)
            successful_orders.append({
                'tag': request['tag'], 'qty': qty, 'price': price, 'ord_no': ord_no, 'tif': request['tif'],
                'order_type': request['order_type_code'], 'status': 'FILLED_SIM', 'filled_qty': qty,
                'sent_at': now_ts, 'filled_at': now_ts, 'simulated_order': True,
                'entry_order_lifecycle': submit_revalidation_fields.get('entry_order_lifecycle', 'standard'),
                'entry_passive_probe_applied': bool(submit_revalidation_fields.get('entry_passive_probe_applied')),
                'best_bid_at_submit': price_snapshot.get('best_bid_at_submit'),
                'best_ask_at_submit': price_snapshot.get('best_ask_at_submit'),
                'price_below_bid_bps': price_snapshot.get('price_below_bid_bps'),
                'price_decision_context_age_ms': submit_revalidation_fields.get('price_decision_context_age_ms'),
                'quote_age_at_submit_ms': submit_revalidation_fields.get('quote_age_at_submit_ms'),
            })
            log_info(
                f"[SWING_LIVE_ORDER_DRY_RUN] {stock.get('name')}({code}) "
                f"buy skipped tag={request['tag']} qty={qty} price={price} type={request['order_type_code']} "
                f"sim_ord_no={ord_no}"
            )
            _log_entry_pipeline(
                stock, code, "swing_sim_buy_order_assumed_filled",
                tag=request['tag'], ord_no=ord_no, qty=qty, price=price,
                order_type=request['order_type_code'], tif=request['tif'],
                simulation_owner=_swing_live_order_dry_run_owner(),
                actual_order_submitted=False,
                would_submit_stage="order_leg_sent",
                **submit_revalidation_fields,
                **price_snapshot,
                **swing_entry_micro_fields,
            )
            continue
        res = kiwoom_orders.send_buy_order(
            code, qty, price, request['order_type_code'], token=KIWOOM_TOKEN,
            order_type_desc="매수" if strategy == 'SCALPING' else "최유리지정가", tif=request['tif'],
        )
        if not isinstance(res, dict):
            _log_entry_pipeline(stock, code, "order_leg_no_response", tag=request['tag'])
            continue
        rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
        if rt_cd != '0':
            log_info(f"[LATENCY_ENTRY_ORDER_FAIL] {stock.get('name')}({code}) tag={planned_order.get('tag')} msg={res.get('return_msg')}")
            _log_entry_pipeline(
                stock, code, "order_leg_fail", tag=request['tag'], return_code=rt_cd,
                message=res.get('return_msg') or res.get('err_msg'),
            )
            continue
        ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
        successful_orders.append({
            'tag': request['tag'], 'qty': qty, 'price': price, 'ord_no': ord_no, 'tif': request['tif'],
            'order_type': request['order_type_code'], 'status': 'OPEN', 'filled_qty': 0, 'sent_at': now_ts,
            'entry_order_lifecycle': submit_revalidation_fields.get('entry_order_lifecycle', 'standard'),
            'entry_passive_probe_applied': bool(submit_revalidation_fields.get('entry_passive_probe_applied')),
            'best_bid_at_submit': price_snapshot.get('best_bid_at_submit'),
            'best_ask_at_submit': price_snapshot.get('best_ask_at_submit'),
            'price_below_bid_bps': price_snapshot.get('price_below_bid_bps'),
            'price_decision_context_age_ms': submit_revalidation_fields.get('price_decision_context_age_ms'),
            'quote_age_at_submit_ms': submit_revalidation_fields.get('quote_age_at_submit_ms'),
            'swing_one_share_real_canary': bool(swing_one_share_real_canary_fields),
        })
        _stage_buy_order_submission(
            stock=stock, code=code, curr_price=curr_price, requested_qty=requested_qty, msg=msg, entry_orders=successful_orders,
        )
        if swing_one_share_real_canary_fields is not None:
            previous_count = int(stock.get("swing_one_share_real_canary_order_count", 0) or 0)
            previous_notional = int(stock.get("swing_one_share_real_canary_notional_krw", 0) or 0)
            order_notional = int(swing_one_share_real_canary_fields.get("order_notional_krw", 0) or 0)
            _mutate_stock_state(
                stock,
                set_fields={
                    "cohort": "swing_one_share_real_canary",
                    "swing_one_share_real_canary": True,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                    "canary_qty_cap": int(swing_one_share_real_canary_fields.get("real_canary_qty_cap") or 1),
                    "real_canary_actual_qty": qty,
                    "swing_one_share_real_canary_order_date": str(
                        swing_one_share_real_canary_fields.get("day_key") or _swing_one_share_real_canary_daily_key(now_ts)
                    ),
                    "swing_one_share_real_canary_order_count": previous_count + 1,
                    "swing_one_share_real_canary_notional_krw": previous_notional + order_notional,
                },
            )
        log_info(
            f"[LATENCY_ENTRY_ORDER_SENT] {stock.get('name')}({code}) "
            f"tag={request['tag']} qty={qty} price={price} type={request['order_type_code']} tif={request['tif']} ord_no={ord_no}"
        )
        _log_entry_pipeline(
            stock,
            code,
            "order_leg_sent",
            tag=request['tag'],
            ord_no=ord_no,
            **(swing_one_share_real_canary_fields or {}),
        )
        if swing_one_share_real_canary_fields is not None:
            _log_entry_pipeline(
                stock,
                code,
                "swing_one_share_real_canary_order_submitted",
                tag=request['tag'],
                ord_no=ord_no,
                request_qty=qty,
                request_price=price,
                **swing_one_share_real_canary_fields,
            )

    if not successful_orders:
        log_info(f"❌ [{stock['name']}] 매수 주문 전송 실패 (성공 주문 없음)")
        clear_signal_reference(stock)
        _log_entry_pipeline(stock, code, "order_bundle_failed")
        if _is_swing_strategy(strategy):
            maybe_start_swing_intraday_probe(
                stock=stock,
                code=code,
                ws_data=ws_data,
                origin_stage="order_bundle_failed",
                runtime=runtime,
                evidence_quality="blocked_stage_intraday_probe",
                extra_fields={
                    "entry_mode": entry_mode,
                    "planned_order_count": len(planned_orders or []),
                    "latency_state": latency_gate.get('latency_state'),
                    "entry_price_guard": latency_gate.get('entry_price_guard'),
                    "order_price": int(latency_gate.get('order_price', 0) or 0),
                    **swing_entry_micro_fields,
                },
            )
        return False

    if swing_order_dry_run:
        _mark_swing_simulated_holding(
            stock=stock,
            code=code,
            curr_price=curr_price,
            requested_qty=requested_qty,
            entry_mode=entry_mode,
            entry_orders=successful_orders,
        )
        bundle_primary_price = successful_orders[0].get('price', latency_gate.get('order_price', 0))
        bundle_price_snapshot = _build_entry_price_snapshot_fields(
            latency_gate, request_price=bundle_primary_price, curr_price=curr_price,
            best_bid=best_bid_at_submit, best_ask=best_ask_at_submit,
        )
        _log_entry_pipeline(
            stock, code, "swing_sim_order_bundle_assumed_filled", entry_mode=entry_mode,
            requested_qty=requested_qty, legs=len(successful_orders),
            wait6579_probe_canary_applied=wait6579_probe_applied,
            entry_price_guard=latency_gate.get('entry_price_guard'),
            entry_price_defensive_ticks=int(latency_gate.get('entry_price_defensive_ticks', 0) or 0),
            normal_defensive_order_price=int(latency_gate.get('normal_defensive_order_price', 0) or 0),
            latency_guarded_order_price=int(latency_gate.get('latency_guarded_order_price', 0) or 0),
            counterfactual_order_price_1tick=int(latency_gate.get('counterfactual_order_price_1tick', 0) or 0),
            order_price=int(latency_gate.get('order_price', 0) or 0),
            simulation_owner=_swing_live_order_dry_run_owner(),
            actual_order_submitted=False,
            would_submit_stage="order_bundle_submitted",
            runtime_effect="in_memory_holding_only",
            **submit_revalidation_fields,
            **bundle_price_snapshot,
            **swing_entry_micro_fields,
        )
        clear_signal_reference(stock)
        return False

    _mutate_stock_state(stock, set_fields={'entry_mode': entry_mode})
    _finalize_buy_order_submission(
        stock=stock, code=code, curr_price=curr_price, requested_qty=requested_qty, msg=msg, entry_orders=successful_orders,
    )
    _publish_buy_signal_submission_notice(
        stock, code, strategy=strategy, curr_price=curr_price, requested_qty=requested_qty, entry_mode=entry_mode,
        latency_gate=latency_gate, liquidity_value=liquidity_value, ai_score=latency_signal_score,
    )
    bundle_primary_price = successful_orders[0].get('price', latency_gate.get('order_price', 0))
    bundle_price_snapshot = _build_entry_price_snapshot_fields(
        latency_gate, request_price=bundle_primary_price, curr_price=curr_price,
        best_bid=best_bid_at_submit, best_ask=best_ask_at_submit,
    )
    _log_entry_pipeline(
        stock, code, "order_bundle_submitted", entry_mode=entry_mode, requested_qty=requested_qty,
        legs=len(successful_orders), wait6579_probe_canary_applied=wait6579_probe_applied,
        entry_price_guard=latency_gate.get('entry_price_guard'),
        entry_price_defensive_ticks=int(latency_gate.get('entry_price_defensive_ticks', 0) or 0),
        normal_defensive_order_price=int(latency_gate.get('normal_defensive_order_price', 0) or 0),
        latency_guarded_order_price=int(latency_gate.get('latency_guarded_order_price', 0) or 0),
        counterfactual_order_price_1tick=int(latency_gate.get('counterfactual_order_price_1tick', 0) or 0),
        order_price=int(latency_gate.get('order_price', 0) or 0),
        **_scalp_pre_ai_gate_context_log_fields(runtime.get("scalp_pre_ai_gate_context")),
        **submit_revalidation_fields,
        **bundle_price_snapshot,
        **swing_entry_micro_fields,
        **(swing_one_share_real_canary_fields or {}),
    )
    _emit_scalp_entry_adm_snapshot(
        stock,
        code,
        "order_bundle_submitted",
        ai_score=latency_signal_score,
        latency_gate=latency_gate,
        submit_fields=submit_revalidation_fields,
        price_snapshot=bundle_price_snapshot,
        orderbook_fields=entry_orderbook_micro_fields,
        actual_order_submitted=True,
        broker_order_forbidden=False,
        extra_fields={
            "entry_mode": entry_mode,
            "requested_qty": requested_qty,
            "legs": len(successful_orders),
            "order_price": int(latency_gate.get('order_price', 0) or 0),
        },
    )

    if strategy in ['SCALPING', 'SCALP']:
        with ENTRY_LOCK:
            alerted_stocks.add(code)
    else:
        _mutate_stock_state(stock, set_fields={'msg_audience': _resolve_telegram_audience_for_stock(stock, strategy)})

    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=stock.get('id')).update({
                "status": "BUY_ORDERED",
                "buy_price": curr_price,
                "buy_qty": requested_qty,
            })
    except Exception as e:
        log_error(f"🚨 [DB 에러] {stock['name']} BUY_ORDERED 장부 업데이트 실패: {e}")

    clear_signal_reference(stock)
    return False


def _coerce_int_value(value, default=0):
    return _safe_int(value, default)


def _price_bucket_step(price):
    try:
        price = abs(_safe_int(price, 0))
    except Exception:
        price = 0
    if price >= 200_000:
        return 500
    if price >= 50_000:
        return 100
    if price >= 10_000:
        return 50
    if price >= 5_000:
        return 10
    return 5


def _bucket_float(value, step):
    try:
        step = float(step)
        if step <= 0:
            return 0
        return round(float(value or 0.0) / step) * step
    except Exception:
        return 0.0


def _floor_bucket_float(value, step):
    try:
        step = float(step)
        if step <= 0:
            return 0.0
        return float(int(float(value or 0.0) // step) * step)
    except Exception:
        return 0.0


def _resolve_holding_ai_fast_reuse_sec(is_critical_zone, dynamic_max_cd):
    configured_sec = (
        float(_rule('AI_HOLDING_FAST_REUSE_CRITICAL_SEC', 8.0) or 8.0)
        if is_critical_zone
        else float(_rule('AI_HOLDING_FAST_REUSE_NORMAL_SEC', 20.0) or 20.0)
    )
    review_window_floor = max(0.0, float(dynamic_max_cd or 0.0)) + 2.0
    return max(configured_sec, review_window_floor)


def _resolve_gatekeeper_fast_reuse_sec():
    configured_sec = float(_rule('AI_GATEKEEPER_FAST_REUSE_SEC', 12.0) or 12.0)
    return max(configured_sec, 20.0)


def _build_gatekeeper_fast_signature(stock, ws_data, strategy, score):
    curr_price = ws_data.get('curr', 0)
    price_bucket = max(_price_bucket_step(curr_price), 50)
    return (
        str(strategy or ''),
        str(stock.get('position_tag', '') or ''),
        _floor_bucket_float(score, 5.0),
        _bucket_int(curr_price, price_bucket * 8),
        _floor_bucket_float(ws_data.get('fluctuation', 0.0), 0.5),
        _bucket_int(ws_data.get('volume', 0), 200_000),
        _floor_bucket_float(ws_data.get('v_pw', 0.0), 10.0),
        _floor_bucket_float(ws_data.get('buy_ratio', 0.0), 20.0),
        _bucket_int_with_deadband(ws_data.get('prog_net_qty', 0), 25_000),
        _bucket_int_with_deadband(ws_data.get('prog_delta_qty', 0), 5_000),
    )


def _build_gatekeeper_fast_snapshot(stock, ws_data, strategy, score):
    """Gatekeeper fast signature 변경 추적용 dict 스냅샷 (sig_delta 비교용)"""
    best_ask, best_bid = _get_best_levels_from_ws(ws_data)
    curr_price = ws_data.get('curr', 0)
    price_bucket = _price_bucket_step(curr_price)
    buy_exec = _coerce_int_value(ws_data.get('buy_exec_volume', 0))
    sell_exec = _coerce_int_value(ws_data.get('sell_exec_volume', 0))
    
    return {
        "curr_price": _bucket_int(curr_price, price_bucket),
        "score": _floor_bucket_float(score, 5.0),
        "v_pw_now": _floor_bucket_float(ws_data.get('v_pw', 0.0), 5.0),
        "buy_ratio_ws": _floor_bucket_float(ws_data.get('buy_ratio', 0.0), 8.0),
        "spread_tick": max(0, _bucket_int(best_ask, price_bucket) - _bucket_int(best_bid, price_bucket)),
        "prog_delta_qty": _bucket_int(ws_data.get('prog_delta_qty', 0), 2_000),
        "net_buy_exec_volume": _bucket_int(buy_exec - sell_exec, 5_000),
    }


def _build_holding_ai_fast_snapshot(ws_data):
    best_ask, best_bid = _get_best_levels_from_ws(ws_data)
    curr_price = ws_data.get('curr', 0)
    price_bucket = _price_bucket_step(curr_price)
    ask_tot = _coerce_int_value(ws_data.get('ask_tot'))
    bid_tot = _coerce_int_value(ws_data.get('bid_tot'))
    buy_exec = _coerce_int_value(ws_data.get('buy_exec_volume'))
    sell_exec = _coerce_int_value(ws_data.get('sell_exec_volume'))
    spread_amount = max(0, _coerce_int_value(best_ask) - _coerce_int_value(best_bid))
    return {
        "curr": _bucket_int(curr_price, price_bucket),
        "fluctuation": _bucket_float(ws_data.get('fluctuation', 0.0), 0.3),
        "v_pw": _bucket_float(ws_data.get('v_pw', 0.0), 10.0),
        "buy_ratio": _bucket_float(ws_data.get('buy_ratio', 0.0), 8.0),
        "spread": _bucket_int(spread_amount, max(1, price_bucket)),
        "ask_bid_balance": _bucket_int(bid_tot - ask_tot, 50_000),
        "depth_balance": _bucket_int(
            _coerce_int_value(ws_data.get('net_bid_depth')) - abs(_coerce_int_value(ws_data.get('net_ask_depth'))),
            20_000,
        ),
        "exec_balance": _bucket_int(buy_exec - sell_exec, 5_000),
        "tick_trade_value": _bucket_int(ws_data.get('tick_trade_value', 0), 20_000),
    }


def _build_holding_ai_fast_signature(ws_data):
    snapshot = _build_holding_ai_fast_snapshot(ws_data)
    return tuple(snapshot.values())


def _maybe_emit_entry_ai_price_skip_followup(stock, code, *, curr_price: int, now_ts: float) -> None:
    started_at = float(stock.get("entry_ai_price_skip_started_at", 0) or 0)
    mark_price = _coerce_int_value(stock.get("entry_ai_price_skip_mark_price"))
    if started_at <= 0 or mark_price <= 0 or curr_price <= 0:
        return

    max_price = max(_coerce_int_value(stock.get("entry_ai_price_skip_max_price")), curr_price)
    min_price = min(
        _coerce_int_value(stock.get("entry_ai_price_skip_min_price")) or curr_price,
        curr_price,
    )
    stock["entry_ai_price_skip_max_price"] = max_price
    stock["entry_ai_price_skip_min_price"] = min_price

    elapsed_sec = max(0, int(now_ts - started_at))
    for interval_sec in (30, 90):
        followup_key = f"entry_ai_price_skip_followup_{interval_sec}s"
        if elapsed_sec < interval_sec or bool(stock.get(followup_key)):
            continue
        mfe_bps = int(round(((max_price - mark_price) / mark_price) * 10000))
        mae_bps = int(round(((min_price - mark_price) / mark_price) * 10000))
        _log_entry_pipeline(
            stock,
            code,
            "entry_ai_price_canary_skip_followup",
            elapsed_sec=interval_sec,
            mark_price=mark_price,
            followup_price=curr_price,
            max_price=max_price,
            min_price=min_price,
            mfe_bps=mfe_bps,
            mae_bps=mae_bps,
            micro_state_at_skip=str(stock.get("entry_ai_price_skip_micro_state") or ""),
            ofi_threshold_source_at_skip=str(stock.get("entry_ai_price_skip_threshold_source") or ""),
            ofi_bucket_key_at_skip=str(stock.get("entry_ai_price_skip_bucket_key") or ""),
            entry_ai_price_skip_policy_warning=str(stock.get("entry_ai_price_skip_policy_warning") or ""),
        )
        stock[followup_key] = True

    if bool(stock.get("entry_ai_price_skip_followup_90s")):
        _mutate_stock_state(
            stock,
            pop_fields=[
                "entry_ai_price_skip_started_at",
                "entry_ai_price_skip_mark_price",
                "entry_ai_price_skip_max_price",
                "entry_ai_price_skip_min_price",
                "entry_ai_price_skip_micro_state",
                "entry_ai_price_skip_policy_warning",
                "entry_ai_price_skip_threshold_source",
                "entry_ai_price_skip_bucket_key",
                "entry_ai_price_skip_followup_30s",
                "entry_ai_price_skip_followup_90s",
            ],
        )


def _describe_snapshot_deltas(previous_snapshot, current_snapshot, *, limit=4):
    if not isinstance(previous_snapshot, dict) or not isinstance(current_snapshot, dict):
        return ""
    deltas = []
    for key in current_snapshot.keys():
        prev = previous_snapshot.get(key)
        curr = current_snapshot.get(key)
        if prev != curr:
            deltas.append(f"{key}:{prev}->{curr}")
        if len(deltas) >= limit:
            break
    return ",".join(deltas)


def _log_strength_momentum_observation(stock, code, result):
    if not isinstance(result, dict):
        return
    stage = "strength_momentum_pass" if result.get("allowed") else "strength_momentum_observed"
    _log_entry_pipeline(
        stock,
        code,
        stage,
        **_build_observation_contract_fields("ops_volume_diagnostic"),
        reason=result.get("reason"),
        base_vpw=f"{float(result.get('base_vpw', 0.0) or 0.0):.1f}",
        current_vpw=f"{float(result.get('current_vpw', 0.0) or 0.0):.1f}",
        delta=f"{float(result.get('vpw_delta', 0.0) or 0.0):.1f}",
        slope=f"{float(result.get('slope_per_sec', 0.0) or 0.0):.2f}",
        window_sec=result.get("window_sec"),
        buy_value=int(result.get("window_buy_value", 0) or 0),
        sell_value=int(result.get("window_sell_value", 0) or 0),
        buy_ratio=f"{float(result.get('window_buy_ratio', 0.0) or 0.0):.2f}",
        exec_buy_ratio=f"{float(result.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
        net_buy_qty=int(result.get("window_net_buy_qty", 0) or 0),
        elapsed=f"{float(result.get('elapsed_sec', 0.0) or 0.0):.2f}",
        threshold_profile=result.get("threshold_profile"),
        momentum_tag=result.get("position_tag"),
        canary_applied=bool(result.get("canary_applied")),
        canary_reason=result.get("canary_reason"),
        canary_origin_reason=result.get("canary_origin_reason"),
    )


def _iter_pending_entry_orders(stock):
    orders = stock.get('pending_entry_orders') or []
    if not isinstance(orders, list):
        return []
    return orders


def _clear_pending_entry_meta(stock):
    with ENTRY_LOCK:
        move_orders_to_terminal(stock, reason='pending_entry_meta_cleared')
        for key in [
            'pending_entry_orders',
            'entry_mode',
            'entry_requested_qty',
            'entry_filled_qty',
            'entry_fill_amount',
            'entry_dynamic_reason',
            'requested_buy_qty',
            'entry_bundle_id',
        ]:
            stock.pop(key, None)
    _clear_entry_arm(stock)


def _merge_pending_entry_orders(existing_orders, entry_orders):
    merged_orders = []
    existing_by_key = {}

    for order in existing_orders or []:
        ord_no = str(order.get('ord_no', '') or '').strip()
        tag = str(order.get('tag', '') or '').strip()
        key = ord_no or f"tag:{tag}"
        if key:
            existing_by_key[key] = order

    for order in entry_orders or []:
        merged = dict(order)
        ord_no = str(order.get('ord_no', '') or '').strip()
        tag = str(order.get('tag', '') or '').strip()
        key = ord_no or f"tag:{tag}"
        previous = existing_by_key.get(key)
        if previous:
            for field in [
                'status',
                'filled_qty',
                'last_fill_price',
                'last_fill_at',
                'cancelled_at',
                'notice_status',
                'notice_at',
            ]:
                if field in previous:
                    merged[field] = previous[field]
        merged_orders.append(merged)

    return merged_orders


def _clear_entry_arm(stock):
    _mutate_stock_state(stock, pop_fields=(
        'entry_armed',
        'entry_armed_at',
        'entry_armed_until',
        'entry_armed_reason',
        'entry_armed_ai_score',
        'entry_armed_ratio',
        'entry_armed_target_buy_price',
        'entry_armed_vpw',
        'entry_armed_dynamic_reason',
        'entry_armed_resume_count',
    ))


def _activate_entry_arm(stock, code, *, ai_score, ratio, target_buy_price, current_vpw, reason, dynamic_reason):
    ttl_sec = int(_rule('SCALP_ENTRY_ARM_TTL_SEC', 20) or 20)
    now_ts = time.time()
    _mutate_stock_state(
        stock,
        set_fields={
            'entry_armed': True,
            'entry_armed_at': now_ts,
            'entry_armed_until': now_ts + ttl_sec,
            'entry_armed_reason': reason,
            'entry_armed_ai_score': float(ai_score),
            'entry_armed_ratio': float(ratio),
            'entry_armed_target_buy_price': int(target_buy_price or 0),
            'entry_armed_vpw': float(current_vpw),
            'entry_armed_dynamic_reason': dynamic_reason,
            'entry_armed_resume_count': 0,
        },
    )
    _log_entry_pipeline(
        stock,
        code,
        'entry_armed',
        ai_score=f"{float(ai_score):.1f}",
        ratio=f"{float(ratio):.4f}",
        target_buy_price=int(target_buy_price or 0),
        current_vpw=f"{float(current_vpw):.1f}",
        reason=reason,
        dynamic_reason=dynamic_reason,
        ttl_sec=ttl_sec,
    )


def _get_live_entry_arm(stock, code):
    if not stock.get('entry_armed'):
        return None
    expires_at = float(stock.get('entry_armed_until', 0) or 0)
    now_ts = time.time()
    if expires_at <= now_ts:
        armed_at = float(stock.get("entry_armed_at", 0) or 0)
        resume_count = int(stock.get("entry_armed_resume_count", 0) or 0)
        waited_sec = max(0.0, now_ts - armed_at) if armed_at > 0 else 0.0
        expired_stage = "entry_armed_expired_after_wait" if resume_count > 0 else "entry_armed_expired"
        _log_entry_pipeline(
            stock,
            code,
            expired_stage,
            waited_sec=f"{waited_sec:.1f}",
            resume_count=resume_count,
            reason=stock.get("entry_armed_reason"),
            dynamic_reason=stock.get("entry_armed_dynamic_reason"),
        )
        _clear_entry_arm(stock)
        return None
    return {
        'armed_at': float(stock.get('entry_armed_at', 0) or 0),
        'expires_at': expires_at,
        'remaining_sec': max(0.0, expires_at - now_ts),
        'ai_score': float(stock.get('entry_armed_ai_score', 50.0) or 50.0),
        'ratio': float(stock.get('entry_armed_ratio', 0.10) or 0.10),
        'target_buy_price': int(stock.get('entry_armed_target_buy_price', 0) or 0),
        'current_vpw': float(stock.get('entry_armed_vpw', 0.0) or 0.0),
        'reason': stock.get('entry_armed_reason'),
        'dynamic_reason': stock.get('entry_armed_dynamic_reason'),
    }


def _has_open_pending_entry_orders(stock):
    return any(
        str(order.get('status', 'OPEN')).upper() in {'OPEN', 'PARTIAL', 'SENT'}
        for order in _iter_pending_entry_orders(stock)
    )


def _cancel_pending_entry_orders(stock, code, *, force=False):
    """
    Cancel unresolved entry BUY orders.

    Returns:
    - 'cancelled': all remaining orders cancelled or already gone
    - 'resolved': nothing left to cancel
    - 'failed': at least one order remains uncertain
    """

    with ENTRY_LOCK:
        open_orders = [
            order for order in _iter_pending_entry_orders(stock)
            if str(order.get('status', 'OPEN')).upper() in {'OPEN', 'PARTIAL', 'SENT'}
            and str(order.get('ord_no', '') or '').strip()
        ]
        if not open_orders:
            _clear_pending_entry_meta(stock)
            return 'resolved'

        had_failure = False
        for order in open_orders:
            ord_no = str(order.get('ord_no', '') or '').strip()
            sent_at = _safe_float(order.get('sent_at'), 0.0)
            order_age_sec = max(0.0, time.time() - sent_at) if sent_at > 0 else 0.0
            cancel_fields = {
                "orig_ord_no": ord_no,
                "tag": order.get('tag'),
                "qty": _coerce_int_value(order.get('qty')),
                "filled_qty": _coerce_int_value(order.get('filled_qty')),
                "remaining_qty": max(0, _coerce_int_value(order.get('qty')) - _coerce_int_value(order.get('filled_qty'))),
                "submitted_price": _coerce_int_value(order.get('price')),
                "order_age_sec": f"{order_age_sec:.1f}",
                "cancel_reason": "entry_timeout_or_reconcile",
                "entry_order_lifecycle": str(order.get('entry_order_lifecycle') or "standard"),
                "entry_passive_probe_applied": bool(order.get('entry_passive_probe_applied')),
                "best_bid_at_submit": _coerce_int_value(order.get('best_bid_at_submit')),
                "best_ask_at_submit": _coerce_int_value(order.get('best_ask_at_submit')),
                "price_below_bid_bps": _coerce_int_value(order.get('price_below_bid_bps')),
                "price_decision_context_age_ms": order.get('price_decision_context_age_ms', "-"),
                "quote_age_at_submit_ms": order.get('quote_age_at_submit_ms', "-"),
            }
            _log_entry_pipeline(stock, code, "entry_order_cancel_requested", **cancel_fields)
            res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=ord_no, token=KIWOOM_TOKEN, qty=0)
            is_success = False
            err_msg = str(res)
            cancel_ord_no = ""
            if isinstance(res, dict):
                if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
                    is_success = True
                err_msg = str(res.get('return_msg', '') or '')
                cancel_ord_no = str(res.get('ord_no', '') or res.get('odno', '') or '')
            elif res:
                is_success = True

            if is_success or any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음', '체결']):
                order['status'] = 'CANCELLED'
                order['cancelled_at'] = time.time()
                _log_entry_pipeline(
                    stock,
                    code,
                    "entry_order_cancel_confirmed",
                    **cancel_fields,
                    cancel_ord_no=cancel_ord_no,
                    cancel_response="success" if is_success else "already_resolved",
                    cancel_message=err_msg[:160],
                )
                continue

            had_failure = True
            _log_entry_pipeline(
                stock,
                code,
                "entry_order_cancel_failed",
                **cancel_fields,
                cancel_response="failed",
                cancel_message=err_msg[:160],
            )
            log_error(
                f"⚠️ [ENTRY_CANCEL] {stock.get('name')}({code}) "
                f"tag={order.get('tag')} ord_no={ord_no} cancel_failed msg={err_msg}"
            )
            if not force:
                break

        if had_failure:
            return 'failed'

        _clear_pending_entry_meta(stock)
        return 'cancelled'


def _stage_buy_order_submission(stock, code, curr_price, requested_qty, msg, entry_orders):
    with ENTRY_LOCK:
        entry_dynamic_reason = str(stock.get('entry_armed_dynamic_reason', '') or '')
        _clear_entry_arm(stock)
        existing_filled_qty = int(stock.get('entry_filled_qty', 0) or 0)
        existing_fill_amount = int(stock.get('entry_fill_amount', 0) or 0)
        stock['status'] = 'HOLDING' if requested_qty > 0 and existing_filled_qty >= requested_qty else 'BUY_ORDERED'
        stock['order_time'] = float(stock.get('order_time', 0) or time.time())
        stock['order_price'] = curr_price
        stock['requested_buy_qty'] = requested_qty
        stock['entry_requested_qty'] = requested_qty
        stock['entry_filled_qty'] = existing_filled_qty
        stock['entry_fill_amount'] = existing_fill_amount
        if entry_dynamic_reason:
            stock['entry_dynamic_reason'] = entry_dynamic_reason
        stock['pending_entry_orders'] = _merge_pending_entry_orders(
            stock.get('pending_entry_orders') or [],
            entry_orders,
        )
        stock.setdefault('entry_bundle_id', f"{code}-{uuid4().hex[:12]}")
        primary_ord_no = ''
        for order in stock.get('pending_entry_orders') or []:
            primary_ord_no = str((order or {}).get('ord_no', '') or '').strip()
            if primary_ord_no:
                break
        if primary_ord_no:
            stock['odno'] = primary_ord_no
        stock['pending_buy_msg'] = msg


def _finalize_buy_order_submission(stock, code, curr_price, requested_qty, msg, entry_orders):
    _stage_buy_order_submission(stock, code, curr_price, requested_qty, msg, entry_orders)
    primary_ord_no = str(stock.get('odno', '') or '').strip()
    log_info(
        f"[ENTRY_SUBMISSION_BUNDLE] {stock.get('name')}({code}) "
        f"mode={stock.get('entry_mode', 'unknown')} requested_qty={requested_qty} "
        f"legs={len(entry_orders)} primary_ord_no={primary_ord_no}"
    )


def _resolve_live_entry_order_request(strategy, entry_mode, planned_order, default_order_type_code, default_price):
    tif = str(planned_order.get('tif', 'DAY') or 'DAY').upper()
    tag = str(planned_order.get('tag', 'normal') or 'normal')
    qty = int(planned_order.get('qty', 0) or 0)
    price = int(planned_order.get('price', default_price) or default_price or 0)

    if tif == 'IOC':
        return {
            'qty': qty,
            'price': 0,
            'order_type_code': '16',
            'tif': tif,
            'tag': tag,
        }

    if strategy == 'SCALPING' or entry_mode == 'fallback':
        return {
            'qty': qty,
            'price': price,
            'order_type_code': '00',
            'tif': tif,
            'tag': tag,
        }

    return {
        'qty': qty,
        'price': int(default_price or 0),
        'order_type_code': default_order_type_code,
        'tif': tif,
        'tag': tag,
    }


def _reconcile_pending_entry_orders(stock, code, strategy):
    if not _has_open_pending_entry_orders(stock):
        return

    order_time = float(stock.get('order_time', 0) or 0)
    if order_time <= 0:
        return

    timeout_sec = _resolve_buy_order_timeout_sec(stock, strategy)
    if time.time() - order_time <= timeout_sec:
        return

    result = _cancel_pending_entry_orders(stock, code, force=True)
    if result == 'failed':
        return

    buy_qty = _safe_int(stock.get('buy_qty'), 0)
    if buy_qty > 0:
        requested_qty = int(stock.get('entry_requested_qty', 0) or stock.get('requested_buy_qty', 0) or buy_qty)
        requested_qty = max(requested_qty, buy_qty, 1)
        fill_ratio = float(buy_qty) / float(requested_qty)

        min_fill_ratio = 0.0
        partial_fill_ratio_guard_enabled = bool(
            _rule_bool('SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED', False)
        )
        if partial_fill_ratio_guard_enabled:
            min_fill_ratio = float(
                _rule_float('SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT', 0.20)
            )
            position_tag = normalize_position_tag(stock.get('strategy'), stock.get('position_tag'))
            if position_tag == 'SCALP_PRESET_TP':
                min_fill_ratio = float(
                    _rule_float('SCALP_PARTIAL_FILL_MIN_RATIO_PRESET_TP', 0.0)
                )
            elif str(stock.get('entry_dynamic_reason', '') or '').strip().lower() == 'strong_absolute_override':
                min_fill_ratio = float(
                    _rule_float('SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE', 0.10)
                )
            min_fill_ratio = max(0.0, min(1.0, min_fill_ratio))

        _log_entry_pipeline(
            stock,
            code,
            "partial_fill_reconciled",
            requested_qty=requested_qty,
            filled_qty=buy_qty,
            fill_ratio=f"{fill_ratio:.3f}",
            min_fill_ratio=f"{min_fill_ratio:.3f}",
            min_fill_ratio_enabled=partial_fill_ratio_guard_enabled,
            dynamic_reason=stock.get('entry_dynamic_reason'),
        )

        if partial_fill_ratio_guard_enabled and min_fill_ratio > 0 and fill_ratio < min_fill_ratio:
            res = kiwoom_orders.send_sell_order_market(code=code, qty=buy_qty, token=KIWOOM_TOKEN)
            if _is_ok_response(res):
                _mutate_stock_state(
                    stock,
                    set_fields={
                        'status': 'SELL_ORDERED',
                        'sell_target_price': int(stock.get('order_price', 0) or 0),
                        'sell_order_time': time.time(),
                        'pending_sell_msg': (
                            f"partial_fill_ratio_below_min(fill_ratio={fill_ratio:.3f},min={min_fill_ratio:.3f})"
                        ),
                    },
                )
                _log_entry_pipeline(
                    stock,
                    code,
                    "partial_fill_ratio_below_min_exit_ordered",
                    requested_qty=requested_qty,
                    filled_qty=buy_qty,
                    fill_ratio=f"{fill_ratio:.3f}",
                    min_fill_ratio=f"{min_fill_ratio:.3f}",
                )
                log_info(
                    f"[ENTRY_RECONCILED] {stock.get('name')}({code}) "
                    f"partial fill ratio {fill_ratio:.3f} < min {min_fill_ratio:.3f}; "
                    "market sell ordered"
                )
                return

            err_msg = str(res.get('return_msg', '') if isinstance(res, dict) else res)
            _log_entry_pipeline(
                stock,
                code,
                "partial_fill_ratio_below_min_exit_failed",
                requested_qty=requested_qty,
                filled_qty=buy_qty,
                fill_ratio=f"{fill_ratio:.3f}",
                min_fill_ratio=f"{min_fill_ratio:.3f}",
                error=err_msg or "unknown",
            )
            log_error(
                f"⚠️ [ENTRY_RECONCILED] {stock.get('name')}({code}) "
                f"partial fill ratio below min but market sell failed: {err_msg}"
            )

        _mutate_stock_state(
            stock,
            set_fields={'status': 'HOLDING'},
            pop_fields=['odno'],
        )
        log_info(f"[ENTRY_RECONCILED] {stock.get('name')}({code}) partial fill kept, remaining entry orders cancelled")
    else:
        _mutate_stock_state(
            stock,
            set_fields={'status': 'WATCHING'},
            pop_fields=[
                'odno',
                'order_time',
                'pending_buy_msg',
                'target_buy_price',
                'order_price',
            ],
        )
        _clear_entry_arm(stock)
        with ENTRY_LOCK:
            HIGHEST_PRICES.pop(code, None)
            ALERTED_STOCKS.discard(code)
        if strategy in ['SCALPING', 'SCALP']:
            with ENTRY_LOCK:
                COOLDOWNS[code] = time.time() + 1200
        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=stock.get('id')).update({
                    "status": "WATCHING",
                    "buy_price": 0,
                    "buy_qty": 0,
                })
        except Exception as exc:
            log_error(f"🚨 [DB 에러] {stock.get('name')} pending entry timeout 복구 실패: {exc}")


# =====================================================================
# 🧠 상태 머신 (State Machine) 핸들러
# =====================================================================

def handle_watching_state(stock, code, ws_data, admin_id, *, now_ts=None, now_dt=None, radar=None, ai_engine=None):
    """
    [WATCHING 상태] 진입 타점 감시 및 AI 교차 검증
    """
    global LAST_AI_CALL_TIMES

    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    event_bus = EVENT_BUS

    # P1: 메인 루프에서 전달받은 시간값 재사용, 없으면 자체 측정
    if now_ts is None:
        now_ts = time.time()
    if now_dt is None:
        now_dt = datetime.now()
    now_t = now_dt.time()

    _log_watching_state_debug(stock, code, radar=radar, ai_engine=ai_engine)

    if is_buy_side_paused():
        last_log = float(stock.get('last_pause_block_log_ts', 0) or 0)
        if (now_ts - last_log) >= 60:
            log_info(
                f"[TRADING_PAUSED_BLOCK] WATCHING buy skipped "
                f"{stock.get('name')}({code}) state={get_pause_state_label()}"
            )
            _mutate_stock_state(stock, set_fields={'last_pause_block_log_ts': now_ts})
        return

    MAX_SCALP_SURGE_PCT = _rule_float('MAX_SCALP_SURGE_PCT', 20.0)
    MAX_INTRADAY_SURGE = _rule_float('MAX_INTRADAY_SURGE', 15.0)
    MIN_SCALP_LIQUIDITY = _rule_float('MIN_SCALP_LIQUIDITY', 500_000_000)
    SNIPER_AGGRESSIVE_PROB = _rule_float('SNIPER_AGGRESSIVE_PROB', 0.70)
    BUY_SCORE_THRESHOLD = _rule_float('BUY_SCORE_THRESHOLD', 70)
    VPW_STRONG_LIMIT = _rule_float('VPW_STRONG_LIMIT', 120)
    INVEST_RATIO_SCALPING_MIN = _rule_float('INVEST_RATIO_SCALPING_MIN', 0.05)
    INVEST_RATIO_SCALPING_MAX = _rule_float('INVEST_RATIO_SCALPING_MAX', 0.25)
    VPW_SCALP_LIMIT = _rule_float('VPW_SCALP_LIMIT', 120)
    AI_WATCHING_COOLDOWN = _rule_int('AI_WATCHING_COOLDOWN', 60)
    VIP_LIQUIDITY_THRESHOLD = _rule_float('VIP_LIQUIDITY_THRESHOLD', 1_000_000_000)
    AI_WAIT_DROP_COOLDOWN = _rule_int('AI_WAIT_DROP_COOLDOWN', 300)
    VPW_KOSDAQ_LIMIT = _rule_float('VPW_KOSDAQ_LIMIT', 105)
    VPW_STRONG_KOSDAQ_LIMIT = _rule_float('VPW_STRONG_KOSDAQ_LIMIT', 120)
    BUY_SCORE_KOSDAQ_THRESHOLD = _rule_float('BUY_SCORE_KOSDAQ_THRESHOLD', 80)
    INVEST_RATIO_KOSDAQ_MIN = _rule_float('INVEST_RATIO_KOSDAQ_MIN', 0.05)
    INVEST_RATIO_KOSDAQ_MAX = _rule_float('INVEST_RATIO_KOSDAQ_MAX', 0.15)
    AI_SCORE_THRESHOLD_KOSDAQ = _rule_float('AI_SCORE_THRESHOLD_KOSDAQ', 60)
    INVEST_RATIO_KOSPI_MIN = _rule_float('INVEST_RATIO_KOSPI_MIN', 0.10)
    INVEST_RATIO_KOSPI_MAX = _rule_float('INVEST_RATIO_KOSPI_MAX', 0.30)
    AI_SCORE_THRESHOLD_KOSPI = _rule_float('AI_SCORE_THRESHOLD_KOSPI', 60)
    BIG_BITE_BOOST_SCORE = _rule_float('BIG_BITE_BOOST_SCORE', 5)
    BIG_BITE_ARMED_ENTRY_BONUS = _rule_float('BIG_BITE_ARMED_ENTRY_BONUS', 2)
    BIG_BITE_HARD_GATE_ENABLED = _rule_bool('BIG_BITE_HARD_GATE_ENABLED', False)
    BIG_BITE_HARD_GATE_TAGS_SCALPING = _rule(
        'BIG_BITE_HARD_GATE_TAGS_SCALPING', ("VCP", "BREAK", "BRK", "SHOOT", "NEXT")
    )
    BIG_BITE_HARD_GATE_TAGS_KOSDAQ = _rule('BIG_BITE_HARD_GATE_TAGS_KOSDAQ', ())
    BIG_BITE_HARD_GATE_TAGS_KOSPI = _rule('BIG_BITE_HARD_GATE_TAGS_KOSPI', ())

    strategy = normalize_strategy(stock.get('strategy'))
    pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))

    if strategy == 'SCALPING':
        strategy_start = TIME_09_00 if pos_tag == 'VCP_NEXT' else TIME_09_03
    else:
        strategy_start = TIME_09_05

    if now_t < strategy_start:
        return

    MAX_SURGE = MAX_SCALP_SURGE_PCT
    MAX_INTRADAY_SURGE = MAX_INTRADAY_SURGE
    MIN_LIQUIDITY = MIN_SCALP_LIQUIDITY
    if code in cooldowns and now_ts < cooldowns[code]:
        _emit_same_symbol_soft_stop_cooldown_shadow(
            stock=stock,
            code=code,
            now_ts=now_ts,
            runtime_remaining_sec=max(0, int(cooldowns[code] - now_ts)),
        )
        return

    if strategy == 'SCALPING' and now_t >= TIME_SCALPING_NEW_BUY_CUTOFF:
        return

    if code in alerted_stocks:
        return

    curr_price = _safe_int(ws_data.get('curr'), 0)
    if curr_price <= 0:
        return
    _maybe_emit_entry_ai_price_skip_followup(stock, code, curr_price=curr_price, now_ts=now_ts)

    current_vpw = float(ws_data.get('v_pw', 0) or 0)
    fluctuation = float(ws_data.get('fluctuation', 0.0) or 0.0)
    current_ai_score = float(stock.get('rt_ai_prob', stock.get('prob', 0.5)) or 0.5) * 100
    runtime = {
        "strategy": strategy,
        "pos_tag": pos_tag,
        "now_ts": now_ts,
        "now_dt": now_dt,
        "curr_price": curr_price,
        "current_vpw": current_vpw,
        "fluctuation": fluctuation,
        "current_ai_score": current_ai_score,
        "liquidity_value": 0,
        "is_trigger": False,
        "msg": "",
        "ratio": 0.10,
        "ai_prob": stock.get('prob', SNIPER_AGGRESSIVE_PROB),
        "buy_threshold": BUY_SCORE_THRESHOLD,
        "strong_vpw": VPW_STRONG_LIMIT,
        "cooldowns": cooldowns,
        "alerted_stocks": alerted_stocks,
        "event_bus": event_bus,
        "ai_engine": ai_engine,
    }
    config = {
        "MAX_SCALP_SURGE_PCT": MAX_SCALP_SURGE_PCT,
        "MAX_INTRADAY_SURGE": MAX_INTRADAY_SURGE,
        "MIN_SCALP_LIQUIDITY": MIN_SCALP_LIQUIDITY,
        "SNIPER_AGGRESSIVE_PROB": SNIPER_AGGRESSIVE_PROB,
        "BUY_SCORE_THRESHOLD": BUY_SCORE_THRESHOLD,
        "VPW_STRONG_LIMIT": VPW_STRONG_LIMIT,
        "INVEST_RATIO_SCALPING_MIN": INVEST_RATIO_SCALPING_MIN,
        "INVEST_RATIO_SCALPING_MAX": INVEST_RATIO_SCALPING_MAX,
        "VPW_SCALP_LIMIT": VPW_SCALP_LIMIT,
        "AI_WATCHING_COOLDOWN": AI_WATCHING_COOLDOWN,
        "VIP_LIQUIDITY_THRESHOLD": VIP_LIQUIDITY_THRESHOLD,
        "AI_WAIT_DROP_COOLDOWN": AI_WAIT_DROP_COOLDOWN,
        "VPW_KOSDAQ_LIMIT": VPW_KOSDAQ_LIMIT,
        "VPW_STRONG_KOSDAQ_LIMIT": VPW_STRONG_KOSDAQ_LIMIT,
        "BUY_SCORE_KOSDAQ_THRESHOLD": BUY_SCORE_KOSDAQ_THRESHOLD,
        "INVEST_RATIO_KOSDAQ_MIN": INVEST_RATIO_KOSDAQ_MIN,
        "INVEST_RATIO_KOSDAQ_MAX": INVEST_RATIO_KOSDAQ_MAX,
        "AI_SCORE_THRESHOLD_KOSDAQ": AI_SCORE_THRESHOLD_KOSDAQ,
        "INVEST_RATIO_KOSPI_MIN": INVEST_RATIO_KOSPI_MIN,
        "INVEST_RATIO_KOSPI_MAX": INVEST_RATIO_KOSPI_MAX,
        "AI_SCORE_THRESHOLD_KOSPI": AI_SCORE_THRESHOLD_KOSPI,
        "BIG_BITE_BOOST_SCORE": BIG_BITE_BOOST_SCORE,
        "BIG_BITE_ARMED_ENTRY_BONUS": BIG_BITE_ARMED_ENTRY_BONUS,
        "BIG_BITE_HARD_GATE_ENABLED": BIG_BITE_HARD_GATE_ENABLED,
        "BIG_BITE_HARD_GATE_TAGS_SCALPING": BIG_BITE_HARD_GATE_TAGS_SCALPING,
        "BIG_BITE_HARD_GATE_TAGS_KOSDAQ": BIG_BITE_HARD_GATE_TAGS_KOSDAQ,
        "BIG_BITE_HARD_GATE_TAGS_KOSPI": BIG_BITE_HARD_GATE_TAGS_KOSPI,
    }

    if not _handle_watching_strategy_branch(stock, code, ws_data, radar, ai_engine, runtime, config):
        return

    if runtime["is_trigger"]:
        maybe_arm_scalp_live_simulator_from_buy_signal(stock, code, ws_data, runtime, ai_engine=ai_engine)
        _submit_watching_triggered_entry(stock, code, ws_data, admin_id, runtime)
        return



def handle_holding_state(stock, code, ws_data, admin_id, market_regime, *, now_ts=None, now_dt=None, radar=None, ai_engine=None):
    """
    [HOLDING 상태] 보유 종목 익절/손절 감시 및 AI 조기 개입
    """
    global LAST_AI_CALL_TIMES

    # P1: 메인 루프에서 전달받은 시간값 재사용
    if now_ts is None:
        now_ts = time.time()
    if now_dt is None:
        now_dt = datetime.now()
    now_t = now_dt.time()

    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    highest_prices = HIGHEST_PRICES
    if not isinstance(highest_prices, dict):
        highest_prices = {}

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
    _mutate_stock_state(stock, set_fields={"position_tag": pos_tag})
    legacy_broker_recovered = bool(stock.get('broker_recovered_legacy'))

    curr_p = _safe_int(ws_data.get('curr'), 0)
    buy_p = _safe_float(stock.get('buy_price'), 0.0)
    _reconcile_pending_entry_orders(stock, code, strategy)
    if curr_p <= 0 or buy_p <= 0:
        return
    _append_holding_price_sample(stock, now_ts=now_ts, curr_price=curr_p)
    price_key = _price_tracking_key(stock, code)

    # --------------------------------------------------------
    # HOLDING 제어 흐름(요약)
    # 1) 현재가/평단/수익률 계산
    # 2) 최고가/보유시간 등 갱신
    # 3) 전략별 청산 조건 평가
    # 4) SELL 신호면 즉시 매도 처리 후 종료
    # 5) stop/trailing 보정(전략별 내장)
    # 6) 추가매수 공통 게이트 확인
    # 7) 전략별 추가매수 시그널 평가
    # 8) 조건 만족 시 추가매수 주문 전송
    # 9) 아니면 HOLD 유지
    # --------------------------------------------------------

    if isinstance(highest_prices, dict):
        with ENTRY_LOCK:
            if price_key not in highest_prices:
                highest_prices[price_key] = curr_p
            highest_prices[price_key] = max(highest_prices[price_key], curr_p)

    profit_rate = calculate_net_profit_rate(buy_p, curr_p)
    peak_profit = calculate_net_profit_rate(buy_p, highest_prices.get(price_key, curr_p))
    trailing_stop_price = float(stock.get('trailing_stop_price') or 0)
    hard_stop_price = float(stock.get('hard_stop_price') or 0)

    if strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        last_log = LAST_LOG_TIMES.get(code, 0)
        if now_ts - last_log >= 600:
            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            log_info(
                f"[{strategy}] 보유 종목 감시 중: {stock['name']}({code}) 수익률 {profit_rate:+.2f}%, "
                f"AI 점수 {current_ai_score:.0f}점"
            )
            with ENTRY_LOCK:
                LAST_LOG_TIMES[code] = now_ts

    if stock.get('exit_mode') == 'SCALP_PRESET_TP':
        if stock.get('exit_requested'):
            return

        profit_rate = calculate_net_profit_rate(buy_p, curr_p) if buy_p > 0 else 0.0
        preset_hard_stop_pct = float(
            stock.get(
                'hard_stop_pct',
                _rule('SCALP_PRESET_HARD_STOP_PCT', -0.7),
            )
            or _rule('SCALP_PRESET_HARD_STOP_PCT', -0.7)
        )
        preset_hard_stop_grace_sec = int(
            stock.get(
                'hard_stop_grace_sec',
                _rule('SCALP_PRESET_HARD_STOP_GRACE_SEC', 0),
            )
            or 0
        )
        preset_hard_stop_emergency_pct = float(
            stock.get(
                'hard_stop_emergency_pct',
                _rule(
                    'SCALP_PRESET_HARD_STOP_EMERGENCY_PCT',
                    min(preset_hard_stop_pct - 0.5, -1.2),
                ),
            )
            or _rule(
                'SCALP_PRESET_HARD_STOP_EMERGENCY_PCT',
                min(preset_hard_stop_pct - 0.5, -1.2),
            )
        )
        preset_held_sec = _resolve_holding_elapsed_sec(stock)
        preset_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        _emit_scalp_hard_time_stop_shadow(
            stock=stock,
            code=code,
            held_sec=preset_held_sec,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=preset_ai_score,
            ai_exit_min_loss_pct=-0.7,
        )

        if legacy_broker_recovered:
            _mutate_stock_state(stock, set_fields={'last_exit_guard_reason': 'broker_recovered_legacy'})
        elif profit_rate <= preset_hard_stop_pct:
            within_grace = preset_hard_stop_grace_sec > 0 and preset_held_sec < preset_hard_stop_grace_sec
            emergency_break = profit_rate <= preset_hard_stop_emergency_pct
            if within_grace and not emergency_break:
                _log_holding_pipeline(
                    stock,
                    code,
                    "preset_hard_stop_grace",
                    profit_rate=f"{profit_rate:+.2f}",
                    held_sec=preset_held_sec,
                    grace_sec=preset_hard_stop_grace_sec,
                    hard_stop_pct=f"{preset_hard_stop_pct:+.2f}",
                    emergency_pct=f"{preset_hard_stop_emergency_pct:+.2f}",
                )
            else:
                log_info(
                    f"🔪 [SCALP 출구엔진] {stock['name']} 손절선 터치({profit_rate:.2f}%). "
                    "즉각 최유리(IOC) 청산!"
                )
                _dispatch_scalp_preset_exit(
                    stock=stock,
                    code=code,
                    now_ts=now_ts,
                    curr_p=curr_p,
                    buy_p=buy_p,
                    profit_rate=profit_rate,
                    peak_profit=peak_profit,
                    strategy=strategy,
                    sell_reason_type="LOSS",
                    reason=f"🛑 SCALP 출구엔진 손절선 도달 ({preset_hard_stop_pct:+.2f}%)",
                    exit_rule="scalp_preset_hard_stop_pct",
                )
                return

        preset_tp_price = _safe_int(stock.get("preset_tp_price"), 0)
        if _is_scalp_simulated_position(stock, strategy) and preset_tp_price > 0 and curr_p >= preset_tp_price:
            _dispatch_scalp_preset_exit(
                stock=stock,
                code=code,
                now_ts=now_ts,
                curr_p=curr_p,
                buy_p=buy_p,
                profit_rate=profit_rate,
                peak_profit=peak_profit,
                strategy=strategy,
                sell_reason_type="PROFIT",
                reason="🎯 SCALP sim preset TP touch",
                exit_rule="scalp_sim_preset_tp_touch",
            )
            return

        if profit_rate >= 0.8 and not stock.get('ai_review_done', False):
            log_info(f"🤖 [SCALP 출구엔진] {stock['name']} +0.8% 도달! AI 1회 검문 실시...")
            _mutate_stock_state(stock, set_fields={'ai_review_done': True})

            if ai_engine:
                try:
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    ai_decision = ai_engine.analyze_target(
                        stock['name'],
                        ws_data,
                        recent_ticks,
                        [],
                        strategy="SCALPING",
                        cache_profile="holding",
                        prompt_profile="holding",
                    )
                    ai_action = ai_decision.get('action', 'WAIT')
                    ai_score = ai_decision.get('score', 50)

                    _mutate_stock_state(
                        stock,
                        set_fields={
                            'ai_review_action': ai_action,
                            'ai_review_score': ai_score,
                        },
                    )

                    # Gemini holding/exit action schema(HOLD/TRIM/EXIT)는 action_v2로 전달된다.
                    # 현 실행경로는 기존 호환을 위해 action(legacy: WAIT/SELL/DROP)을 함께 사용한다.
                    if ai_action in ['SELL', 'DROP']:
                        _log_holding_pipeline(
                            stock,
                            code,
                            "scalp_preset_tp_ai_exit_action",
                            ai_action_raw=ai_action,
                            ai_reason_raw=ai_decision.get('reason', '-'),
                            ai_action_used_for_exit=str(ai_action in ['SELL', 'DROP']).lower(),
                            **_build_ai_ops_log_fields(
                                ai_decision,
                                ai_score_raw=ai_score,
                                ai_score_after_bonus=ai_score,
                                ai_cooldown_blocked=False,
                            ),
                        )
                        log_info(
                            "🛑 [SCALP 출구엔진 AI] 모멘텀 둔화 감지. 1.5% 포기 후 즉시 최유리(IOC) "
                            "청산!"
                        )
                        _dispatch_scalp_preset_exit(
                            stock=stock,
                            code=code,
                            now_ts=now_ts,
                            curr_p=curr_p,
                            buy_p=buy_p,
                            profit_rate=profit_rate,
                            peak_profit=peak_profit,
                            strategy=strategy,
                            sell_reason_type="MOMENTUM_DECAY",
                            reason="🛑 SCALP 출구엔진 AI 모멘텀 둔화 즉시청산",
                            exit_rule="scalp_preset_ai_review_exit",
                        )
                        return
                    else:
                        _log_holding_pipeline(
                            stock,
                            code,
                            "scalp_preset_tp_ai_hold_action",
                            ai_action_raw=ai_action,
                            ai_reason_raw=ai_decision.get('reason', '-'),
                            ai_action_used_for_exit="false",
                            **_build_ai_ops_log_fields(
                                ai_decision,
                                ai_score_raw=ai_score,
                                ai_score_after_bonus=ai_score,
                                ai_cooldown_blocked=False,
                            ),
                        )
                        log_info(
                            "✅ [SCALP 출구엔진 AI] 돌파 모멘텀 유지(WAIT/BUY). 1.5% 유지, +0.3% 보호선 구축."
                        )
                        _mutate_stock_state(stock, set_fields={'protect_profit_pct': 0.3})
                except Exception as e:
                    log_error(f"⚠️ [SCALP 출구엔진 AI] 분석 실패: {e}. 기존 지정가 유지.")

        protect_pct = stock.get('protect_profit_pct')
        if protect_pct is not None and profit_rate <= protect_pct:
            log_info(
                f"🛡️ [SCALP 출구엔진] {stock['name']} +0.3% 보호선 이탈. 최유리(IOC) 약익절!"
            )
            _dispatch_scalp_preset_exit(
                stock=stock,
                code=code,
                now_ts=now_ts,
                curr_p=curr_p,
                buy_p=buy_p,
                profit_rate=profit_rate,
                peak_profit=peak_profit,
                strategy=strategy,
                sell_reason_type="TRAILING",
                reason=f"🛡️ SCALP 출구엔진 보호선 이탈 ({protect_pct:+.2f}%)",
                exit_rule="scalp_preset_protect_profit",
            )
            return

        return

    is_sell_signal = False
    sell_reason_type = "PROFIT"
    reason = ""
    exit_rule = ""

    last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
    current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
    near_ai_exit_score_limit = 35
    near_ai_exit_min_loss_pct = -0.7
    momentum_decay_score_limit = _rule_int('SCALP_AI_MOMENTUM_DECAY_SCORE_LIMIT', 45)
    momentum_decay_min_hold_sec = _rule_int('SCALP_AI_MOMENTUM_DECAY_MIN_HOLD_SEC', 90)
    last_ai_profit = stock.get('last_ai_profit', profit_rate)
    price_change = abs(profit_rate - last_ai_profit)
    time_elapsed = now_ts - last_ai_time
    held_sec = _resolve_holding_elapsed_sec(stock)
    held_time_min = held_sec / 60.0
    if strategy == "SCALPING":
        _emit_scalp_hard_time_stop_shadow(
            stock=stock,
            code=code,
            held_sec=held_sec,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            ai_exit_min_loss_pct=near_ai_exit_min_loss_pct,
        )
        _emit_partial_only_timeout_shadow(
            stock=stock,
            code=code,
            held_sec=held_sec,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
        )

    if strategy == 'SCALPING' and ai_engine and radar:
        safe_profit_pct = _rule_float('SCALP_SAFE_PROFIT', 0.5)
        near_safe_profit_zone = abs(profit_rate - safe_profit_pct) <= 0.20
        is_critical_zone = near_safe_profit_zone or (profit_rate >= safe_profit_pct) or (profit_rate < 0)

        dynamic_min_cd = (
            _rule_int('AI_HOLDING_CRITICAL_MIN_COOLDOWN', 8)
            if is_critical_zone
            else _rule_int('AI_HOLDING_MIN_COOLDOWN', 20)
        )
        dynamic_max_cd = (
            _rule_int('AI_HOLDING_CRITICAL_COOLDOWN', 20)
            if is_critical_zone
            else _rule_int('AI_HOLDING_MAX_COOLDOWN', 90)
        )
        dynamic_price_trigger = 0.20 if is_critical_zone else 0.40
        sim_ai_budget_target = _is_scalp_sim_ai_budget_target(stock, strategy)
        if sim_ai_budget_target:
            dynamic_min_cd = (
                _rule_int('SCALP_SIM_AI_HOLDING_CRITICAL_COOLDOWN_SEC', 30)
                if is_critical_zone
                else _rule_int('SCALP_SIM_AI_HOLDING_MIN_COOLDOWN_SEC', 90)
            )
            dynamic_max_cd = _rule_int('SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC', 180)

        if time_elapsed > dynamic_min_cd and (
            near_safe_profit_zone
            or price_change >= dynamic_price_trigger
            or time_elapsed > dynamic_max_cd
        ):
            holding_ai_review_started = time.perf_counter()
            try:
                market_snapshot = _build_holding_ai_fast_snapshot(ws_data)
                market_signature = tuple(market_snapshot.values())
                reuse_sec = _resolve_holding_ai_fast_reuse_sec(is_critical_zone, dynamic_max_cd)
                max_ws_age_sec = _rule_float('AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC', 1.5)
                ws_age_sec = _get_ws_snapshot_age_sec(ws_data)
                fast_sig_matches = market_signature == stock.get('last_ai_market_signature')
                fast_sig_age = _resolve_reference_age_sec(
                    stock.get('last_ai_market_signature_at'),
                    fallback_ts=stock.get('last_ai_reviewed_at'),
                    now_ts=now_ts,
                )
                fast_sig_age_str = "-" if fast_sig_age is None else f"{fast_sig_age:.1f}"
                sig_delta = _describe_snapshot_deltas(stock.get('last_ai_market_snapshot'), market_snapshot)
                near_ai_exit_band = abs(profit_rate - near_ai_exit_min_loss_pct) <= 0.20
                near_safe_profit_band = near_safe_profit_zone
                near_low_score_band = current_ai_score <= (near_ai_exit_score_limit + 5)
                fast_sig_fresh = fast_sig_age is not None and fast_sig_age < reuse_sec
                price_change_ok = price_change < (dynamic_price_trigger * 1.25)
                ws_fresh = ws_age_sec is None or ws_age_sec <= max_ws_age_sec
                shadow_action = "review"

                if (
                    fast_sig_matches
                    and fast_sig_fresh
                    and price_change_ok
                    and ws_fresh
                    and not near_ai_exit_band
                    and not near_safe_profit_band
                    and not near_low_score_band
                ):
                    shadow_action = "skip"
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_fast_reuse_band",
                        **_build_observation_contract_fields("ops_volume_diagnostic"),
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        ai_exit_min_loss_pct=f"{near_ai_exit_min_loss_pct:+.2f}",
                        safe_profit_pct=f"{safe_profit_pct:+.2f}",
                        near_ai_exit=near_ai_exit_band,
                        near_safe_profit=near_safe_profit_band,
                        distance_to_ai_exit=f"{profit_rate - near_ai_exit_min_loss_pct:+.2f}",
                        distance_to_safe_profit=f"{profit_rate - safe_profit_pct:+.2f}",
                        action=shadow_action,
                        telemetry_only=True,
                    )
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_skip_unchanged",
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        held_sec=int(held_time_min * 60),
                        price_change=f"{price_change:.2f}",
                        reuse_sec=f"{reuse_sec:.1f}",
                        age_sec=fast_sig_age_str,
                        ws_age_sec="-" if ws_age_sec is None else f"{ws_age_sec:.2f}",
                    )
                else:
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_fast_reuse_band",
                        **_build_observation_contract_fields("ops_volume_diagnostic"),
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        ai_exit_min_loss_pct=f"{near_ai_exit_min_loss_pct:+.2f}",
                        safe_profit_pct=f"{safe_profit_pct:+.2f}",
                        near_ai_exit=near_ai_exit_band,
                        near_safe_profit=near_safe_profit_band,
                        distance_to_ai_exit=f"{profit_rate - near_ai_exit_min_loss_pct:+.2f}",
                        distance_to_safe_profit=f"{profit_rate - safe_profit_pct:+.2f}",
                        action=shadow_action,
                        telemetry_only=True,
                    )
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_reuse_bypass",
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        held_sec=int(held_time_min * 60),
                        price_change=f"{price_change:.2f}",
                        reuse_sec=f"{reuse_sec:.1f}",
                        age_sec=fast_sig_age_str,
                        ws_age_sec="-" if ws_age_sec is None else f"{ws_age_sec:.2f}",
                        sig_delta=sig_delta or "-",
                        reason_codes=_reason_codes(
                            sig_changed=fast_sig_matches,
                            age_expired=fast_sig_fresh,
                            price_move=price_change_ok,
                            ws_stale=ws_fresh,
                            near_ai_exit=not near_ai_exit_band,
                            near_safe_profit=not near_safe_profit_band,
                            near_low_score=not near_low_score_band,
                        ),
                    )
                    sim_ai_budget_gate = _resolve_scalp_sim_ai_budget_decision(
                        stock,
                        strategy=strategy,
                        now_ts=now_ts,
                        profit_rate=profit_rate,
                        peak_profit=peak_profit,
                        held_sec=held_sec,
                        current_ai_score=current_ai_score,
                        market_signature=market_signature,
                        is_critical_zone=is_critical_zone,
                        near_ai_exit_band=near_ai_exit_band,
                        near_safe_profit_band=near_safe_profit_band,
                    )
                    sim_ai_budget_skip = bool(
                        sim_ai_budget_gate.get("target")
                        and sim_ai_budget_gate.get("action") in {"reuse", "defer"}
                    )
                    if sim_ai_budget_skip:
                        event_stage = (
                            "scalp_sim_ai_holding_reuse"
                            if sim_ai_budget_gate.get("action") == "reuse"
                            else "scalp_sim_ai_holding_deferred"
                        )
                        _mutate_stock_state(
                            stock,
                            set_fields={
                                "scalp_sim_ai_last_feature_signature": sim_ai_budget_gate.get("feature_signature"),
                                "scalp_sim_ai_last_reuse_at": now_ts
                                if event_stage == "scalp_sim_ai_holding_reuse"
                                else stock.get("scalp_sim_ai_last_reuse_at"),
                                "scalp_sim_ai_last_deferred_at": now_ts
                                if event_stage == "scalp_sim_ai_holding_deferred"
                                else stock.get("scalp_sim_ai_last_deferred_at"),
                            },
                        )
                        _log_holding_pipeline(
                            stock,
                            code,
                            event_stage,
                            **_scalp_sim_event_fields(
                                reuse_reason=sim_ai_budget_gate.get("reuse_reason"),
                                defer_reason=sim_ai_budget_gate.get("defer_reason"),
                                last_ai_action=sim_ai_budget_gate.get("last_ai_action"),
                                last_ai_score=sim_ai_budget_gate.get("last_ai_score"),
                                feature_signature=sim_ai_budget_gate.get("feature_signature"),
                                profit_rate=f"{profit_rate:+.2f}",
                                peak_profit=f"{peak_profit:+.2f}",
                                held_sec=int(held_sec),
                                source_stage="ai_holding_review",
                                decision_authority="sim_observation_only",
                                runtime_effect="sim_ai_reuse_only"
                                if event_stage == "scalp_sim_ai_holding_reuse"
                                else "sim_ai_deferred_review_only",
                                budget_used_per_min=sim_ai_budget_gate.get("budget_used_per_min"),
                                budget_cap_per_min=sim_ai_budget_gate.get("budget_cap_per_min"),
                                state_changed=sim_ai_budget_gate.get("state_changed"),
                                first_review=sim_ai_budget_gate.get("first_review"),
                                critical=sim_ai_budget_gate.get("critical"),
                            ),
                        )
                        if event_stage == "scalp_sim_ai_holding_deferred":
                            _log_holding_pipeline(
                                stock,
                                code,
                                "sim_ai_budget_exhausted",
                                **_scalp_sim_event_fields(
                                    defer_reason=sim_ai_budget_gate.get("defer_reason"),
                                    feature_signature=sim_ai_budget_gate.get("feature_signature"),
                                    profit_rate=f"{profit_rate:+.2f}",
                                    peak_profit=f"{peak_profit:+.2f}",
                                    held_sec=int(held_sec),
                                    source_stage="ai_holding_review",
                                    decision_authority="sim_observation_only",
                                    runtime_effect="sim_ai_deferred_review_only",
                                    budget_used_per_min=sim_ai_budget_gate.get("budget_used_per_min"),
                                    budget_cap_per_min=sim_ai_budget_gate.get("budget_cap_per_min"),
                                ),
                            )
                        persist_scalp_simulator_state()
                    elif sim_ai_budget_gate.get("target") and sim_ai_budget_gate.get("critical_bypass"):
                        _log_holding_pipeline(
                            stock,
                            code,
                            "sim_ai_critical_bypass",
                            **_scalp_sim_event_fields(
                                call_reason=sim_ai_budget_gate.get("call_reason"),
                                feature_signature=sim_ai_budget_gate.get("feature_signature"),
                                profit_rate=f"{profit_rate:+.2f}",
                                peak_profit=f"{peak_profit:+.2f}",
                                held_sec=int(held_sec),
                                source_stage="ai_holding_review",
                                decision_authority="sim_observation_only",
                                runtime_effect="sim_ai_live_call_allowed",
                                budget_used_per_min=sim_ai_budget_gate.get("budget_used_per_min"),
                                budget_cap_per_min=sim_ai_budget_gate.get("budget_cap_per_min"),
                            ),
                        )

                    ai_decision = {"action": "WAIT", "score": current_ai_score, "reason": "holding_ai_not_called"}
                    raw_ai_score = current_ai_score
                    ai_cache_hit = False
                    recent_ticks = [] if sim_ai_budget_skip else kiwoom_utils.get_tick_history_ka10003(
                        KIWOOM_TOKEN, code, limit=10
                    )
                    recent_candles = [] if sim_ai_budget_skip else kiwoom_utils.get_minute_candles_ka10080(
                        KIWOOM_TOKEN, code, limit=40
                    )

                    if (not sim_ai_budget_skip) and ws_data.get('orderbook') and recent_ticks:
                        if sim_ai_budget_gate.get("target"):
                            used_after_record = _record_scalp_sim_ai_budget_call(now_ts)
                        else:
                            used_after_record = None
                        ai_decision = ai_engine.analyze_target(
                            stock['name'],
                            ws_data,
                            recent_ticks,
                            recent_candles,
                            cache_profile="holding",
                            prompt_profile="holding",
                        )
                        raw_ai_score = ai_decision.get('score', 50)
                        ai_cache_hit = bool(ai_decision.get('cache_hit', False))

                        smoothed_score = int((current_ai_score * 0.6) + (raw_ai_score * 0.4))
                        _mutate_stock_state(
                            stock,
                            set_fields={
                                'rt_ai_prob': smoothed_score / 100.0,
                                'last_ai_profit': profit_rate,
                                'last_ai_reviewed_at': now_ts,
                                'last_ai_market_signature': market_signature,
                                'last_ai_market_snapshot': market_snapshot,
                                'last_ai_market_signature_at': now_ts,
                            },
                        )
                        current_ai_score = smoothed_score
                        if sim_ai_budget_gate.get("target"):
                            _mutate_stock_state(
                                stock,
                                set_fields={
                                    "scalp_sim_ai_last_feature_signature": sim_ai_budget_gate.get(
                                        "feature_signature"
                                    ),
                                    "scalp_sim_ai_last_action": ai_decision.get("action_v2")
                                    or ai_decision.get("action"),
                                    "scalp_sim_ai_last_score": raw_ai_score,
                                    "scalp_sim_ai_last_live_call_at": now_ts,
                                    "scalp_sim_ai_live_call_count": _safe_int(
                                        stock.get("scalp_sim_ai_live_call_count"), 0
                                    )
                                    + 1,
                                },
                            )
                            _log_holding_pipeline(
                                stock,
                                code,
                                "scalp_sim_ai_holding_live_call",
                                **_scalp_sim_event_fields(
                                    call_reason=sim_ai_budget_gate.get("call_reason"),
                                    feature_signature=sim_ai_budget_gate.get("feature_signature"),
                                    profit_rate=f"{profit_rate:+.2f}",
                                    peak_profit=f"{peak_profit:+.2f}",
                                    held_sec=int(held_sec),
                                    source_stage="ai_holding_review",
                                    decision_authority="sim_observation_only",
                                    runtime_effect="sim_ai_live_call_only",
                                    budget_used_per_min=used_after_record,
                                    budget_cap_per_min=sim_ai_budget_gate.get("budget_cap_per_min"),
                                    ai_action=ai_decision.get("action_v2") or ai_decision.get("action"),
                                    ai_score_raw=raw_ai_score,
                                    ai_score_smoothed=current_ai_score,
                                    ai_cache="hit" if ai_cache_hit else "miss",
                                ),
                            )
                            persist_scalp_simulator_state()

                    # reversal_add: 수급 피처 저장 및 STAGNATION 상태 갱신
                    if (not sim_ai_budget_skip) and _rule_bool('REVERSAL_ADD_ENABLED', False):
                        if hasattr(ai_engine, '_extract_scalping_features') and recent_ticks:
                            try:
                                feat = ai_engine._extract_scalping_features(ws_data, recent_ticks, recent_candles)
                                _mutate_stock_state(
                                    stock,
                                    set_fields={
                                        'last_reversal_features': {
                                            'buy_pressure_10t': feat.get('buy_pressure_10t', 50.0),
                                            'tick_acceleration_ratio': feat.get('tick_acceleration_ratio', 0.0),
                                            'large_sell_print_detected': feat.get('large_sell_print_detected', False),
                                            'curr_vs_micro_vwap_bp': feat.get('curr_vs_micro_vwap_bp', 0.0),
                                            'net_aggressive_delta_10t': feat.get('net_aggressive_delta_10t', 0),
                                            'same_price_buy_absorption': feat.get('same_price_buy_absorption', 0),
                                            'microprice_edge_bp': feat.get('microprice_edge_bp', 0.0),
                                            'top3_depth_ratio': feat.get('top3_depth_ratio', 999.0),
                                        },
                                    },
                                )
                            except Exception as exc:
                                log_error(f"⚠️ [REVERSAL_ADD] feature extract failed ({code}): {exc}")

                        # AI bottom/history 갱신 (STAGNATION/REVERSAL_CANDIDATE 구간에서만)
                        if stock.get('reversal_add_state') in ('STAGNATION', 'REVERSAL_CANDIDATE'):
                            _ra_hist = list(stock.get('reversal_add_ai_history', []))
                            _ra_hist.append(current_ai_score)
                            _mutate_stock_state(
                                stock,
                                set_fields={
                                    'reversal_add_ai_history': _ra_hist[-4:],
                                    'reversal_add_ai_bottom': min(
                                        int(stock.get('reversal_add_ai_bottom', 100)),
                                        current_ai_score,
                                    ),
                                    'reversal_add_profit_floor': min(
                                        float(stock.get('reversal_add_profit_floor', 0.0)),
                                        profit_rate,
                                    ),
                                },
                            )

                        # STAGNATION 진입 판단
                        _ra_pnl_min = _rule_float('REVERSAL_ADD_PNL_MIN', -0.45)
                        _ra_pnl_max = _rule_float('REVERSAL_ADD_PNL_MAX', -0.10)
                        if (not stock.get('reversal_add_state')
                                and _ra_pnl_min <= profit_rate <= _ra_pnl_max
                        ):
                            _mutate_stock_state(
                                stock,
                                set_fields={
                                    'reversal_add_state': 'STAGNATION',
                                    'reversal_add_profit_floor': profit_rate,
                                    'reversal_add_ai_bottom': current_ai_score,
                                    'reversal_add_ai_history': [current_ai_score],
                                },
                            )
                        # STAGNATION 리셋 조건
                        elif stock.get('reversal_add_state') == 'STAGNATION':
                            if profit_rate < _ra_pnl_min or profit_rate > 0:
                                _mutate_stock_state(
                                    stock,
                                    set_fields={
                                        'reversal_add_state': '',
                                        'reversal_add_profit_floor': 0.0,
                                        'reversal_add_ai_bottom': 100,
                                        'reversal_add_ai_history': [],
                                    },
                                )

                        # REVERSAL_CANDIDATE 전이 판단 (실행 직전 후보 상태)
                        _ra_state = stock.get('reversal_add_state', '')
                        if _ra_state in ('STAGNATION', 'REVERSAL_CANDIDATE'):
                            _ra_floor = float(stock.get('reversal_add_profit_floor', 0.0))
                            _ra_margin = _rule_float('REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN', 0.05)
                            _ra_min_ai = _rule_int('REVERSAL_ADD_MIN_AI_SCORE', 60)
                            _ra_min_hold = _rule_int('REVERSAL_ADD_MIN_HOLD_SEC', 20)
                            _ra_max_hold = _rule_int('REVERSAL_ADD_MAX_HOLD_SEC', 120)
                            _ra_bottom = int(stock.get('reversal_add_ai_bottom', 100))
                            _ra_recovery_delta = _rule_int('REVERSAL_ADD_MIN_AI_RECOVERY_DELTA', 15)
                            _ra_hist = list(stock.get('reversal_add_ai_history', []))
                            _ra_recovering_delta = (current_ai_score >= _ra_bottom + _ra_recovery_delta)
                            _ra_recovering_consec = (
                                len(_ra_hist) >= 2 and _ra_hist[-1] > _ra_hist[-2] and current_ai_score > _ra_hist[-1]
                            )

                            _ra_feat = stock.get('last_reversal_features', {})
                            if _ra_feat:
                                _ra_checks = [
                                    _ra_feat.get('buy_pressure_10t', 0) >= _rule_float('REVERSAL_ADD_MIN_BUY_PRESSURE', 55),
                                    _ra_feat.get('tick_acceleration_ratio', 0) >= _rule_float('REVERSAL_ADD_MIN_TICK_ACCEL', 0.95),
                                    not _ra_feat.get('large_sell_print_detected', True),
                                    _ra_feat.get('curr_vs_micro_vwap_bp', -999) >= _rule_float('REVERSAL_ADD_VWAP_BP_MIN', -5.0),
                                ]
                                _ra_supply_ok = sum(_ra_checks) >= 3
                            else:
                                _ra_bp = float(stock.get('last_reversal_features', {}).get('buy_pressure_10t', 50.0))
                                _ra_supply_ok = _ra_bp >= _rule_float('REVERSAL_ADD_MIN_BUY_PRESSURE', 55)

                            _ra_candidate_ok = (
                                (_ra_pnl_min <= profit_rate <= _ra_pnl_max)
                                and (_ra_min_hold <= held_sec <= _ra_max_hold)
                                and (profit_rate >= _ra_floor - _ra_margin)
                                and current_ai_score >= _ra_min_ai
                                and (_ra_recovering_delta or _ra_recovering_consec)
                                and _ra_supply_ok
                            )

                            if _ra_candidate_ok and _ra_state != 'REVERSAL_CANDIDATE':
                                _mutate_stock_state(stock, set_fields={'reversal_add_state': 'REVERSAL_CANDIDATE'})
                                _log_holding_pipeline(
                                    stock,
                                    code,
                                    "reversal_add_candidate",
                                    state="REVERSAL_CANDIDATE",
                                    reason="candidate_ready",
                                    profit_rate=f"{profit_rate:+.2f}",
                                    ai_score=f"{current_ai_score:.0f}",
                                )
                            elif (not _ra_candidate_ok) and _ra_state == 'REVERSAL_CANDIDATE':
                                _mutate_stock_state(stock, set_fields={'reversal_add_state': 'STAGNATION'})

                    if not sim_ai_budget_skip:
                        log_info(
                            f"👁️ [AI 보유감시: {stock['name']}] 수익: {profit_rate:+.2f}% | "
                            f"AI: {current_ai_score:.0f}점 | "
                            f"갱신주기: {dynamic_max_cd}초 | AI캐시: {'HIT' if ai_cache_hit else 'MISS'}"
                        )
                        _log_holding_pipeline(
                            stock,
                            code,
                            "ai_holding_review",
                            profit_rate=f"{profit_rate:+.2f}",
                            ai_score=f"{current_ai_score:.0f}",
                            held_sec=int(held_time_min * 60),
                            price_change=f"{price_change:.2f}",
                            review_cd_sec=dynamic_max_cd,
                            review_ms=int((time.perf_counter() - holding_ai_review_started) * 1000),
                            ai_cache="hit" if ai_cache_hit else "miss",
                            holding_review_trigger_reason="fast_reuse_bypass",
                            **_build_ai_ops_log_fields(
                                ai_decision,
                                ai_score_raw=raw_ai_score,
                                ai_score_after_bonus=current_ai_score,
                                ai_cooldown_blocked=False,
                            ),
                        )

            except Exception as e:
                log_info(f"🚨 [보유 AI 감시 에러] {stock['name']}({code}): {e}")
            finally:
                with ENTRY_LOCK:
                    LAST_AI_CALL_TIMES[code] = now_ts

    # ── reversal_add POST_ADD_EVAL 집중 감시 ──────────────────
    if not is_sell_signal and stock.get('reversal_add_state') == 'POST_ADD_EVAL':
        _ra_executed_at = float(stock.get('reversal_add_executed_at', 0))
        _ra_eval_sec = _rule_int('REVERSAL_ADD_POST_EVAL_SEC', 25)
        _ra_elapsed = now_ts - _ra_executed_at
        _ra_feat = stock.get('last_reversal_features', {})
        _ra_floor = float(stock.get('reversal_add_profit_floor', -1.0))
        _ra_post_fail = (
            current_ai_score < 55
            or profit_rate < _ra_floor - 0.05
            or _ra_feat.get('large_sell_print_detected', False)
            or _ra_feat.get('tick_acceleration_ratio', 1.0) < 0.90
        )
        if _ra_post_fail and _ra_elapsed < _ra_eval_sec:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🚨 reversal_add POST_EVAL 실패 "
                f"(AI:{current_ai_score:.0f}, profit:{profit_rate:.2f}%, "
                f"elapsed:{_ra_elapsed:.0f}s)"
            )
            exit_rule = "reversal_add_post_eval_fail"
        elif _ra_elapsed >= _ra_eval_sec:
            _mutate_stock_state(stock, set_fields={'reversal_add_state': ''})

    if hard_stop_price > 0 and curr_p <= hard_stop_price:
        is_sell_signal = True
        sell_reason_type = "LOSS"
        reason = f"🛑 보호 하드스탑 이탈 ({hard_stop_price:,.0f}원)"
        exit_rule = "protect_hard_stop"

    elif trailing_stop_price > 0 and curr_p <= trailing_stop_price:
        if _protect_trailing_break_confirmed(
            stock,
            code,
            now_ts=now_ts,
            curr_price=curr_p,
            trailing_stop_price=trailing_stop_price,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
        ):
            is_sell_signal = True
            sell_reason_type = "TRAILING"
            reason = f"🔥 보호 트레일링 이탈 ({trailing_stop_price:,.0f}원)"
            exit_rule = "protect_trailing_stop"

    elif strategy == 'SCALPING':
        base_stop_pct = _rule_float('SCALP_STOP', -1.5)
        hard_stop_pct = _rule_float('SCALP_HARD_STOP', -2.5)
        safe_profit_pct = _rule_float('SCALP_SAFE_PROFIT', 0.5)
        open_reclaim_peak_max_pct = _rule_float('SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT', 0.20)
        open_reclaim_hold_sec = _rule_int('SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC', 300)
        open_reclaim_score_buffer = _rule_int('SCALP_OPEN_RECLAIM_NEAR_AI_EXIT_SCORE_BUFFER', 5)
        open_reclaim_retrace_sustain_sec = _rule_int(
            'SCALP_OPEN_RECLAIM_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC', 120
        )
        scanner_fallback_peak_max_pct = _rule_float('SCALP_SCANNER_FALLBACK_NEVER_GREEN_PEAK_MAX_PCT', 0.20)
        scanner_fallback_hold_sec = _rule_int('SCALP_SCANNER_FALLBACK_NEVER_GREEN_HOLD_SEC', 420)
        scanner_fallback_score_buffer = _rule_int('SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SCORE_BUFFER', 8)
        scanner_fallback_near_ai_exit_sustain_sec = _rule_int(
            'SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SUSTAIN_SEC', 120
        )
        scanner_fallback_retrace_sustain_sec = _rule_int(
            'SCALP_SCANNER_FALLBACK_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC', 150
        )
        if highest_prices.get(price_key, 0) > 0:
            drawdown = (highest_prices[price_key] - curr_p) / highest_prices[price_key] * 100
        else:
            drawdown = 0

        soft_stop_pct = max(base_stop_pct, hard_stop_pct)
        hard_stop_pct = min(base_stop_pct, hard_stop_pct)
        if current_ai_score >= 75:
            dynamic_stop_pct = max(soft_stop_pct - 1.0, hard_stop_pct)
            dynamic_trailing_limit = _rule_float('SCALP_TRAILING_LIMIT_STRONG', 0.8)
        else:
            dynamic_stop_pct = soft_stop_pct
            dynamic_trailing_limit = _rule_float('SCALP_TRAILING_LIMIT_WEAK', 0.4)
        if profit_rate > dynamic_stop_pct:
            if stock.get('soft_stop_absorption_extension_used'):
                _log_holding_pipeline(
                    stock,
                    code,
                    "soft_stop_absorption_recovered",
                    profit_rate=f"{profit_rate:+.2f}",
                    soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                    current_ai_score=f"{current_ai_score:.0f}",
                    held_sec=int(held_time_min * 60),
                )
            _mutate_stock_state(
                stock,
                pop_fields=(
                    'soft_stop_micro_grace_started_at',
                    'soft_stop_micro_grace_extension_used',
                    'soft_stop_absorption_extension_started_at',
                    'soft_stop_absorption_extension_used',
                    'soft_stop_absorption_extension_count',
                    '_soft_stop_expert_shadow_logged_key',
                ),
            )
        _observe_bad_entry_block_candidate(
            stock,
            code,
            strategy=strategy,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
            now_ts=now_ts,
        )
        bad_entry_refined_decision = _build_bad_entry_refined_decision(
            stock,
            strategy=strategy,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
            dynamic_stop_pct=dynamic_stop_pct,
            hard_stop_pct=hard_stop_pct,
        )
        _emit_bad_entry_refined_candidate(
            stock,
            code,
            decision=bad_entry_refined_decision,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
        )

        open_reclaim_near_ai_exit = (
            profit_rate <= near_ai_exit_min_loss_pct
            and current_ai_score <= (near_ai_exit_score_limit + open_reclaim_score_buffer)
        )
        scanner_fallback_near_ai_exit = (
            profit_rate <= near_ai_exit_min_loss_pct
            and current_ai_score <= (near_ai_exit_score_limit + scanner_fallback_score_buffer)
        )
        default_near_ai_exit = (
            profit_rate <= near_ai_exit_min_loss_pct
            and current_ai_score <= near_ai_exit_score_limit
        )
        open_reclaim_near_ai_exit_sustain_sec = _update_boolean_sustain_sec(
            stock,
            key='open_reclaim_near_ai_exit_started_at',
            active=open_reclaim_near_ai_exit,
            now_ts=now_ts,
        )
        scanner_fallback_near_ai_exit_sustain_runtime_sec = _update_boolean_sustain_sec(
            stock,
            key='near_ai_exit_started_at',
            active=scanner_fallback_near_ai_exit,
            now_ts=now_ts,
        )
        _update_boolean_sustain_sec(
            stock,
            key='generic_near_ai_exit_started_at',
            active=default_near_ai_exit,
            now_ts=now_ts,
        )

        if legacy_broker_recovered:
            _mutate_stock_state(stock, set_fields={'last_exit_guard_reason': 'broker_recovered_legacy'})
        elif profit_rate <= hard_stop_pct:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 하드스탑 도달 ({hard_stop_pct}%) [AI: {current_ai_score:.0f}]"
            exit_rule = "scalp_hard_stop_pct"

        elif (
            _should_revert_overnight_flow_override_hold(stock, profit_rate, now_t)
        ):
            overnight_candidate_profit = _safe_float(stock.get("overnight_flow_override_candidate_profit"), profit_rate)
            overnight_worsen_pct = max(
                0.0,
                _safe_float(
                    stock.get("overnight_flow_override_worsen_pct"),
                    _rule_float("HOLDING_FLOW_OVERRIDE_WORSEN_PCT", 0.80),
                ),
            )
            overnight_worsen = overnight_candidate_profit - float(profit_rate or 0.0)
            is_sell_signal = True
            sell_reason_type = "LOSS" if profit_rate < 0 else "TRAILING"
            reason = (
                f"🌙 오버나이트 flow 보류 후 추가악화 "
                f"({overnight_worsen:.2f}%p >= {overnight_worsen_pct:.2f}%p)"
            )
            exit_rule = "overnight_flow_worsen_revert"
            _log_holding_pipeline(
                stock,
                code,
                "overnight_flow_override_revert_sell_today",
                exit_rule=exit_rule,
                profit_rate=f"{profit_rate:+.2f}",
                candidate_profit=f"{overnight_candidate_profit:+.2f}",
                worsen_from_candidate=f"{overnight_worsen:.2f}",
                worsen_pct=f"{overnight_worsen_pct:.2f}",
            )

        elif bad_entry_refined_decision.get("should_exit"):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 refined bad_entry 조기정리 "
                f"(hold={held_sec}s, peak={peak_profit:.2f}%, ai={current_ai_score:.0f}, "
                f"recovery={bad_entry_refined_decision.get('recovery_prob_shadow', 0.0):.3f})"
            )
            exit_rule = "scalp_bad_entry_refined_canary"
            _log_holding_pipeline(
                stock,
                code,
                "bad_entry_refined_exit",
                decision_source="BAD_ENTRY_REFINED_CANARY",
                threshold_family="bad_entry_refined_canary",
                threshold_version=str(
                    _rule("SCALP_BAD_ENTRY_REFINED_THRESHOLD_VERSION", "runtime_default") or "runtime_default"
                ),
                threshold_calibration_state=str(
                    _rule("SCALP_BAD_ENTRY_REFINED_CALIBRATION_STATE", "runtime_default") or "runtime_default"
                ),
                threshold_applied_value=(
                    f"enabled=True|min_hold={bad_entry_refined_decision.get('min_hold_sec', '-')}|"
                    f"min_loss={bad_entry_refined_decision.get('min_loss_pct', 0.0):+.2f}|"
                    f"recovery_max={bad_entry_refined_decision.get('recovery_prob_max', 0.0):.3f}"
                ),
                exit_rule=exit_rule,
                classifier="never_green_ai_fade_refined",
                profit_rate=f"{profit_rate:+.2f}",
                peak_profit=f"{peak_profit:+.2f}",
                current_ai_score=f"{current_ai_score:.0f}",
                held_sec=held_sec,
                thesis_invalidated=bool(bad_entry_refined_decision.get("thesis_invalidated")),
                adverse_fill=bool(bad_entry_refined_decision.get("adverse_fill")),
                absorption_score=bad_entry_refined_decision.get("absorption_score", 0),
                recovery_prob_shadow=f"{bad_entry_refined_decision.get('recovery_prob_shadow', 0.0):.3f}",
            )

        elif profit_rate <= dynamic_stop_pct:
            soft_stop_grace_enabled = _rule_bool(
                'SCALP_SOFT_STOP_MICRO_GRACE_ENABLED', False
            )
            soft_stop_grace_sec = _rule_int(
                'SCALP_SOFT_STOP_MICRO_GRACE_SEC', 0
            )
            soft_stop_grace_extend_enabled = _rule_bool(
                'SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_ENABLED', False
            )
            soft_stop_grace_extend_sec = _rule_int(
                'SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_SEC', 0
            )
            soft_stop_grace_extend_buffer_pct = max(
                0.0,
                _rule_float('SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_BUFFER_PCT', 0.0),
            )
            soft_stop_emergency_pct = min(
                float(
                    _rule(
                        'SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT',
                        dynamic_stop_pct - 0.5,
                    )
                    or (dynamic_stop_pct - 0.5)
                ),
                float(dynamic_stop_pct),
            )
            soft_stop_grace_started_at = float(stock.get('soft_stop_micro_grace_started_at', 0.0) or 0.0)
            if soft_stop_grace_started_at <= 0:
                soft_stop_grace_started_at = now_ts
                _mutate_stock_state(
                    stock,
                    set_fields={'soft_stop_micro_grace_started_at': soft_stop_grace_started_at},
                )
            soft_stop_grace_elapsed_sec = max(0, int(now_ts - soft_stop_grace_started_at))
            soft_stop_within_grace = (
                soft_stop_grace_enabled
                and soft_stop_grace_sec > 0
                and soft_stop_grace_elapsed_sec < soft_stop_grace_sec
                and profit_rate > soft_stop_emergency_pct
            )
            soft_stop_extension_within_grace = (
                soft_stop_grace_enabled
                and soft_stop_grace_extend_enabled
                and soft_stop_grace_extend_sec > 0
                and soft_stop_grace_elapsed_sec < (soft_stop_grace_sec + soft_stop_grace_extend_sec)
                and profit_rate > soft_stop_emergency_pct
                and profit_rate >= (float(dynamic_stop_pct) - soft_stop_grace_extend_buffer_pct)
            )
            if soft_stop_extension_within_grace and soft_stop_grace_elapsed_sec >= soft_stop_grace_sec:
                _mutate_stock_state(
                    stock,
                    set_fields={'soft_stop_micro_grace_extension_used': True},
                )
            soft_stop_within_grace = soft_stop_within_grace or soft_stop_extension_within_grace
            soft_stop_expert_decision = _build_soft_stop_expert_decision(
                stock,
                now_ts=now_ts,
                profit_rate=profit_rate,
                peak_profit=peak_profit,
                current_ai_score=current_ai_score,
                held_sec=held_sec,
                curr_price=curr_p,
                dynamic_stop_pct=dynamic_stop_pct,
                emergency_pct=soft_stop_emergency_pct,
                grace_elapsed_sec=soft_stop_grace_elapsed_sec,
                grace_sec=soft_stop_grace_sec,
            )
            if soft_stop_expert_decision.get("active_after_time_gate"):
                _emit_soft_stop_expert_observations(
                    stock,
                    code,
                    decision=soft_stop_expert_decision,
                    profit_rate=profit_rate,
                    peak_profit=peak_profit,
                    dynamic_stop_pct=dynamic_stop_pct,
                    current_ai_score=current_ai_score,
                    held_sec=held_sec,
                )
            if (
                soft_stop_expert_decision.get("enabled")
                and soft_stop_expert_decision.get("active_after_time_gate")
                and soft_stop_grace_elapsed_sec >= soft_stop_grace_sec
            ):
                _log_holding_pipeline(
                    stock,
                    code,
                    "soft_stop_absorption_probe",
                    profit_rate=f"{profit_rate:+.2f}",
                    soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                    emergency_pct=f"{soft_stop_emergency_pct:+.2f}",
                    elapsed_sec=soft_stop_grace_elapsed_sec,
                    absorption_score=soft_stop_expert_decision.get("absorption_score", 0),
                    min_score=soft_stop_expert_decision.get("min_score", 3),
                    thesis_invalidated=bool(soft_stop_expert_decision.get("thesis_invalidated")),
                    thesis_reason=soft_stop_expert_decision.get("thesis_reason", "-"),
                    exclusion_reason=soft_stop_expert_decision.get("exclusion_reason", "-"),
                    should_extend=bool(soft_stop_expert_decision.get("should_extend")),
                    recovery_prob_shadow=f"{soft_stop_expert_decision.get('recovery_prob_shadow', 0.0):.3f}",
                    hierarchy="stop_arbitration|thesis_invalidation|orderbook_absorption",
                )
            soft_stop_expert_within_grace = False
            if soft_stop_expert_decision.get("should_extend") and not soft_stop_within_grace:
                expert_started_at = float(
                    stock.get('soft_stop_absorption_extension_started_at', 0.0) or 0.0
                )
                expert_extension_sec = _safe_int(soft_stop_expert_decision.get("extension_sec"), 0)
                if expert_started_at <= 0:
                    expert_started_at = now_ts
                    expert_extension_count = _safe_int(
                        stock.get('soft_stop_absorption_extension_count'), 0
                    ) + 1
                    _mutate_stock_state(
                        stock,
                        set_fields={
                            'soft_stop_absorption_extension_started_at': expert_started_at,
                            'soft_stop_absorption_extension_used': True,
                            'soft_stop_absorption_extension_count': expert_extension_count,
                            'soft_stop_micro_grace_extension_used': True,
                        },
                    )
                expert_elapsed_sec = max(0, int(now_ts - expert_started_at))
                soft_stop_expert_within_grace = expert_extension_sec > 0 and expert_elapsed_sec < expert_extension_sec
                if soft_stop_expert_within_grace:
                    _log_holding_pipeline(
                        stock,
                        code,
                        "soft_stop_absorption_extend",
                        profit_rate=f"{profit_rate:+.2f}",
                        soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                        emergency_pct=f"{soft_stop_emergency_pct:+.2f}",
                        elapsed_sec=soft_stop_grace_elapsed_sec,
                        expert_elapsed_sec=expert_elapsed_sec,
                        extension_sec=expert_extension_sec,
                        absorption_score=soft_stop_expert_decision.get("absorption_score", 0),
                        thesis_invalidated=bool(soft_stop_expert_decision.get("thesis_invalidated")),
                        recovery_prob_shadow=f"{soft_stop_expert_decision.get('recovery_prob_shadow', 0.0):.3f}",
                    )
            if (
                soft_stop_expert_decision.get("enabled")
                and soft_stop_expert_decision.get("active_after_time_gate")
                and soft_stop_grace_elapsed_sec >= soft_stop_grace_sec
                and not soft_stop_within_grace
                and not soft_stop_expert_within_grace
            ):
                _log_holding_pipeline(
                    stock,
                    code,
                    "soft_stop_absorption_exit",
                    profit_rate=f"{profit_rate:+.2f}",
                    soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                    exclusion_reason=soft_stop_expert_decision.get("exclusion_reason", "-"),
                    thesis_invalidated=bool(soft_stop_expert_decision.get("thesis_invalidated")),
                    absorption_score=soft_stop_expert_decision.get("absorption_score", 0),
                    exit_rule_candidate="scalp_soft_stop_pct",
                )
            soft_stop_within_grace = soft_stop_within_grace or soft_stop_expert_within_grace
            whipsaw_decision = _build_soft_stop_whipsaw_confirmation_decision(
                stock,
                now_ts=now_ts,
                profit_rate=profit_rate,
                dynamic_stop_pct=dynamic_stop_pct,
                emergency_pct=soft_stop_emergency_pct,
                grace_elapsed_sec=soft_stop_grace_elapsed_sec,
                grace_sec=soft_stop_grace_sec,
                curr_price=curr_p,
                buy_price=buy_p,
            )
            if whipsaw_decision.get("should_confirm") and not soft_stop_within_grace:
                if _safe_float(whipsaw_decision.get("started_at"), 0.0) <= 0:
                    _mutate_stock_state(
                        stock,
                        set_fields={
                            "soft_stop_whipsaw_confirmation_started_at": now_ts,
                            "soft_stop_whipsaw_confirmation_touch_price": int(curr_p or 0),
                            "soft_stop_micro_grace_extension_used": True,
                        },
                    )
                    whipsaw_decision = dict(whipsaw_decision)
                    whipsaw_decision["started_at"] = now_ts
                    whipsaw_decision["touch_price"] = int(curr_p or 0)
                soft_stop_within_grace = True
                _log_holding_pipeline(
                    stock,
                    code,
                    "soft_stop_whipsaw_confirmation",
                    profit_rate=f"{profit_rate:+.2f}",
                    soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                    emergency_pct=f"{soft_stop_emergency_pct:+.2f}",
                    elapsed_sec=soft_stop_grace_elapsed_sec,
                    confirmation_elapsed_sec=int(whipsaw_decision.get("elapsed_sec", 0) or 0),
                    confirmation_sec=int(whipsaw_decision.get("confirm_sec", 0) or 0),
                    buffer_pct=f"{float(whipsaw_decision.get('buffer_pct', 0.0) or 0.0):.2f}",
                    max_worsen_pct=f"{float(whipsaw_decision.get('max_worsen_pct', 0.0) or 0.0):.2f}",
                    additional_worsen=f"{float(whipsaw_decision.get('additional_worsen', 0.0) or 0.0):.2f}",
                    rebound_above_sell=bool(whipsaw_decision.get("rebound_above_sell")),
                    rebound_above_buy=bool(whipsaw_decision.get("rebound_above_buy")),
                    threshold_family=whipsaw_decision.get("threshold_family", "soft_stop_whipsaw_confirmation"),
                    threshold_version=whipsaw_decision.get("threshold_version", "runtime_default"),
                    threshold_calibration_state=whipsaw_decision.get(
                        "threshold_calibration_state", "runtime_default"
                    ),
                    threshold_applied_value=whipsaw_decision.get("threshold_applied_value", "-"),
                    flow_state=stock.get("holding_flow_override_state", "-"),
                    exit_rule_candidate="scalp_soft_stop_pct",
                )
            elif whipsaw_decision.get("expired"):
                _mutate_stock_state(
                    stock,
                    set_fields={"soft_stop_whipsaw_confirmation_used": True},
                )
                _log_holding_pipeline(
                    stock,
                    code,
                    "soft_stop_whipsaw_confirmation_expired",
                    profit_rate=f"{profit_rate:+.2f}",
                    soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                    confirmation_elapsed_sec=int(whipsaw_decision.get("elapsed_sec", 0) or 0),
                    confirmation_sec=int(whipsaw_decision.get("confirm_sec", 0) or 0),
                    additional_worsen=f"{float(whipsaw_decision.get('additional_worsen', 0.0) or 0.0):.2f}",
                    rebound_above_sell=bool(whipsaw_decision.get("rebound_above_sell")),
                    rebound_above_buy=bool(whipsaw_decision.get("rebound_above_buy")),
                    threshold_family=whipsaw_decision.get("threshold_family", "soft_stop_whipsaw_confirmation"),
                    threshold_version=whipsaw_decision.get("threshold_version", "runtime_default"),
                    threshold_calibration_state=whipsaw_decision.get(
                        "threshold_calibration_state", "runtime_default"
                    ),
                    threshold_applied_value=whipsaw_decision.get("threshold_applied_value", "-"),
                    exit_rule_candidate="scalp_soft_stop_pct",
                )
            if soft_stop_within_grace:
                _log_holding_pipeline(
                    stock,
                    code,
                    "soft_stop_micro_grace",
                    profit_rate=f"{profit_rate:+.2f}",
                    soft_stop_pct=f"{dynamic_stop_pct:+.2f}",
                    emergency_pct=f"{soft_stop_emergency_pct:+.2f}",
                    elapsed_sec=soft_stop_grace_elapsed_sec,
                    grace_sec=soft_stop_grace_sec,
                    extension_enabled=soft_stop_grace_extend_enabled,
                    extension_sec=soft_stop_grace_extend_sec,
                    extension_buffer_pct=f"{soft_stop_grace_extend_buffer_pct:+.2f}",
                    extension_used=bool(stock.get('soft_stop_micro_grace_extension_used')),
                    expert_defense_enabled=bool(soft_stop_expert_decision.get("enabled")),
                    expert_defense_active=bool(soft_stop_expert_within_grace),
                    expert_exclusion_reason=soft_stop_expert_decision.get("exclusion_reason", "-"),
                    absorption_score=soft_stop_expert_decision.get("absorption_score", 0),
                    recovery_prob_shadow=f"{soft_stop_expert_decision.get('recovery_prob_shadow', 0.0):.3f}",
                    current_ai_score=f"{current_ai_score:.0f}",
                    held_sec=int(held_time_min * 60),
                    exit_rule_candidate="scalp_soft_stop_pct",
                    **_build_observation_contract_fields("ops_volume_diagnostic"),
                )
            else:
                is_sell_signal = True
                sell_reason_type = "LOSS"
                reason = f"🔪 소프트 손절 ({dynamic_stop_pct}%) [AI: {current_ai_score:.0f}]"
                exit_rule = "scalp_soft_stop_pct"

        elif (
            not legacy_broker_recovered
            and
            pos_tag == 'OPEN_RECLAIM'
            and held_sec >= open_reclaim_hold_sec
            and peak_profit <= open_reclaim_peak_max_pct
            and profit_rate <= near_ai_exit_min_loss_pct
            and current_ai_score <= (near_ai_exit_score_limit + open_reclaim_score_buffer)
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 OPEN_RECLAIM never-green 조기정리 "
                f"(hold={held_sec}s, peak={peak_profit:.2f}%, ai={current_ai_score:.0f})"
            )
            exit_rule = "scalp_open_reclaim_never_green"

        elif (
            not legacy_broker_recovered
            and
            pos_tag == 'OPEN_RECLAIM'
            and held_sec >= open_reclaim_hold_sec
            and peak_profit > open_reclaim_peak_max_pct
            and open_reclaim_near_ai_exit_sustain_sec >= open_reclaim_retrace_sustain_sec
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 OPEN_RECLAIM 양전환 후 재약세 정리 "
                f"(hold={held_sec}s, near_ai_exit={open_reclaim_near_ai_exit_sustain_sec}s, peak={peak_profit:.2f}%)"
            )
            exit_rule = "scalp_open_reclaim_retrace_exit"

        elif (
            not legacy_broker_recovered
            and
            pos_tag == 'SCANNER'
            and str(stock.get('entry_mode', '')).strip().lower() == 'fallback'
            and held_sec >= scanner_fallback_hold_sec
            and peak_profit <= scanner_fallback_peak_max_pct
            and scanner_fallback_near_ai_exit_sustain_runtime_sec >= scanner_fallback_near_ai_exit_sustain_sec
            and current_ai_score <= (near_ai_exit_score_limit + scanner_fallback_score_buffer)
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 SCANNER fallback 지연손절 보정 "
                f"(hold={held_sec}s, near_ai_exit={scanner_fallback_near_ai_exit_sustain_runtime_sec}s, peak={peak_profit:.2f}%)"
            )
            exit_rule = "scalp_scanner_fallback_never_green"

        elif (
            not legacy_broker_recovered
            and
            pos_tag == 'SCANNER'
            and str(stock.get('entry_mode', '')).strip().lower() == 'fallback'
            and held_sec >= scanner_fallback_hold_sec
            and peak_profit > scanner_fallback_peak_max_pct
            and scanner_fallback_near_ai_exit_sustain_runtime_sec >= scanner_fallback_retrace_sustain_sec
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 SCANNER fallback 양전환 후 재약세 정리 "
                f"(hold={held_sec}s, near_ai_exit={scanner_fallback_near_ai_exit_sustain_runtime_sec}s, peak={peak_profit:.2f}%)"
            )
            exit_rule = "scalp_scanner_fallback_retrace_exit"

        elif profit_rate >= safe_profit_pct:
            if current_ai_score < momentum_decay_score_limit and held_sec >= momentum_decay_min_hold_sec:
                is_sell_signal = True
                sell_reason_type = "MOMENTUM_DECAY"
                reason = (
                    f"🤖 AI 틱 가속도 둔화 ({current_ai_score:.0f}점). "
                    f"확인유예({momentum_decay_min_hold_sec}s) 후 익절 (+{profit_rate:.2f}%)"
                )
                exit_rule = "scalp_ai_momentum_decay"

            elif drawdown >= dynamic_trailing_limit:
                in_pyramid_trailing_grace, _, _ = _pyramid_post_add_trailing_grace(stock, now_ts)
                if in_pyramid_trailing_grace:
                    _log_pyramid_post_add_trailing_grace(
                        stock,
                        code,
                        now_ts=now_ts,
                        exit_rule_candidate="scalp_trailing_take_profit",
                        profit_rate=profit_rate,
                        peak_profit=peak_profit,
                        drawdown=drawdown,
                    )
                else:
                    is_sell_signal = True
                    sell_reason_type = "TRAILING"
                    reason = f"🔥 고점 대비 밀림 (-{drawdown:.2f}%). 트레일링 익절 (+{profit_rate:.2f}%)"
                    exit_rule = "scalp_trailing_take_profit"

    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            kosdaq_holding_days = _rule_int('KOSDAQ_HOLDING_DAYS', 2)
            if np.busday_count(buy_date, datetime.now().date()) >= kosdaq_holding_days:
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
                exit_rule = "kosdaq_timeout"
        except Exception as exc:
            log_error(f"[KOSDAQ_TIMEOUT] holding 기간 파싱 실패 ({stock.get('code', '-')}, date={stock.get('date')}) ({exc})")

        kosdaq_target = _rule_float('KOSDAQ_TARGET', 4.0)
        if not is_sell_signal and peak_profit >= kosdaq_target:
            # Follow-up tracked in checklist: SwingTrailingPolicy0506
            drawdown = (highest_prices.get(price_key, curr_p) - curr_p) / max(highest_prices.get(price_key, curr_p), 1) * 100
            if drawdown >= 1.0:
                is_sell_signal = True
                sell_reason_type = "TRAILING"
                reason = (
                    "🏆 KOSDAQ 트레일링 익절 (+"
                    f"{kosdaq_target}% 돌파 후 하락)"
                )
                exit_rule = "kosdaq_trailing_take_profit"

        kosdaq_stop = _rule_float('KOSDAQ_STOP', -2.0)
        if not is_sell_signal and profit_rate <= kosdaq_stop:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({kosdaq_stop}%)"
            exit_rule = "kosdaq_stop_loss"

    elif strategy == 'KOSPI_ML':
        pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
        if pos_tag == 'BREAKOUT':
            current_stop_loss = _rule_float('STOP_LOSS_BREAKOUT', -2.5)
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = _rule_float('STOP_LOSS_BOTTOM', -2.5)
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = (
                _rule_float('STOP_LOSS_BULL', -2.5)
                if market_regime == 'BULL'
                else _rule_float('STOP_LOSS_BEAR', -2.5)
            )
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            holding_days = _rule_int('HOLDING_DAYS', 3)
            if np.busday_count(buy_date, datetime.now().date()) >= holding_days:
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = f"⏳ {holding_days}일 스윙 보유 만료"
                exit_rule = "kospi_timeout"
        except Exception as exc:
            log_error(f"[KOSPI_TIMEOUT] holding 기간 파싱 실패 ({stock.get('code', '-')}, date={stock.get('date')}) ({exc})")

        # Follow-up tracked in checklist: SwingTrailingPolicy0506
        # 현재 로직은 해당 임계 도달 시 즉시 익절로 동작
        trailing_start_pct = _rule_float('TRAILING_START_PCT', 2.0)
        if not is_sell_signal and profit_rate >= trailing_start_pct:
            is_sell_signal = True
            sell_reason_type = "PROFIT"
            reason = (
                f"🎯 트레일링 시작 수익률 도달 (+{trailing_start_pct}%) "
                "(현 로직: 즉시 익절)"
            )
            exit_rule = "kospi_trailing_start_take_profit"

        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"
            exit_rule = "kospi_regime_stop_loss"

    if not is_sell_signal:
        _clear_holding_flow_override_candidate(
            stock,
            code,
            reason="exit_candidate_resolved",
            profit_rate=profit_rate,
        )

    if is_sell_signal:
        if not _evaluate_holding_flow_override(
            stock=stock,
            code=code,
            strategy=strategy,
            ws_data=ws_data,
            ai_engine=ai_engine,
            exit_rule=exit_rule,
            sell_reason_type=sell_reason_type,
            reason=reason,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            drawdown=_safe_float(locals().get("drawdown"), 0.0),
            current_ai_score=current_ai_score,
            held_sec=held_sec,
            curr_price=curr_p,
            buy_price=buy_p,
            now_ts=now_ts,
        ):
            return

        fallback_gate = None
        fallback_action = None
        fallback_candidate = False
        if sell_reason_type == "LOSS" and strategy == "SCALPING":
            fallback_gate = can_consider_scale_in(
                stock=stock,
                code=code,
                ws_data=ws_data,
                strategy=strategy,
                market_regime=market_regime,
            )
            fallback_action = None
            if fallback_gate.get("allowed"):
                fallback_action = _evaluate_scale_in_signal(
                    stock=stock,
                    code=code,
                    strategy=strategy,
                    market_regime=market_regime,
                    profit_rate=profit_rate,
                    peak_profit=peak_profit,
                    curr_price=curr_p,
                    ws_data=ws_data,
                    current_ai_score=current_ai_score,
                    held_sec=held_sec,
                )
            allowed_reasons = set(
                str(item).strip()
                for item in (_rule("SCALP_LOSS_FALLBACK_ALLOWED_REASONS", ("reversal_add_ok",)) or ())
                if str(item).strip()
            )
            min_fallback_ai = _rule_int("SCALP_LOSS_FALLBACK_MIN_AI_SCORE", 65)
            fallback_reason = str((fallback_action or {}).get("reason") or "")
            fallback_candidate = bool(
                fallback_action
                and (not allowed_reasons or fallback_reason in allowed_reasons)
                and float(current_ai_score or 0.0) >= float(min_fallback_ai)
            )
            _log_holding_pipeline(
                stock,
                code,
                "loss_fallback_probe",
                gate_allowed=bool(fallback_gate.get("allowed")),
                gate_reason=fallback_gate.get("reason", "-"),
                fallback_candidate=fallback_candidate,
                fallback_reason=fallback_reason or "-",
                fallback_add_type=(fallback_action or {}).get("add_type", "-"),
                current_ai_score=f"{current_ai_score:.0f}",
                min_ai=min_fallback_ai,
                profit_rate=f"{profit_rate:+.2f}",
                peak_profit=f"{peak_profit:+.2f}",
            )
            if fallback_candidate:
                observe_only = _rule_bool("SCALP_LOSS_FALLBACK_OBSERVE_ONLY", True)
                enabled = _rule_bool("SCALP_LOSS_FALLBACK_ENABLED", False)
                if enabled and not observe_only:
                    log_info(
                        f"[LOSS_FALLBACK] {stock.get('name')}({code}) "
                        f"candidate accepted: reason={fallback_reason}, ai={current_ai_score:.0f}"
                    )
                    add_result = _process_scale_in_action(
                        stock=stock,
                        code=code,
                        ws_data=ws_data,
                        action=fallback_action,
                        admin_id=admin_id,
                    )
                    if add_result:
                        log_info(
                            f"[LOSS_FALLBACK] {stock.get('name')}({code}) "
                            "fallback 추가매수 체결 경로로 전환, 손절 전송을 건너뜁니다."
                        )
                        return

        rejected_actions = []
        if fallback_gate and not fallback_candidate:
            rejected_actions.append(f"avg_down_wait:{fallback_gate.get('reason') or fallback_reason or 'not_candidate'}")

        if strategy == "SCALPING" and now_t >= TIME_15_30:
            block_key = f"{exit_rule or '-'}:{sell_reason_type or '-'}:{now_dt.date().isoformat()}"
            if stock.get("_market_closed_sell_block_key") != block_key:
                exit_decision_source = _resolve_exit_decision_source(
                    stock=stock,
                    exit_rule=exit_rule,
                    reason=reason,
                )
                _mutate_stock_state(
                    stock,
                    set_fields={
                        "_market_closed_sell_block_key": block_key,
                        "market_closed_sell_pending": True,
                        "market_closed_sell_exit_rule": exit_rule or "-",
                        "market_closed_sell_exit_decision_source": exit_decision_source,
                        "last_exit_reason": reason,
                    },
                )
                _remember_exit_context(
                    stock=stock,
                    exit_rule=exit_rule,
                    reason=reason,
                    peak_profit=peak_profit,
                    held_sec=int(held_time_min * 60),
                    current_ai_score=current_ai_score,
                    soft_stop_threshold_pct=dynamic_stop_pct if str(exit_rule or "").strip() == "scalp_soft_stop_pct" else None,
                )
                _emit_stat_action_decision_snapshot(
                    stock=stock,
                    code=code,
                    strategy=strategy,
                    ws_data=ws_data,
                    chosen_action="hold_wait",
                    eligible_actions=["hold_wait"],
                    rejected_actions=["exit_now:market_closed"],
                    profit_rate=profit_rate,
                    peak_profit=peak_profit,
                    current_ai_score=current_ai_score,
                    held_sec=held_sec,
                    curr_price=curr_p,
                    buy_price=buy_p,
                    exit_rule=exit_rule or "-",
                    sell_reason_type=sell_reason_type or "-",
                    scale_in_gate=fallback_gate,
                    scale_in_action=fallback_action,
                    reason="market_closed_sell_block",
                    force=True,
                )
                _log_holding_pipeline(
                    stock,
                    code,
                    "sell_order_blocked_market_closed",
                    sell_reason_type=sell_reason_type,
                    exit_rule=exit_rule or "-",
                    exit_decision_source=exit_decision_source,
                    status=stock.get("status", "-"),
                    profit_rate=f"{profit_rate:+.2f}",
                    peak_profit=f"{peak_profit:+.2f}",
                    current_ai_score=f"{current_ai_score:.0f}",
                    market_close_time=TIME_15_30.isoformat(),
                )
            return

        _emit_stat_action_decision_snapshot(
            stock=stock,
            code=code,
            strategy=strategy,
            ws_data=ws_data,
            chosen_action="exit_now",
            eligible_actions=["exit_now"],
            rejected_actions=rejected_actions,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
            curr_price=curr_p,
            buy_price=buy_p,
            exit_rule=exit_rule or "-",
            sell_reason_type=sell_reason_type or "-",
            scale_in_gate=fallback_gate,
            scale_in_action=fallback_action,
            reason=reason,
            force=True,
        )
        _remember_exit_context(
            stock=stock,
            exit_rule=exit_rule,
            reason=reason,
            peak_profit=peak_profit,
            held_sec=int(held_time_min * 60),
            current_ai_score=current_ai_score,
            soft_stop_threshold_pct=dynamic_stop_pct if str(exit_rule or "").strip() == "scalp_soft_stop_pct" else None,
        )
        _mutate_stock_state(stock, set_fields={'last_exit_reason': reason})
        exit_decision_source = str(stock.get("last_exit_decision_source") or "MANUAL")
        _log_holding_pipeline(
            stock,
            code,
            "exit_signal",
            sell_reason_type=sell_reason_type,
            reason=reason,
            exit_rule=exit_rule or "-",
            exit_decision_source=exit_decision_source,
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            current_ai_score=f"{current_ai_score:.0f}",
            held_sec=int(held_time_min * 60),
            curr_price=curr_p,
            buy_price=buy_p,
            buy_qty=_safe_int(stock.get("buy_qty"), 0),
        )
        if _is_swing_intraday_probe_target(stock):
            _log_holding_pipeline(
                stock,
                code,
                "swing_probe_exit_signal",
                **_swing_probe_event_fields(
                    stock,
                    sell_reason_type=sell_reason_type,
                    reason=reason,
                    exit_rule=exit_rule or "-",
                    exit_decision_source=exit_decision_source,
                    profit_rate=f"{profit_rate:+.2f}",
                    peak_profit=f"{peak_profit:+.2f}",
                    current_ai_score=f"{current_ai_score:.0f}",
                    held_sec=int(held_time_min * 60),
                    curr_price=curr_p,
                    buy_price=buy_p,
                    buy_qty=_safe_int(stock.get("buy_qty"), 0),
                    mfe_pct=f"{peak_profit:+.2f}",
                    mae_pct="-",
                ),
            )
        if _has_open_pending_entry_orders(stock):
            cancel_state = _cancel_pending_entry_orders(stock, code, force=False)
            if cancel_state == 'failed':
                log_error(
                    f"⚠️ [ENTRY_CANCEL] {stock.get('name')}({code}) "
                    "pending entry orders unresolved; delaying sell until next loop"
                )
                return

        if strategy == "SCALPING" and str(exit_rule or "").strip() == "scalp_soft_stop_pct":
            _mark_same_symbol_soft_stop(code, now_ts=now_ts)

        sign = _resolve_sell_order_sign(sell_reason_type, profit_rate)
        msg = (
            f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n"
            f"사유: `{reason}`\n"
            f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)"
        )

        is_success = False
        target_id = stock.get('id')

        mem_buy_qty = _safe_int(stock.get('buy_qty'), 0)
        if _is_scalp_simulated_position(stock, strategy):
            _complete_scalp_simulated_sell(
                stock=stock,
                code=code,
                ws_data=ws_data,
                curr_price=curr_p,
                now_ts=now_ts,
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule,
                profit_rate=profit_rate,
            )
            return
        buy_qty = mem_buy_qty
        try:
            with DB.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                if record and record.buy_qty:
                    buy_qty = max(buy_qty, int(record.buy_qty))
        except Exception as e:
            log_error(f"🚨 [DB 조회 에러] ID {target_id} 수량 조회 실패: {e}")

        if buy_qty <= 0:
            log_info(f"⚠️ [{stock['name']}] 고유 ID({target_id})의 수량이 0주입니다. 실제 키움 잔고로 폴백합니다...")
            real_inventory, _ = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
            real_stock = next(
                (item for item in (real_inventory or []) if str(item.get('code', '')).strip()[:6] == code),
                None,
            )

            if real_stock and _safe_int(real_stock.get('qty'), 0) > 0:
                buy_qty = _safe_int(real_stock.get('qty'), 0)
                _mutate_stock_state(stock, set_fields={'buy_qty': buy_qty})
                log_info(
                    f"🔄 [수량 폴백] 실제 계좌에서 총 잔고 {buy_qty}주를 매도합니다. "
                    "(다중 매매건 합산 수량일 수 있음)"
                )

        if not admin_id and not _is_any_simulated_position(stock, strategy):
            log_error(f"🚨 [매도실패] {stock['name']}: 관리자 ID가 없습니다.")
            return

        if _is_swing_simulated_position(stock, strategy) and _is_swing_live_order_dry_run(strategy):
            if buy_qty <= 0:
                buy_qty = mem_buy_qty
            if buy_qty <= 0:
                zero_stage = "swing_probe_discarded" if _is_swing_intraday_probe_target(stock) else "swing_sim_sell_blocked_zero_qty"
                _log_holding_pipeline(
                    stock,
                    code,
                    zero_stage,
                    **(
                        _swing_probe_event_fields(
                            stock,
                            discard_reason="zero_sell_qty",
                            sell_reason_type=sell_reason_type,
                            exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                            profit_rate=f"{profit_rate:+.2f}",
                        )
                        if _is_swing_intraday_probe_target(stock)
                        else {
                            "sell_reason_type": sell_reason_type,
                            "exit_rule": exit_rule or stock.get("last_exit_rule") or "-",
                            "profit_rate": f"{profit_rate:+.2f}",
                            "simulation_owner": _swing_live_order_dry_run_owner(),
                            "actual_order_submitted": False,
                        }
                    ),
                )
                return

            simulated_profit_rate = calculate_net_profit_rate(stock.get("buy_price"), curr_p)
            _mutate_stock_state(
                stock,
                set_fields={
                    "status": "COMPLETED",
                    "sell_price": curr_p,
                    "sell_qty": buy_qty,
                    "sell_time": now_ts,
                    "simulated_sell_order": True,
                    "actual_order_submitted": False,
                    "profit_rate": simulated_profit_rate,
                },
            )
            with ENTRY_LOCK:
                HIGHEST_PRICES.pop(_price_tracking_key(stock, code), None)
            log_info(
                f"[SWING_LIVE_ORDER_DRY_RUN] {stock.get('name')}({code}) "
                f"sell skipped qty={buy_qty} assumed_price={curr_p} reason={sell_reason_type}"
            )
            swing_sell_micro_fields = (
                _build_swing_micro_log_fields(
                    _build_live_orderbook_micro_context(code, curr_price=curr_p),
                    phase="exit",
                )
                if _is_swing_orderbook_micro_context_enabled(strategy)
                else {}
            )
            _log_holding_pipeline(
                stock,
                code,
                "swing_probe_sell_order_assumed_filled"
                if _is_swing_intraday_probe_target(stock)
                else "swing_sim_sell_order_assumed_filled",
                **(
                    _swing_probe_event_fields(
                        stock,
                        sell_reason_type=sell_reason_type,
                        exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                        exit_decision_source=stock.get("last_exit_decision_source") or "MANUAL",
                        qty=buy_qty,
                        assumed_fill_price=curr_p,
                        buy_price=stock.get("buy_price"),
                        profit_rate=f"{simulated_profit_rate:+.2f}",
                        trigger_profit_rate=f"{profit_rate:+.2f}",
                        final_exit_return_pct=f"{simulated_profit_rate:+.2f}",
                        mfe_pct=f"{peak_profit:+.2f}",
                        mae_pct="-",
                        would_submit_stage="sell_order_sent",
                        runtime_effect="in_memory_completed_only",
                        **swing_sell_micro_fields,
                    )
                    if _is_swing_intraday_probe_target(stock)
                    else {
                        "sell_reason_type": sell_reason_type,
                        "exit_rule": exit_rule or stock.get("last_exit_rule") or "-",
                        "exit_decision_source": stock.get("last_exit_decision_source") or "MANUAL",
                        "qty": buy_qty,
                        "assumed_fill_price": curr_p,
                        "profit_rate": f"{profit_rate:+.2f}",
                        "simulation_owner": _swing_live_order_dry_run_owner(),
                        "actual_order_submitted": False,
                        "would_submit_stage": "sell_order_sent",
                        "runtime_effect": "in_memory_completed_only",
                        **swing_sell_micro_fields,
                    }
                ),
            )
            _record_swing_same_symbol_loss_reentry_cooldown(
                stock,
                code,
                strategy,
                exit_rule=exit_rule or stock.get("last_exit_rule"),
                profit_rate=simulated_profit_rate,
                now_ts=now_ts,
                actual_order_submitted=False,
                source_stage=(
                    "swing_probe_sell_order_assumed_filled"
                    if _is_swing_intraday_probe_target(stock)
                    else "swing_sim_sell_order_assumed_filled"
                ),
            )
            if _is_swing_intraday_probe_target(stock):
                persist_swing_intraday_probe_state(
                    allow_empty_overwrite=True,
                    reason="probe_exit",
                )
            else:
                persist_swing_intraday_probe_state(
                    allow_empty_overwrite=True,
                    reason="swing_loss_reentry_cooldown",
                )
            return

        if buy_qty <= 0:
            log_error(f"🚨 [매도실패] {stock['name']}: 실제 잔고도 0주입니다! 강제 완료(COMPLETED) 처리.")
            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "COMPLETED"})
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} COMPLETED 전환 실패: {e}")

            _mutate_stock_state(stock, set_fields={'status': 'COMPLETED'})
            with ENTRY_LOCK:
                HIGHEST_PRICES.pop(code, None)
            return

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "SELL_ORDERED"})
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")

        _mutate_stock_state(
            stock,
            set_fields={
                'status': 'SELL_ORDERED',
                'sell_target_price': curr_p,
            },
        )

        res = kiwoom_orders.send_smart_sell_order(
            code=code,
            qty=buy_qty,
            token=KIWOOM_TOKEN,
            ws_data=ws_data,
            reason_type=sell_reason_type,
        )

        ord_no = ''

        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                log_error(f"❌ [매도거절] {stock['name']}: {res.get('return_msg')}")
        elif res:
            is_success = True

        if is_success:
            log_info(f"✅ [{stock['name']}] 매도 주문 전송 완료. 체결 영수증 처리 대기 중...")
            set_fields = {
                'pending_sell_msg': msg,
                'sell_order_time': now_ts,
            }
            if ord_no:
                set_fields['sell_odno'] = ord_no
            _mutate_stock_state(stock, set_fields=set_fields)
            _log_holding_pipeline(
                stock,
                code,
                "sell_order_sent",
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                exit_decision_source=stock.get("last_exit_decision_source") or "MANUAL",
                qty=buy_qty,
                ord_no=ord_no or "-",
                order_type=stock.get("exit_order_type") or "-",
                profit_rate=f"{profit_rate:+.2f}",
            )

            if strategy == 'SCALPING' and now_t < TIME_15_30:
                base_cooldown_sec = 1200
                loss_reentry_cooldown_sec = _resolve_same_symbol_loss_reentry_cooldown_sec(
                    exit_rule or stock.get("last_exit_rule"),
                    profit_rate,
                )
                cooldown_sec = max(base_cooldown_sec, loss_reentry_cooldown_sec)
                with ENTRY_LOCK:
                    cooldowns[code] = now_ts + cooldown_sec
                    alerted_stocks.discard(code)
                if loss_reentry_cooldown_sec > base_cooldown_sec:
                    _log_entry_pipeline(
                        stock,
                        code,
                        "same_symbol_loss_reentry_cooldown",
                        exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                        profit_rate=f"{profit_rate:+.2f}",
                        cooldown_sec=cooldown_sec,
                        base_cooldown_sec=base_cooldown_sec,
                    )
                    log_info(
                        f"♻️ [{stock['name']}] 손실 청산 후 동일종목 재진입 {cooldown_sec}초 쿨타임 진입."
                    )
                else:
                    log_info(f"♻️ [{stock['name']}] 스캘핑 청산 완료 후 20분 쿨타임 진입.")
        else:
            err_msg = str(res.get('return_msg', '') if isinstance(res, dict) else '')
            sellable_qty = _extract_sellable_qty_from_error(err_msg)

            # '매도가능수량 부족'은 0주인 경우에만 완료로 간주한다.
            # 양수 수량이면 실계좌 잔고가 남아있는 상태이므로 HOLDING으로 복구해 재시도한다.
            if '매도가능수량' in err_msg and sellable_qty == 0:
                log_error(f"🚨 [{stock['name']}] 잔고 0주(이미 매도됨). COMPLETED로 강제 전환.")
                new_status = 'COMPLETED'
            else:
                if '매도가능수량' in err_msg and sellable_qty and sellable_qty > 0:
                    prev_qty = _safe_int(stock.get('buy_qty'), 0)
                    if prev_qty != sellable_qty:
                        _mutate_stock_state(stock, set_fields={'buy_qty': sellable_qty})
                        log_error(
                            f"⚠️ [{stock['name']}] 매도가능수량 불일치 감지 "
                            f"(요청:{prev_qty}주, 가능:{sellable_qty}주). "
                            "HOLDING 복구 후 재시도 대상으로 유지합니다."
                        )
                else:
                    log_error(f"🚨 [{stock['name']}] 일시적 매도 실패! HOLDING으로 원상복구.")
                new_status = 'HOLDING'

            _mutate_stock_state(stock, set_fields={'status': new_status})
            _log_holding_pipeline(
                stock,
                code,
                "sell_order_failed",
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                exit_decision_source=stock.get("last_exit_decision_source") or "MANUAL",
                new_status=new_status,
                error=err_msg or "unknown",
                sellable_qty=sellable_qty if sellable_qty is not None else "-",
                profit_rate=f"{profit_rate:+.2f}",
            )

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": new_status})
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")

            if new_status == 'COMPLETED':
                with ENTRY_LOCK:
                    HIGHEST_PRICES.pop(code, None)
        return

    # --------------------------------------------------------
    # [추가매수 레이어] SELL 신호가 없을 때만 진입
    # --------------------------------------------------------
    gate = can_consider_scale_in(
        stock=stock,
        code=code,
        ws_data=ws_data,
        strategy=strategy,
        market_regime=market_regime,
    )
    if gate.get('allowed'):
        scale_in_action = _evaluate_scale_in_signal(
            stock=stock,
            code=code,
            strategy=strategy,
            market_regime=market_regime,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            curr_price=curr_p,
            ws_data=ws_data,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
        )
        if scale_in_action:
            chosen_add_type = str(scale_in_action.get("add_type") or "").upper()
            chosen_action = "avg_down_wait" if chosen_add_type == "AVG_DOWN" else "pyramid_wait"
            _emit_stat_action_decision_snapshot(
                stock=stock,
                code=code,
                strategy=strategy,
                ws_data=ws_data,
                chosen_action=chosen_action,
                eligible_actions=[chosen_action, "hold_wait"],
                rejected_actions=["exit_now:no_sell_signal"],
                profit_rate=profit_rate,
                peak_profit=peak_profit,
                current_ai_score=current_ai_score,
                held_sec=held_sec,
                curr_price=curr_p,
                buy_price=buy_p,
                exit_rule="-",
                sell_reason_type="-",
                scale_in_gate=gate,
                scale_in_action=scale_in_action,
                reason=scale_in_action.get("reason") or "-",
                force=True,
            )
            if scale_in_action.get("reason") == "reversal_add_ok":
                _mutate_stock_state(stock, set_fields={'reversal_add_state': 'ADD_ARMED'})
            log_info(
                "[ADD_SIGNAL] "
                f"{stock.get('name')}({code}) "
                f"strategy={strategy} type={scale_in_action.get('add_type')} "
                f"reason={scale_in_action.get('reason')} "
                f"profit={profit_rate:+.2f}% peak={peak_profit:+.2f}%"
            )
            add_result = _process_scale_in_action(
                stock=stock,
                code=code,
                ws_data=ws_data,
                action=scale_in_action,
                admin_id=admin_id,
            )
            if add_result and scale_in_action.get("reason") == "reversal_add_ok":
                _mutate_stock_state(stock, set_fields={'reversal_add_state': 'ADD_ARMED'})
            elif (not add_result) and scale_in_action.get("reason") == "reversal_add_ok":
                _mutate_stock_state(stock, set_fields={'reversal_add_state': 'REVERSAL_CANDIDATE'})
                _log_holding_pipeline(
                    stock,
                    code,
                    "reversal_add_blocked_reason",
                    **_append_reversal_add_probe_fields(
                        {
                            "state": "REVERSAL_CANDIDATE",
                            "blocked_reason": "add_order_failed",
                            "profit_rate": f"{profit_rate:+.2f}",
                            "ai_score": f"{current_ai_score:.0f}",
                        },
                        scale_in_action.get("probe"),
                    ),
                )
            return
        if strategy == 'SCALPING' and _rule_bool('REVERSAL_ADD_ENABLED', False):
            _last_ra_probe_log = float(stock.get('last_reversal_add_probe_log_ts', 0) or 0)
            if now_ts - _last_ra_probe_log >= 30:
                _ra_probe = evaluate_scalping_reversal_add(stock, profit_rate, current_ai_score, held_sec)
                _ra_probe_reason = str(_ra_probe.get("reason") or "")
                if _ra_probe_reason and _ra_probe_reason != "reversal_add_ok":
                    _log_holding_pipeline(
                        stock,
                        code,
                        "reversal_add_blocked_reason",
                        **_append_reversal_add_probe_fields(
                            {
                                "state": stock.get('reversal_add_state', '') or "-",
                                "blocked_reason": _ra_probe_reason,
                                "profit_rate": f"{profit_rate:+.2f}",
                                "ai_score": f"{current_ai_score:.0f}",
                            },
                            _ra_probe.get("probe"),
                        ),
                    )
                    _emit_stat_action_decision_snapshot(
                        stock=stock,
                        code=code,
                        strategy=strategy,
                        ws_data=ws_data,
                        chosen_action="hold_wait",
                        eligible_actions=["hold_wait"],
                        rejected_actions=[f"avg_down_wait:{_ra_probe_reason}"],
                        profit_rate=profit_rate,
                        peak_profit=peak_profit,
                        current_ai_score=current_ai_score,
                        held_sec=held_sec,
                        curr_price=curr_p,
                        buy_price=buy_p,
                        scale_in_gate=gate,
                        scale_in_action=_ra_probe,
                        reason="scale_in_probe_blocked",
                    )
                _mutate_stock_state(stock, set_fields={'last_reversal_add_probe_log_ts': now_ts})
            return
    else:
        last_block = float(stock.get('last_add_block_log_ts', 0) or 0)
        if now_ts - last_block >= 30:
            reversal_probe = None
            if strategy == 'SCALPING' and _rule_bool('REVERSAL_ADD_ENABLED', False):
                reversal_probe = evaluate_scalping_reversal_add(
                    stock,
                    profit_rate,
                    current_ai_score,
                    held_sec,
                )
            if gate.get('reason') == 'buy_side_paused':
                log_info(
                    f"[TRADING_PAUSED_BLOCK] HOLDING add skipped "
                    f"{stock.get('name')}({code}) strategy={strategy} "
                    f"state={get_pause_state_label()}"
                )
            else:
                log_info(
                    "[ADD_BLOCKED] "
                    f"{stock.get('name')}({code}) "
                    f"strategy={strategy} reason={gate.get('reason')}"
                )
            if (
                reversal_probe
                and stock.get('reversal_add_state') in ('STAGNATION', 'REVERSAL_CANDIDATE')
            ):
                _log_holding_pipeline(
                    stock,
                    code,
                    "reversal_add_gate_blocked",
                    **_append_reversal_add_probe_fields(
                        {
                            "state": stock.get('reversal_add_state', '') or "-",
                            "gate_reason": gate.get('reason') or "-",
                            "profit_rate": f"{profit_rate:+.2f}",
                            "ai_score": f"{current_ai_score:.0f}",
                        },
                        reversal_probe.get("probe"),
                    ),
                )
                _emit_stat_action_decision_snapshot(
                    stock=stock,
                    code=code,
                    strategy=strategy,
                    ws_data=ws_data,
                    chosen_action="hold_wait",
                    eligible_actions=["hold_wait"],
                    rejected_actions=[f"avg_down_wait:{gate.get('reason') or '-'}"],
                    profit_rate=profit_rate,
                    peak_profit=peak_profit,
                    current_ai_score=current_ai_score,
                    held_sec=held_sec,
                    curr_price=curr_p,
                    buy_price=buy_p,
                    scale_in_gate=gate,
                    scale_in_action=reversal_probe,
                    reason="scale_in_gate_blocked",
                )
            _mutate_stock_state(stock, set_fields={'last_add_block_log_ts': now_ts})


def can_consider_scale_in(
    stock,
    code,
    ws_data,
    strategy,
    market_regime,
    *,
    skip_add_judgment_lock=False,
):
    """추가매수 공통 게이트: 조건을 만족하는 경우에만 True."""
    _ = (code, ws_data)

    if _rule_bool('SCALE_IN_REQUIRE_HISTORY_TABLE', False):
        return {"allowed": False, "reason": "history_table_required"}

    if stock.get('pending_add_order') and not stock.get('pending_add_ord_no'):
        _cancel_or_reconcile_pending_add(stock, reason="stale_pending_no_ordno")
        return {"allowed": False, "reason": "pending_add_recovered"}

    # 장시간 미체결된 추가매수 주문은 보수적으로 해제
    pending_ts = float(stock.get('pending_add_requested_at', 0) or 0)
    if pending_ts:
        raw_strategy = (strategy or "").upper()
        base_timeout = 20 if raw_strategy == 'SCALPING' else _rule_int('ORDER_TIMEOUT_SEC', 30)
        add_type = (stock.get('pending_add_type') or '').upper()
        if raw_strategy != 'SCALPING' and add_type == 'PYRAMID':
            base_timeout = int(base_timeout * 2)
        timeout_sec = base_timeout
        pending_filled = int(stock.get('pending_add_filled_qty', 0) or 0)
        if pending_filled > 0:
            timeout_sec = timeout_sec * 3
        if (time.time() - pending_ts) > timeout_sec:
            reconcile = _cancel_or_reconcile_pending_add(stock, reason="timeout")
            if reconcile.get('cleared'):
                return {"allowed": False, "reason": "pending_add_timeout_released"}
            return {"allowed": False, "reason": "pending_add_cancel_failed"}

    if stock.get('status') != 'HOLDING':
        return {"allowed": False, "reason": "not_holding"}

    if not _rule_bool('ENABLE_SCALE_IN', False):
        return {"allowed": False, "reason": "scale_in_disabled"}

    if is_buy_side_paused():
        return {"allowed": False, "reason": "buy_side_paused"}

    if stock.get('scale_in_locked'):
        return {"allowed": False, "reason": "scale_in_locked"}

    buy_p = _safe_float(stock.get('buy_price'), 0.0)
    buy_q = _safe_int(stock.get('buy_qty'), 0)
    if buy_p <= 0 or buy_q <= 0:
        return {"allowed": False, "reason": "invalid_position"}

    if stock.get('status') == 'SELL_ORDERED':
        return {"allowed": False, "reason": "sell_ordered"}

    # 동일 루프/짧은 시간 중복 호출 방지
    # 손절 직전 fallback probe는 관찰 타이밍이 짧아 lock을 선택적으로 우회한다.
    if not skip_add_judgment_lock:
        lock_sec = _rule_int('ADD_JUDGMENT_LOCK_SEC', 20)
        last_check = float(stock.get('last_scale_in_check_ts', 0) or 0)
        if last_check > 0 and (time.time() - last_check) < lock_sec:
            return {"allowed": False, "reason": "add_judgment_locked"}

    # 최근 추가매수 직후 쿨다운
    cooldown_sec = _rule_int('SCALE_IN_COOLDOWN_SEC', 180)
    last_add = _resolve_last_add_timestamp(stock)
    if last_add > 0 and (time.time() - last_add) < cooldown_sec:
        return {"allowed": False, "reason": "scale_in_cooldown"}

    cancel_cooldown_sec = _rule_int('SCALE_IN_CANCEL_COOLDOWN_SEC', 120)
    last_add_cancel = float(stock.get('last_add_cancel_at', 0) or 0)
    if last_add_cancel > 0 and (time.time() - last_add_cancel) < cancel_cooldown_sec:
        return {"allowed": False, "reason": "scale_in_cancel_cooldown"}

    # 매수 주문이 이미 진행 중인 경우
    if (
        stock.get('pending_add_order')
        or stock.get('pending_add_ord_no')
        or stock.get('pending_add_requested_at')
        or stock.get('add_order_time')
        or stock.get('pending_add_msg')
        or stock.get('add_odno')
    ):
        return {"allowed": False, "reason": "pending_add_order"}

    # 계좌 리스크 게이트(옵션): 예수금 정보가 있을 때만 적용
    curr_price = _safe_int(ws_data.get('curr'), 0)
    deposit_hint = float(stock.get('account_deposit', 0) or stock.get('deposit', 0) or 0)
    if curr_price > 0 and deposit_hint > 0:
        max_pos_pct = _rule_float('MAX_POSITION_PCT', 0.30)
        if (buy_q * curr_price) >= (deposit_hint * max_pos_pct * 0.98):
            return {"allowed": False, "reason": "position_at_cap"}

    # 전략별 허용 여부
    raw_strategy = (strategy or "").upper()
    if raw_strategy == 'SCALPING':
        allow_reversal = _rule_bool('REVERSAL_ADD_ENABLED', True)
        allow_pyr = _rule_bool('SCALPING_ENABLE_PYRAMID', True)
        if not (allow_reversal or allow_pyr):
            return {"allowed": False, "reason": "scalping_scale_in_disabled"}
    elif raw_strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        allow_pyr = _rule_bool('SWING_ENABLE_PYRAMID', True)
        allow_avg_down_sim = (
            _rule_bool('SWING_ENABLE_AVG_DOWN_SIMULATION', True)
            and _is_swing_live_order_dry_run(raw_strategy)
        )
        if not (allow_pyr or allow_avg_down_sim):
            return {"allowed": False, "reason": "swing_scale_in_disabled"}
    else:
        return {"allowed": False, "reason": "unknown_strategy"}

    # 장 마감 근접 시 추가매수 금지
    now = datetime.now()
    try:
        close_str = _rule("MARKET_CLOSE_TIME", "15:30:00")
        close_t = datetime.strptime(close_str, "%H:%M:%S").time()
        close_dt = datetime.combine(now.date(), close_t) - timedelta(minutes=5)
        if now >= close_dt:
            return {"allowed": False, "reason": "near_market_close"}
    except Exception as exc:
        log_error(f"[SCALE_IN_GUARD] MARKET_CLOSE_TIME parse 실패: {close_str if isinstance(close_str, str) else 'invalid'} ({exc})")

    if raw_strategy == 'SCALPING':
        try:
            cutoff_str = _rule("SCALPING_NEW_BUY_CUTOFF", "15:00:00")
            cutoff_t = datetime.strptime(cutoff_str, "%H:%M:%S").time()
            if now.time() >= cutoff_t:
                return {"allowed": False, "reason": "scalping_cutoff"}
        except Exception as exc:
            log_error(f"[SCALE_IN_GUARD] SCALPING_NEW_BUY_CUTOFF parse 실패: {cutoff_str if isinstance(cutoff_str, str) else 'invalid'} ({exc})")

    if not skip_add_judgment_lock:
        _mutate_stock_state(stock, set_fields={'last_scale_in_check_ts': time.time()})
    return {"allowed": True, "reason": "ok"}


def _clear_pending_add_meta(stock, reason=None):
    _mutate_stock_state(
        stock,
        pop_fields=(
            'pending_add_order',
            'pending_add_type',
            'pending_add_qty',
            'pending_add_ord_no',
            'pending_add_requested_at',
            'pending_add_counted',
            'pending_add_filled_qty',
            'add_order_time',
            'add_odno',
        ),
    )
    if reason:
        log_info(f"[ADD_CANCELLED] pending add cleared ({reason}) for {stock.get('name')}")


def _persist_scale_in_flags(stock):
    target_id = stock.get('id')
    if not DB or not target_id:
        return
    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update({
                "scale_in_locked": bool(stock.get('scale_in_locked', False)),
            })
    except Exception as e:
        log_error(f"[ADD_BLOCKED] scale_in flag persist failed for id={target_id}: {e}")


def _is_ok_response(res):
    if not isinstance(res, dict):
        return bool(res)
    return str(res.get('return_code', res.get('rt_cd', ''))) == '0'


def _cancel_or_reconcile_pending_add(stock, reason):
    """
    보수적으로 pending add를 정리합니다.
    - 주문번호가 있으면 실제 취소를 먼저 시도
    - 주문이 이미 없거나 체결/취소 완료로 보이면 잠금 후 정리
    - 취소 실패 시 pending을 유지해 중복 add를 막음
    """
    ord_no = str(stock.get('pending_add_ord_no', '') or '').strip()
    code = str(stock.get('code', '')).strip()[:6]

    if not ord_no:
        _mutate_stock_state(stock, set_fields={'scale_in_locked': True})
        _persist_scale_in_flags(stock)
        record_add_history_event(
            DB,
            recommendation_id=stock.get('id'),
            stock_code=code,
            stock_name=stock.get('name'),
            strategy=stock.get('strategy'),
            add_type=stock.get('pending_add_type'),
            event_type='CANCELLED',
            order_no=None,
            request_qty=stock.get('pending_add_qty', 0),
            prev_buy_price=stock.get('buy_price'),
            prev_buy_qty=stock.get('buy_qty', 0),
            add_count_after=stock.get('add_count', 0),
            reason=f"{reason}_missing_ordno",
            note='pending add missing order number; scale_in_locked applied',
        )
        _clear_pending_add_meta(stock, reason=f"{reason}_missing_ordno")
        log_error(
            f"[ADD_CANCELLED] {stock.get('name')}({code}) pending add missing order number. "
            "scale_in_locked=True for manual reconciliation."
        )
        return {"cleared": True, "reason": f"{reason}_missing_ordno"}

    if not code or not KIWOOM_TOKEN:
        _mutate_stock_state(stock, set_fields={'scale_in_locked': True})
        _persist_scale_in_flags(stock)
        log_error(
            f"[ADD_BLOCKED] {stock.get('name')}({code}) cannot reconcile pending add "
            f"(token/code missing). keeping pending blocked."
        )
        return {"cleared": False, "reason": "missing_runtime_context"}

    res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=ord_no, token=KIWOOM_TOKEN, qty=0)
    if _is_ok_response(res):
        now_ts = time.time()
        if stock.get("swing_scale_in_real_canary"):
            _log_holding_pipeline(
                stock,
                code,
                "swing_scale_in_real_canary_cancel_requested",
                policy_id="swing_scale_in_real_canary_phase0",
                cohort="swing_scale_in_real_canary_phase0",
                add_type=stock.get("pending_add_type"),
                ord_no=ord_no,
                reason=reason,
                actual_order_submitted=True,
            )
        record_add_history_event(
            DB,
            recommendation_id=stock.get('id'),
            stock_code=code,
            stock_name=stock.get('name'),
            strategy=stock.get('strategy'),
            add_type=stock.get('pending_add_type'),
            event_type='CANCELLED',
            order_no=ord_no,
            request_qty=stock.get('pending_add_qty', 0),
            prev_buy_price=stock.get('buy_price'),
            prev_buy_qty=stock.get('buy_qty', 0),
            add_count_after=stock.get('add_count', 0),
            reason=reason,
            note='pending add order cancelled before release',
        )
        _mutate_stock_state(
            stock,
            set_fields={
                'last_add_cancel_at': now_ts,
                'last_add_cancel_reason': reason,
                'last_add_cancel_type': stock.get('pending_add_type'),
                'last_add_cancel_ord_no': ord_no,
            },
        )
        _clear_pending_add_meta(stock, reason=reason)
        return {"cleared": True, "reason": f"{reason}_cancelled"}

    err_msg = str(res.get('return_msg', '')) if isinstance(res, dict) else str(res)
    uncertain_keywords = ['주문없음', '취소가능수량', '체결', '원주문']
    if any(keyword in err_msg for keyword in uncertain_keywords):
        _mutate_stock_state(stock, set_fields={'scale_in_locked': True})
        _persist_scale_in_flags(stock)
        record_add_history_event(
            DB,
            recommendation_id=stock.get('id'),
            stock_code=code,
            stock_name=stock.get('name'),
            strategy=stock.get('strategy'),
            add_type=stock.get('pending_add_type'),
            event_type='CANCELLED',
            order_no=ord_no,
            request_qty=stock.get('pending_add_qty', 0),
            prev_buy_price=stock.get('buy_price'),
            prev_buy_qty=stock.get('buy_qty', 0),
            add_count_after=stock.get('add_count', 0),
            reason=f"{reason}_uncertain",
            note=f'cancel uncertain: {err_msg}',
        )
        _clear_pending_add_meta(stock, reason=f"{reason}_uncertain")
        log_error(
            f"[ADD_CANCELLED] {stock.get('name')}({code}) pending add uncertain after cancel attempt. "
            "scale_in_locked=True for manual/account reconciliation."
        )
        return {"cleared": True, "reason": f"{reason}_uncertain"}

    log_error(
        f"[ADD_BLOCKED] {stock.get('name')}({code}) pending add cancel failed; keeping pending. "
        f"reason={reason} err={err_msg}"
    )
    return {"cleared": False, "reason": "cancel_failed"}


def _sanitize_pending_add_states(active_targets):
    """재시작/복구 시 보수적으로 pending add 메타를 정리합니다."""
    if not active_targets:
        return
    for stock in active_targets:
        if not isinstance(stock, dict):
            continue
        if stock.get('pending_add_order'):
            # 주문번호가 없으면 복구 불가 → 정리
            if not stock.get('pending_add_ord_no'):
                _mutate_stock_state(stock, set_fields={'scale_in_locked': True})
                _persist_scale_in_flags(stock)
                _clear_pending_add_meta(stock, reason="recovery_no_ordno")
                continue
            # 오래된 pending은 정리
            pending_ts = float(stock.get('pending_add_requested_at', 0) or 0)
            if pending_ts:
                raw_strategy = (stock.get('strategy') or '').upper()
                timeout_sec = 20 if raw_strategy == 'SCALPING' else int(_rule('ORDER_TIMEOUT_SEC', 30) or 30)
                if (time.time() - pending_ts) > timeout_sec:
                    _cancel_or_reconcile_pending_add(stock, reason="recovery_timeout")


def _evaluate_scale_in_signal(
    stock,
    code,
    strategy,
    market_regime,
    profit_rate,
    peak_profit,
    curr_price,
    ws_data,
    current_ai_score=50,
    held_sec=0,
):
    """전략별 추가매수 시그널 평가."""
    _ = (ws_data,)

    raw_strategy = (strategy or "").upper()
    if raw_strategy == 'SCALPING':
        sim_window = _evaluate_scalp_sim_scale_in_window_expansion(
            stock=stock,
            strategy=raw_strategy,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
        )
        if sim_window.get("should_add"):
            return sim_window
        is_new_high = False
        try:
            highest_prices = HIGHEST_PRICES or {}
            is_new_high = curr_price >= float(highest_prices.get(_price_tracking_key(stock, code), curr_price))
        except Exception as exc:
            log_error(f"[SCALEIN_STATE] highest_prices 비교 실패 ({code}, curr_price={curr_price}): {exc}")

        pyramid = evaluate_scalping_pyramid(stock, profit_rate, peak_profit, is_new_high)
        if pyramid.get("should_add"):
            pyramid.update(
                {
                    "profit_rate": profit_rate,
                    "peak_profit": peak_profit,
                    "current_ai_score": current_ai_score,
                    "is_new_high": is_new_high,
                }
            )
            return pyramid
        reversal = evaluate_scalping_reversal_add(stock, profit_rate, current_ai_score, held_sec)
        if reversal.get("should_add"):
            reversal.update(
                {
                    "profit_rate": profit_rate,
                    "peak_profit": peak_profit,
                    "current_ai_score": current_ai_score,
                    "held_sec": held_sec,
                }
            )
            return reversal
        adm_scale_in = resolve_holding_exit_matrix_scale_in_bias(
            strategy=raw_strategy,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
        )
        if adm_scale_in.get("should_add"):
            return adm_scale_in
        return None
    elif raw_strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        _ = market_regime
        pyramid = evaluate_swing_pyramid(stock, profit_rate, peak_profit)
        if pyramid.get("should_add"):
            pyramid.update(
                {
                    "profit_rate": profit_rate,
                    "peak_profit": peak_profit,
                    "current_ai_score": current_ai_score,
                    "held_sec": held_sec,
                }
            )
            return pyramid
        avg_down = evaluate_swing_avg_down(
            stock,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            held_sec=held_sec,
        )
        if avg_down.get("should_add"):
            return avg_down
        return None
    else:
        return None


def _evaluate_scalp_sim_scale_in_window_expansion(
    *,
    stock,
    strategy,
    profit_rate,
    peak_profit,
    current_ai_score=50,
    held_sec=0,
):
    if not _rule_bool("SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED", False):
        return {}
    if not _is_scalp_simulated_position(stock, strategy):
        return {}
    if not _rule_bool("SCALP_LIVE_SIMULATOR_ENABLED", True):
        return {}
    max_per_position = max(0, _rule_int("SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION", 1))
    filled_count = 1 if stock.get("last_simulated_add_ord_no") else 0
    if max_per_position > 0 and filled_count >= max_per_position:
        return {}
    day_key = datetime.now().strftime("%Y-%m-%d")
    max_daily = max(0, _rule_int("SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY", 30))
    created_today = int(_SCALP_SIM_SCALE_IN_WINDOW_DAILY_CREATED.get(day_key, 0) or 0)
    if max_daily > 0 and created_today >= max_daily:
        return {}
    min_profit = _rule_float("SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT", -2.5)
    max_profit = _rule_float("SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT", 2.5)
    if profit_rate < min_profit or profit_rate > max_profit:
        return {}
    allowed = {
        str(item).strip().upper()
        for item in str(_rule("SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS", "PYRAMID,AVG_DOWN") or "").split(",")
        if str(item).strip()
    }
    add_type = "PYRAMID" if profit_rate >= 0 else "AVG_DOWN"
    if add_type not in allowed:
        fallback = sorted(allowed & {"PYRAMID", "AVG_DOWN"})
        if not fallback:
            return {}
        add_type = fallback[0]
    _SCALP_SIM_SCALE_IN_WINDOW_DAILY_CREATED[day_key] = created_today + 1
    return {
        "should_add": True,
        "add_type": add_type,
        "reason": "scalp_sim_scale_in_window_expansion",
        "source": "scalp_sim_scale_in_window_expansion",
        "cohort": "scalp_sim_scale_in_window_expansion",
        "decision_authority": "sim_observation_only",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "profit_rate": profit_rate,
        "peak_profit": peak_profit,
        "current_ai_score": current_ai_score,
        "held_sec": held_sec,
        "max_orders_per_position": max_per_position,
        "max_orders_per_day": max_daily,
    }


def _process_scale_in_action(stock, code, ws_data, action, admin_id):
    """추가매수 주문 처리 (STEP4 이후 구현 예정)."""
    if not action:
        return None
    return execute_scale_in_order(
        stock=stock,
        code=code,
        ws_data=ws_data,
        action=action,
        admin_id=admin_id,
    )


def execute_scale_in_order(*, stock, code, ws_data, action, admin_id):
    """
    HOLDING 상태 추가매수 주문 실행.
    - 성공 시 HOLDING 유지 + pending add 메타 저장
    - 실패 시 pending 메타 저장하지 않음
    """
    if not admin_id and not _is_any_simulated_position(stock, stock.get("strategy")):
        log_error(f"⚠️ [추가매수보류] {stock.get('name')}: 관리자 ID가 없습니다.")
        log_info(f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=no_admin")
        return None

    add_type = (action.get("add_type") or "").upper()
    if add_type not in ("AVG_DOWN", "PYRAMID"):
        log_info(f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=invalid_add_type")
        return None

    curr_price = _safe_int(ws_data.get('curr'), 0)
    if curr_price <= 0:
        log_info(f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=invalid_price")
        return None

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    swing_scale_micro_fields = {}
    if _is_swing_orderbook_micro_context_enabled(strategy):
        swing_scale_micro_fields = _build_swing_micro_log_fields(
            _build_live_orderbook_micro_context(code, curr_price=curr_price),
            phase="scale_in",
            add_type=add_type,
            ws_data=ws_data,
        )
        _log_holding_pipeline(
            stock,
            code,
            "swing_scale_in_micro_context_observed",
            add_type=add_type,
            **swing_scale_micro_fields,
        )
    else:
        swing_scale_micro_fields = _build_orderbook_micro_log_fields(None)
    price_resolution = resolve_scale_in_order_price(
        stock=stock,
        ws_data=ws_data,
        action=action,
        strategy=strategy,
        curr_price=curr_price,
    )
    resolved_price = int(price_resolution.get("order_price", 0) or 0)
    if not price_resolution.get("allowed", False):
        _log_holding_pipeline(
            stock,
            code,
            "scale_in_price_guard_block",
            add_type=add_type,
            reason=price_resolution.get("reason"),
            curr_price=curr_price,
            resolved_price=resolved_price,
            best_bid=price_resolution.get("best_bid"),
            best_ask=price_resolution.get("best_ask"),
            spread_bps="-" if price_resolution.get("spread_bps") is None else f"{price_resolution.get('spread_bps'):.2f}",
            max_spread_bps=f"{float(price_resolution.get('max_spread_bps') or 0):.2f}",
            curr_vs_micro_vwap_bp=f"{float(price_resolution.get('curr_vs_micro_vwap_bp') or 0):.2f}",
            max_micro_vwap_bps=f"{float(price_resolution.get('max_micro_vwap_bps') or 0):.2f}",
            price_source=price_resolution.get("price_source"),
            **swing_scale_micro_fields,
        )
        log_info(
            f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=scale_in_price_guard "
            f"{price_resolution.get('reason')} curr_price={curr_price} resolved_price={resolved_price}"
        )
        return None

    simulated_position = _is_any_simulated_position(stock, strategy)
    deposit = _sim_virtual_budget_krw() if simulated_position else kiwoom_orders.get_deposit(KIWOOM_TOKEN)
    sim_budget_fields = (
        {
            "virtual_budget_override": True,
            "virtual_budget_krw": deposit,
            "budget_authority": "sim_virtual_not_real_orderable_amount",
        }
        if simulated_position
        else {}
    )
    qty_price = resolved_price if strategy == "SCALPING" else curr_price
    qty_details = describe_dynamic_scale_in_qty(
        stock=stock,
        resolved_price=qty_price,
        deposit=deposit,
        add_type=add_type,
        strategy=stock.get('strategy', ''),
        add_reason=action.get('reason'),
        price_resolution=price_resolution,
        action=action,
    )
    qty = int(qty_details.get("qty", 0) or 0)
    template_qty = int(qty_details.get("template_qty", 0) or 0)
    cap_qty = int(qty_details.get("cap_qty", 0) or 0)
    floor_applied = bool(qty_details.get("floor_applied", False))
    would_qty = int(qty_details.get("would_qty", template_qty) or 0)
    effective_qty = int(qty_details.get("effective_qty", qty) or 0)
    qty_reason = qty_details.get("qty_reason", "")
    if qty <= 0:
        _log_holding_pipeline(
            stock,
            code,
            "scale_in_qty_block",
            add_type=add_type,
            reason=qty_reason,
            curr_price=curr_price,
            resolved_price=resolved_price,
            template_qty=template_qty,
            would_qty=would_qty,
            effective_qty=effective_qty,
            cap_qty=cap_qty,
            floor_applied=floor_applied,
            **sim_budget_fields,
            **swing_scale_micro_fields,
        )
        log_info(
            f"[ADD_BLOCKED] {stock.get('name')}({code}) "
            f"reason=zero_qty deposit={deposit} curr_price={curr_price} "
            f"buy_qty={stock.get('buy_qty', 0)} add_type={add_type} "
            f"template_qty={template_qty} would_qty={would_qty} effective_qty={effective_qty} "
            f"cap_qty={cap_qty} floor_applied={floor_applied} qty_reason={qty_reason}"
        )
        log_info(
            f"⚠️ [추가매수보류] {stock.get('name')}: 추가매수 수량 0주 "
            f"(주문가능금액 {deposit:,}원, resolver가격 {qty_price:,}원)"
        )
        return None

    if strategy == 'SCALPING':
        order_type_code = "00"
        final_price = resolved_price
    else:
        order_type_code = "6"
        final_price = 0

    _log_holding_pipeline(
        stock,
        code,
        "scale_in_price_resolved",
        add_type=add_type,
        scale_in_type=add_type,
        add_trigger=action.get("reason"),
        scale_in_trigger=action.get("reason"),
        reason=price_resolution.get("reason"),
        curr_price=curr_price,
        resolved_price=resolved_price,
        price_source=price_resolution.get("price_source"),
        price_policy=price_resolution.get("price_source") or price_resolution.get("reason"),
        best_bid=price_resolution.get("best_bid"),
        best_ask=price_resolution.get("best_ask"),
        spread_bps="-" if price_resolution.get("spread_bps") is None else f"{price_resolution.get('spread_bps'):.2f}",
        curr_vs_micro_vwap_bp=f"{float(price_resolution.get('curr_vs_micro_vwap_bp') or 0):.2f}",
        would_qty=would_qty,
        effective_qty=effective_qty,
        qty_reason=qty_reason,
        **sim_budget_fields,
        **swing_scale_micro_fields,
    )
    _log_holding_pipeline(
        stock,
        code,
        "scale_in_price_p2_observe",
        schema_name="scale_in_price_v1",
        observe_only=True,
        live_runtime_effect=False,
        action=action.get("p2_observe_action", "USE_DEFENSIVE"),
        curr_price=curr_price,
        resolved_price=resolved_price,
        price_source=price_resolution.get("price_source"),
        add_type=add_type,
        **swing_scale_micro_fields,
    )

    if is_buy_side_paused():
        log_info(
            f"[TRADING_PAUSED_BLOCK] add order blocked "
            f"{stock.get('name')}({code}) strategy={strategy} type={add_type} "
            f"state={get_pause_state_label()}"
        )
        return None

    swing_real_canary_fields = None
    if _is_swing_strategy(strategy) and not _is_any_simulated_position(stock, strategy):
        real_canary_decision = _evaluate_swing_scale_in_real_canary(
            stock,
            code,
            add_type=add_type,
            qty=qty,
            final_price=final_price,
            curr_price=curr_price,
            ws_data=ws_data or {},
            price_resolution=price_resolution,
            swing_scale_micro_fields=swing_scale_micro_fields,
            template_qty=template_qty,
            would_qty=would_qty,
            effective_qty=effective_qty,
            cap_qty=cap_qty,
            floor_applied=floor_applied,
            qty_reason=qty_reason,
        )
        if not bool(real_canary_decision.get("allowed")):
            fields = real_canary_decision.get("fields") if isinstance(real_canary_decision.get("fields"), dict) else {}
            _log_holding_pipeline(
                stock,
                code,
                "swing_scale_in_real_canary_blocked",
                block_reason=real_canary_decision.get("reason"),
                actual_order_submitted=False,
                **fields,
            )
            log_info(
                f"[ADD_BLOCKED] {stock.get('name')}({code}) "
                f"reason=swing_scale_in_real_canary_{real_canary_decision.get('reason')} "
                f"add_type={add_type}"
            )
            return None
        swing_real_canary_fields = real_canary_decision.get("fields") or {}
        qty = int(real_canary_decision.get("qty") or 1)
        final_price = int(real_canary_decision.get("order_price") or 0)
        order_type_code = str(real_canary_decision.get("order_type_code") or "00")
        _log_holding_pipeline(
            stock,
            code,
            "swing_scale_in_real_canary_candidate",
            actual_order_submitted=False,
            **swing_real_canary_fields,
        )

    if _is_scalp_simulated_position(stock, strategy):
        touched, fill_price, best_ask, best_bid = _scalp_sim_buy_quote_touch(ws_data or {}, final_price)
        ord_no = _simulated_order_no("SIMADD", code)
        if not touched:
            _log_holding_pipeline(
                stock,
                code,
                "scalp_sim_scale_in_order_unfilled",
                **_scalp_sim_event_fields(
                    threshold_family="scale_in_price_guard",
                    sim_record_id=stock.get("sim_record_id"),
                    sim_parent_record_id=stock.get("sim_parent_record_id"),
                    add_type=add_type,
                    qty=qty,
                    ord_no=ord_no,
                    limit_price=final_price,
                    curr_price=curr_price,
                    best_ask=best_ask,
                    best_bid=best_bid,
                    would_submit_stage="add_order_sent",
                    runtime_effect="virtual_quote_not_touched",
                    template_qty=template_qty,
                    would_qty=would_qty,
                    effective_qty=effective_qty,
                    cap_qty=cap_qty,
                    floor_applied=floor_applied,
                    qty_reason=qty_reason,
                    **sim_budget_fields,
                ),
            )
            persist_scalp_simulator_state()
            return None
        now_ts = time.time()
        prev_qty = _safe_int(stock.get("buy_qty"), 0)
        prev_price = _safe_int(stock.get("buy_price"), curr_price)
        new_qty = prev_qty + qty
        new_avg_price = (
            int(round(((prev_price * prev_qty) + (fill_price * qty)) / new_qty))
            if new_qty > 0
            else fill_price
        )
        _mutate_stock_state(
            stock,
            set_fields={
                "buy_qty": new_qty,
                "buy_price": new_avg_price,
                "add_order_time": now_ts,
                "last_simulated_add_type": add_type,
                "last_simulated_add_qty": qty,
                "last_simulated_add_price": fill_price,
                "last_simulated_add_ord_no": ord_no,
                "actual_order_submitted": False,
            },
        )
        if isinstance(HIGHEST_PRICES, dict):
            with ENTRY_LOCK:
                key = _price_tracking_key(stock, code)
                HIGHEST_PRICES[key] = max(_safe_int(HIGHEST_PRICES.get(key), 0), fill_price)
        _log_holding_pipeline(
            stock,
            code,
            "scalp_sim_scale_in_order_assumed_filled",
            **_scalp_sim_event_fields(
                threshold_family="scale_in_price_guard",
                sim_record_id=stock.get("sim_record_id"),
                sim_parent_record_id=stock.get("sim_parent_record_id"),
                add_type=add_type,
                qty=qty,
                ord_no=ord_no,
                assumed_fill_price=fill_price,
                prev_buy_qty=prev_qty,
                new_buy_qty=new_qty,
                prev_buy_price=prev_price,
                new_buy_price=new_avg_price,
                order_type=order_type_code,
                best_ask=best_ask,
                best_bid=best_bid,
                would_submit_stage="add_order_sent",
                template_qty=template_qty,
                would_qty=would_qty,
                effective_qty=effective_qty,
                cap_qty=cap_qty,
                floor_applied=floor_applied,
                qty_reason=qty_reason,
                **sim_budget_fields,
                runtime_effect="simulated_holding_only",
            ),
        )
        persist_scalp_simulator_state()
        return {
            "return_code": "0",
            "ord_no": ord_no,
            "simulated_order": True,
            "actual_order_submitted": False,
        }

    if _is_swing_simulated_position(stock, strategy) and _is_swing_live_order_dry_run(strategy):
        ord_no = _simulated_order_no("SIMADD", code)
        now_ts = time.time()
        prev_qty = _safe_int(stock.get("buy_qty"), 0)
        prev_price = _safe_int(stock.get("buy_price"), curr_price)
        assumed_price = curr_price if final_price <= 0 else final_price
        new_qty = prev_qty + qty
        scale_in_ratio = (float(qty) / float(prev_qty)) if prev_qty > 0 else 0.0
        price_policy = price_resolution.get("price_source") or price_resolution.get("reason") or "-"
        add_trigger = action.get("reason") or "-"
        new_avg_price = (
            int(round(((prev_price * prev_qty) + (assumed_price * qty)) / new_qty))
            if new_qty > 0
            else assumed_price
        )
        _mutate_stock_state(
            stock,
            set_fields={
                "buy_qty": new_qty,
                "buy_price": new_avg_price,
                "add_order_time": now_ts,
                "last_simulated_add_type": add_type,
                "last_simulated_add_qty": qty,
                "last_simulated_add_price": assumed_price,
                "last_simulated_add_ord_no": ord_no,
                "actual_order_submitted": False,
            },
        )
        log_info(
            f"[SWING_LIVE_ORDER_DRY_RUN] {stock.get('name')}({code}) "
            f"add buy skipped type={add_type} qty={qty} assumed_price={assumed_price} sim_ord_no={ord_no}"
        )
        _log_holding_pipeline(
            stock,
            code,
            "swing_sim_scale_in_order_assumed_filled",
            add_type=add_type,
            scale_in_type=add_type,
            add_trigger=add_trigger,
            scale_in_trigger=add_trigger,
            qty=qty,
            ord_no=ord_no,
            assumed_fill_price=assumed_price,
            prev_buy_qty=prev_qty,
            new_buy_qty=new_qty,
            prev_buy_price=prev_price,
            new_buy_price=new_avg_price,
            order_type=order_type_code,
            price_policy=price_policy,
            add_price_policy=price_policy,
            scale_in_ratio=f"{scale_in_ratio:.4f}",
            add_ratio=f"{scale_in_ratio:.4f}",
            post_add_outcome="pending_followup",
            would_submit_stage="add_order_sent",
            simulation_owner=_swing_live_order_dry_run_owner(),
            actual_order_submitted=False,
            broker_order_forbidden=True,
            template_qty=template_qty,
            would_qty=would_qty,
            effective_qty=effective_qty,
            cap_qty=cap_qty,
            floor_applied=floor_applied,
            qty_reason=qty_reason,
            **sim_budget_fields,
            **swing_scale_micro_fields,
        )
        if _is_swing_intraday_probe_target(stock):
            _log_holding_pipeline(
                stock,
                code,
                "swing_probe_scale_in_order_assumed_filled",
                **_swing_probe_event_fields(
                    stock,
                    add_type=add_type,
                    scale_in_type=add_type,
                    add_trigger=add_trigger,
                    scale_in_trigger=add_trigger,
                    qty=qty,
                    ord_no=ord_no,
                    assumed_fill_price=assumed_price,
                    prev_buy_qty=prev_qty,
                    new_buy_qty=new_qty,
                    prev_buy_price=prev_price,
                    new_buy_price=new_avg_price,
                    price_policy=price_policy,
                    add_price_policy=price_policy,
                    scale_in_ratio=f"{scale_in_ratio:.4f}",
                    add_ratio=f"{scale_in_ratio:.4f}",
                    post_add_outcome="pending_followup",
                    would_submit_stage="add_order_sent",
                    template_qty=template_qty,
                    would_qty=would_qty,
                    effective_qty=effective_qty,
                    cap_qty=cap_qty,
                    floor_applied=floor_applied,
                    qty_reason=qty_reason,
                    **sim_budget_fields,
                    **swing_scale_micro_fields,
                ),
            )
            persist_swing_intraday_probe_state(reason="probe_scale_in")
        return {
            "return_code": "0",
            "ord_no": ord_no,
            "simulated_order": True,
            "actual_order_submitted": False,
        }

    res = kiwoom_orders.send_buy_order(
        code,
        qty,
        final_price,
        order_type_code,
        token=KIWOOM_TOKEN,
        order_type_desc=f"추가매수({add_type})",
    )

    if res is None:
        log_error(f"❌ [{stock.get('name')}] 추가매수 주문 전송 실패 (None 반환)")
        log_info(f"[ADD_ORDER_SENT] {stock.get('name')}({code}) failed=None_response")
        return None

    if isinstance(res, dict):
        rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
        if rt_cd == '0':
            ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            now_ts = time.time()
            set_fields = {
                'pending_add_order': True,
                'pending_add_type': add_type,
                'pending_add_reason': action.get('reason'),
                'pending_add_qty': qty,
                'pending_add_ord_no': ord_no,
                'pending_add_requested_at': now_ts,
                'add_order_time': now_ts,
            }
            if swing_real_canary_fields is not None:
                day_key = str(swing_real_canary_fields.get("day_key") or _swing_scale_in_real_canary_daily_key(now_ts))
                previous_count = int(stock.get("swing_scale_in_real_canary_order_count", 0) or 0)
                previous_notional = int(stock.get("swing_scale_in_real_canary_notional_krw", 0) or 0)
                order_notional = int(swing_real_canary_fields.get("order_notional_krw", 0) or 0)
                set_fields.update(
                    {
                        "cohort": "swing_scale_in_real_canary_phase0",
                        "swing_scale_in_real_canary": True,
                        "swing_scale_in_real_canary_order_date": day_key,
                        "swing_scale_in_real_canary_order_count": previous_count + 1,
                        "swing_scale_in_real_canary_notional_krw": previous_notional + order_notional,
                        "last_swing_scale_in_real_canary_arm": add_type,
                        "last_swing_scale_in_real_canary_order_price": final_price,
                        "last_swing_scale_in_real_canary_qty": qty,
                    }
                )
            if ord_no:
                set_fields['add_odno'] = ord_no
            _mutate_stock_state(stock, set_fields=set_fields)

            log_info(
                f"✅ [{stock.get('name')}] 추가매수 주문 전송 완료. "
                f"type={add_type}, qty={qty}, ord_no={ord_no}"
            )
            log_info(
                "[ADD_ORDER_SENT] "
                f"{stock.get('name')}({code}) "
                f"type={add_type} qty={qty} ord_no={ord_no} "
                f"template_qty={template_qty} would_qty={would_qty} effective_qty={effective_qty} "
                f"cap_qty={cap_qty} floor_applied={floor_applied} "
                f"request_price={final_price if strategy in {'SCALPING', 'KOSPI_ML', 'KOSDAQ_ML'} else '-'} qty_reason={qty_reason}"
            )
            if swing_real_canary_fields is not None:
                _log_holding_pipeline(
                    stock,
                    code,
                    "swing_scale_in_real_canary_order_submitted",
                    ord_no=ord_no,
                    actual_order_submitted=True,
                    request_qty=qty,
                    request_price=final_price,
                    order_type=order_type_code,
                    **swing_real_canary_fields,
                )
            record_add_history_event(
                DB,
                recommendation_id=stock.get('id'),
                stock_code=code,
                stock_name=stock.get('name'),
                strategy=stock.get('strategy'),
                add_type=add_type,
                event_type='ORDER_SENT',
                order_no=ord_no,
                request_qty=qty,
                request_price=final_price if swing_real_canary_fields is not None else resolved_price if strategy == 'SCALPING' else None,
                prev_buy_price=stock.get('buy_price'),
                prev_buy_qty=stock.get('buy_qty', 0),
                add_count_after=stock.get('add_count', 0),
                reason=action.get('reason'),
            )
            return res

        log_error(f"❌ [{stock.get('name')}] 추가매수 주문 거절: {res.get('return_msg')}")
        log_info(
            "[ADD_ORDER_SENT] "
            f"{stock.get('name')}({code}) failed=reject msg={res.get('return_msg')}"
        )
        return None

    log_error(f"❌ [{stock.get('name')}] 추가매수 주문 전송 실패 (응답 파싱 실패)")
    log_info(f"[ADD_ORDER_SENT] {stock.get('name')}({code}) failed=parse_error")
    return None


def handle_buy_ordered_state(stock, code):
    """
    주문 전송 후(BUY_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 로직을 호출합니다.
    """
    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    highest_prices = HIGHEST_PRICES

    target_id = stock.get('id')
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy

    timeout_sec = _resolve_buy_order_timeout_sec(stock, strategy)

    if _has_open_pending_entry_orders(stock) and time_elapsed > timeout_sec:
        _reconcile_pending_entry_orders(stock, code, strategy)
        return

    if time_elapsed > timeout_sec:
        log_info(f"⚠️ [{stock['name']}] 매수 대기 {timeout_sec}초 초과. 취소 절차 진입.")
        orig_ord_no = stock.get('odno')

        if not orig_ord_no:
            _mutate_stock_state(
                stock,
                set_fields={'status': 'WATCHING'},
                pop_fields=[
                    'order_time',
                    'odno',
                    'pending_buy_msg',
                    'target_buy_price',
                    'order_price',
                    'buy_qty',
                ],
            )
            _clear_pending_entry_meta(stock)
            with ENTRY_LOCK:
                highest_prices.pop(code, None)
                alerted_stocks.discard(code)

            if strategy == 'SCALPING':
                with ENTRY_LOCK:
                    cooldowns[code] = time.time() + 1200

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({
                        "status": "WATCHING",
                        "buy_price": 0,
                        "buy_qty": 0,
                    })
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 매수 타임아웃 복구 실패: {e}")
            return

        process_order_cancellation(stock, code, orig_ord_no, DB, strategy)


def handle_sell_ordered_state(stock, code):
    """
    주문 전송 후(SELL_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 후 HOLDING으로 롤백합니다.
    """
    sell_order_time = stock.get('sell_order_time', 0)

    if sell_order_time == 0:
        _mutate_stock_state(stock, set_fields={'sell_order_time': time.time()})
        return

    time_elapsed = time.time() - sell_order_time
    target_id = stock.get('id')
    timeout_sec = _rule_int('SELL_TIMEOUT_SEC', 40)

    if time_elapsed > timeout_sec:
        log_error(
            f"⚠️ [{stock['name']}] 매도 대기 {timeout_sec}초 초과. 호가 꼬임/VI 의심 ➡️ "
            "취소 후 HOLDING 롤백 절차 진입."
        )
        orig_ord_no = stock.get('sell_odno')

        if not orig_ord_no:
            log_error(f"🚨 [{stock['name']}] 취소할 원주문번호(odno)가 없습니다. 상태만 HOLDING으로 강제 롤백합니다.")
            _mutate_stock_state(
                stock,
                set_fields={'status': 'HOLDING'},
                pop_fields=['sell_order_time', 'sell_odno', 'pending_sell_msg', 'sell_target_price'],
            )

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 매도 타임아웃 복구 실패: {e}")
            return

        process_sell_cancellation(stock, code, orig_ord_no, DB)


def process_sell_cancellation(stock, code, orig_ord_no, db):
    """미체결 매도 주문을 전량 취소하고 상태를 다시 HOLDING으로 되돌립니다."""
    target_id = stock.get('id')

    res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0)

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    if is_success:
        log_info(f"✅ [{stock['name']}] 미체결 매도 주문 취소 성공! HOLDING(보유) 상태로 복귀합니다.")
        _mutate_stock_state(
            stock,
            set_fields={'status': 'HOLDING'},
            pop_fields=['sell_odno', 'sell_order_time', 'pending_sell_msg', 'sell_target_price'],
        )

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매도 취소 후 HOLDING 복구 실패: {e}")
        return True

    log_error(f"🚨 [{stock['name']}] 매도 취소 실패! (사유: {err_msg})")
    if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음', '체결']):
        log_info(f"💡 [{stock['name']}] 간발의 차이로 이미 매도 체결된 것으로 판단합니다. COMPLETED로 전환.")
        _mutate_stock_state(stock, set_fields={'status': 'COMPLETED'})
        with ENTRY_LOCK:
            HIGHEST_PRICES.pop(code, None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "COMPLETED"})
        except Exception as exc:
            log_error(f"🚨 [DB 에러] {stock['name']} 매도 취소 후 COMPLETED 복구 실패: {exc}")
    return False


def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    """
    미체결 주문의 실제 취소 처리와 DB/메모리 청소를 담당합니다.
    고유 PK(id)를 사용하여 다중 매매 환경에서도 정확한 레코드를 타겟팅합니다.
    """
    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    highest_prices = HIGHEST_PRICES

    target_id = stock.get('id')

    if _has_open_pending_entry_orders(stock):
        result = _cancel_pending_entry_orders(stock, code, force=True)
        if result != 'failed':
            _mutate_stock_state(
                stock,
                set_fields={'status': 'WATCHING'},
                pop_fields=[
                    'odno',
                    'order_time',
                    'pending_buy_msg',
                    'target_buy_price',
                    'order_price',
                    'buy_qty',
                ],
            )
            _clear_entry_arm(stock)
            with ENTRY_LOCK:
                highest_prices.pop(code, None)

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({
                        "status": "WATCHING",
                        "buy_price": 0,
                        "buy_qty": 0,
                    })
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 후 WATCHING 복구 실패: {e}")

        if strategy in ['SCALPING', 'SCALP']:
            with ENTRY_LOCK:
                alerted_stocks.discard(code)
                cooldowns[code] = time.time() + 1200
            return True

    res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0)

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    if is_success:
        log_info(f"✅ [{stock['name']}] 미체결 매수 취소 성공. 감시 상태로 복귀합니다.")
        _mutate_stock_state(
            stock,
            set_fields={'status': 'WATCHING'},
            pop_fields=[
                'odno',
                'order_time',
                'pending_buy_msg',
                'target_buy_price',
                'order_price',
                'buy_qty',
            ],
        )
        _clear_pending_entry_meta(stock)
        with ENTRY_LOCK:
            highest_prices.pop(code, None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({
                    "status": "WATCHING",
                    "buy_price": 0,
                    "buy_qty": 0,
                })
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 후 WATCHING 복구 실패: {e}")

        if strategy in ['SCALPING', 'SCALP']:
            with ENTRY_LOCK:
                alerted_stocks.discard(code)
                cooldowns[code] = time.time() + 1200
            log_info(f"♻️ [{stock['name']}] 스캘핑 취소 완료. 20분 쿨타임 진입.")
        return True

    log_error(f"🚨 [{stock['name']}] 매수 취소 실패! (사유: {err_msg})")
    if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음']):
        log_info(f"💡 [{stock['name']}] 이미 전량 체결된 것으로 판단. HOLDING으로 전환.")
        _mutate_stock_state(stock, set_fields={'status': 'HOLDING'})

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 실패 후 HOLDING 전환 실패: {e}")

    return False
