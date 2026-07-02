"""Bounded entry opportunity recheck for near-BUY scalping candidates."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping


RUNTIME_FAMILY = "entry_opportunity_recheck_runtime"
POLICY_VERSION = "entry_opportunity_recheck_runtime_v1"
DECISION_AUTHORITY = RUNTIME_FAMILY
FORBIDDEN_USES = (
    "threshold_mutation,provider_route_change,order_price_change,"
    "quantity_or_cap_change,broker_guard_bypass,stale_submit_bypass,"
    "cooldown_bypass,hard_safety_bypass"
)

HARD_BLOCK_REASON_TOKENS = frozenset(
    {
        "cooldown",
        "broker",
        "account",
        "deposit",
        "quantity",
        "zero_qty",
        "paused",
        "manual_control",
        "already_holding",
        "open_pending",
        "loss_reentry",
        "hard_stop",
        "protect_stop",
        "emergency",
    }
)


@dataclass(frozen=True)
class EntryOpportunityRecheckConfig:
    enabled: bool = False
    min_ai_score: float = 70.0
    max_ai_score: float = 74.999
    max_recheck_per_symbol: int = 1
    max_daily_recheck: int = 10
    max_daily_buy_recovery: int = 3
    max_ws_age_ms: int = 1500
    forbid_danger: bool = True
    require_fresh_quote: bool = True
    require_explicit_buy_action: bool = True


@dataclass
class EntryOpportunityRecheckState:
    trade_date: str = ""
    daily_recheck_count: int = 0
    daily_buy_recovery_count: int = 0
    symbol_recheck_counts: dict[str, int] = field(default_factory=dict)

    def reset_if_new_day(self, today: str | None = None) -> None:
        resolved = today or date.today().isoformat()
        if self.trade_date == resolved:
            return
        self.trade_date = resolved
        self.daily_recheck_count = 0
        self.daily_buy_recovery_count = 0
        self.symbol_recheck_counts.clear()

    def symbol_count(self, code: Any) -> int:
        return int(self.symbol_recheck_counts.get(str(code or ""), 0) or 0)

    def record_recheck(self, code: Any) -> None:
        key = str(code or "")
        self.daily_recheck_count += 1
        self.symbol_recheck_counts[key] = self.symbol_count(key) + 1

    def record_buy_recovery(self) -> None:
        self.daily_buy_recovery_count += 1


@dataclass(frozen=True)
class EntryOpportunityRecheckDecision:
    allowed: bool
    reason: str
    stage: str
    action: str
    fields: dict[str, Any]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "")
    text = str(raw).strip().lower()
    if not text:
        return bool(default)
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "")
    text = str(raw).strip()
    if not text:
        return int(default)
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return int(default)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "")
    text = str(raw).strip()
    if not text:
        return float(default)
    try:
        return float(text)
    except (TypeError, ValueError):
        return float(default)


def config_from_env() -> EntryOpportunityRecheckConfig:
    prefix = "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_"
    return EntryOpportunityRecheckConfig(
        enabled=_env_bool(f"{prefix}ENABLED", False),
        min_ai_score=_env_float(f"{prefix}MIN_AI_SCORE", 70.0),
        max_ai_score=_env_float(f"{prefix}MAX_AI_SCORE", 74.999),
        max_recheck_per_symbol=max(0, _env_int(f"{prefix}MAX_RECHECK_PER_SYMBOL", 1)),
        max_daily_recheck=max(0, _env_int(f"{prefix}MAX_DAILY_RECHECK", 10)),
        max_daily_buy_recovery=max(0, _env_int(f"{prefix}MAX_DAILY_BUY_RECOVERY", 3)),
        max_ws_age_ms=max(0, _env_int(f"{prefix}MAX_WS_AGE_MS", 1500)),
        forbid_danger=_env_bool(f"{prefix}FORBID_DANGER", True),
        require_fresh_quote=_env_bool(f"{prefix}REQUIRE_FRESH_QUOTE", True),
        require_explicit_buy_action=_env_bool(f"{prefix}REQUIRE_EXPLICIT_BUY_ACTION", True),
    )


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _base_fields(config: EntryOpportunityRecheckConfig) -> dict[str, Any]:
    return {
        "runtime_family": RUNTIME_FAMILY,
        "threshold_family": RUNTIME_FAMILY,
        "policy_version": POLICY_VERSION,
        "metric_role": "bounded_tunable",
        "decision_authority": DECISION_AUTHORITY,
        "window_policy": "same_day_intraday_runtime_state",
        "sample_floor": "not_applicable_runtime_guard",
        "primary_decision_metric": "entry_opportunity_recheck_reason",
        "source_quality_gate": "fresh_ws_and_explicit_ai_buy_when_required",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "entry_opportunity_recheck_enabled": bool(config.enabled),
        "entry_opportunity_recheck_min_ai_score": float(config.min_ai_score),
        "entry_opportunity_recheck_max_ai_score": float(config.max_ai_score),
        "entry_opportunity_recheck_max_recheck_per_symbol": int(config.max_recheck_per_symbol),
        "entry_opportunity_recheck_max_daily_recheck": int(config.max_daily_recheck),
        "entry_opportunity_recheck_max_daily_buy_recovery": int(config.max_daily_buy_recovery),
        "entry_opportunity_recheck_max_ws_age_ms": int(config.max_ws_age_ms),
        "entry_opportunity_recheck_forbid_danger": bool(config.forbid_danger),
        "entry_opportunity_recheck_require_fresh_quote": bool(config.require_fresh_quote),
        "entry_opportunity_recheck_require_explicit_buy_action": bool(config.require_explicit_buy_action),
    }


def _decision(
    *,
    allowed: bool,
    reason: str,
    stage: str,
    action: str,
    config: EntryOpportunityRecheckConfig,
    fields: Mapping[str, Any] | None = None,
) -> EntryOpportunityRecheckDecision:
    merged = _base_fields(config)
    merged.update(fields or {})
    merged["entry_opportunity_recheck_allowed"] = bool(allowed)
    merged["entry_opportunity_recheck_reason"] = reason
    merged["entry_opportunity_recheck_action"] = action
    merged["entry_opportunity_recheck_stage"] = stage
    if not allowed:
        merged["runtime_effect"] = False
        merged["allowed_runtime_apply"] = False
        merged["actual_order_submitted"] = False
        merged["broker_order_forbidden"] = True
    else:
        merged["runtime_effect"] = True
        merged["allowed_runtime_apply"] = True
        merged["actual_order_submitted"] = False
        merged["broker_order_forbidden"] = False
    return EntryOpportunityRecheckDecision(
        allowed=bool(allowed),
        reason=reason,
        stage=stage,
        action=action,
        fields=merged,
    )


def _contains_hard_block(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    return any(token in text for token in HARD_BLOCK_REASON_TOKENS)


def evaluate_blocked_ai_score_recheck(
    *,
    code: Any,
    strategy: Any,
    position_tag: Any,
    ai_score: Any,
    ai_action: Any,
    ws_age_ms: Any,
    latency_state: Any,
    source_stage: Any = "blocked_ai_score",
    source_reason: Any = "blocked_ai_score_below_buy_score_threshold",
    state: EntryOpportunityRecheckState | None = None,
    config: EntryOpportunityRecheckConfig | None = None,
    today: str | None = None,
) -> EntryOpportunityRecheckDecision:
    config = config or config_from_env()
    state = state or EntryOpportunityRecheckState()
    state.reset_if_new_day(today)

    score = _safe_float(ai_score, -1.0)
    action = str(ai_action or "").strip().upper()
    latency = str(latency_state or "").strip().upper()
    ws_age = _safe_int(ws_age_ms, -1)
    base = {
        "entry_opportunity_recheck_source_stage": str(source_stage or ""),
        "entry_opportunity_recheck_source_reason": str(source_reason or ""),
        "entry_opportunity_recheck_ai_score": round(score, 3),
        "entry_opportunity_recheck_ai_action": action or "-",
        "entry_opportunity_recheck_latency_state": latency or "-",
        "entry_opportunity_recheck_ws_age_ms": ws_age if ws_age >= 0 else "-",
        "entry_opportunity_recheck_daily_count": int(state.daily_recheck_count),
        "entry_opportunity_recheck_daily_buy_recovery_count": int(state.daily_buy_recovery_count),
        "entry_opportunity_recheck_symbol_count": int(state.symbol_count(code)),
    }

    if not config.enabled:
        return _decision(
            allowed=False,
            reason="disabled",
            stage="entry_opportunity_recheck_blocked",
            action="disabled",
            config=config,
            fields=base,
        )
    if str(strategy or "").strip().upper() != "SCALPING":
        return _decision(
            allowed=False,
            reason="non_scalping",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if str(position_tag or "").strip().upper() != "SCANNER":
        return _decision(
            allowed=False,
            reason="non_scanner",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if _contains_hard_block(source_stage) or _contains_hard_block(source_reason):
        return _decision(
            allowed=False,
            reason="hard_safety_source_block",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if score < config.min_ai_score or score > config.max_ai_score:
        return _decision(
            allowed=False,
            reason="score_out_of_range",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.require_explicit_buy_action and action != "BUY":
        return _decision(
            allowed=False,
            reason="ai_action_not_buy",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.forbid_danger and latency == "DANGER":
        return _decision(
            allowed=False,
            reason="latency_state_danger",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.require_fresh_quote and (ws_age < 0 or ws_age > config.max_ws_age_ms):
        return _decision(
            allowed=False,
            reason="quote_freshness_not_confirmed",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.max_daily_recheck <= 0 or state.daily_recheck_count >= config.max_daily_recheck:
        return _decision(
            allowed=False,
            reason="daily_recheck_cap_exhausted",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.max_recheck_per_symbol <= 0 or state.symbol_count(code) >= config.max_recheck_per_symbol:
        return _decision(
            allowed=False,
            reason="symbol_recheck_cap_exhausted",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.max_daily_buy_recovery <= 0 or state.daily_buy_recovery_count >= config.max_daily_buy_recovery:
        return _decision(
            allowed=False,
            reason="daily_buy_recovery_cap_exhausted",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )

    return _decision(
        allowed=True,
        reason="near_buy_explicit_ai_buy_fresh_quote",
        stage="entry_opportunity_recheck_normal_buy_reentered",
        action="allow_normal_buy_reentry",
        config=config,
        fields=base,
    )
