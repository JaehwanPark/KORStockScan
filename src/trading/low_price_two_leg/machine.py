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
