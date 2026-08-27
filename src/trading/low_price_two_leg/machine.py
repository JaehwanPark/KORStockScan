"""Profile-bound persistent state machine for lower-price live episodes."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time
from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.low_price_two_leg.profiles import MachineProfile, get_profile
from src.trading.order.regular_two_leg_machine import KST as KST
from src.trading.order.regular_two_leg_machine import SamsungRegularTwoLegMachine
from src.utils.constants import DATA_DIR

DEFAULT_STATE_DIR = DATA_DIR / "runtime" / "low_price_two_leg"
_SAFE_PRIOR_TERMINAL_POLICY_BLOCK_REASONS = frozenset(
    {"state_leg_target_policy_mismatch"}
)


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
        ownership_source: Callable[
            [object], str
        ] = manual_control_operator_exclusion_source,
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
        )

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

    def _loaded_state_policy(self, now: datetime):
        """Keep prior-date owned orders on the policy that created them."""

        if (
            not self._state.get("legs")
            or self._state.get("trade_date") == now.date().isoformat()
        ):
            return self.profile.policy
        try:
            source_date = date.fromisoformat(str(self._state.get("trade_date") or ""))
            prior = get_profile(self.profile.profile_id, target_date=source_date).policy
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
            )
        except (TypeError, ValueError):
            return None

    def _bind_policy(self, policy) -> None:
        self.policy = policy
        self.leg_ids = tuple(policy.entry_leg_ids)

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        current_policy = self.profile.policy
        custody_policy = self._loaded_state_policy(now)
        if custody_policy is None:
            return self._block(now, "prior_state_policy_snapshot_invalid")
        self._bind_policy(custody_policy)
        try:
            self._roll_prior_terminal_state_before_current_policy_validation(now)
            if self._state.get("trade_date") == now.date().isoformat():
                self._bind_policy(current_policy)
            return super().run_once(now)
        finally:
            self._bind_policy(current_policy)
