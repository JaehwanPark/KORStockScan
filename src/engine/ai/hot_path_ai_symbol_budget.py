"""Process-local per-symbol cadence budget for live hot-path AI calls.

This module owns call cadence only.  It does not choose an AI action, mutate
trading state, or grant broker/order authority.
"""

from __future__ import annotations

import os
import threading
from collections import deque
from dataclasses import dataclass

POLICY_VERSION = "hot_path_ai_symbol_budget_v1"
DEFAULT_WINDOW_SEC = 60.0
DEFAULT_TOTAL_CALLS_PER_WINDOW = 4
DEFAULT_GROUP_CALLS_PER_WINDOW = 2


def _env_float(name: str, default: float) -> float:
    try:
        return max(0.0, float(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return int(default)


def endpoint_group(endpoint: str) -> str:
    normalized = str(endpoint or "unknown").strip().lower()
    if normalized in {"holding_score", "scale_in_holding_score"}:
        return "holding_score"
    if normalized in {"scanner_entry", "rising_missed_entry"}:
        return "scanner_entry"
    return normalized or "unknown"


@dataclass(frozen=True)
class HotPathAISymbolBudgetDecision:
    allowed: bool
    reason: str
    policy_version: str
    code: str
    endpoint: str
    endpoint_group: str
    window_sec: float
    total_count: int
    total_cap: int
    group_count: int
    group_cap: int
    endpoint_age_sec: float | None
    min_interval_sec: float

    def log_fields(self, prefix: str = "hot_path_ai_symbol_budget") -> dict:
        return {
            f"{prefix}_version": self.policy_version,
            f"{prefix}_allowed": bool(self.allowed),
            f"{prefix}_reason": self.reason,
            f"{prefix}_code": self.code,
            f"{prefix}_endpoint": self.endpoint,
            f"{prefix}_endpoint_group": self.endpoint_group,
            f"{prefix}_window_sec": f"{self.window_sec:.3f}",
            f"{prefix}_total_count": int(self.total_count),
            f"{prefix}_total_cap": int(self.total_cap),
            f"{prefix}_group_count": int(self.group_count),
            f"{prefix}_group_cap": int(self.group_cap),
            f"{prefix}_endpoint_age_sec": (
                "-" if self.endpoint_age_sec is None else f"{self.endpoint_age_sec:.3f}"
            ),
            f"{prefix}_min_interval_sec": f"{self.min_interval_sec:.3f}",
            f"{prefix}_metric_role": "ops_volume_diagnostic",
            f"{prefix}_decision_authority": "ai_call_cadence_only",
            f"{prefix}_window_policy": (
                "rolling_process_local_per_symbol_all_live_ai_endpoints"
            ),
            f"{prefix}_sample_floor": "one_live_ai_call_attempt",
            f"{prefix}_primary_decision_metric": (
                "per_symbol_ai_call_count_and_service_share"
            ),
            f"{prefix}_source_quality_gate": (
                "canonical_stock_code_endpoint_and_process_call_record"
            ),
            f"{prefix}_runtime_effect": True,
            f"{prefix}_allowed_runtime_apply": False,
            f"{prefix}_actual_order_submitted": False,
            f"{prefix}_broker_order_forbidden": True,
            f"{prefix}_forbidden_uses": (
                "standalone_buy_or_exit_decision,threshold_mutation,"
                "provider_route_change,order_price_change,quantity_or_cap_change,"
                "broker_guard_bypass"
            ),
        }


class HotPathAISymbolBudget:
    """Atomic rolling budget shared by entry, holding and scale-in call sites."""

    def __init__(
        self,
        *,
        window_sec: float | None = None,
        total_cap: int | None = None,
        group_cap: int | None = None,
    ) -> None:
        self.window_sec = float(
            window_sec
            if window_sec is not None
            else _env_float(
                "KORSTOCKSCAN_HOT_PATH_AI_SYMBOL_BUDGET_WINDOW_SEC",
                DEFAULT_WINDOW_SEC,
            )
        )
        self.total_cap = int(
            total_cap
            if total_cap is not None
            else _env_int(
                "KORSTOCKSCAN_HOT_PATH_AI_SYMBOL_BUDGET_TOTAL_CALLS",
                DEFAULT_TOTAL_CALLS_PER_WINDOW,
            )
        )
        self.group_cap = int(
            group_cap
            if group_cap is not None
            else _env_int(
                "KORSTOCKSCAN_HOT_PATH_AI_SYMBOL_BUDGET_GROUP_CALLS",
                DEFAULT_GROUP_CALLS_PER_WINDOW,
            )
        )
        self._events: dict[str, deque[tuple[float, str]]] = {}
        self._lock = threading.Lock()

    def _prune(self, code: str, now_ts: float) -> deque[tuple[float, str]]:
        events = self._events.get(code, deque())
        cutoff = float(now_ts) - self.window_sec
        while events and events[0][0] <= cutoff:
            events.popleft()
        if not events:
            self._events.pop(code, None)
        return events

    def _decision(
        self,
        *,
        code: str,
        endpoint: str,
        now_ts: float,
        min_interval_sec: float,
        reserve: bool,
    ) -> HotPathAISymbolBudgetDecision:
        canonical_code = str(code or "").strip()
        canonical_endpoint = str(endpoint or "unknown").strip().lower() or "unknown"
        group = endpoint_group(canonical_endpoint)
        with self._lock:
            events = self._prune(canonical_code, float(now_ts))
            group_events = [event for event in events if event[1] == group]
            last_group_ts = group_events[-1][0] if group_events else None
            endpoint_age_sec = (
                None
                if last_group_ts is None
                else max(0.0, float(now_ts) - last_group_ts)
            )
            reason = "allowed"
            allowed = True
            if not canonical_code:
                allowed, reason = False, "missing_code"
            elif len(events) >= self.total_cap:
                allowed, reason = False, "symbol_window_cap"
            elif len(group_events) >= self.group_cap:
                allowed, reason = False, "endpoint_group_window_cap"
            elif endpoint_age_sec is not None and endpoint_age_sec < max(
                0.0, float(min_interval_sec)
            ):
                allowed, reason = False, "endpoint_min_interval"

            if allowed and reserve:
                self._events[canonical_code] = events
                events.append((float(now_ts), group))

            return HotPathAISymbolBudgetDecision(
                allowed=allowed,
                reason=reason,
                policy_version=POLICY_VERSION,
                code=canonical_code,
                endpoint=canonical_endpoint,
                endpoint_group=group,
                window_sec=self.window_sec,
                total_count=len(events),
                total_cap=self.total_cap,
                group_count=len(group_events) + (1 if allowed and reserve else 0),
                group_cap=self.group_cap,
                endpoint_age_sec=endpoint_age_sec,
                min_interval_sec=max(0.0, float(min_interval_sec)),
            )

    def inspect(
        self,
        *,
        code: str,
        endpoint: str,
        now_ts: float,
        min_interval_sec: float = 0.0,
    ) -> HotPathAISymbolBudgetDecision:
        return self._decision(
            code=code,
            endpoint=endpoint,
            now_ts=now_ts,
            min_interval_sec=min_interval_sec,
            reserve=False,
        )

    def reserve(
        self,
        *,
        code: str,
        endpoint: str,
        now_ts: float,
        min_interval_sec: float = 0.0,
    ) -> HotPathAISymbolBudgetDecision:
        return self._decision(
            code=code,
            endpoint=endpoint,
            now_ts=now_ts,
            min_interval_sec=min_interval_sec,
            reserve=True,
        )

    def release(
        self,
        *,
        code: str,
        endpoint: str,
        reserved_at: float,
    ) -> bool:
        """Release one exact reservation that never reached a provider.

        Callers must retain the timestamp returned to their own dispatch state.
        This narrow exact-match API prevents a failed source-quality preflight
        from consuming provider-call cadence while avoiding refunds for another
        concurrent request in the same endpoint group.
        """

        canonical_code = str(code or "").strip()
        group = endpoint_group(endpoint)
        try:
            target_ts = float(reserved_at)
        except (TypeError, ValueError):
            return False
        if not canonical_code or target_ts <= 0.0:
            return False
        with self._lock:
            events = self._events.get(canonical_code)
            if not events:
                return False
            for index in range(len(events) - 1, -1, -1):
                event_ts, event_group = events[index]
                if event_group == group and abs(event_ts - target_ts) <= 1e-6:
                    del events[index]
                    if not events:
                        self._events.pop(canonical_code, None)
                    return True
        return False

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET = HotPathAISymbolBudget()
