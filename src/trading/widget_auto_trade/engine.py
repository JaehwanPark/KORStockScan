"""Daily-reset live execution state machine for widget advisory signals."""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, time as datetime_time
from functools import lru_cache
from inspect import Parameter, signature
from pathlib import Path
from typing import Any, Callable, Protocol

from src.engine.monitoring import doosan_widget_contract as doosan_contract
from src.engine.monitoring import hanwha_ocean_widget_contract as hanwha_contract
from src.engine.monitoring import samsung_widget_contract as samsung_contract
from src.engine.monitoring.widget_symbol_runtime_contract import (
    CONTRACTS as WIDGET_SYMBOL_RUNTIME_CONTRACTS,
)
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.risk.manual_control_exclusion import (
    evaluate_manual_control_exclusion,
    manual_control_operator_exclusion_source,
)
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_up_by_bps
from src.trading.widget_auto_trade.gateway import (
    ExecutionSnapshot,
    KiwoomSharedTokenOrderGateway,
    SubmitResult,
    resolve_widget_broker_route,
)
from src.trading.widget_auto_trade.policy import (
    WIDGET_AUTO_TRADE_LEG_QUANTITY,
    WidgetAutoTradePolicyLoader,
)
from src.utils.constants import PROJECT_ROOT

EXECUTION_AUTHORITY = "operator_directed_widget_auto_trade_v1"
STATE_SCHEMA_VERSION = 1
EVENT_SCHEMA = "widget_signal_auto_trade_event_v1"
DEFAULT_STATE_PATH = PROJECT_ROOT / "data/runtime/widget_signal_auto_trade_state.json"
DEFAULT_EVENT_DIR = PROJECT_ROOT / "data/report/widget_signal_auto_trade_events"
ACTIONABLE_ENTRY_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
FINAL_EXIT_STATE = "EXIT_READY"
ACTIVE_ORDER_STATUSES = frozenset(
    {
        "SUBMITTING",
        "SUBMITTED",
        "AMBIGUOUS",
        "CANCEL_REQUESTED",
        "CANCEL_AMBIGUOUS",
        "CANCEL_FAILED_TERMINAL",
    }
)
MAX_ENTRY_QTY = 100
MAX_CANCEL_ATTEMPTS = 3
MAX_SELL_ATTEMPTS = 3
SELL_RETRY_SEC = 5
TAKE_PROFIT_BPS = 100
CUMULATIVE_RESEARCH_BLOCK_REASONS = frozenset(
    {
        "research_accumulation_incomplete",
        "cumulative_research_40_qualified_dates_incomplete",
    }
)
SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID = "SAMSUNG_EQUAL_10_ADD0P5_ADD1P0_TP0P5_V2"
SAMSUNG_DAILY_EQUAL_SHARE_POLICY = {
    "policy_id": SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    "research_arm": "three_equal_10share_add0p5_1p0_tp0p5",
    "evidence_window": "2026-06-05_2026-08-10",
    "evidence_artifact": (
        "data/report/pure_market_adaptive_opportunity_replay/"
        "pure_market_adaptive_opportunity_replay_2026-06-05_2026-08-10.json"
    ),
    "leg_quantity_each": WIDGET_AUTO_TRADE_LEG_QUANTITY,
    "add_trigger_bps_from_initial_fill": (-50, -100),
    "take_profit_bps_from_equal_share_average": 50,
    "allowed_entry_sessions": ("KRX_REGULAR",),
    "allowed_entry_venues": ("KRX",),
    "allowed_entry_states": ("ENTRY_CAUTION", "ENTRY_READY"),
    "max_completed_entries_per_day": 3,
    "reentry_cooldown_minutes": 10,
    "new_entry_cutoff_time": "15:00:00",
    "force_flat_at_session_end": False,
    "force_exit_time": None,
    "overnight_forbidden": False,
    "additional_leg_window": "original_entry_session_only",
    "source_final_exit_action": "observe_only_no_forced_sell",
    "unhit_policy": "daily_reset_unmanaged_overnight_inventory",
}
MAX_TAKE_PROFIT_FAILURES = 3
OBSERVABILITY_PERSIST_INTERVAL_SEC = 60
POLICY_CATALOG_REFRESH_INTERVAL_SEC = 30

ORDER_ROLE_ENTRY_BUY = "ENTRY_BUY"
ORDER_ROLE_SCALE_IN_BUY = "SCALE_IN_BUY"
ORDER_ROLE_TAKE_PROFIT = "TAKE_PROFIT_SELL"
ORDER_ROLE_FINAL_EXIT = "FINAL_EXIT_SELL"

EXECUTION_CONTRACT = {
    "metric_role": "execution_quality_real_only",
    "decision_authority": EXECUTION_AUTHORITY,
    "window_policy": "trade_date_only_reset_without_overnight_management",
    "sample_floor": "one_source_qualified_unique_widget_entry_signal",
    "primary_decision_metric": "broker_filled_widget_owned_quantity",
    "source_quality_gate": (
        "fresh_contract_valid_widget_snapshot_and_unique_signal;"
        "shared_cached_token_only;exact_order_number_fill_reconciliation"
    ),
    "forbidden_uses": [
        "sell_prior_day_widget_quantity",
        "sell_manual_or_other_strategy_quantity",
        "token_issue_or_refresh",
        "orderable_cash_precheck",
        "non_take_profit_non_final_exit_submission",
        "source_signal_threshold_mutation",
        "main_bot_process_control",
    ],
}


class OrderGateway(Protocol):
    def submit_buy(self, *, code: str, qty: int, route: str) -> SubmitResult: ...

    def submit_sell(self, *, code: str, qty: int, route: str) -> SubmitResult: ...

    def submit_limit_sell(
        self, *, code: str, qty: int, route: str, price: int
    ) -> SubmitResult: ...

    def cancel(
        self, *, code: str, order_no: str, qty: int, route: str
    ) -> SubmitResult: ...

    def execution_snapshot(
        self,
        *,
        code: str,
        order_no: str,
        route: str,
        order_date: str,
    ) -> ExecutionSnapshot: ...


class EntryActionNotifier(Protocol):
    def notify_order_accepted(
        self,
        *,
        symbol: str,
        name: str,
        order: dict[str, Any],
        execution_policy_id: str | None,
        observed_at: datetime,
    ) -> str: ...


@dataclass(frozen=True)
class WidgetSpec:
    code: str
    name: str
    snapshot_path: Path
    contract: Any
    event_based: bool
    structural_execution_qualification: bool = False
    execution_policy_id: str | None = None
    dated_policy_required: bool = False


DEFAULT_WIDGET_SPECS = (
    WidgetSpec(
        samsung_contract.SAMSUNG_CODE,
        samsung_contract.SAMSUNG_NAME,
        samsung_contract.DEFAULT_SNAPSHOT_PATH,
        samsung_contract,
        False,
        True,
    ),
    WidgetSpec(
        doosan_contract.DOOSAN_CODE,
        doosan_contract.DOOSAN_NAME,
        doosan_contract.DEFAULT_SNAPSHOT_PATH,
        doosan_contract,
        True,
        dated_policy_required=True,
    ),
    WidgetSpec(
        hanwha_contract.HANWHA_OCEAN_CODE,
        hanwha_contract.HANWHA_OCEAN_NAME,
        hanwha_contract.DEFAULT_SNAPSHOT_PATH,
        hanwha_contract,
        True,
        dated_policy_required=True,
    ),
)

CALIBRATED_WIDGET_SPECS = tuple(
    WidgetSpec(
        contract.code,
        contract.name,
        contract.DEFAULT_SNAPSHOT_PATH,
        contract,
        True,
        dated_policy_required=True,
    )
    for contract in WIDGET_SYMBOL_RUNTIME_CONTRACTS.values()
)

ALL_WIDGET_SPECS = DEFAULT_WIDGET_SPECS + CALIBRATED_WIDGET_SPECS

SnapshotLoader = Callable[[Path], dict[str, Any]]


def _now_kst() -> datetime:
    return datetime.now(KST)


def _timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


@lru_cache(maxsize=32)
def _validator_snapshot_keyword(validator: Callable[..., Any]) -> str | None:
    """Return the snapshot-time keyword supported by an advisory contract.

    Samsung's original contract calls the field ``snapshot_observed_at`` while
    the lower-price widget contracts expose the same boundary as
    ``snapshot_time``.  Resolve that adapter once per validator instead of
    letting a keyword mismatch terminate the live execution loop.
    """
    try:
        parameters = signature(validator).parameters
    except (TypeError, ValueError):
        return None
    if "snapshot_observed_at" in parameters:
        return "snapshot_observed_at"
    if "snapshot_time" in parameters:
        return "snapshot_time"
    if any(item.kind is Parameter.VAR_KEYWORD for item in parameters.values()):
        return "snapshot_observed_at"
    return None


def _contract_advisory_is_valid(
    contract: Any,
    validator_name: str,
    advisory: object,
    *,
    snapshot_at: datetime,
    context: Any,
    evaluated_at: datetime,
) -> bool:
    """Invoke a symbol contract through its declared snapshot-time keyword."""
    validator = getattr(contract, validator_name, None)
    if not callable(validator):
        return False
    snapshot_keyword = _validator_snapshot_keyword(validator)
    if snapshot_keyword is None:
        return False
    try:
        return bool(
            validator(
                advisory,
                **{
                    snapshot_keyword: snapshot_at,
                    "context": context,
                    "evaluated_at": evaluated_at,
                },
            )
        )
    except (AttributeError, TypeError, ValueError):
        # Contract failures are a fail-closed signal-quality result, never a
        # reason to terminate reconciliation for already accepted orders.
        return False


def _positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _take_profit_price(fill_price: int, *, profit_bps: int = TAKE_PROFIT_BPS) -> int:
    """Return the first valid tick at or above the requested gross return."""
    clean_fill = _positive_int(fill_price)
    clean_bps = _positive_int(profit_bps)
    if clean_fill <= 0 or clean_bps <= 0:
        raise ValueError("invalid_take_profit_basis")
    return move_price_up_by_bps(clean_fill, clean_bps)


def _legacy_execution_policy(spec: WidgetSpec) -> dict[str, Any] | None:
    if spec.code != samsung_contract.SAMSUNG_CODE or not spec.execution_policy_id:
        return None
    if spec.execution_policy_id != SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID:
        raise ValueError(f"unknown_widget_execution_policy:{spec.execution_policy_id}")
    return SAMSUNG_DAILY_EQUAL_SHARE_POLICY


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


class WidgetTradeEventRecorder:
    def __init__(self, output_dir: Path = DEFAULT_EVENT_DIR) -> None:
        self.output_dir = output_dir

    def record(self, event: dict[str, Any], observed_at: datetime) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / (
            f"widget_signal_auto_trade_events_{observed_at.strftime('%Y%m%d')}.jsonl"
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


class WidgetSignalAutoTrader:
    """Submit one configurable order per widget entry episode.

    Broker holdings are intentionally not used to calculate sell quantity.
    Only fills tied to this service's current-trade-date order numbers enter
    the sellable ledger.  At the date boundary any remaining quantity becomes
    unmanaged prior-day inventory and is never sold by the new date's state.
    """

    def __init__(
        self,
        *,
        gateway: OrderGateway | None = None,
        specs: tuple[WidgetSpec, ...] = DEFAULT_WIDGET_SPECS,
        state_path: Path = DEFAULT_STATE_PATH,
        event_recorder: WidgetTradeEventRecorder | None = None,
        snapshot_loader: SnapshotLoader = _load_json,
        entry_action_notifier: EntryActionNotifier | None = None,
        policy_loader: WidgetAutoTradePolicyLoader | None = None,
        dynamic_spec_catalog: tuple[WidgetSpec, ...] = (),
        entry_qty: int = WIDGET_AUTO_TRADE_LEG_QUANTITY,
        enabled: bool = False,
    ) -> None:
        qty = int(entry_qty)
        if qty < 1 or qty > MAX_ENTRY_QTY:
            raise ValueError(f"entry_qty must be between 1 and {MAX_ENTRY_QTY}")
        self.gateway = gateway or KiwoomSharedTokenOrderGateway()
        dynamic_codes = {spec.code for spec in dynamic_spec_catalog}
        self._static_specs = tuple(
            spec for spec in specs if spec.code not in dynamic_codes
        )
        self._dynamic_spec_catalog = tuple(dynamic_spec_catalog)
        self.specs = tuple(specs)
        self.state_path = state_path
        self.event_recorder = event_recorder or WidgetTradeEventRecorder()
        self.snapshot_loader = snapshot_loader
        self.entry_action_notifier = entry_action_notifier
        self.policy_loader = policy_loader or WidgetAutoTradePolicyLoader()
        self.entry_qty = qty
        self.enabled = bool(enabled)
        self._policy_date = _now_kst().date()
        self._dated_execution_policies = self.policy_loader.resolve_all(
            observed_date=self._policy_date
        )
        self._refresh_dynamic_specs()
        self._configured_execution_policies = self._policy_manifest()
        self._last_policy_catalog_refresh_at: datetime | None = None
        self._validate_policy_quantities()
        self._state = self._load_state()

    def _refresh_dynamic_specs(self) -> None:
        promoted = set(self._dated_execution_policies)
        self.specs = self._static_specs + tuple(
            spec for spec in self._dynamic_spec_catalog if spec.code in promoted
        )

    def _validate_policy_quantities(self) -> None:
        for spec in self.specs:
            policies = list(self._dated_execution_policies.get(spec.code, {}).values())
            legacy = _legacy_execution_policy(spec)
            if not policies and legacy is not None:
                policies = [legacy]
            for policy in policies:
                if self.entry_qty != int(policy["leg_quantity_each"]):
                    raise ValueError(
                        "widget_execution_policy_entry_qty_mismatch:"
                        f"{spec.code}:expected={policy['leg_quantity_each']}:"
                        f"actual={self.entry_qty}"
                    )

    def _policy_manifest(self) -> dict[str, Any]:
        manifest: dict[str, Any] = {}
        for spec in self.specs:
            sessions = self._dated_execution_policies.get(spec.code)
            if sessions:
                manifest[spec.code] = {
                    session: policy["policy_id"]
                    for session, policy in sorted(sessions.items())
                }
            elif spec.execution_policy_id:
                manifest[spec.code] = spec.execution_policy_id
        return manifest

    def _policy_execution_sessions(self) -> dict[str, list[str]]:
        """Expose policy sessions eligible to open a new runtime entry."""
        result: dict[str, list[str]] = {}
        for spec in self.specs:
            dated_sessions = self._dated_execution_policies.get(spec.code)
            if dated_sessions:
                eligible = sorted(
                    session
                    for session, policy in dated_sessions.items()
                    if policy.get("new_entry_runtime_eligible") is not False
                )
            else:
                legacy = _legacy_execution_policy(spec)
                eligible = (
                    sorted(str(value) for value in legacy["allowed_entry_sessions"])
                    if legacy is not None
                    else []
                )
            if eligible:
                result[spec.code] = eligible
        return result

    def _execution_policy(
        self,
        spec: WidgetSpec,
        *,
        session: str | None = None,
        symbol_state: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if symbol_state is not None and symbol_state.get("entry_episode_open"):
            episode_policy = symbol_state.get("entry_execution_policy")
            if isinstance(episode_policy, dict):
                return episode_policy
        dated_sessions = self._dated_execution_policies.get(spec.code)
        if dated_sessions:
            return dated_sessions.get(str(session or ""))
        return _legacy_execution_policy(spec)

    def _load_state(self) -> dict[str, Any]:
        state = _load_json(self.state_path)
        if (
            state.get("schema_version") != STATE_SCHEMA_VERSION
            or state.get("execution_authority") != EXECUTION_AUTHORITY
        ):
            return {}
        stored_policies = state.get("execution_policies")
        stored_policies = stored_policies if isinstance(stored_policies, dict) else {}
        if stored_policies != self._configured_execution_policies:
            same_trade_date = state.get("active_date") == _now_kst().date().isoformat()
            additive_policy_catalog = all(
                self._configured_execution_policies.get(symbol) == sessions
                for symbol, sessions in stored_policies.items()
            )
            symbols = state.get("symbols")
            symbols = symbols if isinstance(symbols, dict) else {}
            live_intent_symbols = {
                symbol
                for symbol, symbol_state in symbols.items()
                if isinstance(symbol_state, dict)
                and (
                    self._open_qty(symbol_state) > 0
                    or any(
                        order.get("status") in ACTIVE_ORDER_STATUSES
                        for order in symbol_state.get("orders") or []
                    )
                )
            }
            added_policy_symbols = (
                set(self._configured_execution_policies) - set(stored_policies)
            )
            additive_policy_catalog = bool(
                additive_policy_catalog
                and not (added_policy_symbols & live_intent_symbols)
            )
            if same_trade_date and live_intent_symbols and not additive_policy_catalog:
                raise ValueError(
                    "widget_execution_policy_state_mismatch_with_active_orders"
                )
            if same_trade_date and not additive_policy_catalog:
                return {}
        return state

    def _refresh_same_day_policy_catalog(self, observed_at: datetime) -> None:
        """Admit only additive exact-date policies published after process start.

        The postclose policy producer normally finishes before this service
        starts.  Persistent-timer catch-up can legitimately publish the same
        exact-date artifact later in preopen, though.  Re-read the catalog at a
        bounded cadence so a long-running process does not miss that symbol.

        Existing symbol/session policies are immutable for the trade date.
        A replacement, removal, or quantity mismatch is ignored here and thus
        cannot mutate an active episode or widen broker authority silently.
        """

        if observed_at.date() != self._policy_date:
            return
        last_refresh = self._last_policy_catalog_refresh_at
        if last_refresh is not None:
            elapsed = (observed_at - last_refresh).total_seconds()
            if 0 <= elapsed < POLICY_CATALOG_REFRESH_INTERVAL_SEC:
                return
        self._last_policy_catalog_refresh_at = observed_at

        candidate = self.policy_loader.resolve_all(observed_date=self._policy_date)
        if not isinstance(candidate, dict) or not candidate:
            return

        catalog_codes = {spec.code for spec in self._dynamic_spec_catalog}
        spec_codes = {spec.code for spec in self._static_specs} | catalog_codes
        additions: dict[str, dict[str, Any]] = {}
        for symbol, sessions in candidate.items():
            if symbol not in spec_codes or not isinstance(sessions, dict):
                continue
            current_sessions = self._dated_execution_policies.get(symbol, {})
            for session, policy in sessions.items():
                if session in current_sessions or not isinstance(policy, dict):
                    continue
                if _positive_int(policy.get("leg_quantity_each")) != self.entry_qty:
                    continue
                additions.setdefault(symbol, {})[session] = policy
        if not additions:
            return

        merged = {
            symbol: dict(sessions)
            for symbol, sessions in self._dated_execution_policies.items()
        }
        for symbol, sessions in additions.items():
            merged.setdefault(symbol, {}).update(sessions)
        self._dated_execution_policies = merged
        self._refresh_dynamic_specs()
        self._validate_policy_quantities()
        self._configured_execution_policies = self._policy_manifest()

        symbols = self._state.get("symbols")
        if not isinstance(symbols, dict):
            symbols = {}
            self._state["symbols"] = symbols
        specs_by_code = {spec.code: spec for spec in self.specs}
        for symbol in additions:
            spec = specs_by_code.get(symbol)
            if spec is not None and symbol not in symbols:
                symbols[symbol] = self._empty_symbol_state(spec)
        self._state["last_policy_catalog_refresh_at"] = observed_at.isoformat()
        self._state["last_policy_catalog_additions"] = {
            symbol: sorted(sessions) for symbol, sessions in sorted(additions.items())
        }
        self._save()

    @staticmethod
    def _empty_symbol_state(spec: WidgetSpec) -> dict[str, Any]:
        return {
            "code": spec.code,
            "name": spec.name,
            "entry_episode_open": False,
            "entry_signal_id": None,
            "exit_signal_id": None,
            "exit_requested": False,
            "orders": [],
            "sell_attempt_count": 0,
            "last_sell_attempt_at": None,
            "take_profit_failure_count": 0,
            "last_take_profit_attempt_at": None,
            "last_source_state": None,
            "last_blocked_source_exit_signal_id": None,
        }

    def _save(self) -> None:
        monitored_symbols = [spec.code for spec in self.specs]
        policy_sessions = self._policy_execution_sessions()
        runtime_sessions = policy_sessions if self.enabled else {}
        execution_eligible_symbols = sorted(runtime_sessions)
        self._state.update(
            {
                "schema_version": STATE_SCHEMA_VERSION,
                "execution_authority": EXECUTION_AUTHORITY,
                "runtime_effect": self.enabled,
                "actual_order_submitted": any(
                    order.get("broker_accepted") is True
                    for symbol in (self._state.get("symbols") or {}).values()
                    for order in symbol.get("orders") or []
                ),
                "cash_precheck_performed": False,
                "token_mode": "shared_cache_only_no_issue_no_refresh",
                "entry_qty": self.entry_qty,
                # Retain enabled_symbols for backward-compatible readers; the
                # explicit fields below separate observation from order scope.
                "enabled_symbols": monitored_symbols,
                "monitored_symbols": monitored_symbols,
                "policy_execution_eligible_symbols": sorted(policy_sessions),
                "policy_execution_sessions": policy_sessions,
                "execution_eligible_symbols": execution_eligible_symbols,
                "observation_only_symbols": sorted(
                    set(monitored_symbols) - set(execution_eligible_symbols)
                ),
                "runtime_execution_policy_sessions": runtime_sessions,
                "execution_policies": self._configured_execution_policies,
                "execution_contract": EXECUTION_CONTRACT,
            }
        )
        _atomic_write(self.state_path, self._state)

    @staticmethod
    def _filled_qty(symbol_state: dict[str, Any], side: str) -> int:
        return sum(
            _positive_int(order.get("filled_qty"))
            for order in symbol_state.get("orders") or []
            if order.get("side") == side and order.get("broker_accepted") is True
        )

    @classmethod
    def _open_qty(cls, symbol_state: dict[str, Any]) -> int:
        return max(
            0,
            cls._filled_qty(symbol_state, "BUY")
            - cls._filled_qty(symbol_state, "SELL"),
        )

    def _activate_date(self, observed_at: datetime) -> None:
        day = observed_at.date().isoformat()
        if self._state.get("active_date") == day:
            symbols = self._state.get("symbols")
            if not isinstance(symbols, dict):
                symbols = {}
                self._state["symbols"] = symbols
            changed = False
            for spec in self.specs:
                if spec.code not in symbols:
                    symbols[spec.code] = self._empty_symbol_state(spec)
                    changed = True
            if changed:
                self._save()
            return
        prior_symbols = self._state.get("symbols") or {}
        history = self._state.get("history")
        history = history if isinstance(history, list) else []
        prior_date = str(self._state.get("active_date") or "")
        if prior_date and isinstance(prior_symbols, dict):
            history.append(
                {
                    "trade_date": prior_date,
                    "reset_at": observed_at.isoformat(),
                    "symbols": {
                        code: {
                            "buy_filled_qty": self._filled_qty(value, "BUY"),
                            "sell_filled_qty": self._filled_qty(value, "SELL"),
                            "unmanaged_overnight_qty": self._open_qty(value),
                            "unresolved_order_count": sum(
                                1
                                for order in value.get("orders") or []
                                if order.get("status") in ACTIVE_ORDER_STATUSES
                            ),
                            "orders": deepcopy(value.get("orders") or []),
                        }
                        for code, value in prior_symbols.items()
                        if isinstance(value, dict)
                    },
                    "overnight_policy": "no_action_daily_reset",
                }
            )
        self._policy_date = observed_at.date()
        self._dated_execution_policies = self.policy_loader.resolve_all(
            observed_date=self._policy_date
        )
        self._refresh_dynamic_specs()
        self._validate_policy_quantities()
        self._configured_execution_policies = self._policy_manifest()
        new_symbols: dict[str, dict[str, Any]] = {}
        for spec in self.specs:
            symbol_state = self._empty_symbol_state(spec)
            prior_state = prior_symbols.get(spec.code)
            if isinstance(prior_state, dict):
                symbol_state["prior_day_unmanaged_qty"] = self._open_qty(prior_state)
                symbol_state["prior_day_unresolved_order_count"] = sum(
                    1
                    for order in prior_state.get("orders") or []
                    if order.get("status") in ACTIVE_ORDER_STATUSES
                )
            new_symbols[spec.code] = symbol_state
        self._state = {
            "active_date": day,
            "symbols": new_symbols,
            "history": history[-30:],
        }
        self._save()

    def _event(
        self, event_type: str, spec: WidgetSpec, now: datetime, **fields: Any
    ) -> None:
        policy_session = str(fields.pop("execution_policy_session", "") or "")
        if not policy_session:
            policy_session = str(spec.contract.session_context(now).name or "")
        symbol_state = (self._state.get("symbols") or {}).get(spec.code)
        symbol_state = symbol_state if isinstance(symbol_state, dict) else None
        execution_policy = self._execution_policy(
            spec,
            session=policy_session,
            symbol_state=symbol_state,
        )
        explicit_policy_id = fields.get("execution_policy_id")
        payload = {
            "schema": EVENT_SCHEMA,
            "event_type": event_type,
            "observed_at": now.isoformat(),
            "trade_date": now.date().isoformat(),
            "symbol": spec.code,
            "name": spec.name,
            "execution_authority": EXECUTION_AUTHORITY,
            "runtime_effect": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": False,
            "cash_precheck_performed": False,
            "token_mode": "shared_cache_only_no_issue_no_refresh",
            "execution_policy_id": (
                explicit_policy_id
                or (execution_policy["policy_id"] if execution_policy else None)
            ),
            "execution_policy_research_arm": (
                execution_policy["research_arm"] if execution_policy else None
            ),
            "execution_policy_evidence_window": (
                execution_policy["evidence_window"] if execution_policy else None
            ),
            "execution_policy_evidence_artifact": (
                execution_policy["evidence_artifact"] if execution_policy else None
            ),
            **EXECUTION_CONTRACT,
            **fields,
        }
        self.event_recorder.record(payload, now)

    def _record_entry_block_once(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        signal_id: str,
        reason: str,
        now: datetime,
        **fields: Any,
    ) -> None:
        if (
            symbol_state.get("last_entry_block_signal_id") == signal_id
            and symbol_state.get("last_entry_block_reason") == reason
        ):
            return
        symbol_state["last_entry_block_signal_id"] = signal_id
        symbol_state["last_entry_block_reason"] = reason
        symbol_state["last_entry_block_at"] = now.isoformat()
        self._save()
        self._event(reason, spec, now, signal_id=signal_id, **fields)

    @staticmethod
    def _snapshot_time(payload: dict[str, Any]) -> datetime | None:
        return samsung_contract.snapshot_observed_at(payload)

    def _validated_context(
        self, spec: WidgetSpec, payload: dict[str, Any], now: datetime
    ) -> tuple[Any | None, datetime | None]:
        context = spec.contract.session_context(now)
        snapshot_at = self._snapshot_time(payload)
        expected_profile = str(getattr(spec.contract, "STRATEGY_PROFILE", "") or "")
        if (
            not context.active
            or snapshot_at is None
            or payload.get("status") != "ok"
            or payload.get("symbol") != spec.code
            or payload.get("market_venue") != context.market_venue
            or (
                expected_profile
                and str(payload.get("strategy_profile") or "") != expected_profile
            )
        ):
            return None, None
        fresh = spec.contract.snapshot_is_fresh(payload, now=now)
        return (context, snapshot_at) if fresh else (None, None)

    def _entry_signal(
        self,
        spec: WidgetSpec,
        payload: dict[str, Any],
        now: datetime,
    ) -> tuple[str, str, str | None, dict[str, Any] | None] | None:
        context, snapshot_at = self._validated_context(spec, payload, now)
        if context is None or snapshot_at is None:
            return None
        advisory = payload.get("advisory")
        if not isinstance(advisory, dict):
            return None
        dated_sessions = self._dated_execution_policies.get(spec.code)
        execution_policy = self._execution_policy(spec, session=context.name)
        runtime_block_reason = (
            str(execution_policy.get("new_entry_runtime_block_reason") or "")
            if execution_policy is not None
            else ""
        )
        policy_block_reason = (
            "entry_blocked_execution_policy_session_unavailable"
            if (dated_sessions or spec.dated_policy_required)
            and execution_policy is None
            else (
                (
                    "entry_blocked_cumulative_research_gate"
                    if runtime_block_reason in CUMULATIVE_RESEARCH_BLOCK_REASONS
                    else "entry_blocked_execution_policy_ineligible"
                )
                if execution_policy is not None
                and execution_policy.get("new_entry_runtime_eligible") is False
                else (
                    "entry_blocked_execution_policy_venue"
                    if execution_policy is not None
                    and (
                        context.name not in execution_policy["allowed_entry_sessions"]
                        or context.market_venue
                        not in execution_policy["allowed_entry_venues"]
                    )
                    else None
                )
            )
        )
        if spec.event_based:
            event = payload.get("entry_event")
            if not isinstance(
                event, dict
            ) or not spec.contract.advisory_event_contract_is_valid(
                event, expected_type="ENTRY", evaluated_at=now
            ):
                return None
            state = str(event.get("state") or "")
            event_id = str(event.get("event_id") or "")
            return (
                (event_id, state, policy_block_reason, execution_policy)
                if event_id
                and state
                in (
                    execution_policy.get(
                        "allowed_entry_states", ACTIONABLE_ENTRY_STATES
                    )
                    if execution_policy
                    else ACTIONABLE_ENTRY_STATES
                )
                else None
            )
        if not _contract_advisory_is_valid(
            spec.contract,
            "advisory_contract_is_valid",
            advisory,
            snapshot_at=snapshot_at,
            context=context,
            evaluated_at=now,
        ):
            return None
        state = str(advisory.get("state") or "")
        allowed_states = (
            execution_policy.get("allowed_entry_states", ACTIONABLE_ENTRY_STATES)
            if execution_policy
            else ACTIONABLE_ENTRY_STATES
        )
        if state not in allowed_states:
            return None
        block_reason = policy_block_reason
        if (
            not block_reason
            and spec.structural_execution_qualification
            and execution_policy is None
        ):
            derived = advisory.get("derived")
            derived = derived if isinstance(derived, dict) else {}
            regime = advisory.get("intraday_regime")
            regime = regime if isinstance(regime, dict) else {}
            structural_recovery = bool(
                derived.get("recent_resistance_reclaimed") is True
                and derived.get("higher_high_and_low") is True
            )
            reward_risk = derived.get("entry_reward_risk_guard")
            reward_risk = reward_risk if isinstance(reward_risk, dict) else {}
            if regime.get("state") not in {"unavailable", "not_down", "down"}:
                block_reason = "entry_blocked_intraday_regime_missing"
            elif regime.get("state") == "down" and not structural_recovery:
                block_reason = "entry_blocked_intraday_down_regime"
            elif derived.get("recent_resistance_reclaimed") is not True:
                block_reason = "entry_blocked_recent_resistance_not_reclaimed"
            elif derived.get("resistance_reclaim_hold_confirmed") is not True:
                block_reason = "entry_blocked_resistance_reclaim_hold_pending"
            elif reward_risk.get("passed") is not True:
                block_reason = "entry_blocked_reward_risk_not_qualified"
        return (
            f"{spec.code}:{now.date().isoformat()}:ENTRY:{context.name}:"
            f"{advisory.get('observed_at')}",
            state,
            block_reason,
            execution_policy,
        )

    def _exit_signal(
        self,
        spec: WidgetSpec,
        payload: dict[str, Any],
        now: datetime,
    ) -> str | None:
        context, snapshot_at = self._validated_context(spec, payload, now)
        if context is None or snapshot_at is None:
            return None
        if spec.event_based:
            event = payload.get("exit_event")
            if not isinstance(
                event, dict
            ) or not spec.contract.advisory_event_contract_is_valid(
                event, expected_type="EXIT", evaluated_at=now
            ):
                return None
            return str(event.get("event_id") or "") or None
        exit_advisory = payload.get("exit_advisory")
        if (
            not isinstance(exit_advisory, dict)
            or exit_advisory.get("state") != FINAL_EXIT_STATE
            or not _contract_advisory_is_valid(
                spec.contract,
                "exit_advisory_contract_is_valid",
                exit_advisory,
                snapshot_at=snapshot_at,
                context=context,
                evaluated_at=now,
            )
        ):
            return None
        continuity = exit_advisory.get("continuity")
        continuity = continuity if isinstance(continuity, dict) else {}
        return ":".join(
            [
                spec.code,
                now.date().isoformat(),
                "EXIT",
                context.name,
                str(continuity.get("ready_bar") or exit_advisory.get("observed_at")),
            ]
        )

    @staticmethod
    def _route(payload: dict[str, Any]) -> str:
        route = str(payload.get("market_venue") or "").upper()
        return route if route in {"KRX", "NXT"} else ""

    def _order_record(
        self,
        *,
        side: str,
        qty: int,
        route: str,
        signal_id: str,
        now: datetime,
        order_role: str,
        limit_price: int | None = None,
        parent_entry_signal_id: str | None = None,
        scale_in_leg_index: int | None = None,
        execution_policy_id: str | None = None,
    ) -> dict[str, Any]:
        broker_route = resolve_widget_broker_route(route)
        return {
            "side": side,
            "requested_qty": qty,
            "filled_qty": 0,
            "remaining_qty": qty,
            "market_venue": route,
            "route": broker_route,
            "broker_route": broker_route,
            "signal_id": signal_id,
            "order_role": order_role,
            "limit_price": limit_price,
            "parent_entry_signal_id": parent_entry_signal_id,
            "scale_in_leg_index": scale_in_leg_index,
            "execution_policy_id": execution_policy_id,
            "order_date": now.date().isoformat(),
            "intent_created_at": now.isoformat(),
            "status": "SUBMITTING",
            "order_no": "",
            "return_code": "",
            "return_msg": "",
            "fill_price": None,
            "broker_accepted": False,
        }

    def _notify_pending_buy_actions(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> None:
        """Best-effort notify accepted BUY actions without affecting execution."""
        if self.entry_action_notifier is None:
            return
        for order in symbol_state.get("orders") or []:
            if (
                order.get("side") != "BUY"
                or order.get("broker_accepted") is not True
                or order.get("order_role")
                not in {ORDER_ROLE_ENTRY_BUY, ORDER_ROLE_SCALE_IN_BUY}
                or order.get("entry_telegram_status") == "sent"
            ):
                continue
            try:
                result = self.entry_action_notifier.notify_order_accepted(
                    symbol=spec.code,
                    name=spec.name,
                    order=order,
                    execution_policy_id=(
                        str(order.get("execution_policy_id") or "") or None
                    ),
                    observed_at=now,
                )
            except Exception as exc:
                result = "notifier_error_isolated"
                error = type(exc).__name__
            else:
                error = None
            normalized = "sent" if result in {"sent", "duplicate"} else result
            if (
                order.get("entry_telegram_status") == normalized
                and order.get("entry_telegram_error") == error
            ):
                continue
            order["entry_telegram_status"] = normalized
            order["entry_telegram_last_observed_at"] = now.isoformat()
            order["entry_telegram_error"] = error
            if normalized == "sent":
                order["entry_telegram_sent_at"] = now.isoformat()
            self._save()
            try:
                self._event(
                    "entry_action_telegram_delivery",
                    spec,
                    now,
                    order_no=order.get("order_no"),
                    order_role=order.get("order_role"),
                    requested_qty=order.get("requested_qty"),
                    signal_id=order.get("signal_id"),
                    delivery_status=normalized,
                    delivery_error=error,
                    actual_order_submitted=True,
                )
            except Exception:
                # Delivery audit is subordinate to the already-persisted order
                # and must not stop reconciliation or protective-order work.
                pass

    def _submit(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        side: str,
        qty: int,
        route: str,
        signal_id: str,
        now: datetime,
        order_role: str,
        limit_price: int | None = None,
        parent_entry_signal_id: str | None = None,
        scale_in_leg_index: int | None = None,
    ) -> dict[str, Any]:
        order = self._order_record(
            side=side,
            qty=qty,
            route=route,
            signal_id=signal_id,
            now=now,
            order_role=order_role,
            limit_price=limit_price,
            parent_entry_signal_id=parent_entry_signal_id,
            scale_in_leg_index=scale_in_leg_index,
            execution_policy_id=(
                str(symbol_state.get("execution_policy_id") or "") or None
            ),
        )
        symbol_state.setdefault("orders", []).append(order)
        self._save()  # crash-before/after-submit ambiguity guard
        broker_route = str(order["broker_route"])
        try:
            if side == "BUY":
                result = self.gateway.submit_buy(
                    code=spec.code, qty=qty, route=broker_route
                )
            elif order_role == ORDER_ROLE_TAKE_PROFIT and limit_price is not None:
                result = self.gateway.submit_limit_sell(
                    code=spec.code,
                    qty=qty,
                    route=broker_route,
                    price=limit_price,
                )
            else:
                result = self.gateway.submit_sell(
                    code=spec.code, qty=qty, route=broker_route
                )
        except Exception as exc:
            order.update(
                {
                    "status": "AMBIGUOUS",
                    "return_code": type(exc).__name__,
                    "return_msg": str(exc)[:160],
                }
            )
            self._save()
            self._event(
                "order_submit_ambiguous",
                spec,
                now,
                side=side,
                requested_qty=qty,
                signal_id=signal_id,
                error=type(exc).__name__,
                market_venue=route,
                broker_route=broker_route,
            )
            return order
        order.update(
            {
                "order_no": result.order_no,
                "return_code": result.return_code,
                "return_msg": result.return_msg[:160],
                "status": (
                    "SUBMITTED"
                    if result.accepted
                    else "AMBIGUOUS" if result.ambiguous else "FAILED"
                ),
                "broker_accepted": result.accepted,
                "submitted_at": now.isoformat(),
                "source_advisory_state": symbol_state.get("entry_source_state"),
            }
        )
        self._save()
        self._event(
            "order_submitted" if result.accepted else "order_submit_failed",
            spec,
            now,
            side=side,
            requested_qty=qty,
            signal_id=signal_id,
            route=broker_route,
            market_venue=route,
            broker_route=broker_route,
            order_no=result.order_no,
            return_code=result.return_code,
            ambiguous=result.ambiguous,
            actual_order_submitted=result.accepted,
            order_role=order_role,
            limit_price=limit_price,
            parent_entry_signal_id=parent_entry_signal_id,
            scale_in_leg_index=scale_in_leg_index,
        )
        return order

    def _reconcile(
        self, spec: WidgetSpec, symbol_state: dict[str, Any], now: datetime
    ) -> None:
        changed = False
        for order in symbol_state.get("orders") or []:
            if order.get("status") not in {
                "SUBMITTED",
                "CANCEL_REQUESTED",
                "CANCEL_AMBIGUOUS",
                "CANCEL_FAILED_TERMINAL",
            }:
                continue
            order_no = str(order.get("order_no") or "")
            if not order_no:
                continue
            try:
                snapshot = self.gateway.execution_snapshot(
                    code=spec.code,
                    order_no=order_no,
                    route=str(order.get("route") or ""),
                    order_date=str(order.get("order_date") or now.date().isoformat()),
                )
            except Exception as exc:
                order["last_reconcile_error"] = type(exc).__name__
                order["last_reconcile_error_at"] = now.isoformat()
                changed = True
                continue
            if not snapshot.source_ok:
                last_error_at = _timestamp(order.get("last_reconcile_error_at"))
                if (
                    last_error_at is None
                    or (now - last_error_at).total_seconds()
                    >= OBSERVABILITY_PERSIST_INTERVAL_SEC
                ):
                    order["last_reconcile_error"] = snapshot.error or "source_not_ok"
                    order["last_reconcile_error_at"] = now.isoformat()
                    changed = True
                continue
            if not snapshot.found:
                last_not_found_at = _timestamp(order.get("last_reconcile_not_found_at"))
                if (
                    last_not_found_at is None
                    or (now - last_not_found_at).total_seconds()
                    >= OBSERVABILITY_PERSIST_INTERVAL_SEC
                ):
                    order["reconcile_not_found_count"] = (
                        _positive_int(order.get("reconcile_not_found_count")) + 1
                    )
                    order["last_reconcile_not_found_at"] = now.isoformat()
                    changed = True
                continue
            requested = _positive_int(order.get("requested_qty"))
            prior_filled = _positive_int(order.get("filled_qty"))
            prior_status = str(order.get("status") or "")
            filled = min(requested, max(prior_filled, snapshot.filled_qty))
            remaining = min(max(0, requested - filled), snapshot.remaining_qty)
            order["filled_qty"] = filled
            order["remaining_qty"] = remaining
            if snapshot.fill_price is not None:
                order["fill_price"] = snapshot.fill_price
            order["last_reconciled_at"] = now.isoformat()
            if remaining == 0:
                order["status"] = (
                    "FILLED"
                    if filled == requested
                    else "PARTIAL_CANCELED" if filled else "CANCELED"
                )
            changed = True
            if filled != prior_filled or order.get("status") != prior_status:
                self._event(
                    "order_execution_reconciled",
                    spec,
                    now,
                    side=order.get("side"),
                    order_no=order_no,
                    requested_qty=requested,
                    filled_qty=filled,
                    remaining_qty=remaining,
                    order_status=order.get("status"),
                    order_role=order.get("order_role"),
                    limit_price=order.get("limit_price"),
                    parent_entry_signal_id=order.get("parent_entry_signal_id"),
                    signal_id=order.get("signal_id"),
                    fill_price=order.get("fill_price"),
                    market_venue=order.get("market_venue"),
                    broker_route=order.get("broker_route"),
                    submitted_at=order.get("submitted_at"),
                    scale_in_leg_index=order.get("scale_in_leg_index"),
                    actual_order_submitted=True,
                )
        if changed:
            self._save()

    def _cancel_pending_buys(
        self, spec: WidgetSpec, symbol_state: dict[str, Any], now: datetime
    ) -> None:
        for order in symbol_state.get("orders") or []:
            if order.get("side") != "BUY" or order.get("status") != "SUBMITTED":
                continue
            remaining = _positive_int(order.get("remaining_qty"))
            if remaining <= 0:
                continue
            attempts = _positive_int(order.get("cancel_attempt_count"))
            if attempts >= MAX_CANCEL_ATTEMPTS:
                if order.get("status") != "CANCEL_FAILED_TERMINAL":
                    order["status"] = "CANCEL_FAILED_TERMINAL"
                    order["cancel_terminal_at"] = now.isoformat()
                    self._save()
                    self._event(
                        "buy_cancel_terminal_failure",
                        spec,
                        now,
                        order_no=order.get("order_no"),
                        remaining_qty=remaining,
                        cancel_attempt_count=attempts,
                    )
                continue
            last_attempt = _timestamp(order.get("cancel_attempted_at"))
            if (
                last_attempt is not None
                and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
            ):
                continue
            order["cancel_attempt_count"] = attempts + 1
            try:
                result = self.gateway.cancel(
                    code=spec.code,
                    order_no=str(order.get("order_no") or ""),
                    qty=remaining,
                    route=str(order.get("route") or ""),
                )
            except Exception as exc:
                order["cancel_error"] = type(exc).__name__
                order["cancel_attempted_at"] = now.isoformat()
                order["status"] = "CANCEL_AMBIGUOUS"
                self._save()
                self._event(
                    "buy_cancel_ambiguous",
                    spec,
                    now,
                    order_no=order.get("order_no"),
                    remaining_qty=remaining,
                    error=type(exc).__name__,
                )
                continue
            order["cancel_attempted_at"] = now.isoformat()
            order["cancel_return_code"] = result.return_code
            order["cancel_order_no"] = result.order_no
            if result.accepted:
                order["status"] = "CANCEL_REQUESTED"
            elif result.ambiguous:
                order["status"] = "CANCEL_AMBIGUOUS"
            self._save()
            self._event(
                "buy_cancel_requested" if result.accepted else "buy_cancel_failed",
                spec,
                now,
                order_no=order.get("order_no"),
                remaining_qty=remaining,
                return_code=result.return_code,
            )

    @staticmethod
    def _has_pending(symbol_state: dict[str, Any], side: str) -> bool:
        return any(
            order.get("side") == side and order.get("status") in ACTIVE_ORDER_STATUSES
            for order in symbol_state.get("orders") or []
        )

    @staticmethod
    def _take_profit_pending_qty(
        symbol_state: dict[str, Any], parent_entry_signal_id: str
    ) -> int:
        return sum(
            _positive_int(order.get("remaining_qty"))
            for order in symbol_state.get("orders") or []
            if order.get("order_role") == ORDER_ROLE_TAKE_PROFIT
            and order.get("parent_entry_signal_id") == parent_entry_signal_id
            and order.get("status") in ACTIVE_ORDER_STATUSES
        )

    @staticmethod
    def _entry_fill_basis(
        symbol_state: dict[str, Any], entry_signal_id: str
    ) -> tuple[int, int]:
        rows = [
            order
            for order in symbol_state.get("orders") or []
            if order.get("order_role")
            in {None, "", ORDER_ROLE_ENTRY_BUY, ORDER_ROLE_SCALE_IN_BUY}
            and order.get("side") == "BUY"
            and (
                order.get("signal_id") == entry_signal_id
                or order.get("parent_entry_signal_id") == entry_signal_id
            )
            and order.get("broker_accepted") is True
            and _positive_int(order.get("filled_qty")) > 0
            and _positive_int(order.get("fill_price")) > 0
        ]
        total_qty = sum(_positive_int(order.get("filled_qty")) for order in rows)
        if total_qty <= 0:
            return 0, 0
        total_notional = sum(
            _positive_int(order.get("filled_qty"))
            * _positive_int(order.get("fill_price"))
            for order in rows
        )
        return total_qty, total_notional // total_qty

    @staticmethod
    def _initial_entry_fill_price(
        symbol_state: dict[str, Any], entry_signal_id: str
    ) -> int:
        prices = [
            _positive_int(order.get("fill_price"))
            for order in symbol_state.get("orders") or []
            if order.get("order_role") in {None, "", ORDER_ROLE_ENTRY_BUY}
            and order.get("side") == "BUY"
            and order.get("signal_id") == entry_signal_id
            and order.get("broker_accepted") is True
            and _positive_int(order.get("filled_qty")) > 0
        ]
        return prices[0] if prices else 0

    @staticmethod
    def _take_profit_filled_qty(
        symbol_state: dict[str, Any], entry_signal_id: str
    ) -> int:
        return sum(
            _positive_int(order.get("filled_qty"))
            for order in symbol_state.get("orders") or []
            if order.get("order_role") == ORDER_ROLE_TAKE_PROFIT
            and order.get("parent_entry_signal_id") == entry_signal_id
            and order.get("broker_accepted") is True
        )

    def _close_completed_take_profit_episode(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> bool:
        entry_signal_id = str(symbol_state.get("entry_signal_id") or "")
        if (
            not entry_signal_id
            or not symbol_state.get("entry_episode_open")
            or self._take_profit_filled_qty(symbol_state, entry_signal_id) <= 0
            or self._open_qty(symbol_state) > 0
            or self._has_pending(symbol_state, "BUY")
            or self._has_pending(symbol_state, "SELL")
        ):
            return False
        symbol_state["entry_episode_open"] = False
        symbol_state["take_profit_completed_at"] = now.isoformat()
        symbol_state["last_episode_completed_at"] = now.isoformat()
        symbol_state["completed_entry_count"] = (
            _positive_int(symbol_state.get("completed_entry_count")) + 1
        )
        symbol_state["scale_in_requested"] = False
        self._save()
        self._event(
            "take_profit_episode_completed",
            spec,
            now,
            signal_id=entry_signal_id,
            take_profit_filled_qty=self._take_profit_filled_qty(
                symbol_state, entry_signal_id
            ),
            actual_order_submitted=True,
        )
        return True

    def _maybe_submit_scale_in(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        payload: dict[str, Any],
        now: datetime,
    ) -> None:
        policy = self._execution_policy(spec, symbol_state=symbol_state)
        if policy is None or not symbol_state.get("entry_episode_open"):
            return
        entry_signal_id = str(symbol_state.get("entry_signal_id") or "")
        if not entry_signal_id or symbol_state.get("exit_requested"):
            return
        scale_orders = [
            order
            for order in symbol_state.get("orders") or []
            if order.get("order_role") == ORDER_ROLE_SCALE_IN_BUY
            and order.get("parent_entry_signal_id") == entry_signal_id
        ]
        if any(order.get("status") in ACTIVE_ORDER_STATUSES for order in scale_orders):
            return
        completed_scale_orders = [
            order
            for order in scale_orders
            if order.get("broker_accepted") is True
            and _positive_int(order.get("filled_qty"))
            >= _positive_int(order.get("requested_qty"))
        ]
        next_leg_index = len(completed_scale_orders) + 1
        trigger_bps = tuple(policy["add_trigger_bps_from_initial_fill"])
        if next_leg_index > len(trigger_bps):
            return
        if any(
            _positive_int(order.get("scale_in_leg_index")) == next_leg_index
            for order in scale_orders
        ):
            # A failed or ambiguous submission is never silently retried.
            return
        entry_consumed_at = _timestamp(symbol_state.get("entry_consumed_at"))
        context = spec.contract.session_context(now)
        validated_context, snapshot_at = self._validated_context(spec, payload, now)
        if (
            entry_consumed_at is None
            or entry_consumed_at.date() != now.date()
            or not context.active
            or context.name != symbol_state.get("entry_session")
            or context.name not in policy["allowed_entry_sessions"]
            or context.market_venue not in policy["allowed_entry_venues"]
            or validated_context is None
            or snapshot_at is None
        ):
            return
        advisory = payload.get("advisory")
        advisory = advisory if isinstance(advisory, dict) else {}
        advisory_validator = getattr(spec.contract, "advisory_contract_is_valid", None)
        if callable(advisory_validator) and not _contract_advisory_is_valid(
            spec.contract,
            "advisory_contract_is_valid",
            advisory,
            snapshot_at=snapshot_at,
            context=validated_context,
            evaluated_at=now,
        ):
            return
        source_quality = advisory.get("source_quality")
        if (
            not isinstance(source_quality, dict)
            or source_quality.get("status") != "PASS"
        ):
            return
        current_price = _positive_int(payload.get("current_price"))
        initial_fill_price = self._initial_entry_fill_price(
            symbol_state, entry_signal_id
        )
        if current_price <= 0 or initial_fill_price <= 0:
            return
        trigger_price = clamp_price_to_tick(
            initial_fill_price * (1.0 + int(trigger_bps[next_leg_index - 1]) / 10_000.0)
        )
        if current_price > trigger_price:
            return
        exclusion = evaluate_manual_control_exclusion(spec.code)
        operator_source = manual_control_operator_exclusion_source(spec.code)
        if not exclusion.excluded or not operator_source:
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=f"{entry_signal_id}:ADD{next_leg_index}",
                reason="scale_in_blocked_main_bot_ownership_not_excluded",
                now=now,
                exclusion_applied=exclusion.excluded,
                exclusion_source=exclusion.source,
                required_source="manual_operator_or_explicit_env",
            )
            return
        if is_buy_side_paused():
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=f"{entry_signal_id}:ADD{next_leg_index}",
                reason="scale_in_blocked_global_buy_pause",
                now=now,
            )
            return
        if self._take_profit_filled_qty(symbol_state, entry_signal_id) > 0:
            if not symbol_state.get("scale_in_blocked_after_take_profit_fill_at"):
                symbol_state["scale_in_blocked_after_take_profit_fill_at"] = (
                    now.isoformat()
                )
                self._save()
                self._event(
                    "scale_in_blocked_after_take_profit_fill",
                    spec,
                    now,
                    signal_id=entry_signal_id,
                    trigger_price=trigger_price,
                    current_price=current_price,
                )
            return
        leg_trigger_already_requested = (
            _positive_int(symbol_state.get("scale_in_triggered_leg_count"))
            == next_leg_index
        )
        open_qty = self._open_qty(symbol_state)
        pending_take_profit_qty = self._take_profit_pending_qty(
            symbol_state, entry_signal_id
        )
        if not leg_trigger_already_requested and (
            open_qty <= 0 or pending_take_profit_qty < open_qty
        ):
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=f"{entry_signal_id}:ADD{next_leg_index}",
                reason="scale_in_blocked_take_profit_coverage_missing",
                now=now,
                current_day_open_qty=open_qty,
                pending_take_profit_qty=pending_take_profit_qty,
            )
            return
        if not leg_trigger_already_requested:
            symbol_state["scale_in_requested"] = True
            symbol_state["scale_in_trigger_price"] = trigger_price
            symbol_state["scale_in_triggered_at"] = now.isoformat()
            symbol_state["scale_in_triggered_leg_count"] = next_leg_index
            self._save()
            self._event(
                "scale_in_triggered",
                spec,
                now,
                signal_id=entry_signal_id,
                scale_in_leg_index=next_leg_index,
                trigger_price=trigger_price,
                current_price=current_price,
            )
        self._cancel_pending_take_profit_sells(spec, symbol_state, now)
        if self._has_pending(symbol_state, "SELL") or self._has_pending(
            symbol_state, "BUY"
        ):
            return
        route = str(symbol_state.get("entry_route") or "").upper()
        if route not in {"KRX", "NXT"}:
            return
        self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="BUY",
            qty=int(policy["leg_quantity_each"]),
            route=route,
            signal_id=f"{entry_signal_id}:ADD{next_leg_index}:{trigger_price}",
            now=now,
            order_role=ORDER_ROLE_SCALE_IN_BUY,
            parent_entry_signal_id=entry_signal_id,
            scale_in_leg_index=next_leg_index,
        )

    def _maybe_submit_take_profit(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> None:
        pending_scale_in = any(
            order.get("order_role") == ORDER_ROLE_SCALE_IN_BUY
            and order.get("status") in ACTIVE_ORDER_STATUSES
            for order in symbol_state.get("orders") or []
        )
        if symbol_state.get("exit_requested") or pending_scale_in:
            return
        entry_signal_id = str(symbol_state.get("entry_signal_id") or "")
        if not entry_signal_id or not symbol_state.get("entry_episode_open"):
            return
        if any(
            order.get("order_role") == ORDER_ROLE_TAKE_PROFIT
            and order.get("parent_entry_signal_id") == entry_signal_id
            and order.get("status") in {"SUBMITTING", "AMBIGUOUS"}
            for order in symbol_state.get("orders") or []
        ):
            # A crash/transport ambiguity may already have reached the broker.
            # Never create a second sell until an operator resolves that intent.
            return
        open_qty = self._open_qty(symbol_state)
        pending_qty = self._take_profit_pending_qty(symbol_state, entry_signal_id)
        uncovered_qty = max(0, open_qty - pending_qty)
        if uncovered_qty <= 0:
            return
        filled_qty, average_fill_price = self._entry_fill_basis(
            symbol_state, entry_signal_id
        )
        if filled_qty <= 0 or average_fill_price <= 0:
            if symbol_state.get("take_profit_basis_block_signal_id") != entry_signal_id:
                symbol_state["take_profit_basis_block_signal_id"] = entry_signal_id
                symbol_state["take_profit_basis_blocked_at"] = now.isoformat()
                self._save()
                self._event(
                    "take_profit_blocked_missing_fill_price",
                    spec,
                    now,
                    signal_id=entry_signal_id,
                    current_day_open_qty=open_qty,
                )
            return
        failure_count = _positive_int(symbol_state.get("take_profit_failure_count"))
        if failure_count >= MAX_TAKE_PROFIT_FAILURES:
            if not symbol_state.get("take_profit_terminal_failure_at"):
                symbol_state["take_profit_terminal_failure_at"] = now.isoformat()
                self._save()
                self._event(
                    "take_profit_terminal_failure",
                    spec,
                    now,
                    signal_id=entry_signal_id,
                    current_day_open_qty=open_qty,
                    failure_count=failure_count,
                )
            return
        last_attempt = _timestamp(symbol_state.get("last_take_profit_attempt_at"))
        if (
            last_attempt is not None
            and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
        ):
            return
        # Bind the protective order to the broker-accepted entry route. A later
        # stale/session-transition snapshot must not rewrite order provenance.
        route = str(symbol_state.get("entry_route") or "").upper()
        if route not in {"KRX", "NXT"}:
            return
        policy = self._execution_policy(spec, symbol_state=symbol_state)
        take_profit_bps = (
            int(policy["take_profit_bps_from_equal_share_average"])
            if policy is not None
            else TAKE_PROFIT_BPS
        )
        target_price = _take_profit_price(
            average_fill_price,
            profit_bps=take_profit_bps,
        )
        symbol_state["take_profit_target_price"] = target_price
        symbol_state["take_profit_basis_fill_price"] = average_fill_price
        symbol_state["take_profit_bps"] = take_profit_bps
        self._save()
        order = self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="SELL",
            qty=uncovered_qty,
            route=route,
            signal_id=f"{entry_signal_id}:TP:{target_price}",
            now=now,
            order_role=ORDER_ROLE_TAKE_PROFIT,
            limit_price=target_price,
            parent_entry_signal_id=entry_signal_id,
        )
        if order.get("status") == "FAILED":
            symbol_state["take_profit_failure_count"] = failure_count + 1
            symbol_state["last_take_profit_attempt_at"] = now.isoformat()
            self._save()
        elif order.get("broker_accepted") is True:
            symbol_state["take_profit_last_submitted_at"] = now.isoformat()
            symbol_state["last_take_profit_attempt_at"] = None
            self._save()

    def _cancel_pending_take_profit_sells(
        self, spec: WidgetSpec, symbol_state: dict[str, Any], now: datetime
    ) -> None:
        for order in symbol_state.get("orders") or []:
            if order.get("order_role") != ORDER_ROLE_TAKE_PROFIT or order.get(
                "status"
            ) not in {"SUBMITTED", "CANCEL_AMBIGUOUS"}:
                continue
            remaining = _positive_int(order.get("remaining_qty"))
            if remaining <= 0:
                continue
            attempts = _positive_int(order.get("cancel_attempt_count"))
            if attempts >= MAX_CANCEL_ATTEMPTS:
                if order.get("status") != "CANCEL_FAILED_TERMINAL":
                    order["status"] = "CANCEL_FAILED_TERMINAL"
                    order["cancel_terminal_at"] = now.isoformat()
                    self._save()
                    self._event(
                        "take_profit_cancel_terminal_failure",
                        spec,
                        now,
                        order_no=order.get("order_no"),
                        remaining_qty=remaining,
                        cancel_attempt_count=attempts,
                    )
                continue
            last_attempt = _timestamp(order.get("cancel_attempted_at"))
            if (
                last_attempt is not None
                and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
            ):
                continue
            order["cancel_attempt_count"] = attempts + 1
            try:
                result = self.gateway.cancel(
                    code=spec.code,
                    order_no=str(order.get("order_no") or ""),
                    qty=remaining,
                    route=str(order.get("route") or ""),
                )
            except Exception as exc:
                order["cancel_error"] = type(exc).__name__
                order["cancel_attempted_at"] = now.isoformat()
                order["status"] = "CANCEL_AMBIGUOUS"
                self._save()
                self._event(
                    "take_profit_cancel_ambiguous",
                    spec,
                    now,
                    order_no=order.get("order_no"),
                    remaining_qty=remaining,
                    error=type(exc).__name__,
                )
                continue
            order["cancel_attempted_at"] = now.isoformat()
            order["cancel_return_code"] = result.return_code
            order["cancel_order_no"] = result.order_no
            if result.accepted:
                order["status"] = "CANCEL_REQUESTED"
            elif result.ambiguous:
                order["status"] = "CANCEL_AMBIGUOUS"
            self._save()
            self._event(
                (
                    "take_profit_cancel_requested"
                    if result.accepted
                    else "take_profit_cancel_failed"
                ),
                spec,
                now,
                order_no=order.get("order_no"),
                remaining_qty=remaining,
                return_code=result.return_code,
            )

    def _maybe_submit_exit(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        payload: dict[str, Any],
        now: datetime,
    ) -> None:
        if not symbol_state.get("exit_requested"):
            return
        self._cancel_pending_buys(spec, symbol_state, now)
        self._cancel_pending_take_profit_sells(spec, symbol_state, now)
        if self._has_pending(symbol_state, "BUY") or self._has_pending(
            symbol_state, "SELL"
        ):
            return
        qty = self._open_qty(symbol_state)
        if qty <= 0:
            completed_signal_id = str(symbol_state.get("entry_signal_id") or "")
            if (
                symbol_state.get("entry_episode_open")
                and completed_signal_id
                and symbol_state.get("last_completed_entry_signal_id")
                != completed_signal_id
            ):
                symbol_state["completed_entry_count"] = (
                    _positive_int(symbol_state.get("completed_entry_count")) + 1
                )
                symbol_state["last_completed_entry_signal_id"] = completed_signal_id
                symbol_state["last_episode_completed_at"] = now.isoformat()
            symbol_state["entry_episode_open"] = False
            symbol_state["exit_requested"] = False
            symbol_state["exit_completed_at"] = now.isoformat()
            symbol_state["sell_attempt_count"] = 0
            symbol_state["last_sell_attempt_at"] = None
            self._save()
            return
        attempts = _positive_int(symbol_state.get("sell_attempt_count"))
        if attempts >= MAX_SELL_ATTEMPTS:
            if not symbol_state.get("sell_terminal_failure_at"):
                symbol_state["sell_terminal_failure_at"] = now.isoformat()
                self._save()
                self._event(
                    "sell_terminal_failure",
                    spec,
                    now,
                    remaining_qty=qty,
                    sell_attempt_count=attempts,
                    exit_signal_id=symbol_state.get("exit_signal_id"),
                )
            return
        last_attempt = _timestamp(symbol_state.get("last_sell_attempt_at"))
        if (
            last_attempt is not None
            and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
        ):
            return
        route = str(symbol_state.get("exit_route") or self._route(payload))
        if route not in {"KRX", "NXT"}:
            return
        symbol_state["sell_attempt_count"] = attempts + 1
        symbol_state["last_sell_attempt_at"] = now.isoformat()
        self._save()
        self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="SELL",
            qty=qty,
            route=route,
            signal_id=str(symbol_state.get("exit_signal_id") or ""),
            now=now,
            order_role=ORDER_ROLE_FINAL_EXIT,
            parent_entry_signal_id=str(symbol_state.get("entry_signal_id") or ""),
        )

    def _maybe_request_policy_force_exit(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> None:
        policy = self._execution_policy(spec, symbol_state=symbol_state)
        if (
            policy is None
            or not symbol_state.get("entry_episode_open")
            or symbol_state.get("exit_requested")
            or policy.get("force_flat_at_session_end") is not True
        ):
            return
        force_exit_time = str(policy.get("force_exit_time") or "")
        try:
            cutoff = datetime_time.fromisoformat(force_exit_time)
        except ValueError:
            return
        if now.time().replace(tzinfo=None) < cutoff:
            return
        entry_signal_id = str(symbol_state.get("entry_signal_id") or "")
        symbol_state.update(
            {
                "exit_signal_id": (
                    f"{spec.code}:{now.date().isoformat()}:POLICY_FORCE_FLAT:"
                    f"{force_exit_time}"
                ),
                "exit_requested": True,
                "exit_route": str(symbol_state.get("entry_route") or ""),
                "exit_requested_at": now.isoformat(),
            }
        )
        self._save()
        self._event(
            "policy_force_flat_requested",
            spec,
            now,
            signal_id=entry_signal_id,
            force_exit_time=force_exit_time,
            current_day_open_qty=self._open_qty(symbol_state),
            execution_policy_id=policy["policy_id"],
        )

    def process_payload(
        self, spec: WidgetSpec, payload: dict[str, Any], now: datetime
    ) -> None:
        symbol_state = self._state["symbols"][spec.code]
        self._reconcile(spec, symbol_state, now)
        if self._close_completed_take_profit_episode(spec, symbol_state, now):
            return

        self._maybe_request_policy_force_exit(spec, symbol_state, now)
        exit_signal_id = self._exit_signal(spec, payload, now)
        current_context = spec.contract.session_context(now)
        execution_policy = self._execution_policy(
            spec,
            session=current_context.name,
            symbol_state=symbol_state,
        )
        source_exit_action = (
            str(execution_policy.get("source_final_exit_action") or "")
            if execution_policy is not None
            else ""
        )
        source_exit_action_invalid = bool(
            exit_signal_id
            and execution_policy is not None
            and source_exit_action
            not in {"observe_only_no_forced_sell", "sell_own_filled_quantity"}
        )
        if source_exit_action_invalid:
            if exit_signal_id != symbol_state.get("last_blocked_source_exit_signal_id"):
                symbol_state["last_blocked_source_exit_signal_id"] = exit_signal_id
                self._save()
                self._event(
                    "source_final_exit_blocked_invalid_policy_action",
                    spec,
                    now,
                    signal_id=exit_signal_id,
                    source_final_exit_action=source_exit_action,
                    execution_policy_id=execution_policy.get("policy_id"),
                )
            exit_signal_id = None
        source_exit_observed = bool(
            exit_signal_id
            and execution_policy is not None
            and source_exit_action == "observe_only_no_forced_sell"
        )
        if source_exit_observed:
            if symbol_state.get(
                "entry_episode_open"
            ) and exit_signal_id != symbol_state.get(
                "last_observed_source_exit_signal_id"
            ):
                symbol_state["last_observed_source_exit_signal_id"] = exit_signal_id
                self._save()
                self._event(
                    "source_final_exit_observed_without_forced_sell",
                    spec,
                    now,
                    signal_id=exit_signal_id,
                    current_day_open_qty=self._open_qty(symbol_state),
                    execution_policy_id=execution_policy["policy_id"],
                )
            exit_signal_id = None
        if source_exit_action_invalid:
            self._maybe_submit_take_profit(spec, symbol_state, now)
            return
        if exit_signal_id and exit_signal_id != symbol_state.get("exit_signal_id"):
            symbol_state.update(
                {
                    "exit_signal_id": exit_signal_id,
                    "exit_requested": True,
                    "exit_route": self._route(payload),
                    "exit_requested_at": now.isoformat(),
                }
            )
            self._save()
            self._event(
                "final_exit_signal_consumed",
                spec,
                now,
                signal_id=exit_signal_id,
                current_day_open_qty=self._open_qty(symbol_state),
            )

        self._maybe_submit_exit(spec, symbol_state, payload, now)
        # A source-qualified final exit dominates any entry payload carried in
        # the same snapshot.  Re-entry is possible only after the producer has
        # cleared that final-exit event and emitted a new entry episode.
        if symbol_state.get("exit_requested") or exit_signal_id:
            return

        # The fixed-target policy observes source EXIT without forcing a sell,
        # but that bearish snapshot must not create fresh exposure. Keep only
        # the already-owned quantity's target order covered in this cycle.
        if source_exit_observed:
            self._maybe_submit_take_profit(spec, symbol_state, now)
            return

        self._maybe_submit_scale_in(spec, symbol_state, payload, now)
        self._maybe_submit_take_profit(spec, symbol_state, now)

        entry_signal = self._entry_signal(spec, payload, now)
        if entry_signal is None or symbol_state.get("entry_episode_open"):
            return
        signal_id, source_state, structural_block_reason, entry_policy = entry_signal
        if structural_block_reason:
            advisory = payload.get("advisory")
            advisory = advisory if isinstance(advisory, dict) else {}
            derived = advisory.get("derived")
            derived = derived if isinstance(derived, dict) else {}
            stable_block_id = ":".join(
                [
                    spec.code,
                    now.date().isoformat(),
                    "STRUCTURAL_EXECUTION_BLOCK",
                    structural_block_reason,
                    str(advisory.get("session") or "UNKNOWN"),
                    source_state,
                    str(advisory.get("trigger") or "none"),
                    str(derived.get("confirmed_support") or "none"),
                    str(derived.get("recent_resistance") or "none"),
                ]
            )
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=stable_block_id,
                reason=structural_block_reason,
                now=now,
                source_signal_id=signal_id,
                source_state=source_state,
                trigger=advisory.get("trigger"),
                intraday_regime=advisory.get("intraday_regime"),
                recent_resistance_reclaimed=derived.get("recent_resistance_reclaimed"),
                new_entry_runtime_eligible=(
                    entry_policy.get("new_entry_runtime_eligible")
                    if entry_policy
                    else None
                ),
                new_entry_runtime_block_reason=(
                    entry_policy.get("new_entry_runtime_block_reason")
                    if entry_policy
                    else None
                ),
                research_accumulation_start_date=(
                    entry_policy.get("research_accumulation_start_date")
                    if entry_policy
                    else None
                ),
                research_qualified_observation_date_count=(
                    entry_policy.get("research_qualified_observation_date_count")
                    if entry_policy
                    else None
                ),
                research_minimum_qualified_observation_dates=(
                    entry_policy.get("research_minimum_qualified_observation_dates")
                    if entry_policy
                    else None
                ),
                research_accumulation_gate_status=(
                    entry_policy.get("research_accumulation_gate_status")
                    if entry_policy
                    else None
                ),
            )
            return
        if signal_id == symbol_state.get("entry_signal_id"):
            return
        if entry_policy is not None:
            cutoff_text = str(entry_policy.get("new_entry_cutoff_time") or "")
            try:
                cutoff = datetime_time.fromisoformat(cutoff_text)
            except ValueError:
                self._record_entry_block_once(
                    spec=spec,
                    symbol_state=symbol_state,
                    signal_id=signal_id,
                    reason="entry_blocked_execution_policy_cutoff_invalid",
                    now=now,
                )
                return
            if now.time().replace(tzinfo=None) > cutoff:
                self._record_entry_block_once(
                    spec=spec,
                    symbol_state=symbol_state,
                    signal_id=signal_id,
                    reason="entry_blocked_execution_policy_cutoff",
                    now=now,
                    new_entry_cutoff_time=cutoff_text,
                )
                return
            if _positive_int(symbol_state.get("completed_entry_count")) >= int(
                entry_policy.get("max_completed_entries_per_day", 1)
            ):
                self._record_entry_block_once(
                    spec=spec,
                    symbol_state=symbol_state,
                    signal_id=signal_id,
                    reason="entry_blocked_daily_entry_limit",
                    now=now,
                    completed_entry_count=symbol_state.get("completed_entry_count"),
                )
                return
            last_completed_at = _timestamp(
                symbol_state.get("last_episode_completed_at")
            )
            if (
                last_completed_at is not None
                and (now - last_completed_at).total_seconds()
                < int(entry_policy["reentry_cooldown_minutes"]) * 60
            ):
                self._record_entry_block_once(
                    spec=spec,
                    symbol_state=symbol_state,
                    signal_id=signal_id,
                    reason="entry_blocked_reentry_cooldown",
                    now=now,
                    reentry_cooldown_minutes=entry_policy["reentry_cooldown_minutes"],
                )
                return
            if (
                entry_policy.get("overnight_forbidden") is True
                and _positive_int(symbol_state.get("prior_day_unmanaged_qty")) > 0
            ):
                self._record_entry_block_once(
                    spec=spec,
                    symbol_state=symbol_state,
                    signal_id=signal_id,
                    reason="entry_blocked_prior_day_widget_inventory",
                    now=now,
                    prior_day_unmanaged_qty=symbol_state.get("prior_day_unmanaged_qty"),
                )
                return
        route = self._route(payload)
        if route not in {"KRX", "NXT"}:
            return
        exclusion = evaluate_manual_control_exclusion(spec.code)
        operator_source = manual_control_operator_exclusion_source(spec.code)
        if not exclusion.excluded or not operator_source:
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_main_bot_ownership_not_excluded",
                now=now,
                exclusion_applied=exclusion.excluded,
                exclusion_source=exclusion.source,
                required_source="manual_operator_or_explicit_env",
            )
            return
        if is_buy_side_paused():
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_global_buy_pause",
                now=now,
            )
            return
        for key in (
            "take_profit_basis_block_signal_id",
            "take_profit_basis_blocked_at",
            "take_profit_terminal_failure_at",
            "take_profit_target_price",
            "take_profit_basis_fill_price",
            "take_profit_bps",
            "scale_in_requested",
            "scale_in_trigger_price",
            "scale_in_triggered_at",
            "scale_in_blocked_after_take_profit_fill_at",
            "scale_in_triggered_leg_count",
        ):
            symbol_state.pop(key, None)
        symbol_state.update(
            {
                "entry_episode_open": True,
                "entry_signal_id": signal_id,
                "entry_source_state": source_state,
                "entry_route": route,
                "entry_session": spec.contract.session_context(now).name,
                "entry_consumed_at": now.isoformat(),
                "execution_policy_id": (
                    entry_policy["policy_id"] if entry_policy else None
                ),
                "entry_execution_policy": deepcopy(entry_policy),
                "take_profit_failure_count": 0,
                "last_take_profit_attempt_at": None,
            }
        )
        self._save()
        self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="BUY",
            qty=(
                int(entry_policy["leg_quantity_each"])
                if entry_policy is not None
                else self.entry_qty
            ),
            route=route,
            signal_id=signal_id,
            now=now,
            order_role=ORDER_ROLE_ENTRY_BUY,
        )

    def run_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        now = (observed_at or _now_kst()).astimezone(KST)
        self._activate_date(now)
        self._refresh_same_day_policy_catalog(now)
        if not self.enabled:
            return deepcopy(self._state)
        for spec in self.specs:
            payload = self.snapshot_loader(spec.snapshot_path)
            if payload:
                self.process_payload(spec, payload, now)
            self._notify_pending_buy_actions(
                spec, self._state["symbols"][spec.code], now
            )
        last_cycle_at = _timestamp(self._state.get("last_cycle_at"))
        if (
            last_cycle_at is None
            or (now - last_cycle_at).total_seconds()
            >= OBSERVABILITY_PERSIST_INTERVAL_SEC
        ):
            self._state["last_cycle_at"] = now.isoformat()
            self._save()
        return deepcopy(self._state)

    def run_forever(self, *, interval_sec: float = 1.0) -> None:
        interval = max(0.5, float(interval_sec))
        while True:
            started = time.monotonic()
            self.run_once()
            remaining = interval - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
