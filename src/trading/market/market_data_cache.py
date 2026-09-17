from __future__ import annotations

import time
import math
from collections import deque
from dataclasses import dataclass, field

from src.trading.market.quote_health import QuoteHealth


@dataclass(slots=True)
class QuietTapeState:
    """Bounded receive-side state. Getters cannot manufacture quiet episodes.

    Scope/epoch is owned by the enclosing exact-route WS record. A missing
    cumulative-volume advance or broken quote continuity is not no-trade proof.
    """

    last_quote: float = 0.0
    last_trade: float = 0.0
    last_volume: int = 0
    last_sequence: int = 0
    closed_episodes: int = 0
    active_since: float = 0.0
    last_provider_event: float = 0.0

    def observe(
        self,
        *,
        kind: str,
        now: float,
        sequence: int,
        volume: int = 0,
        provider_event_at: float | None = None,
    ) -> None:
        if kind == "0D":
            if now <= self.last_quote:
                return
            if (
                self.last_quote
                and now - self.last_quote > 3.0
                or not self.last_quote
                and self.last_trade
                and now - self.last_trade > 3.0
            ):
                self.last_trade = 0.0
                self.closed_episodes = 0
                self.active_since = 0.0
            self.last_quote = now
            return
        if kind != "0B" or sequence <= self.last_sequence or volume <= self.last_volume:
            return
        event_at = now if provider_event_at is None else provider_event_at
        if not 0 <= now - event_at <= 10.0 or event_at < self.last_provider_event:
            self.last_trade = 0.0
            self.closed_episodes = 0
            self.active_since = 0.0
            return
        self.last_provider_event = event_at
        self.last_sequence = sequence
        self.last_volume = volume
        if now <= self.last_trade:
            return
        if not self.last_quote or not 0 <= now - self.last_quote <= 3.0:
            self.closed_episodes = 0
            self.active_since = 0.0
        elif self.last_trade and now - self.last_trade >= 10.0:
            self.closed_episodes = min(3, self.closed_episodes + 1)
            self.active_since = now
        elif not self.active_since:
            self.active_since = now
        elif now - self.active_since >= 10.0:
            self.closed_episodes = 0
        self.last_trade = now

    def facts(self, *, now: float) -> dict:
        proven = bool(
            self.last_quote
            and self.last_trade
            and 0 <= now - self.last_quote <= 3.0
            and now >= self.last_trade
        )
        quiet = proven and now - self.last_trade >= 10.0
        count = min(3, self.closed_episodes + int(quiet)) if proven else None
        return {
            "observation_continuity_proven": proven,
            "quiet_episode_count": count,
            "trade_activity_state": (
                "OBSERVATION_UNPROVEN"
                if not proven
                else (
                    "REPEATED_QUIET_TAPE_OBSERVED"
                    if quiet and count >= 3
                    else "QUIET_TAPE_OBSERVED" if quiet else "RECENT_TRADE"
                )
            ),
        }


@dataclass(slots=True)
class _SymbolQuote:
    last_price: int = 0
    best_ask: int = 0
    best_bid: int = 0
    last_packet_ts: float = 0.0
    receipt_conflict: bool = False
    source_identity: tuple | None = None
    packet_intervals_ms: deque[int] = field(default_factory=lambda: deque(maxlen=20))


class MarketDataCache:
    """Stores latest websocket-derived quote state without last-moment refetches."""

    def __init__(self, *, stale_after_ms: int = 1_000) -> None:
        self._quotes: dict[str | tuple, _SymbolQuote] = {}
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
        scope: tuple | None = None,
        source_identity: tuple | None = None,
    ) -> None:
        now = received_at if received_at is not None else time.time()
        if isinstance(now, bool):
            return
        try:
            now = float(now)
        except (TypeError, ValueError, OverflowError):
            return
        if not math.isfinite(now) or now <= 0 or now > time.time():
            return
        if source_identity is not None and (
            not isinstance(source_identity, tuple)
            or len(source_identity) != 2
            or source_identity[0] not in ("0B", "0D")
            or type(source_identity[1]) is not int
            or source_identity[1] <= 0
        ):
            return
        key = symbol if scope is None else (symbol, *scope)
        quote = self._quotes.setdefault(key, _SymbolQuote())
        if (source_identity is not None and quote.source_identity is not None
                and source_identity[0] == quote.source_identity[0]
                and source_identity[1] <= quote.source_identity[1]
                and now != quote.last_packet_ts):
            return
        advanced_identity = bool(
            source_identity is not None and quote.source_identity is not None
            and source_identity != quote.source_identity
            and (source_identity[0] != quote.source_identity[0]
                 or source_identity[1] > quote.source_identity[1])
        )
        if now < quote.last_packet_ts or (now == quote.last_packet_ts and not advanced_identity):
            if now == quote.last_packet_ts and (
                (best_ask is not None and int(best_ask) != quote.best_ask)
                or (best_bid is not None and int(best_bid) != quote.best_bid)
            ):
                quote.receipt_conflict = True
            return
        quote.receipt_conflict = False
        quote.source_identity = source_identity
        while len(self._quotes) > 4096:
            self._quotes.pop(next(iter(self._quotes)))
        if quote.last_packet_ts > 0:
            interval_ms = int((now - quote.last_packet_ts) * 1000)
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

    def get_last_price(self, symbol: str, *, scope: tuple | None = None) -> int:
        key = symbol if scope is None else (symbol, *scope)
        return self._quotes.get(key, _SymbolQuote()).last_price

    def get_best_ask(self, symbol: str, *, scope: tuple | None = None) -> int:
        key = symbol if scope is None else (symbol, *scope)
        return self._quotes.get(key, _SymbolQuote()).best_ask

    def get_best_bid(self, symbol: str, *, scope: tuple | None = None) -> int:
        key = symbol if scope is None else (symbol, *scope)
        return self._quotes.get(key, _SymbolQuote()).best_bid

    def get_quote_health(self, symbol: str, *, scope: tuple | None = None) -> QuoteHealth:
        key = symbol if scope is None else (symbol, *scope)
        quote = self._quotes.get(key, _SymbolQuote())
        now = time.time()
        ws_age_ms = (
            int(max(0.0, (now - quote.last_packet_ts) * 1000))
            if quote.last_packet_ts
            else 10**9
        )
        intervals = list(quote.packet_intervals_ms)
        ws_jitter_ms = (max(intervals) - min(intervals)) if len(intervals) >= 2 else 0
        spread_ratio = 0.0
        if quote.best_ask > 0 and quote.best_bid > 0 and quote.last_price > 0:
            spread_ratio = max(
                0.0, (quote.best_ask - quote.best_bid) / quote.last_price
            )
        return QuoteHealth(
            ws_age_ms=ws_age_ms,
            ws_jitter_ms=ws_jitter_ms,
            quote_stale=(quote.receipt_conflict or quote.last_packet_ts > now
                         or not 0 <= ws_age_ms <= self._stale_after_ms),
            spread_ratio=spread_ratio,
            best_ask=quote.best_ask,
            best_bid=quote.best_bid,
            last_price=quote.last_price,
        )
