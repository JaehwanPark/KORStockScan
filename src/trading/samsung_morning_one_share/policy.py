"""Fixed, auditable policy for the Samsung morning one-share machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks


@dataclass(frozen=True)
class EntryWindow:
    route: str
    open_time: time
    deadline: time
    drawdown_pct: float


@dataclass(frozen=True)
class MorningOneSharePolicy:
    symbol: str = "005930"
    quantity: int = 1
    nxt: EntryWindow = EntryWindow("NXT", time(8, 0), time(8, 10), 3.0)
    sor: EntryWindow = EntryWindow("SOR", time(9, 0), time(9, 30), 0.75)
    target_ticks: int = 2

    def __post_init__(self) -> None:
        if self.symbol != "005930" or self.quantity != 1:
            raise ValueError("policy_is_hard_limited_to_005930_one_share")
        if self.target_ticks <= 0:
            raise ValueError("invalid_exit_policy")
        if self.nxt.route != "NXT" or self.sor.route != "SOR":
            raise ValueError("invalid_route_priority")

    @staticmethod
    def entry_price(open_price: int, drawdown_pct: float) -> int:
        if open_price <= 0 or drawdown_pct <= 0:
            raise ValueError("invalid_open_or_drawdown")
        return clamp_price_to_tick(open_price * (1.0 - drawdown_pct / 100.0))

    def target_price(self, fill_price: int) -> int:
        if fill_price <= 0:
            raise ValueError("invalid_fill_price")
        return move_price_by_ticks(fill_price, self.target_ticks)


DEFAULT_POLICY = MorningOneSharePolicy()
