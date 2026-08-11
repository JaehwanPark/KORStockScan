"""Persistent state machine for the independent Samsung midday two-leg episode."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.order.regular_two_leg_machine import KST as KST
from src.trading.order.regular_two_leg_machine import SamsungRegularTwoLegMachine
from src.trading.samsung_midday_one_share.policy import (
    DEFAULT_POLICY,
    MiddayOneSharePolicy,
)
from src.utils.constants import DATA_DIR

DEFAULT_STATE_PATH = DATA_DIR / "runtime" / "samsung_midday_one_share_state.json"


class SamsungMiddayOneShareMachine(SamsungRegularTwoLegMachine):
    """Compatibility class name; runtime authority is two one-share legs."""

    def __init__(
        self,
        *,
        gateway,
        state_path: Path = DEFAULT_STATE_PATH,
        policy: MiddayOneSharePolicy = DEFAULT_POLICY,
        live_enabled: bool = False,
        ownership_source: Callable[
            [object], str
        ] = manual_control_operator_exclusion_source,
    ) -> None:
        super().__init__(
            gateway=gateway,
            state_path=state_path,
            policy=policy,
            strategy_name="midday",
            schema="samsung_midday_two_leg_state_v2",
            legacy_schema="samsung_midday_one_share_state_v1",
            live_enabled=live_enabled,
            ownership_source=ownership_source,
        )
