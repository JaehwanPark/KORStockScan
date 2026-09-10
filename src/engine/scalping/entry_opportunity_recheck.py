"""Bounded entry opportunity recheck for near-BUY scalping candidates."""

from __future__ import annotations

import os
from hashlib import sha256
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping
from uuid import uuid4

from src.engine.scalping.entry_ai_gate import evaluate_ai_score_prior
from src.engine.scalping.entry_recheck_economics import LEDGER_KEY, terminal_economics
from src.engine.scalping.entry_recheck_policy import (
    ATTRIBUTION_VERSION,
    SCOPES,
    canonical_wait_probe_contract,
    finite_number,
    runtime_scope,
)

RUNTIME_FAMILY = "entry_opportunity_recheck_runtime"
POLICY_VERSION = "entry_opportunity_recheck_runtime_v4"
DECISION_AUTHORITY = RUNTIME_FAMILY
DIRECT_SUBMIT_MAX_DELAY_SEC = 120.0
ATTRIBUTION_KEYS = (
    "entry_opportunity_recheck_attempt_id",
    "entry_opportunity_recheck_armed",
    "entry_opportunity_recheck_armed_at",
    "entry_opportunity_recheck_source_stage",
    "entry_opportunity_recheck_score",
    "entry_opportunity_recheck_reason",
    "entry_opportunity_recheck_ai_action",
    "entry_opportunity_recheck_probe_only",
    "entry_opportunity_recheck_probe_intent",
    "entry_opportunity_recheck_submit_observed",
    "entry_opportunity_recheck_submitted_at",
    "entry_opportunity_recheck_submit_delay_sec",
    "entry_opportunity_recheck_direct_submit",
    "entry_opportunity_recheck_broker_order_no",
    "entry_opportunity_recheck_requested_qty",
    "entry_opportunity_recheck_fill_observed",
    "entry_opportunity_recheck_filled_at",
    "entry_opportunity_recheck_fill_order_no",
    "entry_opportunity_recheck_fill_price",
    "entry_opportunity_recheck_fill_qty",
    "entry_opportunity_recheck_scope",
    "entry_opportunity_recheck_attribution_schema",
    "entry_opportunity_recheck_exploration_probe_only",
    LEDGER_KEY,
)
FORBIDDEN_USES = (
    "threshold_mutation,provider_route_change,order_price_change,"
    "order_quantity_or_position_cap_change,broker_guard_bypass,stale_submit_bypass,"
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


def mint_attempt_id(
    *, record_id: Any, code: Any, observed_at: Any, nonce: str | None = None
) -> str:
    """Mint one opaque identity for an evaluated recheck attempt.

    The ID is intentionally independent from the ordinary lifecycle attempt ID.
    A recommendation record can be evaluated more than once, so record ID and
    symbol alone are not sufficient attribution keys.
    """

    payload = "|".join(
        (
            str(record_id or "missing-record"),
            str(code or "")[:6],
            f"{_safe_float(observed_at, 0.0):.6f}",
            str(nonce or uuid4().hex),
        )
    )
    return f"eor-{sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def attribution_fields(
    stock: Mapping[str, Any] | None,
    *,
    stage: str = "",
    event_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy immutable recheck lineage and terminal economics to an event."""

    if not isinstance(stock, Mapping):
        return {}
    fields = event_fields if isinstance(event_fields, Mapping) else {}
    # Evaluation is a new attempt, not a snapshot of the previous order's
    # custody. Never copy old arm/submit/fill state into that event, even if
    # the new decision is rejected. Existing stock custody remains untouched.
    if stage == "entry_opportunity_recheck_evaluated":
        return {}
    attempt_id = str(stock.get("entry_opportunity_recheck_attempt_id") or "").strip()
    if not attempt_id:
        return {}
    event_attempt = str(
        fields.get("entry_opportunity_recheck_attempt_id") or ""
    ).strip()
    if event_attempt and event_attempt != attempt_id:
        return {}
    result = {
        key: stock.get(key)
        for key in ATTRIBUTION_KEYS
        if key != LEDGER_KEY and stock.get(key) not in (None, "", "-")
    }
    result.update(
        {
            "entry_opportunity_recheck_attempt_id": attempt_id,
            "entry_opportunity_recheck_attribution_schema": (
                stock.get("entry_opportunity_recheck_attribution_schema")
                or "entry_opportunity_recheck_exact_attempt_v1"
            ),
            "entry_opportunity_recheck_runtime_family": RUNTIME_FAMILY,
        }
    )
    if stage in {"sell_completed", "entry_opportunity_recheck_sell_completed"}:
        if (
            LEDGER_KEY in stock
            or stock.get("entry_opportunity_recheck_attribution_schema")
            == ATTRIBUTION_VERSION
        ):
            result.update(terminal_economics(stock, fields))
            result["entry_opportunity_recheck_terminal_outcome"] = "sell_completed"
            return result
        profit_rate = fields.get(
            "entry_opportunity_recheck_cost_adjusted_profit_pct",
            fields.get("profit_rate"),
        )
        realized_pnl = fields.get("realized_pnl_krw")
        if realized_pnl in (None, "", "-"):
            realized_pnl = fields.get("main_lifecycle_realized_net_pnl_krw")
        result.update(
            {
                "entry_opportunity_recheck_terminal_outcome": "sell_completed",
                "entry_opportunity_recheck_cost_adjusted_profit_pct": profit_rate,
                "entry_opportunity_recheck_realized_net_pnl_krw": realized_pnl,
                "entry_opportunity_recheck_economics_complete": (
                    _truthy(fields.get("sell_execution_receipt_economics_complete"))
                    and finite_number(fields.get("cumulative_sell_qty")) == 1
                ),
                "entry_opportunity_recheck_economics_source": (
                    "broker_sell_completed_receipt"
                ),
            }
        )
    return result


@dataclass(frozen=True)
class EntryOpportunityRecheckConfig:
    enabled: bool = False
    allowed_scopes: frozenset[str] = frozenset()
    intraday_escalation_scopes: frozenset[str] = frozenset()
    min_ai_score: float = 69.0
    max_ai_score: float = 74.999
    max_recheck_per_symbol: int = 1
    max_daily_recheck: int = 10
    max_daily_buy_recovery: int = 3
    max_ws_age_ms: int = 1500
    forbid_danger: bool = True
    require_fresh_quote: bool = True
    require_explicit_buy_action: bool = True
    allow_wait_probe_intent: bool = False
    require_probe_first_contract: bool = True
    probe_first_enabled: bool = False
    probe_first_active_date: str = ""
    probe_qty: int = 1
    post_probe_resolver_enabled: bool = False
    intraday_escalation_enabled: bool = False
    escalation_step_recheck: int = 10
    escalation_step_buy_recovery: int = 2
    escalation_max_daily_recheck: int = 30
    escalation_max_daily_buy_recovery: int = 7
    escalation_min_successful_recoveries: int = 2
    escalation_min_avg_profit_pct: float = 0.0
    escalation_min_peak_profit_pct: float = 0.3
    escalation_max_worst_profit_pct: float = -0.6


@dataclass
class EntryOpportunityRecheckState:
    trade_date: str = ""
    daily_recheck_count: int = 0
    daily_buy_recovery_count: int = 0
    daily_exploration_probe_submit_count: int = 0
    symbol_recheck_counts: dict[str, int] = field(default_factory=dict)
    effective_max_daily_recheck_by_scope: dict[str, int] = field(default_factory=dict)
    effective_max_daily_buy_recovery_by_scope: dict[str, int] = field(
        default_factory=dict
    )
    escalation_levels_by_scope: dict[str, int] = field(default_factory=dict)
    recovery_marks: dict[str, dict[str, Any]] = field(default_factory=dict)

    def reset_if_new_day(self, today: str | None = None) -> None:
        resolved = today or date.today().isoformat()
        if self.trade_date == resolved:
            return
        self.trade_date = resolved
        self.daily_recheck_count = 0
        self.daily_buy_recovery_count = 0
        self.daily_exploration_probe_submit_count = 0
        self.symbol_recheck_counts.clear()
        self.effective_max_daily_recheck_by_scope.clear()
        self.effective_max_daily_buy_recovery_by_scope.clear()
        self.escalation_levels_by_scope.clear()
        self.recovery_marks.clear()

    def symbol_count(self, code: Any) -> int:
        return int(self.symbol_recheck_counts.get(str(code or ""), 0) or 0)

    @staticmethod
    def _scope_can_escalate(
        config: EntryOpportunityRecheckConfig, scope: str | None
    ) -> bool:
        return bool(
            scope
            and scope in config.allowed_scopes
            and scope in config.intraday_escalation_scopes
        )

    def daily_recheck_limit(
        self, config: EntryOpportunityRecheckConfig, scope: str | None = None
    ) -> int:
        if not self._scope_can_escalate(config, scope):
            return int(config.max_daily_recheck)
        return int(
            self.effective_max_daily_recheck_by_scope.get(scope or "", 0)
            or config.max_daily_recheck
        )

    def daily_buy_recovery_limit(
        self, config: EntryOpportunityRecheckConfig, scope: str | None = None
    ) -> int:
        if not self._scope_can_escalate(config, scope):
            return int(config.max_daily_buy_recovery)
        return int(
            self.effective_max_daily_buy_recovery_by_scope.get(scope or "", 0)
            or config.max_daily_buy_recovery
        )

    def record_recheck(self, code: Any) -> None:
        key = str(code or "")
        self.daily_recheck_count += 1
        self.symbol_recheck_counts[key] = self.symbol_count(key) + 1

    def record_buy_recovery(self) -> None:
        self.daily_buy_recovery_count += 1

    def record_exploration_probe_submit(self) -> None:
        self.daily_exploration_probe_submit_count += 1

    def sync_exploration_probe_submit_count(self, value: Any) -> None:
        self.daily_exploration_probe_submit_count = max(
            self.daily_exploration_probe_submit_count,
            max(0, _safe_int(value, 0)),
        )

    def record_recovery_mark(
        self,
        code: Any,
        *,
        profit_rate: Any,
        peak_profit: Any,
        status: Any = "open",
        now_ts: Any = None,
        scope: Any = "",
    ) -> None:
        code_key = str(code or "").strip()
        canonical_scope = str(scope or "").strip()
        if not code_key:
            return
        key = f"{canonical_scope}:{code_key}" if canonical_scope else code_key
        profit = _safe_float(profit_rate, 0.0)
        previous = self.recovery_marks.get(key) or {}
        previous_peak = _safe_float(previous.get("peak_profit"), profit)
        peak = max(previous_peak, _safe_float(peak_profit, profit))
        self.recovery_marks[key] = {
            "code": code_key,
            "scope": canonical_scope,
            "profit_rate": round(profit, 4),
            "peak_profit": round(peak, 4),
            "status": str(status or "open"),
            "updated_at": _safe_float(now_ts, 0.0),
        }

    def escalation_snapshot(
        self,
        config: EntryOpportunityRecheckConfig,
        *,
        scope: str | None = None,
    ) -> dict[str, Any]:
        marks = [
            mark
            for mark in self.recovery_marks.values()
            if scope is None or str(mark.get("scope") or "") == scope
        ]
        profits = [_safe_float(mark.get("profit_rate"), 0.0) for mark in marks]
        avg_profit = sum(profits) / len(profits) if profits else 0.0
        worst_profit = min(profits) if profits else None
        successful = [
            mark
            for mark in marks
            if (
                _safe_float(mark.get("profit_rate"), 0.0)
                >= config.escalation_min_avg_profit_pct
            )
            and (
                _safe_float(mark.get("peak_profit"), 0.0)
                >= config.escalation_min_peak_profit_pct
            )
        ]
        return {
            "entry_opportunity_recheck_recovery_mark_count": len(marks),
            "entry_opportunity_recheck_successful_recovery_count": len(successful),
            "entry_opportunity_recheck_recovery_avg_profit_pct": round(avg_profit, 4),
            "entry_opportunity_recheck_recovery_worst_profit_pct": (
                "-" if worst_profit is None else round(worst_profit, 4)
            ),
        }

    def escalation_fields(
        self,
        config: EntryOpportunityRecheckConfig,
        *,
        scope: str | None = None,
        attempt_reason: str = "not_evaluated",
    ) -> dict[str, Any]:
        scope_approved = self._scope_can_escalate(config, scope)
        fields = {
            "entry_opportunity_recheck_intraday_escalation_enabled": (
                bool(config.intraday_escalation_enabled)
            ),
            "entry_opportunity_recheck_escalation_level": int(
                self.escalation_levels_by_scope.get(scope or "", 0)
            ),
            "entry_opportunity_recheck_intraday_escalation_scopes": ",".join(
                sorted(config.intraday_escalation_scopes)
            ),
            "entry_opportunity_recheck_scope_escalation_approved": scope_approved,
            "entry_opportunity_recheck_effective_max_daily_recheck": self.daily_recheck_limit(
                config, scope
            ),
            "entry_opportunity_recheck_effective_max_daily_buy_recovery": (
                self.daily_buy_recovery_limit(config, scope)
            ),
            "entry_opportunity_recheck_escalation_step_recheck": int(
                config.escalation_step_recheck
            ),
            "entry_opportunity_recheck_escalation_step_buy_recovery": int(
                config.escalation_step_buy_recovery
            ),
            "entry_opportunity_recheck_escalation_max_daily_recheck": int(
                config.escalation_max_daily_recheck
            ),
            "entry_opportunity_recheck_escalation_max_daily_buy_recovery": int(
                config.escalation_max_daily_buy_recovery
            ),
            "entry_opportunity_recheck_escalation_min_successful_recoveries": int(
                config.escalation_min_successful_recoveries
            ),
            "entry_opportunity_recheck_escalation_min_avg_profit_pct": float(
                config.escalation_min_avg_profit_pct
            ),
            "entry_opportunity_recheck_escalation_min_peak_profit_pct": float(
                config.escalation_min_peak_profit_pct
            ),
            "entry_opportunity_recheck_escalation_max_worst_profit_pct": float(
                config.escalation_max_worst_profit_pct
            ),
            "entry_opportunity_recheck_escalation_attempt_reason": attempt_reason,
        }
        fields.update(self.escalation_snapshot(config, scope=scope))
        return fields

    def maybe_escalate_intraday(
        self, config: EntryOpportunityRecheckConfig, *, scope: str
    ) -> str:
        if not config.intraday_escalation_enabled:
            return "disabled"
        if not self._scope_can_escalate(config, scope):
            return "scope_not_approved"
        if config.max_daily_recheck <= 0 or config.max_daily_buy_recovery <= 0:
            return "base_cap_disabled"

        current_recheck_limit = self.daily_recheck_limit(config, scope)
        current_recovery_limit = self.daily_buy_recovery_limit(config, scope)
        recheck_exhausted = (
            current_recheck_limit <= 0
            or self.daily_recheck_count >= current_recheck_limit
        )
        recovery_exhausted = (
            current_recovery_limit <= 0
            or self.daily_buy_recovery_count >= current_recovery_limit
        )
        if not recheck_exhausted and not recovery_exhausted:
            return "cap_not_exhausted"

        max_recheck = max(
            int(config.max_daily_recheck), int(config.escalation_max_daily_recheck)
        )
        max_recovery = max(
            int(config.max_daily_buy_recovery),
            int(config.escalation_max_daily_buy_recovery),
        )
        if (
            current_recheck_limit >= max_recheck
            and current_recovery_limit >= max_recovery
        ):
            return "max_cap_reached"

        snapshot = self.escalation_snapshot(config, scope=scope)
        if (
            int(snapshot["entry_opportunity_recheck_successful_recovery_count"])
            < config.escalation_min_successful_recoveries
        ):
            return "successful_recovery_floor_not_met"

        worst_profit = snapshot["entry_opportunity_recheck_recovery_worst_profit_pct"]
        if (
            worst_profit != "-"
            and _safe_float(worst_profit, 0.0) < config.escalation_max_worst_profit_pct
        ):
            return "worst_profit_guard_block"
        if (
            _safe_float(
                snapshot["entry_opportunity_recheck_recovery_avg_profit_pct"], 0.0
            )
            < config.escalation_min_avg_profit_pct
        ):
            return "avg_profit_floor_not_met"

        self.effective_max_daily_recheck_by_scope[scope] = min(
            max_recheck,
            max(current_recheck_limit, int(config.max_daily_recheck))
            + max(0, int(config.escalation_step_recheck)),
        )
        self.effective_max_daily_buy_recovery_by_scope[scope] = min(
            max_recovery,
            max(current_recovery_limit, int(config.max_daily_buy_recovery))
            + max(0, int(config.escalation_step_buy_recovery)),
        )
        self.escalation_levels_by_scope[scope] = (
            self.escalation_levels_by_scope.get(scope, 0) + 1
        )
        return "escalated"


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


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def config_from_env() -> EntryOpportunityRecheckConfig:
    prefix = "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_"
    return EntryOpportunityRecheckConfig(
        enabled=_env_bool(f"{prefix}ENABLED", False),
        min_ai_score=_env_float(f"{prefix}MIN_AI_SCORE", 70.0),
        max_ai_score=_env_float(f"{prefix}MAX_AI_SCORE", 74.999),
        max_recheck_per_symbol=max(0, _env_int(f"{prefix}MAX_RECHECK_PER_SYMBOL", 1)),
        max_daily_recheck=max(0, _env_int(f"{prefix}MAX_DAILY_RECHECK", 10)),
        max_daily_buy_recovery=max(0, _env_int(f"{prefix}MAX_DAILY_BUY_RECOVERY", 3)),
        allowed_scopes=frozenset(
            scope.strip()
            for scope in os.getenv(f"{prefix}ALLOWED_SCOPES", "").split(",")
            if scope.strip() in SCOPES
        ),
        intraday_escalation_scopes=frozenset(
            scope.strip()
            for scope in os.getenv(f"{prefix}INTRADAY_ESCALATION_SCOPES", "").split(",")
            if scope.strip() in SCOPES
        ),
        max_ws_age_ms=max(0, _env_int(f"{prefix}MAX_WS_AGE_MS", 1500)),
        forbid_danger=_env_bool(f"{prefix}FORBID_DANGER", True),
        require_fresh_quote=_env_bool(f"{prefix}REQUIRE_FRESH_QUOTE", True),
        require_explicit_buy_action=_env_bool(
            f"{prefix}REQUIRE_EXPLICIT_BUY_ACTION", True
        ),
        allow_wait_probe_intent=_env_bool(f"{prefix}ALLOW_WAIT_PROBE_INTENT", False),
        require_probe_first_contract=_env_bool(
            f"{prefix}REQUIRE_PROBE_FIRST_CONTRACT", True
        ),
        probe_first_enabled=_env_bool(
            "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", False
        ),
        probe_first_active_date=str(
            os.getenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "") or ""
        ).strip(),
        probe_qty=_env_int("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", 0),
        post_probe_resolver_enabled=_env_bool(
            "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", False
        ),
        intraday_escalation_enabled=_env_bool(
            f"{prefix}INTRADAY_ESCALATION_ENABLED", False
        ),
        escalation_step_recheck=max(
            0, _env_int(f"{prefix}ESCALATION_STEP_RECHECK", 10)
        ),
        escalation_step_buy_recovery=max(
            0, _env_int(f"{prefix}ESCALATION_STEP_BUY_RECOVERY", 2)
        ),
        escalation_max_daily_recheck=max(
            0, _env_int(f"{prefix}ESCALATION_MAX_DAILY_RECHECK", 30)
        ),
        escalation_max_daily_buy_recovery=max(
            0,
            _env_int(f"{prefix}ESCALATION_MAX_DAILY_BUY_RECOVERY", 7),
        ),
        escalation_min_successful_recoveries=max(
            0,
            _env_int(f"{prefix}ESCALATION_MIN_SUCCESSFUL_RECOVERIES", 2),
        ),
        escalation_min_avg_profit_pct=_env_float(
            f"{prefix}ESCALATION_MIN_AVG_PROFIT_PCT", 0.0
        ),
        escalation_min_peak_profit_pct=_env_float(
            f"{prefix}ESCALATION_MIN_PEAK_PROFIT_PCT", 0.3
        ),
        escalation_max_worst_profit_pct=_env_float(
            f"{prefix}ESCALATION_MAX_WORST_PROFIT_PCT",
            -0.6,
        ),
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
        "source_quality_gate": (
            "trusted_edge_wait_recovery_probe_intent_fresh_ws_strong_micro_"
            "and_probe_first_post_probe_contract"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "entry_opportunity_recheck_enabled": bool(config.enabled),
        "entry_opportunity_recheck_min_ai_score": float(config.min_ai_score),
        "entry_opportunity_recheck_max_ai_score": float(config.max_ai_score),
        "entry_opportunity_recheck_max_recheck_per_symbol": int(
            config.max_recheck_per_symbol
        ),
        "entry_opportunity_recheck_max_daily_recheck": int(config.max_daily_recheck),
        "entry_opportunity_recheck_max_daily_buy_recovery": int(
            config.max_daily_buy_recovery
        ),
        "entry_opportunity_recheck_max_ws_age_ms": int(config.max_ws_age_ms),
        "entry_opportunity_recheck_forbid_danger": bool(config.forbid_danger),
        "entry_opportunity_recheck_require_fresh_quote": bool(
            config.require_fresh_quote
        ),
        "entry_opportunity_recheck_require_explicit_buy_action": bool(
            config.require_explicit_buy_action
        ),
        "entry_opportunity_recheck_allow_wait_probe_intent": bool(
            config.allow_wait_probe_intent
        ),
        "entry_opportunity_recheck_require_probe_first_contract": bool(
            config.require_probe_first_contract
        ),
        "entry_opportunity_recheck_probe_first_enabled": bool(
            config.probe_first_enabled
        ),
        "entry_opportunity_recheck_probe_first_active_date": (
            config.probe_first_active_date or "-"
        ),
        "entry_opportunity_recheck_probe_qty": int(config.probe_qty),
        "entry_opportunity_recheck_post_probe_resolver_enabled": bool(
            config.post_probe_resolver_enabled
        ),
        "entry_opportunity_recheck_intraday_escalation_enabled": bool(
            config.intraday_escalation_enabled
        ),
        "entry_opportunity_recheck_intraday_escalation_scopes": ",".join(
            sorted(config.intraday_escalation_scopes)
        ),
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
    effective_venue: Any = "UNKNOWN",
    market_session_bucket: Any = "UNKNOWN",
    source_stage: Any = "blocked_ai_score",
    source_reason: Any = "entry_policy_no_buy_score_prior",
    ai_contract_status: Any = None,
    ai_edge_state: Any = None,
    ai_probe_intent: Any = False,
    ai_probe_intent_status: Any = None,
    ai_recovery_trigger: Any = None,
    microstructure_confirmed: Any = False,
    microstructure_fields: Mapping[str, Any] | None = None,
    buy_recovery_cap_observed_count: int | None = None,
    buy_recovery_cap_source_quality_ok: bool = True,
    buy_recovery_cap_source_status: str = "",
    state: EntryOpportunityRecheckState | None = None,
    config: EntryOpportunityRecheckConfig | None = None,
    today: str | None = None,
) -> EntryOpportunityRecheckDecision:
    config = config or config_from_env()
    state = state or EntryOpportunityRecheckState()
    state.reset_if_new_day(today)

    effective_buy_recovery_cap_count = (
        int(state.daily_buy_recovery_count)
        if buy_recovery_cap_observed_count is None
        else max(0, _safe_int(buy_recovery_cap_observed_count, 0))
    )
    budget_bootstrap_pending = bool(
        not buy_recovery_cap_source_quality_ok
        and buy_recovery_cap_source_status
        in {"bootstrap_pending", "bootstrap_pending_other_date"}
    )

    score = _safe_float(ai_score, -1.0)
    action = str(ai_action or "").strip().upper()
    latency = str(latency_state or "").strip().upper()
    contract_status = str(ai_contract_status or "").strip().lower()
    edge_state = str(ai_edge_state or "").strip().upper()
    probe_intent = _truthy(ai_probe_intent)
    probe_intent_status = str(ai_probe_intent_status or "").strip().lower()
    recovery_trigger = str(ai_recovery_trigger or "").strip().lower()
    micro_confirmed = _truthy(microstructure_confirmed)
    ws_age = _safe_int(ws_age_ms, -1)
    score_prior = evaluate_ai_score_prior(
        action,
        score,
        {
            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": config.min_ai_score,
        },
        threshold_key="ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
        default_threshold=config.min_ai_score,
        usable=score >= 0,
    )
    score_in_prior_band = bool(config.min_ai_score <= score <= config.max_ai_score)
    base = {
        "entry_opportunity_recheck_scope": runtime_scope(
            effective_venue, market_session_bucket
        ),
        "entry_opportunity_recheck_source_stage": str(source_stage or ""),
        "entry_opportunity_recheck_source_reason": str(source_reason or ""),
        "entry_opportunity_recheck_ai_score": round(score, 3),
        "entry_opportunity_recheck_ai_action": action or "-",
        "entry_opportunity_recheck_score_gate_converted_to_prior": True,
        "entry_opportunity_recheck_score_in_prior_band": score_in_prior_band,
        "entry_opportunity_recheck_score_prior_band": score_prior.get(
            "score_prior_band"
        ),
        "entry_opportunity_recheck_ai_score_prior_weight": score_prior.get(
            "ai_score_prior_weight"
        ),
        "entry_opportunity_recheck_score_prior_reason": score_prior.get(
            "score_prior_reason"
        ),
        "entry_opportunity_recheck_hard_gate_veto": False,
        "entry_opportunity_recheck_latency_state": latency or "-",
        "entry_opportunity_recheck_ws_age_ms": ws_age if ws_age >= 0 else "-",
        "entry_opportunity_recheck_daily_count": int(state.daily_recheck_count),
        "entry_opportunity_recheck_daily_buy_recovery_count": int(
            state.daily_buy_recovery_count
        ),
        "entry_opportunity_recheck_buy_recovery_cap_observed_count": (
            effective_buy_recovery_cap_count
            if buy_recovery_cap_source_quality_ok
            else None
        ),
        "entry_opportunity_recheck_buy_recovery_cap_basis": (
            "unavailable_ledger"
            if not buy_recovery_cap_source_quality_ok
            else (
                "in_memory_recovery_count"
                if buy_recovery_cap_observed_count is None
                else "caller_verified_reservations_and_submissions"
            )
        ),
        "entry_opportunity_recheck_symbol_count": int(state.symbol_count(code)),
        "entry_opportunity_recheck_ai_contract_status": contract_status or "unreported",
        "entry_opportunity_recheck_ai_edge_state": edge_state or "-",
        "entry_opportunity_recheck_ai_probe_intent": probe_intent,
        "entry_opportunity_recheck_ai_probe_intent_status": (
            probe_intent_status or "not_reported"
        ),
        "entry_opportunity_recheck_ai_recovery_trigger": recovery_trigger or "-",
        "entry_opportunity_recheck_canonical_probe_candidate": canonical_wait_probe_contract(
            action=action,
            contract_status=contract_status,
            edge_state=edge_state,
            probe_intent=probe_intent,
            probe_intent_status=probe_intent_status,
            recovery_trigger=recovery_trigger,
        ),
        "entry_opportunity_recheck_microstructure_confirmed": micro_confirmed,
    }
    base.update(dict(microstructure_fields or {}))
    current_scope = str(base["entry_opportunity_recheck_scope"])
    base.update(state.escalation_fields(config, scope=current_scope))

    if not config.enabled:
        return _decision(
            allowed=False,
            reason="disabled",
            stage="entry_opportunity_recheck_blocked",
            action="disabled",
            config=config,
            fields=base,
        )
    if not buy_recovery_cap_source_quality_ok and not budget_bootstrap_pending:
        return _decision(
            allowed=False,
            reason="recheck_submit_budget_ledger_invalid",
            stage="entry_opportunity_recheck_blocked",
            action="block",
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
    if base["entry_opportunity_recheck_scope"] not in config.allowed_scopes:
        return _decision(
            allowed=False,
            reason="scope_not_selected_by_drought_policy",
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
    if action == "BUY":
        return _decision(
            allowed=False,
            reason="normal_buy_does_not_require_recheck",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if config.require_explicit_buy_action:
        return _decision(
            allowed=False,
            reason="legacy_explicit_buy_contract_incompatible",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if not config.allow_wait_probe_intent:
        return _decision(
            allowed=False,
            reason="wait_probe_intent_not_enabled",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if action not in {"WAIT", "WAIT_REQUOTE"}:
        return _decision(
            allowed=False,
            reason="ai_action_not_supported_wait",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if not canonical_wait_probe_contract(
        action=action,
        contract_status=contract_status,
        edge_state=edge_state,
        probe_intent=probe_intent,
        probe_intent_status=probe_intent_status,
        recovery_trigger=recovery_trigger,
    ):
        return _decision(
            allowed=False,
            reason="canonical_wait_probe_contract_not_confirmed",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    probe_date_active = config.probe_first_active_date.upper() in {
        str(today or date.today().isoformat()),
        "DAILY",
    }
    probe_contract_active = bool(
        config.probe_first_enabled
        and probe_date_active
        and config.probe_qty == 1
        and config.post_probe_resolver_enabled
    )
    base["entry_opportunity_recheck_probe_first_contract_active"] = (
        probe_contract_active
    )
    if not config.require_probe_first_contract:
        return _decision(
            allowed=False,
            reason="probe_first_contract_requirement_disabled",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if not probe_contract_active:
        return _decision(
            allowed=False,
            reason="probe_first_post_probe_contract_not_active",
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
    if budget_bootstrap_pending:
        return _decision(
            allowed=False,
            reason="recheck_submit_budget_bootstrap_pending",
            stage="entry_opportunity_recheck_blocked",
            action="wait_for_submit_budget_bootstrap",
            config=config,
            fields=base,
        )
    if not micro_confirmed:
        return _decision(
            allowed=False,
            reason="strong_micro_confirmation_missing",
            stage="entry_opportunity_recheck_blocked",
            action="wait_for_recovery_micro",
            config=config,
            fields=base,
        )
    escalation_attempt_reason = state.maybe_escalate_intraday(
        config, scope=current_scope
    )
    base.update(
        state.escalation_fields(
            config,
            scope=current_scope,
            attempt_reason=escalation_attempt_reason,
        )
    )
    daily_recheck_limit = state.daily_recheck_limit(config, current_scope)
    daily_buy_recovery_limit = state.daily_buy_recovery_limit(config, current_scope)

    if daily_recheck_limit <= 0 or state.daily_recheck_count >= daily_recheck_limit:
        return _decision(
            allowed=False,
            reason="daily_recheck_cap_exhausted",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if (
        config.max_recheck_per_symbol <= 0
        or state.symbol_count(code) >= config.max_recheck_per_symbol
    ):
        return _decision(
            allowed=False,
            reason="symbol_recheck_cap_exhausted",
            stage="entry_opportunity_recheck_blocked",
            action="block",
            config=config,
            fields=base,
        )
    if (
        daily_buy_recovery_limit <= 0
        or effective_buy_recovery_cap_count >= daily_buy_recovery_limit
    ):
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
        reason="edge_wait_recovery_probe_intent_fresh_strong_micro",
        stage="entry_opportunity_recheck_probe_armed",
        action="allow_one_share_probe_entry",
        config=config,
        fields=base,
    )
