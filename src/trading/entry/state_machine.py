from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class StateTransition:
    """One symbol-level state transition record."""

    symbol: str
    from_state: str | None
    to_state: str
    reason: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


class EntryStateMachine:
    """Maintains current entry state and transition history per symbol."""

    ALLOWED_TRANSITIONS = {
        None: {"SIGNAL_DETECTED"},
        "SIGNAL_DETECTED": {"POLICY_CHECKING"},
        "POLICY_CHECKING": {
            "REJECTED_TIMEOUT",
            "REJECTED_SLIPPAGE",
            "REJECTED_DANGER",
            "REJECTED_MARKET_CONDITION",
            "NORMAL_ORDER_SUBMITTING",
            "FALLBACK_ORDER_SUBMITTING",
        },
        "NORMAL_ORDER_SUBMITTING": {
            "ORDER_FILLED",
            "ORDER_PARTIAL_FILLED",
            "ORDER_CANCELLED",
            "ENTRY_EXPIRED",
        },
        "FALLBACK_ORDER_SUBMITTING": {
            "SCOUT_ORDER_SUBMITTED",
            "MAIN_ORDER_SUBMITTED",
            "ORDER_FILLED",
            "ORDER_PARTIAL_FILLED",
            "ORDER_CANCELLED",
        },
        "SCOUT_ORDER_SUBMITTED": {
            "MAIN_ORDER_SUBMITTED",
            "ORDER_FILLED",
            "ORDER_PARTIAL_FILLED",
            "ENTRY_EXPIRED",
        },
        "MAIN_ORDER_SUBMITTED": {
            "ORDER_FILLED",
            "ORDER_PARTIAL_FILLED",
            "ORDER_CANCELLED",
            "ENTRY_EXPIRED",
        },
        "ORDER_PARTIAL_FILLED": {"ORDER_FILLED", "ORDER_CANCELLED", "ENTRY_EXPIRED"},
    }

    def __init__(self) -> None:
        self.current_state: dict[str, str] = {}
        self.history: dict[str, list[StateTransition]] = defaultdict(list)

    def transition(self, symbol: str, to_state: str, *, reason: str) -> None:
        from_state = self.current_state.get(symbol)
        allowed = self.ALLOWED_TRANSITIONS.get(from_state)
        if allowed is not None and to_state not in allowed:
            raise ValueError(
                f"invalid transition for {symbol}: {from_state} -> {to_state}"
            )
        self.current_state[symbol] = to_state
        self.history[symbol].append(
            StateTransition(symbol, from_state, to_state, reason)
        )
