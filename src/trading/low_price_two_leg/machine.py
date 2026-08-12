"""Profile-bound persistent state machine for lower-price live episodes."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.low_price_two_leg.profiles import MachineProfile
from src.trading.order.regular_two_leg_machine import KST as KST
from src.trading.order.regular_two_leg_machine import SamsungRegularTwoLegMachine
from src.utils.constants import DATA_DIR

DEFAULT_STATE_DIR = DATA_DIR / "runtime" / "low_price_two_leg"


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
