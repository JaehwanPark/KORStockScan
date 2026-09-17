from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class QuoteHealth:
    """Realtime quote health summary derived from cached websocket data."""

    ws_age_ms: int
    ws_jitter_ms: int
    quote_stale: bool
    spread_ratio: float
    best_ask: int
    best_bid: int
    last_price: int
    quote_received_epoch: float | None = None
    quote_receive_age_ms: float | None = None
    source_scope: tuple | None = None
    source_identity: tuple | None = None
    # Raw input frame facts; an adopted observer quote has its own receipt.
    market_data_health: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
