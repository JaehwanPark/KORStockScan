from __future__ import annotations

from datetime import UTC, datetime

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_types import (
    EntryDecision,
    LatencyState,
    LatencyStatus,
    PolicyResult,
    SignalSnapshot,
)
from src.trading.order.tick_utils import move_price_by_ticks


class EntryPolicy:
    """Hard policy filter for latency-aware entry acceptance."""

    def __init__(self, config: EntryConfig) -> None:
        self.config = config

    def evaluate(
        self,
        *,
        snapshot: SignalSnapshot,
        latency_status: LatencyStatus,
        latest_price: int,
        now: datetime | None = None,
    ) -> PolicyResult:
        current_time = now or datetime.now(UTC)
        elapsed_ms = int(
            max(0.0, (current_time - snapshot.signal_time).total_seconds() * 1000)
        )
        if elapsed_ms > self.config.entry_deadline_ms:
            return PolicyResult(
                decision=EntryDecision.REJECT_TIMEOUT,
                reason="signal_deadline_exceeded",
                fallback_allowed=False,
                computed_allowed_slippage=0,
                computed_deadline_ms=self.config.entry_deadline_ms,
                latest_price=int(latest_price),
            )

        if latency_status.state == LatencyState.DANGER:
            return PolicyResult(
                decision=EntryDecision.REJECT_DANGER,
                reason="latency_state_danger",
                fallback_allowed=False,
                computed_allowed_slippage=0,
                computed_deadline_ms=self.config.entry_deadline_ms,
                latest_price=int(latest_price),
            )

        if latency_status.state == LatencyState.SAFE:
            allowed = self._allowed_slippage(
                signal_price=snapshot.signal_price,
                latest_price=latest_price,
                tick_limit=self.config.normal_allowed_slippage_ticks,
                pct_limit=self.config.normal_allowed_slippage_pct,
            )
            if not self._slippage_ok(
                snapshot.signal_price, latest_price, allowed, snapshot.side
            ):
                return PolicyResult(
                    decision=EntryDecision.REJECT_SLIPPAGE,
                    reason="safe_slippage_exceeded",
                    fallback_allowed=False,
                    computed_allowed_slippage=allowed,
                    computed_deadline_ms=self.config.entry_deadline_ms,
                    latest_price=int(latest_price),
                )
            return PolicyResult(
                decision=EntryDecision.ALLOW_NORMAL,
                reason="safe_normal_entry_allowed",
                fallback_allowed=False,
                computed_allowed_slippage=allowed,
                computed_deadline_ms=self.config.entry_deadline_ms,
                latest_price=int(latest_price),
            )

        allowed = self._allowed_slippage(
            signal_price=snapshot.signal_price,
            latest_price=latest_price,
            tick_limit=self.config.fallback_allowed_slippage_ticks,
            pct_limit=self.config.fallback_allowed_slippage_pct,
        )
        if not self._slippage_ok(
            snapshot.signal_price, latest_price, allowed, snapshot.side
        ):
            return PolicyResult(
                decision=EntryDecision.REJECT_SLIPPAGE,
                reason="caution_slippage_exceeded",
                fallback_allowed=False,
                computed_allowed_slippage=allowed,
                computed_deadline_ms=self.config.entry_deadline_ms,
                latest_price=int(latest_price),
            )
        return PolicyResult(
            decision=EntryDecision.ALLOW_NORMAL,
            reason="caution_normal_entry_allowed",
            fallback_allowed=False,
            computed_allowed_slippage=allowed,
            computed_deadline_ms=self.config.entry_deadline_ms,
            latest_price=int(latest_price),
        )

    def _allowed_slippage(
        self,
        *,
        signal_price: int,
        latest_price: int,
        tick_limit: int,
        pct_limit: float,
    ) -> int:
        tick_based = abs(move_price_by_ticks(signal_price, tick_limit) - signal_price)
        pct_based = int(max(signal_price, latest_price) * pct_limit)
        return max(1, tick_based, pct_based)

    @staticmethod
    def _slippage_ok(
        signal_price: int, latest_price: int, allowed: int, side: str
    ) -> bool:
        normalized_side = str(side).upper()
        if normalized_side == "SELL":
            return latest_price >= (signal_price - allowed)
        return latest_price <= (signal_price + allowed)
