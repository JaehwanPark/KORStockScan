from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from src.trading.market.quote_health import QuoteHealth


@dataclass(slots=True)
class _SymbolQuote:
    last_price: int = 0
    best_ask: int = 0
    best_bid: int = 0
    last_packet_ts: float = 0.0
    packet_intervals_ms: deque[int] = field(default_factory=lambda: deque(maxlen=20))


class MarketDataCache:
    """Stores latest websocket-derived quote state without last-moment refetches."""

    def __init__(self, *, stale_after_ms: int = 1_000) -> None:
        self._quotes: dict[str, _SymbolQuote] = {}
        self._stale_after_ms = stale_after_ms
        self._jitter_reset_gap_ms = max(1_500, int(stale_after_ms) * 3)

    def update(
        self,
        symbol: str,
        *,
        last_price: int | None = None,
        best_ask: int | None = None,
        best_bid: int | None = None,
        received_at: float | None = None,
    ) -> None:
        now = received_at if received_at is not None else time.time()
        quote = self._quotes.setdefault(symbol, _SymbolQuote())
        if quote.last_packet_ts > 0:
            interval_ms = int(max(0.0, (now - quote.last_packet_ts) * 1000))
            if interval_ms <= 0:
                interval_ms = 0
            if interval_ms >= self._jitter_reset_gap_ms:
                quote.packet_intervals_ms.clear()
            elif interval_ms > 0:
                quote.packet_intervals_ms.append(interval_ms)
        if now > quote.last_packet_ts:
            quote.last_packet_ts = now
        if last_price is not None:
            quote.last_price = int(last_price)
        if best_ask is not None:
            quote.best_ask = int(best_ask)
        if best_bid is not None:
            quote.best_bid = int(best_bid)

    def get_last_price(self, symbol: str) -> int:
        return self._quotes.get(symbol, _SymbolQuote()).last_price

    def get_best_ask(self, symbol: str) -> int:
        return self._quotes.get(symbol, _SymbolQuote()).best_ask

    def get_best_bid(self, symbol: str) -> int:
        return self._quotes.get(symbol, _SymbolQuote()).best_bid

    def get_quote_health(self, symbol: str) -> QuoteHealth:
        quote = self._quotes.get(symbol, _SymbolQuote())
        now = time.time()
        ws_age_ms = int(max(0.0, (now - quote.last_packet_ts) * 1000)) if quote.last_packet_ts else 10**9
        intervals = list(quote.packet_intervals_ms)
        ws_jitter_ms = (max(intervals) - min(intervals)) if len(intervals) >= 2 else 0
        spread_ratio = 0.0
        if quote.best_ask > 0 and quote.best_bid > 0 and quote.last_price > 0:
            spread_ratio = max(0.0, (quote.best_ask - quote.best_bid) / quote.last_price)
        return QuoteHealth(
            ws_age_ms=ws_age_ms,
            ws_jitter_ms=ws_jitter_ms,
            quote_stale=ws_age_ms > self._stale_after_ms,
            spread_ratio=spread_ratio,
            best_ask=quote.best_ask,
            best_bid=quote.best_bid,
            last_price=quote.last_price,
        )
