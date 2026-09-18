"""Profile-bound persistent state machine for lower-price live episodes."""

from __future__ import annotations

import hashlib
import json
import os

from dataclasses import asdict, replace
from datetime import date, datetime, time
from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    independent_machine_ownership_source,
)
from src.trading.low_price_two_leg.profiles import MachineProfile, get_profile
from src.trading.order.regular_two_leg_machine import KST as KST
from src.trading.order.regular_two_leg_machine import SamsungRegularTwoLegMachine
from src.utils.constants import DATA_DIR

DEFAULT_STATE_DIR = DATA_DIR / "runtime" / "low_price_two_leg"
_SAFE_PRIOR_TERMINAL_POLICY_BLOCK_REASONS = frozenset(
    {"state_leg_target_policy_mismatch"}
)
_SEPARATE_EXIT_OWNER_KEYS = frozenset(
    {"adaptive_exit_session", "profit_stagnation_exit", "holding_target_amendment"}
)


def _episode_ownership_source(code: object) -> str:
    return independent_machine_ownership_source(code, owner="episode")


def default_state_path(profile: MachineProfile) -> Path:
    return DEFAULT_STATE_DIR / f"{profile.profile_id}_state.json"


class LowPriceTwoLegMachine(SamsungRegularTwoLegMachine):
    """One profile, one state file, and one exact broker-order ledger."""

    def __init__(
        self,
        *,
        profile: MachineProfile,
        gateway,
        state_path: Path | None = None,
        live_enabled: bool = False,
        ownership_source: Callable[[object], str] = _episode_ownership_source,
        adaptive_exit_services=None,
    ) -> None:
        self.profile = profile
        super().__init__(
            gateway=gateway,
            state_path=state_path or default_state_path(profile),
            policy=profile.policy,
            strategy_name=profile.profile_id,
            schema=f"low_price_two_leg_{profile.profile_id}_state_v1",
            legacy_schema=f"low_price_two_leg_{profile.profile_id}_legacy_unsupported",
            live_enabled=live_enabled,
            ownership_source=ownership_source,
            entry_timing_owner="episode",
            entry_timing_scope_id=profile.profile_id,
            entry_timing_session=profile.session,
            adaptive_exit_services=adaptive_exit_services,
        )

    def _source(self, now):
        source = super()._source(now)
        bars = [asdict(bar) for bar in source.bars[-(self.policy.lookback_bars + 1):]]
        encoded = json.dumps(bars, sort_keys=True, default=str)
        self._economic_bar_source = {"source_ok": source.source_ok, "error": source.error,
            "observed_at_kst": now.isoformat(), "completed_bars": bars,
            "content_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            "source": "existing_completed_sor_minute_bars_no_extra_poll"}
        return source

    def _record(self, now: datetime, action: str, **fields: object) -> None:
        super()._record(now, action, **fields)
        # Publish every completed-bar evaluation and ledger transition through
        # the existing lossless raw writer. The bounded state audit is not input.
        from src.utils.pipeline_event_logger import emit_pipeline_event
        body = {"schema": "low_price_actual_economic_observation_v1",
            "profile_id": self.profile.profile_id, "symbol": self.profile.symbol,
            "session": self.profile.session, "owner": "episode",
            "logical_date": now.date().isoformat(), "observed_at_kst": now.isoformat(),
            "trade_date": self._state.get("trade_date"), "action": action,
            "policy_hash": self.policy.runtime_policy_hash,
            "policy_source": self.policy.runtime_policy_source,
            "policy_parameters": {"rolling_high_drawdown_pct": self.policy.rolling_high_drawdown_pct,
                "rolling_low_proximity_pct": self.policy.rolling_low_proximity_pct,
                "lookback_bars": self.policy.lookback_bars, "target_ticks": self.policy.target_ticks,
                "entry_valid_completed_bars": self.policy.entry_valid_completed_bars},
            "last_evaluated_bar": self._state.get("last_evaluated_bar"),
            "signal_features": self._state.get("signal_features"),
            "bar_source": getattr(self, "_economic_bar_source", None),
            "legs": self._state.get("legs", []), "position_qty": self._state.get("position_qty"),
            "owned_order_nos": self._state.get("owned_order_nos", []),
            "state_path": str(self.state_path), "runtime_pid": os.getpid(),
            "runtime_cwd": str(Path.cwd().resolve()), "fields": fields,
            "quote_source": "unavailable_in_state", "capital_source": "unavailable_in_state"}
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
        try:
            receipt = emit_pipeline_event("LOW_PRICE_TWO_LEG", self.profile.name, self.profile.symbol,
                "low_price_actual_economic_observation", fields={"logical_date": body["logical_date"],
                    "profile_id": self.profile.profile_id, "owner": "episode", "session": self.profile.session,
                    "observation_schema": body["schema"], "observation_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                    "observation_json": encoded, "policy_hash": self.policy.runtime_policy_hash or "unavailable",
                    "action": action})
            persisted = receipt.get("structured_append_succeeded") is True
        except Exception:
            persisted = False
        # Capture failure blocks economic promotion, not owned inventory exits.
        self._state["economic_capture"] = {"status": "persisted" if persisted else "source_gap",
            "observed_at_kst": now.isoformat(), "observation_sha256": hashlib.sha256(encoded.encode()).hexdigest()}
        self._save()

    def _validate_state_contract(self, now) -> bool:
        if not super()._validate_state_contract(now):
            return False
        legs = self._state.get("legs") or []
        if not legs:
            return True
        try:
            signal_close = int(self._state.get("signal_close", 0) or 0)
            expected_entries = {
                str(plan["leg_id"]): int(plan["entry_price"])
                for plan in self.policy.entry_legs(signal_close)
            }
        except (TypeError, ValueError):
            self._block(now, "state_signal_close_or_entry_plan_invalid")
            return False
        if signal_close <= 0 or any(
            int(leg.get("entry_price", 0) or 0)
            != expected_entries.get(str(leg.get("leg_id") or ""))
            for leg in legs
        ):
            self._block(now, "state_leg_entry_policy_mismatch")
            return False
        for leg in legs:
            try:
                fill_price = int(leg.get("fill_price", 0) or 0)
                target_price = int(leg.get("target_price", 0) or 0)
            except (TypeError, ValueError):
                self._block(now, "state_leg_target_price_invalid")
                return False
            if target_price < 0 or (
                target_price > 0
                and (
                    fill_price <= 0
                    or target_price != self.policy.target_price(fill_price)
                )
            ):
                self._block(now, "state_leg_target_policy_mismatch")
                return False
        return True

    def _roll_prior_terminal_state_before_current_policy_validation(
        self, now: datetime
    ) -> None:
        """Roll a structurally complete prior-day ledger before policy checks.

        Prices in a completed prior-day ledger belong to that day's applied
        policy.  Validating them against today's policy before
        date rollover can turn a clean terminal ledger into a permanent block
        when postclose calibration changes the target rule.  Recovery is
        deliberately limited to zero-exposure, fully terminal ledgers.
        """

        if any(
            "adaptive_exit_session" in leg
            for leg in self._state.get("legs", [])
            if isinstance(leg, dict)
        ):
            return
        if not self._state or self._state.get("trade_date") == now.date().isoformat():
            return
        try:
            position_qty = int(self._state.get("position_qty", 0) or 0)
        except (TypeError, ValueError):
            return
        status = str(self._state.get("status") or "")
        prior_reason = str(self._state.get("blocked_reason") or "")
        if position_qty != 0 or status not in {"COMPLETE", "BLOCKED"}:
            return
        if status == "BLOCKED" and (
            prior_reason not in _SAFE_PRIOR_TERMINAL_POLICY_BLOCK_REASONS
            or self._derive_status() != "COMPLETE"
        ):
            return

        prior_date = str(self._state.get("trade_date") or "")
        self._state.update({"status": "COMPLETE", "blocked_reason": ""})
        if not super()._validate_state_contract(now):
            return
        if not self._roll_date(now):
            return
        self._record(
            now,
            "daily_state_initialized_from_prior_terminal_policy",
            prior_trade_date=prior_date,
            prior_blocked_reason=prior_reason,
        )

    def _has_separate_exit_owner(self) -> bool:
        return any(
            _SEPARATE_EXIT_OWNER_KEYS.intersection(leg)
            for leg in self._state.get("legs", [])
            if isinstance(leg, dict)
        )

    def _reconcile_prior_held_targets_before_rollover(self, now: datetime) -> None:
        """Refresh an old HELD target before treating it as terminal.

        A target can disappear from the open-order query immediately before
        its final execution receipt arrives.  The old state then becomes HELD
        and the bounded service exits.  On the next scheduled start, reusing
        the existing exact dated execution reconciliation closes that narrow
        race without adopting another owner's order or changing live policy.
        """

        if (
            not self._state
            or self._state.get("trade_date") == now.date().isoformat()
            or self._state.get("status") != "HELD"
            or self._has_separate_exit_owner()
        ):
            return
        try:
            if int(self._state.get("position_qty", 0) or 0) <= 0:
                return
        except (TypeError, ValueError):
            return
        if not self._validate_state_contract(now):
            return
        for leg in self._state.get("legs", []):
            if (
                not isinstance(leg, dict)
                or leg.get("status") != "HELD"
                or int(leg.get("position_qty", 0) or 0) <= 0
                or not str(leg.get("target_order_no") or "").strip()
                or not str(leg.get("target_order_date") or "").strip()
                or int(leg.get("target_quantity", 0) or 0) <= 0
            ):
                continue
            self._reconcile_target(now, leg)
            if self._state.get("status") == "BLOCKED":
                return

    def _loaded_state_policy(self, now: datetime):
        """Keep prior-date owned orders on the policy that created them."""

        if (
            not self._state.get("legs")
            or self._state.get("trade_date") == now.date().isoformat()
        ):
            return self.profile.policy
        try:
            source_date = date.fromisoformat(str(self._state.get("trade_date") or ""))
            try:
                prior = get_profile(
                    self.profile.profile_id, target_date=source_date
                ).policy
            except ValueError:
                if not self.profile.policy.dynamic_authority_hash:
                    raise
                prior = self.profile.policy
            features = self._state.get("signal_features") or {}
            if not isinstance(features, dict):
                return None
            return replace(
                prior,
                scan_start=time.fromisoformat(
                    str(features.get("scan_start") or prior.scan_start.isoformat())
                ),
                scan_last_bar=time.fromisoformat(
                    str(
                        features.get("scan_last_bar") or prior.scan_last_bar.isoformat()
                    )
                ),
                lookback_bars=int(features.get("lookback_bars", prior.lookback_bars)),
                rolling_high_drawdown_pct=float(
                    features.get(
                        "required_drawdown_pct",
                        prior.rolling_high_drawdown_pct,
                    )
                ),
                rolling_low_proximity_pct=float(
                    features.get("max_near_low_pct", prior.rolling_low_proximity_pct)
                ),
                entry_valid_completed_bars=int(
                    features.get(
                        "entry_valid_completed_bars",
                        prior.entry_valid_completed_bars,
                    )
                ),
                target_ticks=int(features.get("target_ticks", prior.target_ticks)),
                runtime_policy_source=str(
                    features.get("runtime_policy_source")
                    or "prior_state_custody_compatibility"
                ),
                runtime_policy_hash=str(features.get("runtime_policy_hash") or ""),
                candidate_revision_sha256=str(
                    features.get("candidate_revision_sha256") or ""
                ),
            )
        except (TypeError, ValueError):
            return None

    def _bind_policy(self, policy) -> None:
        self.policy = policy
        self.leg_ids = tuple(policy.entry_leg_ids)

    def _submit_planned_buys(self, now):
        if not self.profile.entry_runtime_eligible and any(
            leg.get("status") == "PLANNED" for leg in self._state.get("legs", [])
        ):
            self._state["blocked_reason"] = "exact_date_profile_entry_retired"
            self._save()
            return
        return super()._submit_planned_buys(now)

    def _consider_entry(self, now):
        if not self.profile.entry_runtime_eligible:
            self._state["last_action"] = "retired_entry_exit_custody_only"
            self._state["blocked_reason"] = "exact_date_profile_entry_retired"
            self._save()
            return self.snapshot()
        return super()._consider_entry(now)

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        set_order_context = getattr(self.gateway, "set_order_context", None)
        if callable(set_order_context):
            set_order_context(observed_at=now)
        current_policy = self.profile.policy
        custody_policy = self._loaded_state_policy(now)
        if custody_policy is None:
            return self._block(now, "prior_state_policy_snapshot_invalid")
        self._bind_policy(custody_policy)
        try:
            self._reconcile_prior_held_targets_before_rollover(now)
            self._roll_prior_terminal_state_before_current_policy_validation(now)
            if self._state.get("trade_date") == now.date().isoformat():
                self._bind_policy(current_policy)
            return super().run_once(now)
        finally:
            self._bind_policy(current_policy)
