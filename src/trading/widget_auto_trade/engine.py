"""Daily-reset live execution state machine for widget advisory signals."""

from __future__ import annotations

from src.trading.order import entry_adverse_guard, entry_adverse_owners

from src.trading.order.profit_stagnation_exit import KEY as PROFIT_EXIT_KEY
from src.trading.order.target_ratchet import KEY as RATCHET_KEY
from src.trading.order.target_ratchet import wait_for_pressure
from src.trading.order.profit_stagnation_owners import OBSERVATION_KEY as PROFIT_OBSERVATION_KEY, active_widget, widget_symbol as run_profit_exit_symbol

import json
import os
import time
import hashlib
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time, timedelta
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
    independent_machine_ownership_source,
)
from src.engine.risk.market_weakness_entry_guard import (
    MarketWeaknessEntryDecision,
    evaluate_market_weakness_entry_guard,
    record_market_weakness_blocked_entry,
)
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocityDecision,
    EntryLiquidityDecision,
    evaluate_entry_execution_velocity,
    evaluate_executable_micro_confirmation,
    evaluate_entry_liquidity,
    unavailable_entry_execution_velocity_snapshot,
    unavailable_entry_liquidity_snapshot,
)
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_up_by_bps
from src.trading.order.adaptive_exit.source import (
    record_first_fill_observation,
    record_target_observation,
)
from src.trading.order.adaptive_exit.owner_loop import (
    OwnerLoopServices,
    step_session,
    binding_authorized,
)
from src.trading.order.adaptive_exit.enrollment import (
    ENROLLMENT_KEY,
    EnrollmentReloadRequired,
    validate_registered_admission,
)
from src.trading.order.adaptive_exit.group_owner_loop import (
    SESSION_KEY as GROUP_SESSION_KEY,
    GroupOwnerPort,
    GroupOwnerSession,
)
from src.trading.order.adaptive_exit.group_whole_exit import (
    SCHEMA as WHOLE_EXIT_SCHEMA,
    make_whole_exit_request,
    validate_whole_exit_request,
)
from src.trading.order.adaptive_exit.group_pending_buy import (
    capture_pending_buys,
    validate_pending_buys,
)
from src.trading.order.adaptive_exit.runtime import OwnerSession
from src.trading.order.adaptive_exit.models import Clock
from src.trading.order.adaptive_exit.arbitration import (
    FINAL_EXIT_KEY,
    make_final_exit_request,
    validate_final_exit_request,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.terminal import (
    TERMINAL_KEY,
    validate_terminal,
    same_terminal,
)
from src.trading.config.symbol_owner_policy import (
    SymbolOwnerPolicyError,
    resolve_symbol_owner_policy,
)
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
    OwnerRegistryError,
    default_order_owner_registry,
)
from src.trading.config.machine_entry_timing_policy import (
    DYNAMIC_MODE,
    ENTRY_CONFIRMATION_MAX_LATE_SEC,
    resolve_entry_confirmation_policy,
)
from src.trading.market.micro_confirmation import advance_live_dynamic_confirmation
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
DEFAULT_ENTRY_REJECT_COOLDOWN_SEC = 60
MAX_ENTRY_REJECT_COOLDOWN_SEC = 1800
CUMULATIVE_RESEARCH_BLOCK_REASONS = frozenset(
    {
        "research_accumulation_incomplete",
        "cumulative_research_40_qualified_dates_incomplete",
    }
)


def _widget_order_ownership_source(code: str, *, target_date: date) -> str:
    """Resolve exact coexistence before the non-veto machine-scope fallback."""

    return independent_machine_ownership_source(
        code,
        owner="widget_auto_trade",
        target_date=target_date,
        new_entry=True,
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
        "fresh_ka10004_integrated_or_nxt_touch_depth;"
        "fresh_route_qualified_ka10003_latest_10_print_velocity;"
        "shared_cached_token_only;exact_order_number_fill_reconciliation"
    ),
    "forbidden_uses": [
        "sell_prior_day_widget_quantity",
        "sell_manual_or_other_strategy_quantity",
        "token_issue_or_refresh",
        "orderable_cash_precheck",
        "non_take_profit_non_final_exit_submission",
        "source_signal_threshold_mutation",
        "entry_liquidity_guard_as_cancel_or_exit_authority",
        "entry_execution_velocity_guard_as_cancel_or_exit_authority",
        "main_bot_process_control",
    ],
}


class OrderGateway(Protocol):
    def entry_liquidity_snapshot(self, *, code: str, route: str): ...
    def entry_execution_velocity_snapshot(self, *, code: str, route: str): ...

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


def _entry_reject_cooldown_sec() -> int:
    """Return bounded retry suppression after a definitive broker rejection.

    Zero explicitly disables the operational guard for rollback.  The guard
    never changes quantity or interprets a rejection as broker authorization;
    it only prevents a stream of distinct widget snapshots from repeating the
    same rejected order every few seconds.
    """

    raw = os.getenv(
        "KORSTOCKSCAN_WIDGET_ENTRY_REJECT_COOLDOWN_SEC",
        str(DEFAULT_ENTRY_REJECT_COOLDOWN_SEC),
    )
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        value = DEFAULT_ENTRY_REJECT_COOLDOWN_SEC
    if value <= 0:
        return 0
    return min(value, MAX_ENTRY_REJECT_COOLDOWN_SEC)


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
        # An adaptive execution journal must not claim durability if the
        # directory containing its atomic rename could not be synchronized.
        if any(
            isinstance(value, dict)
            and (
                "adaptive_exit_sessions" in value
                or GROUP_SESSION_KEY in value
                or PROFIT_EXIT_KEY in value
                or RATCHET_KEY in value
                or value.get("adaptive_exit_history")
            )
            for group in [payload, *(payload.get("history") or [])]
            for value in (group.get("symbols") or {}).values()
        ):
            raise
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
        owner_registry: OrderOwnerRegistry | None = None,
        adaptive_exit_services: OwnerLoopServices | None = None,
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
        self.owner_registry = owner_registry or default_order_owner_registry()
        self.adaptive_exit_services = adaptive_exit_services
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
        # Unlike optional market snapshots, an unreadable custody journal is
        # never an empty portfolio. Keep the file for owner recovery.
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            state = {}
        except (OSError, ValueError) as exc:
            raise ValueError("widget_owner_state_unreadable") from exc
        if not isinstance(state, dict):
            raise ValueError("widget_owner_state_invalid")
        adaptive_claimed = any(
            isinstance(value, dict)
            and ("adaptive_exit_sessions" in value or GROUP_SESSION_KEY in value or PROFIT_EXIT_KEY in value or RATCHET_KEY in value)
            for value in (state.get("symbols") or {}).values()
        )
        adaptive_evidence = adaptive_claimed or any(
            isinstance(value, dict) and value.get("adaptive_exit_history")
            for group in [state, *(state.get("history") or [])]
            for value in (group.get("symbols") or {}).values()
        )
        if (
            state.get("schema_version") != STATE_SCHEMA_VERSION
            or state.get("execution_authority") != EXECUTION_AUTHORITY
        ):
            if adaptive_evidence:
                raise ValueError("adaptive_exit_state_schema_requires_recovery")
            return {}
        if adaptive_claimed:
            # Frozen custody cannot be reset by a new entry-policy catalog.
            return state
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
            added_policy_symbols = set(self._configured_execution_policies) - set(
                stored_policies
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
                if adaptive_evidence:
                    raise ValueError("adaptive_exit_archive_policy_requires_recovery")
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
            "pending_entry_confirmation": None,
        }

    def _save(self) -> None:
        if getattr(self, "_adaptive_enrollment_reload_required", False):
            raise EnrollmentReloadRequired("adaptive_enrollment_reload_required")
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

    @classmethod
    def _unmanaged_overnight_qty(cls, symbol_state: dict[str, Any]) -> int:
        """Preserve older widget-owned carry across trade-date resets.

        ``orders`` contains only the active trade date after each reset.  The
        prior-day field therefore owns inventory carried from still older
        dates and must be added to the active-date open quantity instead of
        being replaced by it.
        """

        prior_qty = _positive_int(symbol_state.get("prior_day_unmanaged_qty"))
        return prior_qty + cls._open_qty(symbol_state)

    def _activate_date(self, observed_at: datetime) -> None:
        day = observed_at.date().isoformat()
        if self._state.get("active_date") == day:
            symbols = self._state.get("symbols")
            if not isinstance(symbols, dict):
                symbols = {}
                self._state["symbols"] = symbols
            changed = False
            for spec in self.specs:
                symbol_state = symbols.get(spec.code)
                if not isinstance(symbol_state, dict):
                    symbol_state = self._empty_symbol_state(spec)
                    symbols[spec.code] = symbol_state
                    changed = True
            if changed:
                self._save()
            return
        prior_symbols = self._state.get("symbols") or {}
        frozen_symbols = {
            code: value
            for code, value in prior_symbols.items()
            if isinstance(value, dict)
            and ("adaptive_exit_sessions" in value or GROUP_SESSION_KEY in value or PROFIT_EXIT_KEY in value or RATCHET_KEY in value)
        }
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
                            "unmanaged_overnight_qty": self._unmanaged_overnight_qty(
                                value
                            ),
                            "unresolved_order_count": sum(
                                1
                                for order in value.get("orders") or []
                                if order.get("status") in ACTIVE_ORDER_STATUSES
                            ),
                            "orders": deepcopy(value.get("orders") or []),
                            "adaptive_exit_history": deepcopy(
                                value.get("adaptive_exit_history", [])
                            ),
                        }
                        for code, value in prior_symbols.items()
                        if isinstance(value, dict) and code not in frozen_symbols
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
            if spec.code in frozen_symbols:
                new_symbols[spec.code] = frozen_symbols[spec.code]
                continue
            symbol_state = self._empty_symbol_state(spec)
            prior_state = prior_symbols.get(spec.code)
            if isinstance(prior_state, dict):
                symbol_state["prior_day_unmanaged_qty"] = self._unmanaged_overnight_qty(
                    prior_state
                )
                symbol_state["prior_day_unmanaged_qty_source"] = (
                    "previous_state_prior_carry_plus_current_day_widget_orders"
                )
                symbol_state["prior_day_unmanaged_qty_broker_reconciled"] = False
                symbol_state["prior_day_unresolved_order_count"] = sum(
                    1
                    for order in prior_state.get("orders") or []
                    if order.get("status") in ACTIVE_ORDER_STATUSES
                )
            new_symbols[spec.code] = symbol_state
        # Carry only claimed owners, including removed catalog symbols. Other
        # symbols can start their normal day; never redate the frozen orders.
        new_symbols.update(frozen_symbols)
        self._state = {
            "active_date": day,
            "symbols": new_symbols,
            "history": [
                row
                for index, row in enumerate(history)
                if index >= len(history) - 30
                or any(
                    isinstance(value, dict) and value.get("adaptive_exit_history")
                    for value in (row.get("symbols") or {}).values()
                )
            ],
        }
        self._save()

    def _event(
        self, event_type: str, spec: WidgetSpec, now: datetime, **fields: Any
    ) -> None:
        policy_session = str(fields.pop("execution_policy_session", "") or "")
        symbol_state = (self._state.get("symbols") or {}).get(spec.code)
        symbol_state = symbol_state if isinstance(symbol_state, dict) else None
        if not policy_session:
            for key in (
                "signal_id",
                "parent_entry_signal_id",
                "source_signal_id",
                "exit_signal_id",
            ):
                identifier = str(fields.get(key) or "").upper()
                matched = next(
                    (
                        candidate
                        for candidate in (
                            "KRX_REGULAR",
                            "NXT_PREMARKET",
                            "NXT_AFTERMARKET",
                        )
                        if f":{candidate}:" in identifier
                    ),
                    None,
                )
                if matched:
                    policy_session = matched
                    break
        episode_owned_event = event_type.startswith(
            ("order_", "buy_cancel_", "take_profit_", "scale_in_")
        ) or event_type in {
            "entry_action_telegram_delivery",
            "policy_force_flat_requested",
            "sell_terminal_failure",
        }
        if not policy_session and episode_owned_event and symbol_state is not None:
            stored_session = str(symbol_state.get("entry_session") or "").upper()
            if stored_session in {
                "KRX_REGULAR",
                "NXT_PREMARKET",
                "NXT_AFTERMARKET",
            }:
                policy_session = stored_session
        if not policy_session:
            policy_session = str(spec.contract.session_context(now).name or "")
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
            # Keep the exact policy/session owner on every event.  The venue
            # alone cannot distinguish NXT premarket from NXT aftermarket,
            # and downstream execution-quality calibration must never borrow
            # a successful KRX event to clear an NXT session (or vice versa).
            "execution_policy_session": policy_session or None,
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
            "market_weakness_entry_guard": (
                symbol_state.get("market_weakness_entry_guard")
                if symbol_state
                else None
            ),
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
        pending_confirmation = symbol_state.get("pending_entry_confirmation")
        if isinstance(pending_confirmation, dict):
            symbol_state["pending_entry_confirmation"] = None
            self._save()
            self._event(
                "entry_confirmation_invalidated",
                spec,
                now,
                signal_id=str(pending_confirmation.get("signal_id") or ""),
                reason=reason,
                entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
            )
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

    def _market_weakness_blocks_entry(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        signal_id: str,
        now: datetime,
        counterfactual_anchor: dict[str, Any] | None = None,
    ) -> bool:
        decision = self._market_weakness_decision(spec=spec, now=now)
        symbol_state["market_weakness_entry_guard"] = {
            **decision.event_fields(),
            "decision_checked_at": now.isoformat(),
        }
        if not decision.blocked:
            return False
        counterfactual_receipt: dict[str, Any] | None = None
        if isinstance(counterfactual_anchor, dict):
            counterfactual_receipt = record_market_weakness_blocked_entry(
                decision,
                now=now,
                scope_id=str(counterfactual_anchor.get("scope_id") or ""),
                session=str(counterfactual_anchor.get("session") or ""),
                source_signal_id=str(
                    counterfactual_anchor.get("source_signal_id") or signal_id
                ),
                signal_bar=str(counterfactual_anchor.get("signal_bar") or ""),
                reference_price=counterfactual_anchor.get("reference_price"),
                target_price=counterfactual_anchor.get("target_price"),
                required_quantity=_positive_int(
                    counterfactual_anchor.get("required_quantity")
                ),
                expected_venues=list(
                    counterfactual_anchor.get("expected_venues") or []
                ),
            )
        self._record_entry_block_once(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=(
                f"{signal_id}:market_weakness:"
                f"{decision.observation_id or decision.phase}"
            ),
            reason=decision.reason,
            now=now,
            source_signal_id=signal_id,
            actual_order_submitted=False,
            market_weakness_counterfactual_observation=counterfactual_receipt,
            **decision.event_fields(),
        )
        return True

    @staticmethod
    def _market_weakness_decision(
        *, spec: WidgetSpec, now: datetime
    ) -> MarketWeaknessEntryDecision:
        return evaluate_market_weakness_entry_guard(
            symbol=spec.code,
            owner="widget",
            now=now,
        )

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

    @staticmethod
    def _snapshot_entry_confirmation_identity(
        *,
        spec: WidgetSpec,
        payload: dict[str, Any],
        advisory: dict[str, Any],
        context: Any,
        now: datetime,
    ) -> str:
        """Build a stable confirmation identity for a non-event setup.

        ``observed_at`` is refreshed by the collector even when the actionable
        setup is unchanged.  Using it as the identity would turn a learned
        1/3/5-second confirmation into repeated invalidation.  The completed
        bar plus the decision-bearing setup fields stay stable across snapshot
        refreshes, while a changed setup or a later bar creates a new signal.
        """

        observation = payload.get("observation")
        observation = observation if isinstance(observation, dict) else {}
        latest_bar = observation.get("latest_completed_bar")
        if not isinstance(latest_bar, dict):
            latest_bar = payload.get("latest_completed_bar")
        latest_bar = latest_bar if isinstance(latest_bar, dict) else {}
        derived = advisory.get("derived")
        derived = derived if isinstance(derived, dict) else {}
        continuity = advisory.get("continuity")
        continuity = continuity if isinstance(continuity, dict) else {}
        identity = {
            "symbol": spec.code,
            "trade_date": now.date().isoformat(),
            "session": context.name,
            "state": advisory.get("state"),
            "trigger": advisory.get("trigger"),
            "entry_price_low": advisory.get("entry_price_low"),
            "entry_price_high": advisory.get("entry_price_high"),
            "completed_bar_source_time": latest_bar.get("source_time"),
            "confirmed_support": derived.get("confirmed_support"),
            "recent_resistance": derived.get("recent_resistance"),
            "recent_resistance_reclaimed": derived.get("recent_resistance_reclaimed"),
            "break_bar_source_time": continuity.get("break_bar_source_time"),
            "reclaim_bar_source_times": continuity.get("reclaim_bar_source_times"),
        }
        if not identity["completed_bar_source_time"]:
            # Without a completed-bar episode anchor, do not merge refreshed
            # snapshots into one confirmation window.
            identity["snapshot_observed_at_fallback"] = advisory.get("observed_at")
        digest = hashlib.sha256(
            json.dumps(
                identity,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return f"SETUP:{digest}"

    @staticmethod
    def _pending_entry_confirmation_is_valid(value: Any, *, target_date: date) -> bool:
        if not isinstance(value, dict):
            return False
        armed_at = _timestamp(value.get("armed_at"))
        due_at = _timestamp(value.get("due_at"))
        delay = value.get("delay_sec")
        provenance = value.get("policy_provenance")
        anchor_snapshot = value.get("anchor_liquidity_snapshot")
        confirmation_mode = str(value.get("confirmation_mode") or "fixed_delay")
        checkpoint_sec = value.get("checkpoint_sec")
        fixed_state_valid = (
            bool(
                confirmation_mode == "fixed_delay"
                and delay in {1, 3, 5}
                and abs((due_at - armed_at).total_seconds() - delay) <= 0.001
                and isinstance(anchor_snapshot, dict)
                and str(anchor_snapshot.get("symbol") or "")
                and str(anchor_snapshot.get("route") or "") in {"KRX", "NXT"}
                and _positive_int(anchor_snapshot.get("best_bid")) > 0
                and _positive_int(anchor_snapshot.get("best_ask")) > 0
            )
            if armed_at is not None and due_at is not None
            else False
        )
        dynamic_state_valid = (
            bool(
                confirmation_mode == DYNAMIC_MODE
                and delay == 0
                and checkpoint_sec in {1, 3, 5}
                and abs((due_at - armed_at).total_seconds() - checkpoint_sec) <= 0.001
                and isinstance(value.get("dynamic_checkpoints"), dict)
                and isinstance(value.get("dynamic_anchor"), dict)
            )
            if armed_at is not None and due_at is not None
            else False
        )
        return bool(
            armed_at is not None
            and due_at is not None
            and not isinstance(delay, bool)
            and isinstance(delay, int)
            and (fixed_state_valid or dynamic_state_valid)
            and armed_at.date() == target_date
            and str(value.get("signal_id") or "")
            and str(value.get("confirmation_identity") or "")
            and str(value.get("source_state") or "")
            and str(value.get("session") or "")
            and str(value.get("route") or "") in {"KRX", "NXT"}
            and isinstance(provenance, dict)
            and provenance.get("status") == "applied"
            and provenance.get("target_date") == target_date.isoformat()
            and len(str(provenance.get("policy_hash") or "")) == 64
            and isinstance(provenance.get("executable_confirmation"), dict)
        )

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

    @staticmethod
    def _owner_context_from_order(order: dict[str, Any]) -> OwnerOrderContext:
        return OwnerOrderContext(
            owner_type="widget_auto_trade",
            owner_id=str(order.get("owner_id") or ""),
            position_id=str(order.get("owner_position_id") or ""),
            client_intent_id=str(order.get("owner_client_intent_id") or ""),
        )

    def _reserve_owner_intent(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        order: dict[str, Any],
        side: str,
        qty: int,
        route: str,
        signal_id: str,
        order_role: str,
        parent_entry_signal_id: str | None,
        now: datetime,
    ) -> str:
        policy = resolve_symbol_owner_policy(spec.code, target_date=now.date())
        if not policy.coexistence_enabled:
            if policy.symbol_selected and not policy.owner_allowed(
                "widget_auto_trade", new_entry=side == "BUY"
            ):
                raise OwnerRegistryError("widget_owner_policy_action_forbidden")
            if self.owner_registry.symbol_registered(spec.code):
                raise OwnerRegistryError(
                    "registered_coexistence_symbol_requires_exact_date_policy"
                )
            return ""
        if not self.owner_registry.decision_activation_matches(policy):
            raise OwnerRegistryError(
                "coexistence_policy_activation_missing_or_mismatched"
            )
        is_new_entry = side == "BUY"
        if not policy.owner_allowed("widget_auto_trade", new_entry=is_new_entry):
            raise OwnerRegistryError("widget_owner_policy_action_forbidden")
        entry_anchor = str(
            parent_entry_signal_id or symbol_state.get("entry_signal_id") or signal_id
        ).strip()
        if not entry_anchor:
            raise OwnerRegistryError("widget_owner_position_anchor_missing")
        position_id = (
            f"widget_auto_trade:{spec.code}:{now.date().isoformat()}:{entry_anchor}"
        )
        order_ordinal = len(symbol_state.get("orders") or [])
        context = OwnerOrderContext(
            owner_type="widget_auto_trade",
            owner_id=f"widget_auto_trade:{spec.code}:{now.date().isoformat()}",
            position_id=position_id,
            client_intent_id=(
                f"{position_id}:{side}:{order_role}:{signal_id}:{order_ordinal}"
            ),
        )
        intent_id = self.owner_registry.reserve(
            context=context,
            symbol=spec.code,
            side=side,
            quantity=qty,
            route=route,
            order_date=now.date(),
            authority_policy_id=policy.policy_id,
            authority_policy_hash=policy.policy_hash,
        )
        order.update(
            {
                "owner_type": context.owner_type,
                "owner_id": context.owner_id,
                "owner_position_id": context.position_id,
                "owner_client_intent_id": context.client_intent_id,
                "owner_registry_intent_id": intent_id,
                "owner_policy_id": policy.policy_id,
                "owner_policy_hash": policy.policy_hash,
            }
        )
        return intent_id

    def _transition_owner_submit(
        self, order: dict[str, Any], result: SubmitResult | None, *, error: str = ""
    ) -> bool:
        intent_id = str(order.get("owner_registry_intent_id") or "")
        if not intent_id:
            return True
        try:
            if result is None:
                self.owner_registry.transition(
                    intent_id, state="INTENT_AMBIGUOUS", reason=error
                )
                return False
            if result.accepted:
                self.owner_registry.transition(
                    intent_id,
                    state="ORDER_BOUND",
                    broker_order_no=result.order_no,
                )
                return True
            self.owner_registry.transition(
                intent_id,
                state=("INTENT_AMBIGUOUS" if result.ambiguous else "INTENT_REJECTED"),
                reason=result.return_msg,
            )
            return not result.ambiguous
        except OwnerRegistryError as exc:
            order["owner_registry_error"] = str(exc)
            try:
                self.owner_registry.transition(
                    intent_id,
                    state="INTENT_AMBIGUOUS",
                    reason=f"registry_transition_failed:{type(exc).__name__}",
                )
            except OwnerRegistryError:
                pass
            return False

    def _cancel_with_owner_registry(
        self,
        *,
        spec: WidgetSpec,
        order: dict[str, Any],
        quantity: int,
        now: datetime,
    ) -> SubmitResult:
        original_intent_id = str(order.get("owner_registry_intent_id") or "")
        if not original_intent_id:
            return self.gateway.cancel(
                code=spec.code,
                order_no=str(order.get("order_no") or ""),
                qty=quantity,
                route=str(order.get("route") or ""),
            )
        original_context = self._owner_context_from_order(order)
        self.owner_registry.assert_owner(
            context=original_context,
            order_date=str(order.get("order_date") or now.date().isoformat()),
            broker_order_no=str(order.get("order_no") or ""),
        )
        cancel_context = OwnerOrderContext(
            owner_type=original_context.owner_type,
            owner_id=original_context.owner_id,
            position_id=original_context.position_id,
            client_intent_id=(
                f"{original_context.client_intent_id}:CANCEL:"
                f"{_positive_int(order.get('cancel_attempt_count'))}"
            ),
        )
        cancel_intent_id = self.owner_registry.reserve(
            context=cancel_context,
            symbol=spec.code,
            side=str(order.get("side") or "BUY"),
            quantity=quantity,
            route=str(order.get("route") or "SOR"),
            order_date=str(order.get("order_date") or now.date().isoformat()),
            action="CANCEL",
            original_order_no=str(order.get("order_no") or ""),
            authority_policy_id=str(order.get("owner_policy_id") or ""),
            authority_policy_hash=str(order.get("owner_policy_hash") or ""),
        )
        order["owner_registry_cancel_intent_id"] = cancel_intent_id
        try:
            result = self.gateway.cancel(
                code=spec.code,
                order_no=str(order.get("order_no") or ""),
                qty=quantity,
                route=str(order.get("route") or ""),
            )
        except Exception as exc:
            try:
                self.owner_registry.transition(
                    cancel_intent_id,
                    state="INTENT_AMBIGUOUS",
                    reason=type(exc).__name__,
                )
            except OwnerRegistryError as registry_exc:
                order["owner_registry_cancel_error"] = str(registry_exc)
                order["owner_registry_cancel_reconciliation_required"] = True
            raise
        try:
            self.owner_registry.transition(
                cancel_intent_id,
                state=(
                    "ORDER_BOUND"
                    if result.accepted
                    else "INTENT_AMBIGUOUS" if result.ambiguous else "INTENT_REJECTED"
                ),
                broker_order_no=result.order_no if result.accepted else "",
                reason=result.return_msg,
            )
        except OwnerRegistryError as exc:
            order.update(
                {
                    "owner_registry_cancel_error": str(exc),
                    "owner_registry_cancel_reconciliation_required": True,
                    "cancel_order_no": result.order_no,
                    "broker_cancel_accepted": bool(result.accepted),
                }
            )
            return SubmitResult(
                accepted=bool(result.accepted),
                order_no=result.order_no,
                return_code="OWNER_REGISTRY_AMBIGUOUS",
                return_msg=str(exc)[:160],
                ambiguous=True,
            )
        return result

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
            self._reserve_owner_intent(
                spec=spec,
                symbol_state=symbol_state,
                order=order,
                side=side,
                qty=qty,
                route=broker_route,
                signal_id=signal_id,
                order_role=order_role,
                parent_entry_signal_id=parent_entry_signal_id,
                now=now,
            )
        except (OwnerRegistryError, SymbolOwnerPolicyError, OSError, ValueError) as exc:
            order.update(
                {
                    "status": "AMBIGUOUS",
                    "return_code": "OWNER_REGISTRY_BLOCKED",
                    "return_msg": str(exc)[:160],
                    "owner_registry_error": str(exc),
                }
            )
            self._save()
            self._event(
                "order_submit_owner_registry_blocked",
                spec,
                now,
                side=side,
                requested_qty=qty,
                signal_id=signal_id,
                reason=str(exc),
                actual_order_submitted=False,
                broker_order_forbidden=True,
            )
            return order
        self._save()
        try:
            if side == "BUY":
                callback = (
                    entry_adverse_owners.widget_callback(self, spec, symbol_state)
                    if order_role == ORDER_ROLE_ENTRY_BUY else None
                )
                with entry_adverse_guard.transport_check(callback):
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
        except entry_adverse_guard.EntryNotSent as exc:
            released = self._transition_owner_submit(order, exc.result)
            order.update(
                status="NOT_SENT" if released else "AMBIGUOUS",
                return_code=exc.result.return_code, return_msg=str(exc),
                broker_accepted=False, actual_order_submitted=False,
            )
            if released:
                symbol_state["entry_episode_open"] = False
                symbol_state.pop("entry_signal_id", None)
            self._save()
            self._event("entry_adverse_not_sent", spec, now, signal_id=signal_id,
                        entry_adverse_flow=dict(symbol_state.get(entry_adverse_guard.KEY) or {}))
            return order
        except Exception as exc:
            self._transition_owner_submit(order, None, error=type(exc).__name__)
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
        registry_transition_ok = self._transition_owner_submit(order, result)
        registry_transition_failed = bool(
            not registry_transition_ok
            and (result.accepted or order.get("owner_registry_intent_id"))
        )
        order.update(
            {
                "order_no": result.order_no,
                "return_code": result.return_code,
                "return_msg": result.return_msg[:160],
                "status": (
                    "AMBIGUOUS"
                    if result.ambiguous or registry_transition_failed
                    else (
                        "SUBMITTED"
                        if result.accepted and registry_transition_ok
                        else "FAILED"
                    )
                ),
                # Broker acceptance is immutable external truth. Registry
                # binding is tracked separately and must not rewrite it.
                "broker_accepted": bool(result.accepted),
                "owner_registry_bind_confirmed": bool(registry_transition_ok),
                "submitted_at": now.isoformat(),
                "source_advisory_state": symbol_state.get("entry_source_state"),
            }
        )
        if registry_transition_failed:
            order["return_code"] = "OWNER_REGISTRY_AMBIGUOUS"
            order["return_msg"] = str(
                order.get("owner_registry_error") or "owner registry binding failed"
            )[:160]
        self._save()
        self._event(
            (
                "order_submit_owner_registry_ambiguous"
                if registry_transition_failed
                else (
                    "order_submit_ambiguous"
                    if result.ambiguous
                    else "order_submitted" if result.accepted else "order_submit_failed"
                )
            ),
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
                "AMBIGUOUS",
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
            prior_execution_venue = str(
                order.get("broker_execution_venue") or ""
            ).strip()
            filled = min(requested, max(prior_filled, snapshot.filled_qty))
            remaining = min(max(0, requested - filled), snapshot.remaining_qty)
            intent_id = str(order.get("owner_registry_intent_id") or "")
            if intent_id:
                try:
                    if order.get("owner_registry_bind_confirmed") is not True:
                        # A broker snapshot with the exact order number is the
                        # recovery proof for an accepted/ambiguous submit whose
                        # initial registry append failed. Bind before applying
                        # any fill so the order can never be inferred from the
                        # aggregate symbol balance.
                        self.owner_registry.transition(
                            intent_id,
                            state="ORDER_BOUND",
                            broker_order_no=order_no,
                            reason="widget_exact_broker_snapshot_rebind",
                        )
                        order["owner_registry_bind_confirmed"] = True
                        order.pop("owner_registry_error", None)
                    self.owner_registry.record_fill(
                        context=self._owner_context_from_order(order),
                        symbol=spec.code,
                        side=str(order.get("side") or ""),
                        order_quantity=requested,
                        order_date=str(
                            order.get("order_date") or now.date().isoformat()
                        ),
                        broker_order_no=order_no,
                        cumulative_filled_qty=filled,
                        cumulative_fill_amount=None,
                    )
                    if remaining == 0:
                        self.owner_registry.transition(
                            intent_id,
                            state="ORDER_TERMINAL",
                            broker_order_no=order_no,
                            reason="widget_execution_snapshot_terminal",
                        )
                except OwnerRegistryError as exc:
                    order["owner_registry_error"] = str(exc)
                    order["owner_registry_reconciliation_required"] = True
                    order["last_reconcile_error"] = "owner_registry_conflict"
                    order["last_reconcile_error_at"] = now.isoformat()
                    changed = True
                    continue
            if order.get("side") == "BUY":
                record_first_fill_observation(
                    order,
                    previous_filled_qty=prior_filled,
                    filled_qty=snapshot.filled_qty,
                    observed_at=now.isoformat(),
                )
            order["filled_qty"] = filled
            order["remaining_qty"] = remaining
            if snapshot.fill_price is not None:
                order["fill_price"] = snapshot.fill_price
            if snapshot.execution_venue:
                # Preserve the signal/intent market_venue and broker_route,
                # while recording where a SOR order actually resides.  This
                # is reconciliation provenance only and never changes submit,
                # cancel, price, quantity, or owner authority.
                order["broker_execution_venue"] = snapshot.execution_venue
            order["last_reconciled_at"] = now.isoformat()
            if remaining == 0:
                order["status"] = (
                    "FILLED"
                    if filled == requested
                    else "PARTIAL_CANCELED" if filled else "CANCELED"
                )
            changed = True
            execution_venue_changed = bool(
                snapshot.execution_venue
                and snapshot.execution_venue != prior_execution_venue
            )
            if (
                filled != prior_filled
                or order.get("status") != prior_status
                or execution_venue_changed
            ):
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
                    broker_execution_venue=order.get("broker_execution_venue"),
                    submitted_at=order.get("submitted_at"),
                    scale_in_leg_index=order.get("scale_in_leg_index"),
                    actual_order_submitted=True,
                )
        if changed:
            self._save()

    def _cancel_pending_buys(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
        *,
        cancel_reason: str = "final_exit_requested",
        allowed_order_roles: frozenset[str] | None = None,
        require_current_day: bool = False,
        require_fresh_reconciliation: bool = False,
        provenance: dict[str, Any] | None = None,
    ) -> None:
        provenance = dict(provenance or {})
        for order in symbol_state.get("orders") or []:
            if order.get("side") != "BUY" or order.get("status") not in {
                "SUBMITTED",
                "CANCEL_AMBIGUOUS",
            }:
                continue
            if (
                allowed_order_roles is not None
                and order.get("order_role") not in allowed_order_roles
            ):
                continue
            if order.get("broker_accepted") is not True:
                continue
            order_no = str(order.get("order_no") or "").strip()
            if not order_no:
                continue
            if require_current_day and str(order.get("order_date") or "") != (
                now.date().isoformat()
            ):
                continue
            if (
                require_fresh_reconciliation
                and order.get("last_reconciled_at") != now.isoformat()
            ):
                fingerprint = ":".join(
                    [
                        order_no,
                        cancel_reason,
                        str(
                            provenance.get("market_weakness_entry_guard_observation_id")
                            or ""
                        ),
                        str(order.get("last_reconcile_error") or "not_fresh"),
                    ]
                )
                if order.get("last_cancel_reconciliation_block_fingerprint") != (
                    fingerprint
                ):
                    order["last_cancel_reconciliation_block_fingerprint"] = fingerprint
                    self._save()
                    self._event(
                        "buy_cancel_blocked_reconciliation_not_fresh",
                        spec,
                        now,
                        order_no=order_no,
                        order_role=order.get("order_role"),
                        cancel_reason=cancel_reason,
                        last_reconcile_error=order.get("last_reconcile_error"),
                        last_reconciled_at=order.get("last_reconciled_at"),
                        actual_order_submitted=False,
                        **provenance,
                    )
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
                        order_role=order.get("order_role"),
                        remaining_qty=remaining,
                        cancel_attempt_count=attempts,
                        cancel_reason=cancel_reason,
                        **provenance,
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
                result = self._cancel_with_owner_registry(
                    spec=spec,
                    order=order,
                    quantity=remaining,
                    now=now,
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
                    order_no=order_no,
                    order_role=order.get("order_role"),
                    filled_qty=_positive_int(order.get("filled_qty")),
                    remaining_qty=remaining,
                    error=type(exc).__name__,
                    cancel_reason=cancel_reason,
                    actual_order_submitted=False,
                    **provenance,
                )
                continue
            order["cancel_attempted_at"] = now.isoformat()
            order["cancel_return_code"] = result.return_code
            order["cancel_order_no"] = result.order_no
            order["cancel_reason"] = cancel_reason
            if provenance:
                order["cancel_provenance"] = provenance
            if result.ambiguous:
                order["status"] = "CANCEL_AMBIGUOUS"
            elif result.accepted:
                order["status"] = "CANCEL_REQUESTED"
            self._save()
            self._event(
                (
                    "buy_cancel_ambiguous"
                    if result.ambiguous
                    else (
                        "buy_cancel_requested"
                        if result.accepted
                        else "buy_cancel_failed"
                    )
                ),
                spec,
                now,
                order_no=order_no,
                cancel_order_no=result.order_no,
                order_role=order.get("order_role"),
                filled_qty=_positive_int(order.get("filled_qty")),
                remaining_qty=remaining,
                return_code=result.return_code,
                ambiguous=result.ambiguous,
                cancel_reason=cancel_reason,
                actual_order_submitted=False,
                broker_cancel_submitted=result.accepted,
                **provenance,
            )

    @staticmethod
    def _has_market_weakness_cancellable_buy(
        symbol_state: dict[str, Any], now: datetime
    ) -> bool:
        return any(
            order.get("side") == "BUY"
            and order.get("order_role")
            in {ORDER_ROLE_ENTRY_BUY, ORDER_ROLE_SCALE_IN_BUY}
            and order.get("broker_accepted") is True
            and str(order.get("order_no") or "").strip()
            and str(order.get("order_date") or "") == now.date().isoformat()
            and order.get("status") in {"SUBMITTED", "CANCEL_AMBIGUOUS"}
            and _positive_int(order.get("remaining_qty")) > 0
            for order in symbol_state.get("orders") or []
        )

    def _cancel_market_weakness_pending_buys(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> None:
        if not self._has_market_weakness_cancellable_buy(symbol_state, now):
            return
        decision = self._market_weakness_decision(spec=spec, now=now)
        if not decision.exact_market_open_buy_cancel_allowed:
            return
        self._cancel_pending_buys(
            spec,
            symbol_state,
            now,
            cancel_reason="market_weakness_active_exact_market",
            allowed_order_roles=frozenset(
                {ORDER_ROLE_ENTRY_BUY, ORDER_ROLE_SCALE_IN_BUY}
            ),
            require_current_day=True,
            require_fresh_reconciliation=True,
            provenance=decision.event_fields(),
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

    def _recover_definitive_rejected_entry_episode(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> bool:
        """Close persisted entry intent after a definitive broker rejection."""
        entry_signal_id = str(symbol_state.get("entry_signal_id") or "")
        if (
            not entry_signal_id
            or not symbol_state.get("entry_episode_open")
            or self._open_qty(symbol_state) > 0
            or self._has_pending(symbol_state, "BUY")
            or self._has_pending(symbol_state, "SELL")
        ):
            return False
        entry_orders = [
            order
            for order in symbol_state.get("orders") or []
            if order.get("side") == "BUY"
            and order.get("order_role") in {None, "", ORDER_ROLE_ENTRY_BUY}
            and order.get("signal_id") == entry_signal_id
        ]
        if not entry_orders or not all(
            order.get("status") == "FAILED" and order.get("broker_accepted") is False
            for order in entry_orders
        ):
            return False
        latest = entry_orders[-1]
        cooldown_sec = _entry_reject_cooldown_sec()
        rejection_fingerprint = self._entry_rejection_fingerprint(
            spec.code,
            latest.get("return_code"),
            latest.get("return_msg"),
        )
        symbol_state.update(
            {
                "entry_episode_open": False,
                "entry_submit_rejected_at": now.isoformat(),
                "entry_submit_rejected_signal_id": entry_signal_id,
                "entry_submit_rejected_return_code": latest.get("return_code"),
                "entry_submit_rejected_return_msg": latest.get("return_msg"),
                "entry_submit_rejected_fingerprint": rejection_fingerprint,
                "entry_submit_rejected_cooldown_sec": cooldown_sec,
                "entry_submit_rejected_cooldown_until": (
                    (now + timedelta(seconds=cooldown_sec)).isoformat()
                    if cooldown_sec > 0
                    else None
                ),
            }
        )
        self._save()
        self._event(
            "entry_episode_recovered_submit_rejected",
            spec,
            now,
            signal_id=entry_signal_id,
            return_code=latest.get("return_code"),
            return_msg=latest.get("return_msg"),
            rejection_fingerprint=rejection_fingerprint,
            retry_cooldown_sec=cooldown_sec,
            actual_order_submitted=False,
            execution_policy_id=symbol_state.get("execution_policy_id"),
        )
        return True

    @staticmethod
    def _entry_rejection_fingerprint(
        code: str, return_code: object, return_msg: object
    ) -> str:
        normalized_msg = " ".join(str(return_msg or "").strip().lower().split())
        return "|".join(
            (
                str(code or "").strip(),
                str(return_code or "").strip(),
                normalized_msg[:160],
            )
        )

    def _block_recent_definitive_entry_rejection(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        source_signal_id: str,
        now: datetime,
    ) -> bool:
        cooldown_until = _timestamp(
            symbol_state.get("entry_submit_rejected_cooldown_until")
        )
        if cooldown_until is None or now >= cooldown_until:
            return False
        fingerprint = str(
            symbol_state.get("entry_submit_rejected_fingerprint") or "unknown"
        )
        remaining_sec = max(0, int((cooldown_until - now).total_seconds()))
        stable_block_id = ":".join(
            (
                spec.code,
                now.date().isoformat(),
                "BROKER_REJECT_COOLDOWN",
                fingerprint,
                cooldown_until.isoformat(),
            )
        )
        self._record_entry_block_once(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=stable_block_id,
            reason="entry_blocked_recent_broker_rejection",
            now=now,
            source_signal_id=source_signal_id,
            rejection_fingerprint=fingerprint,
            rejected_return_code=symbol_state.get("entry_submit_rejected_return_code"),
            rejected_return_msg=symbol_state.get("entry_submit_rejected_return_msg"),
            retry_cooldown_until=cooldown_until.isoformat(),
            retry_cooldown_remaining_sec=remaining_sec,
            actual_order_submitted=False,
        )
        return True

    def _entry_liquidity_decision(
        self, *, spec: WidgetSpec, route: str, requested_quantity: int
    ) -> EntryLiquidityDecision:
        try:
            snapshot = self.gateway.entry_liquidity_snapshot(
                code=spec.code, route=route
            )
        except Exception as exc:
            snapshot = unavailable_entry_liquidity_snapshot(
                symbol=spec.code,
                route=route,
                error=type(exc).__name__,
            )
        return evaluate_entry_liquidity(snapshot, requested_quantity=requested_quantity)

    def _entry_execution_velocity_decision(
        self, *, spec: WidgetSpec, route: str, requested_quantity: int
    ) -> EntryExecutionVelocityDecision:
        try:
            snapshot = self.gateway.entry_execution_velocity_snapshot(
                code=spec.code, route=route
            )
        except Exception as exc:
            snapshot = unavailable_entry_execution_velocity_snapshot(
                symbol=spec.code,
                route=route,
                error=type(exc).__name__,
            )
        return evaluate_entry_execution_velocity(
            snapshot, requested_quantity=requested_quantity
        )

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
        route = str(symbol_state.get("entry_route") or "").upper()
        if route not in {"KRX", "NXT"}:
            return
        scale_in_signal_id = f"{entry_signal_id}:ADD{next_leg_index}"
        scale_in_counterfactual_anchor = {
            "scope_id": f"{spec.code}:{context.name}:SCALE_IN",
            "session": context.name,
            "source_signal_id": scale_in_signal_id,
            "signal_bar": str(
                advisory.get("event_at")
                or advisory.get("source_bar_at")
                or now.isoformat()
            ),
            "reference_price": current_price,
            "target_price": (
                symbol_state.get("take_profit_target_price")
                or advisory.get("target_price")
            ),
            "required_quantity": int(policy["leg_quantity_each"]),
            "expected_venues": [route],
        }
        exclusion = evaluate_manual_control_exclusion(spec.code)
        operator_source = _widget_order_ownership_source(
            spec.code, target_date=now.date()
        )
        if not operator_source:
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=f"{entry_signal_id}:ADD{next_leg_index}",
                reason="scale_in_blocked_main_bot_ownership_not_excluded",
                now=now,
                exclusion_applied=exclusion.excluded,
                exclusion_source=exclusion.source,
                required_source="exact_owner_policy_or_machine_owner_scope",
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
        if self._market_weakness_blocks_entry(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=scale_in_signal_id,
            now=now,
            counterfactual_anchor=scale_in_counterfactual_anchor,
        ):
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
        scale_in_liquidity_identity = (
            f"{entry_signal_id}:ADD{next_leg_index}:{trigger_price}"
        )
        if (
            symbol_state.get("last_scale_in_liquidity_block_identity")
            == scale_in_liquidity_identity
            or symbol_state.get("last_scale_in_execution_velocity_block_identity")
            == scale_in_liquidity_identity
        ):
            return
        liquidity_decision = self._entry_liquidity_decision(
            spec=spec,
            route=route,
            requested_quantity=int(policy["leg_quantity_each"]),
        )
        symbol_state["last_scale_in_liquidity_check"] = (
            liquidity_decision.event_fields()
        )
        if not liquidity_decision.allowed:
            symbol_state["last_scale_in_liquidity_block_identity"] = (
                scale_in_liquidity_identity
            )
            self._save()
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=scale_in_liquidity_identity,
                reason="scale_in_blocked_liquidity_guard",
                now=now,
                trigger_price=trigger_price,
                current_price=current_price,
                actual_order_submitted=False,
                **liquidity_decision.event_fields(),
            )
            return
        symbol_state.pop("last_scale_in_liquidity_block_identity", None)
        self._save()
        self._event(
            "scale_in_liquidity_guard_passed",
            spec,
            now,
            signal_id=scale_in_liquidity_identity,
            trigger_price=trigger_price,
            current_price=current_price,
            actual_order_submitted=False,
            **liquidity_decision.event_fields(),
        )
        velocity_decision = self._entry_execution_velocity_decision(
            spec=spec,
            route=route,
            requested_quantity=int(policy["leg_quantity_each"]),
        )
        symbol_state["last_scale_in_execution_velocity_check"] = (
            velocity_decision.event_fields()
        )
        if not velocity_decision.allowed:
            symbol_state["last_scale_in_execution_velocity_block_identity"] = (
                scale_in_liquidity_identity
            )
            self._save()
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=scale_in_liquidity_identity,
                reason="scale_in_blocked_execution_velocity_guard",
                now=now,
                trigger_price=trigger_price,
                current_price=current_price,
                actual_order_submitted=False,
                **velocity_decision.event_fields(),
            )
            return
        symbol_state.pop("last_scale_in_execution_velocity_block_identity", None)
        self._save()
        self._event(
            "scale_in_execution_velocity_guard_passed",
            spec,
            now,
            signal_id=scale_in_liquidity_identity,
            trigger_price=trigger_price,
            current_price=current_price,
            actual_order_submitted=False,
            **velocity_decision.event_fields(),
        )
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
        # A scale-in creates new exposure and is covered by the same weakness
        # freeze. Re-read before canceling the current target and again before
        # the additional BUY broker write.
        if self._market_weakness_blocks_entry(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=scale_in_signal_id,
            now=now,
            counterfactual_anchor=scale_in_counterfactual_anchor,
        ):
            return
        self._cancel_pending_take_profit_sells(spec, symbol_state, now)
        if self._has_pending(symbol_state, "SELL") or self._has_pending(
            symbol_state, "BUY"
        ):
            return
        if self._market_weakness_blocks_entry(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=scale_in_signal_id,
            now=now,
            counterfactual_anchor=scale_in_counterfactual_anchor,
        ):
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
            # Preserve the exact target's entry basis before a later scale-in,
            # target replacement, or day rollover changes the mutable state.
            entries = [
                {
                    "episode_id": entry_signal_id,
                    "lot_id": (
                        "entry"
                        if row.get("signal_id") == entry_signal_id
                        else f"scale_in:{row.get('scale_in_leg_index')}"
                    ),
                    "order_date": row.get("order_date"),
                    "order_no": row.get("order_no"),
                    "quantity": row.get("filled_qty"),
                    "requested_quantity": row.get("requested_qty"),
                    "price": row.get("fill_price"),
                    "first_fill_observation": row.get(
                        "adaptive_exit_first_fill_observation"
                    ),
                }
                for row in symbol_state.get("orders") or []
                if row.get("side") == "BUY"
                and row.get("broker_accepted") is True
                and (
                    row.get("signal_id") == entry_signal_id
                    or row.get("parent_entry_signal_id") == entry_signal_id
                )
            ]
            parts = entry_signal_id.split(":", 4)
            source_session = parts[3] if len(parts) == 5 else "unknown"
            record_target_observation(
                order,
                owner="widget",
                profile=f"actual:{spec.code}:{source_session}",
                symbol=spec.code,
                session=source_session,
                target={
                    "order_date": order.get("order_date"),
                    "order_no": order.get("order_no"),
                    "route": order.get("broker_route"),
                    "quantity": uncovered_qty,
                    "price": target_price,
                },
                entries=entries,
                entry_policy={
                    "execution_policy_id": symbol_state.get("execution_policy_id"),
                    "execution_policy": policy,
                    "take_profit_bps": take_profit_bps,
                },
                observed_at=datetime.now(KST).isoformat(),
            )
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
                result = self._cancel_with_owner_registry(
                    spec=spec,
                    order=order,
                    quantity=remaining,
                    now=now,
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
            if result.ambiguous:
                order["status"] = "CANCEL_AMBIGUOUS"
            elif result.accepted:
                order["status"] = "CANCEL_REQUESTED"
            self._save()
            self._event(
                (
                    "take_profit_cancel_ambiguous"
                    if result.ambiguous
                    else (
                        "take_profit_cancel_requested"
                        if result.accepted
                        else "take_profit_cancel_failed"
                    )
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
        entry_adverse_owners.expire_pending(self, symbol_state, now)
        if (active_widget(symbol_state) or PROFIT_OBSERVATION_KEY in symbol_state) and getattr(self, "profit_exit_lock_held", lambda: False)() is not True:
            return
        if getattr(self, "_adaptive_enrollment_reload_required", False):
            raise EnrollmentReloadRequired("adaptive_enrollment_reload_required")
        if not active_widget(symbol_state) and self._try_adaptive_enrollment(spec.code, symbol_state, now):
            return
        if GROUP_SESSION_KEY in symbol_state:
            self._run_adaptive_group(
                spec.code, symbol_state, now, source_spec=spec, source_payload=payload
            )
            return
        if "adaptive_exit_sessions" in symbol_state:
            self._run_adaptive_symbol(
                spec.code, symbol_state, now, source_spec=spec, source_payload=payload
            )
            return
        if not active_widget(symbol_state):
            self._reconcile(spec, symbol_state, now)
        self._cancel_market_weakness_pending_buys(
            spec=spec,
            symbol_state=symbol_state,
            now=now,
        )
        self._recover_definitive_rejected_entry_episode(spec, symbol_state, now)
        if not active_widget(symbol_state) and self._close_completed_take_profit_episode(spec, symbol_state, now):
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
            if active_widget(symbol_state):
                run_profit_exit_symbol(self, symbol_state, now)
                return
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
            pending_confirmation = symbol_state.get("pending_entry_confirmation")
            if isinstance(pending_confirmation, dict):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="source_exit_policy_invalid",
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
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

        if run_profit_exit_symbol(self, symbol_state, now, allow_new_target_ratchet=True):
            return
        if self._close_completed_take_profit_episode(spec, symbol_state, now):
            return
        self._maybe_submit_exit(spec, symbol_state, payload, now)
        # A source-qualified final exit dominates any entry payload carried in
        # the same snapshot.  Re-entry is possible only after the producer has
        # cleared that final-exit event and emitted a new entry episode.
        if symbol_state.get("exit_requested") or exit_signal_id:
            pending_confirmation = symbol_state.get("pending_entry_confirmation")
            if isinstance(pending_confirmation, dict):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="final_exit_dominates_entry",
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
            return

        # The fixed-target policy observes source EXIT without forcing a sell,
        # but that bearish snapshot must not create fresh exposure. Keep only
        # the already-owned quantity's target order covered in this cycle.
        if source_exit_observed:
            pending_confirmation = symbol_state.get("pending_entry_confirmation")
            if isinstance(pending_confirmation, dict):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="source_exit_observed",
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
            self._maybe_submit_take_profit(spec, symbol_state, now)
            return

        self._maybe_submit_scale_in(spec, symbol_state, payload, now)
        self._maybe_submit_take_profit(spec, symbol_state, now)

        entry_signal = self._entry_signal(spec, payload, now)
        if entry_signal is None:
            adverse = symbol_state.get(entry_adverse_guard.KEY)
            if isinstance(adverse, dict) and not entry_adverse_guard.terminal(adverse):
                entry_adverse_guard._skip(adverse, "SKIP_SIGNAL_INVALIDATED")
                entry_adverse_owners.record(symbol_state)
                self._save()
            pending_confirmation = symbol_state.get("pending_entry_confirmation")
            if isinstance(pending_confirmation, dict):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="source_signal_no_longer_actionable",
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
            return
        if symbol_state.get("entry_episode_open"):
            return
        signal_id, source_state, structural_block_reason, entry_policy = entry_signal
        pending_confirmation = symbol_state.get("pending_entry_confirmation")
        if (
            pending_confirmation is not None
            and not self._pending_entry_confirmation_is_valid(
                pending_confirmation, target_date=now.date()
            )
        ):
            symbol_state["pending_entry_confirmation"] = None
            self._save()
            self._event(
                "entry_confirmation_invalidated",
                spec,
                now,
                signal_id=(
                    str(pending_confirmation.get("signal_id") or "")
                    if isinstance(pending_confirmation, dict)
                    else ""
                ),
                reason="persisted_confirmation_contract_invalid",
            )
            return
        if isinstance(pending_confirmation, dict):
            pending_due_at = _timestamp(pending_confirmation.get("due_at"))
            if pending_due_at is not None and now > pending_due_at + timedelta(
                seconds=ENTRY_CONFIRMATION_MAX_LATE_SEC
            ):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="confirmation_recheck_window_expired",
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
                return
        if structural_block_reason:
            if isinstance(pending_confirmation, dict):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason=structural_block_reason,
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
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
        if self._block_recent_definitive_entry_rejection(
            spec=spec,
            symbol_state=symbol_state,
            source_signal_id=signal_id,
            now=now,
        ):
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
            pending_confirmation = symbol_state.get("pending_entry_confirmation")
            if isinstance(pending_confirmation, dict):
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="entry_route_invalid",
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
            return
        exclusion = evaluate_manual_control_exclusion(spec.code)
        operator_source = _widget_order_ownership_source(
            spec.code, target_date=now.date()
        )
        if not operator_source:
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_main_bot_ownership_not_excluded",
                now=now,
                exclusion_applied=exclusion.excluded,
                exclusion_source=exclusion.source,
                required_source="exact_owner_policy_or_machine_owner_scope",
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
        timing_session = spec.contract.session_context(now).name
        timing_scope_id = f"{spec.code}:{timing_session}"
        advisory = payload.get("advisory")
        advisory = advisory if isinstance(advisory, dict) else {}
        entry_quantity = (
            int(entry_policy["leg_quantity_each"])
            if entry_policy is not None
            else self.entry_qty
        )
        counterfactual_reference_price = _positive_int(
            advisory.get("entry_price_high")
            or advisory.get("entry_price")
            or payload.get("current_price")
        )
        counterfactual_target_price = _positive_int(advisory.get("target_price"))
        if counterfactual_target_price <= 0 and counterfactual_reference_price > 0:
            counterfactual_target_price = _take_profit_price(
                counterfactual_reference_price,
                profit_bps=(
                    int(entry_policy["take_profit_bps_from_equal_share_average"])
                    if entry_policy is not None
                    else TAKE_PROFIT_BPS
                ),
            )
        counterfactual_anchor = {
            "scope_id": timing_scope_id,
            "session": timing_session,
            "source_signal_id": signal_id,
            "signal_bar": str(
                advisory.get("event_at") or advisory.get("source_bar_at") or signal_id
            ),
            "reference_price": counterfactual_reference_price or None,
            "target_price": counterfactual_target_price or None,
            "required_quantity": entry_quantity,
            "expected_venues": [route],
        }
        if self._market_weakness_blocks_entry(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=signal_id,
            now=now,
            counterfactual_anchor=counterfactual_anchor,
        ):
            return
        confirmation_identity = (
            signal_id
            if spec.event_based
            else self._snapshot_entry_confirmation_identity(
                spec=spec,
                payload=payload,
                advisory=advisory,
                context=spec.contract.session_context(now),
                now=now,
            )
        )
        pending_confirmation = symbol_state.get("pending_entry_confirmation")
        confirmation_delay_sec = 0
        timing_policy_provenance: dict[str, Any] = {}
        if isinstance(pending_confirmation, dict):
            same_signal = bool(
                pending_confirmation.get("confirmation_identity")
                == confirmation_identity
                and pending_confirmation.get("source_state") == source_state
                and pending_confirmation.get("session") == timing_session
                and pending_confirmation.get("route") == route
            )
            if not same_signal:
                symbol_state["pending_entry_confirmation"] = None
                self._save()
                self._event(
                    "entry_confirmation_invalidated",
                    spec,
                    now,
                    signal_id=str(pending_confirmation.get("signal_id") or ""),
                    reason="source_signal_identity_changed",
                    replacement_signal_id=signal_id,
                    entry_confirmation_delay_sec=pending_confirmation.get("delay_sec"),
                )
                pending_confirmation = None
            else:
                signal_id = str(pending_confirmation["signal_id"])
                due_at = _timestamp(pending_confirmation.get("due_at"))
                if due_at is None:
                    symbol_state["pending_entry_confirmation"] = None
                    self._save()
                    self._event(
                        "entry_confirmation_invalidated",
                        spec,
                        now,
                        signal_id=signal_id,
                        reason="persisted_confirmation_due_at_invalid",
                    )
                    return
                if now < due_at:
                    return
                confirmation_delay_sec = int(pending_confirmation["delay_sec"])
                timing_policy_provenance = dict(
                    pending_confirmation.get("policy_provenance") or {}
                )
                active_policy = resolve_entry_confirmation_policy(
                    target_date=now.date(),
                    owner="widget",
                    scope_id=timing_scope_id,
                    symbol=spec.code,
                    session=timing_session,
                    entry_state=source_state,
                )
                active_delay = int(active_policy["delay_sec"])
                active_provenance = dict(active_policy["provenance"])
                pending_mode = str(
                    pending_confirmation.get("confirmation_mode") or "fixed_delay"
                )
                if (
                    active_delay != confirmation_delay_sec
                    or active_policy["mode"] != pending_mode
                    or active_provenance.get("status") != "applied"
                    or active_provenance.get("policy_hash")
                    != timing_policy_provenance.get("policy_hash")
                ):
                    symbol_state["pending_entry_confirmation"] = None
                    self._save()
                    self._event(
                        "entry_confirmation_invalidated",
                        spec,
                        now,
                        signal_id=signal_id,
                        reason="entry_timing_policy_revalidation_failed",
                        entry_confirmation_delay_sec=confirmation_delay_sec,
                        active_policy_status=active_provenance.get("status"),
                    )
                    return
                if pending_mode == DYNAMIC_MODE:
                    armed_at = _timestamp(pending_confirmation.get("armed_at"))
                    checkpoint_sec = int(pending_confirmation["checkpoint_sec"])
                    if armed_at is None:
                        symbol_state["pending_entry_confirmation"] = None
                        self._save()
                        return
                    dynamic_step = advance_live_dynamic_confirmation(
                        now=now,
                        signal_decision_at=armed_at,
                        checkpoint_sec=checkpoint_sec,
                        prior_checkpoints=pending_confirmation.get(
                            "dynamic_checkpoints"
                        ),
                        prior_anchor=pending_confirmation.get("dynamic_anchor"),
                        symbol=spec.code,
                        route=route,
                        owner="widget",
                        baseline_fill_price=counterfactual_reference_price,
                        owner_entry_limit_price=counterfactual_reference_price,
                        owner_target_price=counterfactual_target_price,
                        round_trip_cost_pct=(
                            timing_policy_provenance.get("executable_confirmation")
                            or {}
                        ).get("round_trip_cost_pct"),
                        widget_take_profit=True,
                    )
                    if dynamic_step["action"] == "WAIT":
                        next_checkpoint = int(dynamic_step["next_checkpoint_sec"])
                        pending_confirmation.update(
                            {
                                "due_at": (
                                    armed_at + timedelta(seconds=next_checkpoint)
                                ).isoformat(),
                                "checkpoint_sec": next_checkpoint,
                                "dynamic_checkpoints": dynamic_step["checkpoints"],
                                "dynamic_anchor": dynamic_step["anchor"],
                            }
                        )
                        symbol_state["pending_entry_confirmation"] = (
                            pending_confirmation
                        )
                        self._save()
                        self._event(
                            "entry_dynamic_confirmation_wait",
                            spec,
                            now,
                            signal_id=signal_id,
                            source_state=source_state,
                            checkpoint_sec=next_checkpoint,
                            dynamic_confirmation=dynamic_step,
                        )
                        return
                    symbol_state["pending_entry_confirmation"] = None
                    if dynamic_step["action"] == "REJECT":
                        symbol_state[
                            "last_entry_dynamic_confirmation_block_identity"
                        ] = confirmation_identity
                        self._save()
                        self._record_entry_block_once(
                            spec=spec,
                            symbol_state=symbol_state,
                            signal_id=signal_id,
                            reason="entry_blocked_dynamic_micro_confirmation",
                            now=now,
                            confirmation_identity=confirmation_identity,
                            source_state=source_state,
                            dynamic_confirmation=dynamic_step,
                            actual_order_submitted=False,
                        )
                        return
                    confirmation_delay_sec = int(
                        dynamic_step.get("selected_delay_sec") or checkpoint_sec
                    )
                    timing_policy_provenance["dynamic_runtime_decision"] = dynamic_step
        if (
            symbol_state.get("last_entry_liquidity_block_identity")
            == confirmation_identity
            or symbol_state.get("last_entry_execution_velocity_block_identity")
            == confirmation_identity
            or symbol_state.get("last_entry_executable_micro_block_identity")
            == confirmation_identity
            or symbol_state.get("last_entry_dynamic_confirmation_block_identity")
            == confirmation_identity
        ):
            return
        if pending_confirmation is None:
            timing_policy = resolve_entry_confirmation_policy(
                target_date=now.date(),
                owner="widget",
                scope_id=timing_scope_id,
                symbol=spec.code,
                session=timing_session,
                entry_state=source_state,
            )
            confirmation_delay_sec = int(timing_policy["delay_sec"])
            timing_policy_provenance = dict(timing_policy["provenance"])
            if timing_policy["mode"] == DYNAMIC_MODE:
                dynamic_step = advance_live_dynamic_confirmation(
                    now=now,
                    signal_decision_at=now,
                    checkpoint_sec=0,
                    prior_checkpoints={},
                    prior_anchor={},
                    symbol=spec.code,
                    route=route,
                    owner="widget",
                    baseline_fill_price=counterfactual_reference_price,
                    owner_entry_limit_price=counterfactual_reference_price,
                    owner_target_price=counterfactual_target_price,
                    round_trip_cost_pct=(
                        timing_policy_provenance.get("executable_confirmation") or {}
                    ).get("round_trip_cost_pct"),
                    widget_take_profit=True,
                )
                if dynamic_step["action"] == "WAIT":
                    next_checkpoint = int(dynamic_step["next_checkpoint_sec"])
                    due_at = now + timedelta(seconds=next_checkpoint)
                    symbol_state["pending_entry_confirmation"] = {
                        "signal_id": signal_id,
                        "confirmation_identity": confirmation_identity,
                        "source_state": source_state,
                        "session": timing_session,
                        "route": route,
                        "armed_at": now.isoformat(),
                        "due_at": due_at.isoformat(),
                        "delay_sec": 0,
                        "checkpoint_sec": next_checkpoint,
                        "confirmation_mode": DYNAMIC_MODE,
                        "policy_provenance": timing_policy_provenance,
                        "dynamic_checkpoints": dynamic_step["checkpoints"],
                        "dynamic_anchor": dynamic_step["anchor"],
                    }
                    self._save()
                    self._event(
                        "entry_dynamic_confirmation_armed",
                        spec,
                        now,
                        signal_id=signal_id,
                        source_state=source_state,
                        checkpoint_sec=next_checkpoint,
                        due_at=due_at.isoformat(),
                        timing_policy_hash=timing_policy_provenance.get("policy_hash"),
                        dynamic_confirmation=dynamic_step,
                    )
                    return
                if dynamic_step["action"] == "REJECT":
                    symbol_state["last_entry_dynamic_confirmation_block_identity"] = (
                        confirmation_identity
                    )
                    self._save()
                    self._record_entry_block_once(
                        spec=spec,
                        symbol_state=symbol_state,
                        signal_id=signal_id,
                        reason="entry_blocked_dynamic_micro_confirmation",
                        now=now,
                        confirmation_identity=confirmation_identity,
                        source_state=source_state,
                        dynamic_confirmation=dynamic_step,
                        actual_order_submitted=False,
                    )
                    return
                confirmation_delay_sec = int(
                    dynamic_step.get("selected_delay_sec") or 0
                )
                timing_policy_provenance["dynamic_runtime_decision"] = dynamic_step
            elif confirmation_delay_sec > 0:
                due_at = now + timedelta(seconds=confirmation_delay_sec)
                anchor_liquidity = self._entry_liquidity_decision(
                    spec=spec,
                    route=route,
                    requested_quantity=entry_quantity,
                )
                anchor_snapshot = anchor_liquidity.event_fields()[
                    "entry_liquidity_snapshot"
                ]
                symbol_state["pending_entry_confirmation"] = {
                    "signal_id": signal_id,
                    "confirmation_identity": confirmation_identity,
                    "source_state": source_state,
                    "session": timing_session,
                    "route": route,
                    "armed_at": now.isoformat(),
                    "due_at": due_at.isoformat(),
                    "delay_sec": confirmation_delay_sec,
                    "confirmation_mode": "fixed_delay",
                    "policy_provenance": timing_policy_provenance,
                    "anchor_liquidity_snapshot": anchor_snapshot,
                }
                self._save()
                self._event(
                    "entry_confirmation_armed",
                    spec,
                    now,
                    signal_id=signal_id,
                    source_state=source_state,
                    due_at=due_at.isoformat(),
                    entry_confirmation_delay_sec=confirmation_delay_sec,
                    timing_policy_hash=timing_policy_provenance.get("policy_hash"),
                    anchor_liquidity_snapshot=anchor_snapshot,
                )
                return
        if not entry_adverse_owners.widget_prepare(
            self, spec, symbol_state, identity=confirmation_identity,
            signal_id=signal_id, source_state=source_state, route=route,
            session=timing_session, observed=now, entry_policy=entry_policy,
        ):
            return
        liquidity_decision = self._entry_liquidity_decision(
            spec=spec,
            route=route,
            requested_quantity=entry_quantity,
        )
        symbol_state["last_entry_liquidity_check"] = liquidity_decision.event_fields()
        if not liquidity_decision.allowed:
            symbol_state["last_entry_liquidity_block_identity"] = confirmation_identity
            self._save()
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_liquidity_guard",
                now=now,
                confirmation_identity=confirmation_identity,
                source_state=source_state,
                actual_order_submitted=False,
                **liquidity_decision.event_fields(),
            )
            return
        symbol_state.pop("last_entry_liquidity_block_identity", None)
        self._save()
        self._event(
            "entry_liquidity_guard_passed",
            spec,
            now,
            signal_id=signal_id,
            confirmation_identity=confirmation_identity,
            source_state=source_state,
            actual_order_submitted=False,
            **liquidity_decision.event_fields(),
        )
        executable_micro_decision = None
        if (
            confirmation_delay_sec > 0
            and timing_policy_provenance.get("entry_confirmation_mode") != DYNAMIC_MODE
        ):
            take_profit_bps = (
                int(entry_policy["take_profit_bps_from_equal_share_average"])
                if entry_policy is not None
                else TAKE_PROFIT_BPS
            )
            executable_target_price = _take_profit_price(
                int(liquidity_decision.snapshot.best_ask),
                profit_bps=take_profit_bps,
            )
            anchor_snapshot = (
                pending_confirmation.get("anchor_liquidity_snapshot")
                if isinstance(pending_confirmation, dict)
                else None
            )
            anchor_best_ask = _positive_int(
                anchor_snapshot.get("best_ask")
                if isinstance(anchor_snapshot, dict)
                else None
            )
            executable_micro_decision = evaluate_executable_micro_confirmation(
                anchor_snapshot=anchor_snapshot,
                current_snapshot=liquidity_decision.snapshot,
                requested_quantity=entry_quantity,
                reference_price=counterfactual_reference_price,
                maximum_entry_price=anchor_best_ask,
                target_price=executable_target_price,
                policy=timing_policy_provenance.get("executable_confirmation"),
            )
            symbol_state["last_entry_executable_micro_confirmation_check"] = (
                executable_micro_decision.event_fields()
            )
            if not executable_micro_decision.allowed:
                symbol_state["last_entry_executable_micro_block_identity"] = (
                    confirmation_identity
                )
                self._save()
                self._record_entry_block_once(
                    spec=spec,
                    symbol_state=symbol_state,
                    signal_id=signal_id,
                    reason="entry_blocked_executable_micro_confirmation",
                    now=now,
                    confirmation_identity=confirmation_identity,
                    source_state=source_state,
                    actual_order_submitted=False,
                    **executable_micro_decision.event_fields(),
                )
                return
            symbol_state.pop("last_entry_executable_micro_block_identity", None)
            self._save()
            self._event(
                "entry_executable_micro_confirmation_passed",
                spec,
                now,
                signal_id=signal_id,
                confirmation_identity=confirmation_identity,
                source_state=source_state,
                actual_order_submitted=False,
                **executable_micro_decision.event_fields(),
            )
        velocity_decision = self._entry_execution_velocity_decision(
            spec=spec,
            route=route,
            requested_quantity=entry_quantity,
        )
        symbol_state["last_entry_execution_velocity_check"] = (
            velocity_decision.event_fields()
        )
        if not velocity_decision.allowed:
            symbol_state["last_entry_execution_velocity_block_identity"] = (
                confirmation_identity
            )
            self._save()
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_execution_velocity_guard",
                now=now,
                confirmation_identity=confirmation_identity,
                source_state=source_state,
                actual_order_submitted=False,
                **velocity_decision.event_fields(),
            )
            return
        symbol_state.pop("last_entry_execution_velocity_block_identity", None)
        self._save()
        self._event(
            "entry_execution_velocity_guard_passed",
            spec,
            now,
            signal_id=signal_id,
            confirmation_identity=confirmation_identity,
            source_state=source_state,
            actual_order_submitted=False,
            **velocity_decision.event_fields(),
        )
        # Re-read the independently updated latch immediately before consuming
        # the signal and writing broker intent.  Liquidity/velocity collection
        # may overlap a market-weakness transition.
        if self._market_weakness_blocks_entry(
            spec=spec,
            symbol_state=symbol_state,
            signal_id=signal_id,
            now=now,
            counterfactual_anchor=counterfactual_anchor,
        ):
            return
        for key in (
            "entry_submit_rejected_at",
            "entry_submit_rejected_signal_id",
            "entry_submit_rejected_return_code",
            "entry_submit_rejected_return_msg",
            "entry_submit_rejected_fingerprint",
            "entry_submit_rejected_cooldown_sec",
            "entry_submit_rejected_cooldown_until",
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
                "pending_entry_confirmation": None,
                "entry_episode_open": True,
                "entry_signal_id": signal_id,
                "entry_source_state": source_state,
                "entry_route": route,
                "entry_session": spec.contract.session_context(now).name,
                "entry_consumed_at": now.isoformat(),
                "entry_confirmation_delay_sec": confirmation_delay_sec,
                "entry_timing_policy_provenance": timing_policy_provenance,
                "entry_executable_micro_confirmation": (
                    executable_micro_decision.event_fields()
                    if executable_micro_decision is not None
                    else None
                ),
                "execution_policy_id": (
                    entry_policy["policy_id"] if entry_policy else None
                ),
                "entry_execution_policy": deepcopy(entry_policy),
                "take_profit_failure_count": 0,
                "last_take_profit_attempt_at": None,
            }
        )
        self._save()
        entry_order = self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="BUY",
            qty=entry_quantity,
            route=route,
            signal_id=signal_id,
            now=now,
            order_role=ORDER_ROLE_ENTRY_BUY,
        )
        adverse = symbol_state.get(entry_adverse_guard.KEY)
        if isinstance(adverse, dict):
            if adverse.get("action") == "CONTINUE" and entry_order.get("broker_accepted") is False:
                entry_adverse_guard._skip(adverse, "SKIP_ORIGINAL_OWNER_REJECTED")
            adverse["order_receipt"] = {
                key: entry_order.get(key) for key in
                ("order_no", "status", "broker_accepted", "return_code", "owner_registry_intent_id")
            }
            entry_adverse_owners.record(symbol_state)
            self._save()
        if (
            entry_order.get("status") == "FAILED"
            and entry_order.get("broker_accepted") is False
        ):
            # A definitive broker rejection creates no custody and must not
            # leave the source episode open. Keep the consumed signal id so
            # the same snapshot cannot submit repeatedly, and retain a short
            # rejection cooldown so timestamp-varying snapshots cannot create
            # a broker rejection storm. Ambiguous transport outcomes remain
            # open for broker reconciliation.
            cooldown_sec = _entry_reject_cooldown_sec()
            rejection_fingerprint = self._entry_rejection_fingerprint(
                spec.code,
                entry_order.get("return_code"),
                entry_order.get("return_msg"),
            )
            symbol_state.update(
                {
                    "entry_episode_open": False,
                    "entry_submit_rejected_at": now.isoformat(),
                    "entry_submit_rejected_signal_id": signal_id,
                    "entry_submit_rejected_return_code": entry_order.get("return_code"),
                    "entry_submit_rejected_return_msg": entry_order.get("return_msg"),
                    "entry_submit_rejected_fingerprint": rejection_fingerprint,
                    "entry_submit_rejected_cooldown_sec": cooldown_sec,
                    "entry_submit_rejected_cooldown_until": (
                        (now + timedelta(seconds=cooldown_sec)).isoformat()
                        if cooldown_sec > 0
                        else None
                    ),
                }
            )
            self._save()
            self._event(
                "entry_episode_closed_submit_rejected",
                spec,
                now,
                signal_id=signal_id,
                return_code=entry_order.get("return_code"),
                return_msg=entry_order.get("return_msg"),
                rejection_fingerprint=rejection_fingerprint,
                retry_cooldown_sec=cooldown_sec,
                actual_order_submitted=False,
                execution_policy_id=symbol_state.get("execution_policy_id"),
            )

    def _adaptive_final_exit_requested(
        self,
        code,
        symbol_state,
        sessions,
        now,
        *,
        source_spec=None,
        source_payload=None,
    ) -> bool:
        """Consume only the original policy's qualified EXIT under its lock.

        A consumed request is sticky across source loss/restart and dominates
        trailing. It never dispatches the old parallel SELL/BUY path. Actual
        pending orders and force-flat policy recovery remain separate work.
        """
        services = self.adaptive_exit_services
        policy = symbol_state.get("entry_execution_policy")
        entry_id = symbol_state.get("entry_signal_id")
        now_ms = int(now.timestamp() * 1000)
        receipt = symbol_state.get(FINAL_EXIT_KEY)
        authorize = (
            services.authorize_final_exit
            if isinstance(services, OwnerLoopServices)
            else None
        )
        if receipt is not None:
            validate_final_exit_request(
                receipt,
                sessions=sessions,
                entry_signal_id=entry_id,
                execution_policy=policy,
                now_ms=now_ms,
            )
            if (
                symbol_state.get("exit_requested") is not True
                or symbol_state.get("exit_signal_id") != receipt["signal_id"]
                or symbol_state.get("exit_route") != receipt["route"]
            ):
                raise ValueError("adaptive_final_exit_owner_intent_conflict")
            if not callable(authorize) or authorize(receipt) is not True:
                raise PermissionError("adaptive_final_exit_policy_authority_missing")
            return True
        if symbol_state.get("exit_requested"):
            raise ValueError("adaptive_exit_existing_intent_arbitration_required")
        if (
            not isinstance(services, OwnerLoopServices)
            or services.lock_held() is not True
            or any(
                not binding_authorized(
                    services,
                    s,
                    symbol_state.get(ENROLLMENT_KEY, {}).get(s.position.lot_id),
                    now=now,
                )
                for s in sessions
            )
        ):
            return False
        if source_spec is None:
            source_spec = next((s for s in self.specs if s.code == code), None)
            if source_spec is not None:
                source_payload = self.snapshot_loader(source_spec.snapshot_path)
        if (
            source_spec is None
            or source_spec.code != code
            or not isinstance(source_payload, dict)
        ):
            return False
        signal_id = self._exit_signal(source_spec, source_payload, now)
        if not signal_id:
            return False
        source_at = self._snapshot_time(source_payload)
        if source_at is None:
            return False
        action = (
            policy.get("source_final_exit_action") if isinstance(policy, dict) else None
        )
        if action != "sell_own_filled_quantity":
            # Observe-only/invalid sources cannot request a forced SELL. Keep
            # the adaptive manager running under its own frozen policy.
            symbol_state["adaptive_source_exit_status"] = (
                "observe_only_no_forced_sell"
                if action == "observe_only_no_forced_sell"
                else "source_final_exit_policy_missing_or_invalid"
            )
            return False
        try:
            receipt = make_final_exit_request(
                sessions=sessions,
                entry_signal_id=entry_id,
                execution_policy=policy,
                signal_id=signal_id,
                source_hash=canonical_sha256(source_payload),
                observed_at_ms=int(source_at.timestamp() * 1000),
                accepted_at_ms=now_ms,
                route=self._route(source_payload),
                source_session=source_spec.contract.session_context(now).name,
            )
        except ValueError:
            symbol_state["adaptive_source_exit_status"] = (
                "source_final_exit_scope_or_policy_invalid"
            )
            return False
        if not callable(authorize) or authorize(receipt) is not True:
            symbol_state["adaptive_source_exit_status"] = (
                "source_final_exit_policy_authority_missing"
            )
            return False
        if services.lock_held() is not True:
            raise PermissionError("original_owner_lock_required")
        if any(
            not binding_authorized(
                services,
                s,
                symbol_state.get(ENROLLMENT_KEY, {}).get(s.position.lot_id),
                now=now,
            )
            for s in sessions
        ):
            raise PermissionError("frozen_policy_authority_missing")
        prior = deepcopy(self._state)
        superseded_confirmation = deepcopy(
            symbol_state.get("pending_entry_confirmation")
        )
        symbol_state.update(
            **{FINAL_EXIT_KEY: receipt},
            exit_requested=True,
            exit_signal_id=signal_id,
            exit_route=receipt["route"],
            exit_requested_at=now.isoformat(),
            pending_entry_confirmation=None,
            scale_in_requested=False,
            adaptive_exit_superseded_entry_confirmation=superseded_confirmation,
            adaptive_source_exit_status="original_owner_final_exit_consumed",
        )
        try:
            self._save()
        except BaseException:
            self._state = prior
            raise
        return True

    def _try_adaptive_enrollment(self, code, state, now) -> bool:
        """Persist new independent lot bindings under the original owner lock."""
        if getattr(self, "_adaptive_enrollment_reload_required", False):
            raise EnrollmentReloadRequired("adaptive_enrollment_reload_required")
        services = self.adaptive_exit_services
        if ENROLLMENT_KEY in state and "adaptive_exit_sessions" not in state:
            raise ValueError("adaptive_enrollment_session_missing")
        if (
            not isinstance(services, OwnerLoopServices)
            or services.admission is None
            or not self.enabled
            or services.lock_held() is not True
            or self._state.get("active_date") != now.date().isoformat()
            or "adaptive_exit_sessions" in state
            or ENROLLMENT_KEY in state
            or GROUP_SESSION_KEY in state
            or state.get("owner_registry_reconciliation_required")
            or state.get("pending_entry_confirmation")
            or state.get("exit_requested")
            or state.get("scale_in_requested")
            or state.get("entry_episode_open") is not True
        ):
            return False
        proposals = {}
        buy_keys, target_keys = set(), set()
        try:
            orders = state.get("orders") or []
            targets = [
                o
                for o in orders
                if o.get("side") == "SELL"
                and o.get("order_role") == ORDER_ROLE_TAKE_PROFIT
                and o.get("broker_accepted") is True
                and o.get("status") in {"SUBMITTED", "ACCEPTED"}
            ]
            if not targets:
                return False
            if any(
                o not in targets
                and not (
                    o.get("status") == "FILLED"
                    or o.get("status") == "FAILED"
                    and o.get("broker_accepted") is False
                )
                for o in orders
            ):
                raise ValueError("new_enrollment_competing_order")
            entry_id = state["entry_signal_id"]
            parts = entry_id.split(":", 4)
            if len(parts) != 5:
                raise ValueError("new_enrollment_signal_identity_invalid")
            for target in targets:
                source = target.get("adaptive_exit_target_observations", {}).get(
                    f"{target.get('order_date')}:{target.get('order_no')}"
                )
                if not isinstance(source, dict):
                    raise ValueError("new_target_observation_missing")
                context = self._owner_context_from_order(target)
                session, receipt = services.admission.prepare(
                    source_receipt=source,
                    context=context,
                    target_intent_id=target["owner_registry_intent_id"],
                    now=now,
                )
                entry, p = source["entries"][0], session.position
                buy_key = (entry["order_date"], entry["order_no"])
                target_key = (target["order_date"], target["order_no"])
                if buy_key in buy_keys or target_key in target_keys:
                    raise ValueError("new_enrollment_duplicate_original_order")
                buy_keys.add(buy_key)
                target_keys.add(target_key)
                matches = [
                    o
                    for o in orders
                    if o.get("side") == "BUY"
                    and o.get("order_date") == entry["order_date"]
                    and o.get("order_no") == entry["order_no"]
                ]
                if len(matches) != 1:
                    raise ValueError("new_enrollment_original_buy_missing_or_duplicate")
                buy = matches[0]
                if (
                    session.policy.scope_key
                    != f"widget|actual:{code}:{parts[3]}|{code}|{source['target']['route']}|{parts[3]}"
                    or entry.get("episode_id") != entry_id
                    or target.get("parent_entry_signal_id") != entry_id
                    or target.get("filled_qty") != 0
                    or type(target.get("filled_qty")) is not int
                    or target.get("requested_qty") != p.open_qty
                    or target.get("limit_price") != p.original_target
                    or buy.get("filled_qty") != p.open_qty
                    or buy.get("requested_qty") != p.open_qty
                    or buy.get("fill_price") != p.entry_price
                    or buy.get("status") != "FILLED"
                    or buy.get("broker_accepted") is not True
                    or not (
                        buy.get("signal_id") == entry_id
                        or buy.get("parent_entry_signal_id") == entry_id
                    )
                    or buy.get("adaptive_exit_first_fill_observation")
                    != entry.get("first_fill_observation")
                    or p.lot_id in proposals
                ):
                    raise ValueError("enrollment_original_widget_source_mismatch")
                validate_registered_admission(session, source, self.owner_registry)
                if (
                    not binding_authorized(services, session, receipt, now=now)
                    or services.owner_guard(
                        session.binding,
                        state=session.driver.orders,
                        quantity=p.open_qty,
                        worst_bid=None,
                        now_ms=int(now.timestamp() * 1000),
                    )
                    is not True
                ):
                    raise PermissionError("new_enrollment_owner_authority_missing")
                proposals[p.lot_id] = (session, receipt)
            if buy_keys != {
                (o.get("order_date"), o.get("order_no"))
                for o in orders
                if o.get("side") == "BUY" and o.get("filled_qty", 0) > 0
            }:
                raise ValueError("new_enrollment_unaccounted_original_buy")
            if sum(
                s.position.open_qty for s, _ in proposals.values()
            ) != self._open_qty(state):
                raise ValueError("new_enrollment_whole_episode_quantity_mismatch")
            if (
                services.lock_held() is not True
                or self.adaptive_exit_services is not services
            ):
                raise PermissionError("original_owner_lock_required")
            if any(
                not binding_authorized(services, s, r, now=now)
                for s, r in proposals.values()
            ):
                raise PermissionError("new_enrollment_owner_authority_missing")
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            OwnerRegistryError,
        ) as exc:
            if services.lock_held() is not True:
                raise PermissionError("original_owner_lock_required") from exc
            state["adaptive_exit_enrollment_status"] = str(exc)
            return False
        state["adaptive_exit_sessions"] = {
            k: s.to_payload() for k, (s, _) in proposals.items()
        }
        state[ENROLLMENT_KEY] = {k: r for k, (_, r) in proposals.items()}
        state["adaptive_exit_enrollment_status"] = "enrolled_original_owner_no_order"
        try:
            self._save()
        except BaseException as exc:
            self._adaptive_enrollment_reload_required = True
            raise EnrollmentReloadRequired(
                "adaptive_enrollment_save_uncertain_reload_required"
            ) from exc
        return True

    def _run_adaptive_symbol(
        self, code, symbol_state, now, *, source_spec=None, source_payload=None
    ) -> None:
        """Claim the existing episode; never fall through to source EXIT/BUY.

        Quantity-only reconciliation stays a separate view until an exact
        execution consumer folds exact quantities into the ordinary order ledger.
        A flat episode is not a profitable episode or permission for the next BUY.
        """
        services = self.adaptive_exit_services
        if isinstance(services, OwnerLoopServices) and services.lock_held() is not True:
            return
        try:
            records = symbol_state["adaptive_exit_sessions"]
            if ENROLLMENT_KEY in symbol_state and not isinstance(
                symbol_state[ENROLLMENT_KEY], dict
            ):
                raise ValueError("adaptive_enrollment_receipt_map_invalid")
            if symbol_state.get("owner_registry_reconciliation_required"):
                raise ValueError("adaptive_exit_owner_reconciliation_required")
            if not isinstance(records, dict) or not records:
                raise ValueError("adaptive_exit_session_map_invalid")
            if ENROLLMENT_KEY in symbol_state and (
                set(symbol_state[ENROLLMENT_KEY]) != set(records)
                or any(
                    not isinstance(v, dict)
                    for v in symbol_state[ENROLLMENT_KEY].values()
                )
            ):
                raise ValueError("adaptive_enrollment_receipt_coverage_invalid")
            sessions = [OwnerSession.from_payload(value) for value in records.values()]
            orders = symbol_state.get("orders") or []
            targets = []
            for key, session in zip(records, sessions):
                s, p = session.driver.orders, session.position
                matches = [
                    order
                    for order in orders
                    if order.get("order_no") == s.target.order_no
                    and order.get("order_date") == s.target.trading_date
                ]
                if len(matches) != 1:
                    raise ValueError(
                        "adaptive_exit_original_target_missing_or_duplicate"
                    )
                target = matches[0]
                context = self._owner_context_from_order(target)
                if (
                    key != p.lot_id
                    or (
                        ENROLLMENT_KEY not in symbol_state
                        and p.lot_id != session.target_intent_id
                    )
                    or p.owner_id != "widget"
                    or session.policy.scope_key.split("|")[2] != code
                    or p.episode_id != context.position_id
                    or session.context != context
                    or target.get("owner_registry_intent_id")
                    != session.target_intent_id
                    or target.get("side") != "SELL"
                    or target.get("order_role") != ORDER_ROLE_TAKE_PROFIT
                    or target.get("broker_accepted") is not True
                    or target.get("requested_qty") != p.open_qty
                    or target.get("limit_price") != p.original_target
                    or s.target_filled_qty < target.get("filled_qty", 0)
                ):
                    raise ValueError("adaptive_exit_original_lot_binding_mismatch")
                targets.append(target)
                if isinstance(services, OwnerLoopServices) and not binding_authorized(
                    services,
                    session,
                    symbol_state.get(ENROLLMENT_KEY, {}).get(key),
                    now=now,
                ):
                    raise ValueError("frozen_policy_authority_missing")
            target_keys = {
                (s.driver.orders.target.trading_date, s.driver.orders.target.order_no)
                for s in sessions
            }
            if len(target_keys) != len(sessions):
                raise ValueError("adaptive_exit_duplicate_target_claim")
            if any(
                (order.get("order_date"), order.get("order_no")) not in target_keys
                and not (
                    order.get("status") in {"FILLED", "CANCELED", "TERMINAL_UNFILLED"}
                    or order.get("status") == "FAILED"
                    and order.get("broker_accepted") is False
                )
                for order in orders
            ):
                raise ValueError(
                    "adaptive_exit_competing_order_requires_owner_recovery"
                )
            residual = sum(s.driver.orders.open_qty for s in sessions)
            removed = sum(
                s.driver.orders.exit_filled_qty
                + s.driver.orders.target_filled_qty
                - target.get("filled_qty", 0)
                for s, target in zip(sessions, targets)
            )
            if residual != self._open_qty(symbol_state) - removed:
                raise ValueError("adaptive_exit_whole_episode_custody_mismatch")
            if not self.enabled:
                raise ValueError("adaptive_exit_owner_disabled")
            final_exit = self._adaptive_final_exit_requested(
                code,
                symbol_state,
                sessions,
                now,
                source_spec=source_spec,
                source_payload=source_payload,
            )
            if symbol_state.get("pending_entry_confirmation"):
                raise ValueError("adaptive_exit_existing_intent_arbitration_required")
            for key, session in zip(records, sessions):

                def persist(payload, *, lot_key=key):
                    prior = deepcopy(self._state)
                    records[lot_key] = payload
                    symbol_state["adaptive_exit_remaining_qty"] = sum(
                        OwnerSession.from_payload(value).driver.orders.open_qty
                        for value in records.values()
                    )
                    symbol_state["adaptive_exit_realized_pnl_status"] = (
                        "unreconciled_exact_fill_cost_required"
                    )
                    try:
                        self._save()
                    except BaseException:
                        self._state = prior
                        raise

                reason = step_session(
                    session=session,
                    services=self.adaptive_exit_services,
                    adapter_factory=lambda guard: self.gateway.adaptive_exit_adapter(
                        registry=self.owner_registry,
                        context=session.context,
                        code=code,
                        policy_hash=session.policy.policy_hash,
                        write_guard=guard,
                    ),
                    persist_record=persist,
                    enrollment_receipt=symbol_state.get(ENROLLMENT_KEY, {}).get(key),
                    clock=Clock(int(now.timestamp() * 1000), 0),
                    final_exit_requested=final_exit,
                    final_exit_request=symbol_state.get(FINAL_EXIT_KEY),
                    persist_terminal=lambda receipt, lot_key=key: (
                        self._persist_adaptive_terminal(symbol_state, lot_key, receipt)
                    ),
                )
                symbol_state["adaptive_exit_loop_status"] = reason
                if (
                    isinstance(services, OwnerLoopServices)
                    and services.lock_held() is not True
                ):
                    return
            self._finish_adaptive_episode(code, symbol_state, now)
        except (ValueError, TypeError, PermissionError, OwnerRegistryError) as exc:
            symbol_state["adaptive_exit_loop_status"] = str(exc)
        if not isinstance(services, OwnerLoopServices) or services.lock_held() is True:
            self._save()

    def _validate_adaptive_group_owner(
        self, code, state, session, *, now_ms, proposed_whole=None
    ):
        """Bind the pooled target and ALL admitted BUY lots to ordinary custody."""
        group, context = session.group, session.context
        whole = [
            r
            for r in session.payload["records"].values()
            if r.get("schema") == WHOLE_EXIT_SCHEMA
        ]
        if len(whole) > 1:
            raise ValueError("adaptive_group_multiple_whole_exit_claims")
        request = whole[0]["request"] if whole else proposed_whole
        pending = []
        if request is not None:
            validate_whole_exit_request(
                request,
                session,
                execution_policy=state.get("entry_execution_policy"),
                entry_signal_id=state.get("entry_signal_id"),
                now_ms=now_ms,
            )
            pending = request.get("pending_buys", [])
            validate_pending_buys(
                pending,
                session,
                registry=self.owner_registry,
                orders=state.get("orders"),
            )
            if "pending_confirmation_sha256" in request and (
                request["pending_confirmation_sha256"]
                != canonical_sha256(
                    {"pending": state.get("pending_entry_confirmation")}
                )
                or request["scale_in_requested"]
                != bool(state.get("scale_in_requested"))
            ):
                raise ValueError("adaptive_group_pending_entry_intent_changed")
        if (
            "adaptive_exit_sessions" in state
            or state.get(TERMINAL_KEY)
            or state.get("owner_registry_reconciliation_required")
            or (
                state.get("pending_entry_confirmation")
                and not (request and "pending_confirmation_sha256" in request)
            )
            or state.get("exit_requested")
            or (state.get("scale_in_requested") and not (request and pending))
            or state.get(FINAL_EXIT_KEY)
            or state.get("adaptive_exit_group_recovery_reason")
            or _positive_int(state.get("prior_day_unmanaged_qty"))
            or _positive_int(state.get("prior_day_unresolved_order_count"))
        ):
            raise ValueError("adaptive_group_competing_owner_requires_recovery")
        if (
            not self.enabled
            or group.scope.owner != "widget"
            or group.scope.symbol != code
            or context.owner_type != "widget_auto_trade"
            or group.episode_id != context.position_id
            or state.get("entry_episode_open") is not True
            or not isinstance(state.get("entry_signal_id"), str)
            or not state["entry_signal_id"]
        ):
            raise ValueError("adaptive_group_original_episode_mismatch")
        orders = state.get("orders")
        if not isinstance(orders, list) or not all(isinstance(o, dict) for o in orders):
            raise ValueError("adaptive_group_ordinary_orders_invalid")
        expected = {group.target: ("SELL", group.quantity, group.target_price)}
        expected.update(
            {order: ("BUY", qty, price) for _, order, qty, _, price in group.lots}
        )
        target = None
        for key, (side, qty, price) in expected.items():
            matches = [
                o
                for o in orders
                if o.get("order_date") == key.trading_date
                and o.get("order_no") == key.order_no
            ]
            if len(matches) != 1:
                raise ValueError("adaptive_group_original_order_missing_or_duplicate")
            order = matches[0]
            registered = self.owner_registry.assert_owner(
                context=context,
                order_date=key.trading_date,
                broker_order_no=key.order_no,
            )
            if (
                order.get("side") != side
                or order.get("broker_accepted") is not True
                or order.get("requested_qty") != qty
                or type(order.get("requested_qty")) is not int
                or order.get("owner_id") != context.owner_id
                or order.get("owner_position_id") != context.position_id
                or order.get("route") != group.scope.route
                or order.get("owner_registry_intent_id") != registered.get("intent_id")
                or order.get("owner_client_intent_id")
                != registered.get("client_intent_id")
            ):
                raise ValueError("adaptive_group_original_order_binding_mismatch")
            if side == "BUY":
                if (
                    order.get("filled_qty") != qty
                    or type(order.get("filled_qty")) is not int
                    or order.get("status") != "FILLED"
                    or order.get("fill_price") != price
                ):
                    raise ValueError("adaptive_group_full_buy_receipt_required")
            else:
                target = order
                if (
                    self._owner_context_from_order(order) != context
                    or order.get("order_role") != ORDER_ROLE_TAKE_PROFIT
                    or order.get("limit_price") != price
                    or order.get("parent_entry_signal_id") != state["entry_signal_id"]
                    or type(order.get("filled_qty")) is not int
                    or not 0 <= order["filled_qty"] <= qty
                ):
                    raise ValueError("adaptive_group_original_target_mismatch")
        if any(
            (o.get("order_date"), o.get("order_no"))
            not in (
                {(key.trading_date, key.order_no) for key in expected}
                | {
                    (r["identity"]["order_date"], r["identity"]["broker_order_no"])
                    for r in pending
                }
            )
            and (
                o.get("status") not in {"FILLED", "CANCELED", "TERMINAL_UNFILLED"}
                or o.get("owner_position_id") == context.position_id
            )
            for o in orders
        ):
            raise ValueError("adaptive_group_unaccounted_ordinary_order")
        if (
            self._open_qty(state)
            != group.quantity
            + sum(r["initial_ordinary_filled_qty"] for r in pending)
            - target["filled_qty"]
        ):
            raise ValueError("adaptive_group_whole_episode_quantity_mismatch")
        return True

    def _run_adaptive_group(
        self, code, state, now, *, source_spec=None, source_payload=None
    ):
        """Resume pooled custody before the ordinary source-EXIT/BUY paths."""
        services = self.adaptive_exit_services
        if isinstance(services, OwnerLoopServices) and services.lock_held() is not True:
            return
        try:
            if not isinstance(services, OwnerLoopServices) or services.group is None:
                raise ValueError("group_owner_services_missing")
            # Original-policy full EXIT has a separate sticky journal and writer.
            # Missing independent whole services still fail closed as before.
            policy = state.get("entry_execution_policy")
            whole_supported = services.group.whole_exit is not None
            whole_request = None
            session = GroupOwnerSession.from_payload(state[GROUP_SESSION_KEY])
            whole_active = any(
                r.get("schema") == WHOLE_EXIT_SCHEMA
                for r in session.payload["records"].values()
            )
            if (
                isinstance(policy, dict)
                and policy.get("force_flat_at_session_end") is True
            ):
                try:
                    cutoff = datetime_time.fromisoformat(
                        str(policy.get("force_exit_time") or "")
                    )
                except ValueError:
                    raise ValueError("adaptive_group_force_flat_time_invalid") from None
                if now.time().replace(tzinfo=None) >= cutoff:
                    if whole_supported and not whole_active:
                        whole_request = make_whole_exit_request(
                            session,
                            execution_policy=policy,
                            entry_signal_id=state.get("entry_signal_id"),
                            reason="force_flat",
                            signal_id="force_flat:" + state["entry_signal_id"],
                            source_hash=canonical_sha256(policy),
                            observed_at_ms=int(now.timestamp() * 1000),
                            accepted_at_ms=int(now.timestamp() * 1000),
                            route=session.group.scope.route,
                            source_session=session.group.scope.session,
                        )
                    elif not whole_supported:
                        state["adaptive_exit_group_recovery_reason"] = (
                            "force_flat_requires_group_arbitration"
                        )
            if (
                not whole_active
                and whole_request is None
                and source_spec is not None
                and self._exit_signal(source_spec, source_payload, now)
            ):
                action = (
                    policy.get("source_final_exit_action")
                    if isinstance(policy, dict)
                    else None
                )
                if action == "sell_own_filled_quantity":
                    if whole_supported:
                        source_at = self._snapshot_time(source_payload)
                        if source_at is None or source_spec.code != code:
                            raise ValueError("whole_exit_source_time_or_symbol_missing")
                        whole_request = make_whole_exit_request(
                            session,
                            execution_policy=policy,
                            entry_signal_id=state.get("entry_signal_id"),
                            reason="source_final_exit",
                            signal_id=self._exit_signal(
                                source_spec, source_payload, now
                            ),
                            source_hash=canonical_sha256(source_payload),
                            observed_at_ms=int(source_at.timestamp() * 1000),
                            accepted_at_ms=int(now.timestamp() * 1000),
                            route=self._route(source_payload),
                            source_session=source_spec.contract.session_context(
                                now
                            ).name,
                        )
                    else:
                        state["adaptive_exit_group_recovery_reason"] = (
                            "original_source_exit_requires_group_arbitration"
                        )
                else:
                    state["adaptive_source_exit_status"] = (
                        "observe_only_no_forced_sell"
                        if action == "observe_only_no_forced_sell"
                        else "source_final_exit_policy_missing_or_invalid"
                    )

            def persist(expected, payload):
                if services.lock_held() is not True:
                    raise PermissionError("original_owner_lock_required")
                current = GroupOwnerSession.from_payload(state[GROUP_SESSION_KEY])
                if current.payload["canonical_sha256"] != expected:
                    raise ValueError("group_owner_session_generation_changed")
                prior = deepcopy(self._state)
                state[GROUP_SESSION_KEY] = deepcopy(payload)
                try:
                    self._save()
                    saved = self._read_adaptive_group_file()
                    if (
                        saved.get("symbols", {}).get(code, {}).get(GROUP_SESSION_KEY)
                        != payload
                    ):
                        raise OSError("group_owner_durable_file_readback_missing")
                except BaseException:
                    self._state = prior
                    raise

            if whole_request is not None:
                pending = capture_pending_buys(
                    session,
                    state.get("orders"),
                    self.owner_registry,
                    state.get("entry_signal_id"),
                )
                if (
                    pending
                    or state.get("pending_entry_confirmation")
                    or state.get("scale_in_requested")
                ):
                    whole_request = make_whole_exit_request(
                        session,
                        execution_policy=policy,
                        **{
                            k: whole_request[k]
                            for k in (
                                "entry_signal_id",
                                "reason",
                                "signal_id",
                                "source_hash",
                                "observed_at_ms",
                                "accepted_at_ms",
                                "route",
                                "source_session",
                            )
                        },
                        pending_buys=pending,
                        pending_confirmation=state.get("pending_entry_confirmation"),
                        scale_in_requested=bool(state.get("scale_in_requested")),
                    )

            port = GroupOwnerPort(
                services=services.group,
                lock_held=services.lock_held,
                load_session=lambda: state[GROUP_SESSION_KEY],
                persist_session=persist,
                owner_binding_guard=lambda s: self._validate_adaptive_group_owner(
                    code,
                    state,
                    s,
                    now_ms=int(now.timestamp() * 1000),
                    proposed_whole=whole_request,
                ),
                adapter_factory=lambda s, guard: self.gateway.adaptive_exit_adapter(
                    registry=self.owner_registry,
                    context=s.context,
                    code=code,
                    policy_hash=s.allocation.policy_hash,
                    write_guard=guard,
                ),
            )
            if whole_request is not None:
                port.claim_whole_exit(whole_request)
            result = port.step(int(now.timestamp() * 1000))
            state["adaptive_exit_loop_status"] = result["status"]
            state["adaptive_exit_realized_pnl_status"] = (
                "unreconciled_exact_fill_cost_required"
            )
            if result.get("group_terminal") is True:
                self._finish_adaptive_group(code, state, now, port, result["receipt"])
        except (
            ValueError,
            TypeError,
            KeyError,
            PermissionError,
            OwnerRegistryError,
        ) as exc:
            state["adaptive_exit_loop_status"] = str(exc)
        if not isinstance(services, OwnerLoopServices) or services.lock_held() is True:
            self._save()

    def _read_adaptive_group_file(self):
        try:
            saved = json.loads(self.state_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            # Do not catch this as an ordinary loop diagnostic and overwrite
            # unreadable on-disk evidence with the pre-save in-memory version.
            raise OSError("group_owner_durable_file_invalid") from exc
        if not isinstance(saved, dict):
            raise OSError("group_owner_durable_file_invalid")
        return saved

    def _finish_adaptive_group(self, code, state, now, port, receipt):
        """Full exact group quantities, not BOOK lot profits, close one episode."""
        port.validate_terminal(receipt)
        session = GroupOwnerSession.from_payload(state[GROUP_SESSION_KEY])
        context, signal = session.context, state["entry_signal_id"]
        orders = deepcopy(state["orders"])
        for row in receipt.get("buy_orders", []):
            if "reconciliation_sha256" not in row:
                continue
            matches = [
                o
                for o in orders
                if o.get("order_date") == row["order_date"]
                and o.get("order_no") == row["broker_order_no"]
            ]
            if (
                len(matches) != 1
                or matches[0].get("owner_registry_intent_id") != row["intent_id"]
            ):
                raise ValueError("adaptive_group_terminal_pending_buy_binding_invalid")
            order = matches[0]
            old_filled = order["filled_qty"]
            order.update(
                filled_qty=row["filled_qty"],
                remaining_qty=0,
                status=(
                    "FILLED"
                    if row["filled_qty"] == row["quantity"]
                    else "TERMINAL_UNFILLED"
                ),
                reconciliation_sha256=row["reconciliation_sha256"],
                adaptive_exit_terminal_id=receipt["terminal_id"],
            )
            if old_filled != row["filled_qty"]:
                order.update(
                    fill_price=None,
                    fill_amount_krw=None,
                    commission_krw=None,
                    tax_krw=None,
                )
        for index, row in enumerate(receipt["orders"]):
            matches = [
                o
                for o in orders
                if o.get("order_no") == row["order_no"]
                and o.get("order_date") == row["trading_date"]
            ]
            if index == 0:
                if (
                    len(matches) != 1
                    or matches[0].get("owner_registry_intent_id") != row["intent_id"]
                ):
                    raise ValueError("adaptive_group_terminal_target_binding_invalid")
                order = matches[0]
            else:
                if matches:
                    raise ValueError("adaptive_group_terminal_duplicate_replacement")
                order = dict(
                    side="SELL",
                    order_role="ADAPTIVE_EXIT_SELL",
                    order_no=row["order_no"],
                    order_date=row["trading_date"],
                    parent_entry_signal_id=signal,
                    signal_id=receipt["terminal_id"],
                    owner_id=context.owner_id,
                    owner_position_id=context.position_id,
                    owner_registry_intent_id=row["intent_id"],
                    owner_client_intent_id=row["client_intent_id"],
                    requested_qty=row["requested_qty"],
                    route=row["route"],
                    broker_route=row["route"],
                    broker_accepted=True,
                    fill_price=None,
                )
                orders.append(order)
            order.update(
                filled_qty=row["filled_qty"],
                remaining_qty=0,
                status=(
                    "FILLED"
                    if row["filled_qty"] == row["requested_qty"]
                    else "TERMINAL_UNFILLED"
                ),
                adaptive_exit_terminal_id=receipt["terminal_id"],
                reconciliation_sha256=row["reconciliation_sha256"],
                realized_pnl_status=receipt["realized_pnl_status"],
            )
        if self._filled_qty({"orders": orders}, "BUY") != self._filled_qty(
            {"orders": orders}, "SELL"
        ):
            raise ValueError("adaptive_group_terminal_ordinary_ledger_not_flat")
        # Recheck policy/lock/registry after projection, before archival.
        port.validate_terminal(receipt)
        prior = deepcopy(self._state)
        state.setdefault("adaptive_exit_history", []).append(
            {
                "group_session": session.to_payload(),
                "group_terminal": deepcopy(receipt),
                "entry_signal_id": signal,
                "superseded_pending_entry_confirmation": deepcopy(
                    state.get("pending_entry_confirmation")
                ),
                "superseded_scale_in_requested": bool(state.get("scale_in_requested")),
                "completed_observed_at": datetime.fromtimestamp(
                    receipt["observed_at_ms"] / 1000, KST
                ).isoformat(),
            }
        )
        state.update(
            orders=orders,
            entry_episode_open=False,
            exit_requested=False,
            scale_in_requested=False,
            pending_entry_confirmation=None,
            last_episode_completed_at=datetime.fromtimestamp(
                receipt["observed_at_ms"] / 1000, KST
            ).isoformat(),
            last_completed_entry_signal_id=signal,
            completed_entry_count=_positive_int(state.get("completed_entry_count")) + 1,
            adaptive_exit_loop_status="execution_terminal_handoff_completed",
        )
        del state[GROUP_SESSION_KEY]
        try:
            self._save()
            saved = self._read_adaptive_group_file()
            if saved.get("symbols", {}).get(code) != state:
                raise OSError("group_owner_terminal_file_readback_missing")
        except BaseException:
            self._state = prior
            raise

    def _persist_adaptive_terminal(self, symbol_state, key, receipt):
        session = OwnerSession.from_payload(symbol_state["adaptive_exit_sessions"][key])
        validate_terminal(receipt, session)
        existing = symbol_state.get(TERMINAL_KEY, {}).get(key)
        if existing is not None:
            validate_terminal(existing, session)
            same_terminal(existing, receipt)
            return
        prior = deepcopy(self._state)
        symbol_state.setdefault(TERMINAL_KEY, {})[key] = receipt
        try:
            self._save()
        except BaseException:
            self._state = prior
            raise

    def _finish_adaptive_episode(self, code, symbol_state, now):
        """Release only a fully reconciled episode to unchanged entry gates."""
        services = self.adaptive_exit_services
        if (
            not isinstance(services, OwnerLoopServices)
            or services.lock_held() is not True
        ):
            return
        sessions = symbol_state["adaptive_exit_sessions"]
        if any(
            OwnerSession.from_payload(raw).manager_required for raw in sessions.values()
        ):
            return
        signal_id = symbol_state.get("entry_signal_id")
        if (
            not isinstance(signal_id, str)
            or not signal_id
            or symbol_state.get("entry_episode_open") is not True
        ):
            raise ValueError("adaptive_terminal_entry_episode_identity_missing")
        receipts = symbol_state.get(TERMINAL_KEY, {})
        entry_dates = {
            datetime.fromtimestamp(
                OwnerSession.from_payload(raw).position.first_fill_at_ms / 1000, KST
            )
            .date()
            .isoformat()
            for raw in sessions.values()
        }
        if len(entry_dates) != 1:
            raise ValueError("adaptive_terminal_mixed_entry_dates")
        entry_date = next(iter(entry_dates))
        orders = deepcopy(symbol_state["orders"])
        for key, raw in sessions.items():
            session = OwnerSession.from_payload(raw)
            receipt = receipts.get(key)
            validate_terminal(receipt, session)
            if not binding_authorized(
                services,
                session,
                symbol_state.get(ENROLLMENT_KEY, {}).get(key),
                now=now,
            ):
                raise ValueError("frozen_policy_authority_missing")
            if (
                self.owner_registry.owner_position_qty(
                    session.context.position_id, symbol=code
                )
                != 0
            ):
                raise ValueError("adaptive_terminal_owner_custody_not_flat")
            target = next(
                o
                for o in orders
                if o.get("order_no") == session.driver.orders.target.order_no
                and o.get("order_date") == session.driver.orders.target.trading_date
            )
            if target.get("parent_entry_signal_id") != signal_id:
                raise ValueError("adaptive_terminal_entry_signal_mismatch")
            for index, row in enumerate(receipt["orders"]):
                if index:
                    if any(
                        o.get("order_no") == row["order_no"]
                        and o.get("order_date") == row["trading_date"]
                        for o in orders
                    ):
                        raise ValueError("adaptive_terminal_duplicate_replacement")
                    order = {
                        "side": "SELL",
                        "order_role": "ADAPTIVE_EXIT_SELL",
                        "order_no": row["order_no"],
                        "order_date": row["trading_date"],
                        "parent_entry_signal_id": signal_id,
                        "signal_id": receipt["terminal_id"],
                        "owner_id": session.context.owner_id,
                        "owner_position_id": session.context.position_id,
                        "owner_registry_intent_id": row["intent_id"],
                        "owner_client_intent_id": row["client_intent_id"],
                        "requested_qty": row["requested_qty"],
                        "route": row["route"],
                        "broker_route": row["route"],
                        "broker_accepted": True,
                        "fill_price": None,
                    }
                    orders.append(order)
                else:
                    order = target
                order.update(
                    filled_qty=row["filled_qty"],
                    remaining_qty=0,
                    status=(
                        "FILLED"
                        if row["filled_qty"] == row["requested_qty"]
                        else "TERMINAL_UNFILLED"
                    ),
                    adaptive_exit_terminal_id=receipt["terminal_id"],
                    reconciliation_sha256=row["reconciliation_sha256"],
                    realized_pnl_status=receipt["realized_pnl_status"],
                )
        if self._open_qty({"orders": orders}) != 0:
            raise ValueError("adaptive_terminal_ordinary_ledger_not_flat")
        prior = deepcopy(self._state)
        if services.lock_held() is not True:
            return
        symbol_state.setdefault("adaptive_exit_history", []).append(
            {
                "sessions": deepcopy(sessions),
                "enrollments": deepcopy(symbol_state.get(ENROLLMENT_KEY)),
                "terminals": deepcopy(receipts),
                "entry_signal_id": signal_id,
                "completed_observed_at": now.isoformat(),
                "final_exit_request": deepcopy(symbol_state.get(FINAL_EXIT_KEY)),
                "superseded_entry_confirmation": deepcopy(
                    symbol_state.get("adaptive_exit_superseded_entry_confirmation")
                ),
            }
        )
        symbol_state.update(
            orders=orders,
            entry_episode_open=False,
            exit_requested=False,
            scale_in_requested=False,
            last_episode_completed_at=now.isoformat(),
            last_completed_entry_signal_id=signal_id,
            completed_entry_count=_positive_int(
                symbol_state.get("completed_entry_count")
            )
            + 1,
            adaptive_exit_loop_status="execution_terminal_handoff_completed",
        )
        del symbol_state["adaptive_exit_sessions"]
        symbol_state.pop(ENROLLMENT_KEY, None)
        del symbol_state[TERMINAL_KEY]
        symbol_state.pop(FINAL_EXIT_KEY, None)
        symbol_state.pop("adaptive_exit_superseded_entry_confirmation", None)
        if entry_date != now.date().isoformat():
            # A recovered prior-day completion must not spend today's entry cap
            # or retain yesterday's signal latch. Preserve the complete ledger.
            from types import SimpleNamespace

            self._state.setdefault("history", []).append(
                {
                    "trade_date": entry_date,
                    "reset_at": now.isoformat(),
                    "symbols": {code: deepcopy(symbol_state)},
                    "overnight_policy": "adaptive_exact_flat_handoff",
                }
            )
            self._state["symbols"][code] = self._empty_symbol_state(
                SimpleNamespace(code=code, name=symbol_state.get("name", code))
            )
        try:
            self._save()
        except BaseException:
            self._state = prior
            raise

    def run_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        now = (observed_at or _now_kst()).astimezone(KST)
        if getattr(self, "_profit_exit_reload_required", False):
            raise OSError("profit_exit_owner_reload_required")
        if any(active_widget(s) or PROFIT_OBSERVATION_KEY in s for s in (self._state.get("symbols") or {}).values()) and getattr(self, "profit_exit_lock_held", lambda: False)() is not True:
            return deepcopy(self._state)
        if getattr(self, "_adaptive_enrollment_reload_required", False):
            raise EnrollmentReloadRequired("adaptive_enrollment_reload_required")
        services = self.adaptive_exit_services
        if isinstance(services, OwnerLoopServices) and services.lock_held() is not True:
            result = deepcopy(self._state)
            result["adaptive_exit_loop_status"] = "original_owner_lock_required"
            return result
        self._activate_date(now)
        claimed = set()
        # Also resume removed catalog symbols and the producer-no-snapshot
        # branch; a new entry catalog must not orphan a frozen SELL manager.
        for code, state in (self._state.get("symbols") or {}).items():
            if isinstance(state, dict) and active_widget(state):
                claimed.add(code)
                spec = next((s for s in self.specs if s.code == code), None)
                payload = self.snapshot_loader(spec.snapshot_path) if spec else None
                if payload:
                    self.process_payload(spec, payload, now)
                else:
                    run_profit_exit_symbol(self, state, now)
                continue
            if isinstance(state, dict) and self._try_adaptive_enrollment(
                code, state, now
            ):
                claimed.add(code)
                continue
            if isinstance(state, dict) and (
                "adaptive_exit_sessions" in state or GROUP_SESSION_KEY in state
            ):
                claimed.add(code)
                if GROUP_SESSION_KEY in state:
                    spec = next((s for s in self.specs if s.code == code), None)
                    payload = self.snapshot_loader(spec.snapshot_path) if spec else None
                    self._run_adaptive_group(
                        code,
                        state,
                        now,
                        source_spec=spec if payload else None,
                        source_payload=payload,
                    )
                else:
                    self._run_adaptive_symbol(code, state, now)
                if (
                    isinstance(services, OwnerLoopServices)
                    and services.lock_held() is not True
                ):
                    return deepcopy(self._state)
        if self._state.get("active_date") != now.date().isoformat():
            return deepcopy(self._state)
        self._refresh_same_day_policy_catalog(now)
        if not self.enabled:
            return deepcopy(self._state)
        for spec in self.specs:
            if spec.code in claimed:
                continue
            payload = self.snapshot_loader(spec.snapshot_path)
            if payload:
                self.process_payload(spec, payload, now)
            else:
                # Broker reconciliation and an approved market-weakness
                # cancellation must not depend on a producer snapshot being
                # present.  This branch never creates a new entry signal.
                symbol_state = self._state["symbols"][spec.code]
                if run_profit_exit_symbol(self, symbol_state, now):
                    continue
                self._reconcile(spec, symbol_state, now)
                self._cancel_market_weakness_pending_buys(
                    spec=spec,
                    symbol_state=symbol_state,
                    now=now,
                )
                self._recover_definitive_rejected_entry_episode(spec, symbol_state, now)
                self._close_completed_take_profit_episode(spec, symbol_state, now)
                self._maybe_submit_take_profit(spec, symbol_state, now)
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
                wait_for_pressure(
                    self, remaining, owner_type="widget_auto_trade",
                    now_fn=lambda: datetime.now(tz=KST),
                )
