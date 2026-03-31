import threading
from datetime import datetime, timedelta

import fear_and_greed

from .data_provider import YahooMarketDataProvider
from .rules import evaluate_market_regime
from .schemas import MarketRegimeSnapshot


class MarketRegimeService:
    def __init__(self, refresh_minutes: int = 15):
        self.provider = YahooMarketDataProvider()
        self.refresh_minutes = refresh_minutes
        self._lock = threading.RLock()
        self._last_refresh_at = None
        self._snapshot = MarketRegimeSnapshot(
            timestamp=datetime.now(),
            reasons=["시장환경 초기 미평가 상태"]
        )

    def _fetch_fear_and_greed_data(self) -> dict:
        """
        fear-and-greed 패키지를 사용해 공포탐욕지수 조회.
        previous_value는 직전 snapshot 값을 사용한다.
        실패 시 cached 값 유지.
        """
        try:
            fg = fear_and_greed.get()

            curr_value = float(getattr(fg, "value", 0.0) or 0.0)
            prev_value = float(getattr(self._snapshot, "fng_value", 0.0) or 0.0)
            desc = str(getattr(fg, "description", "") or "")
            last_update = getattr(fg, "last_update", None)

            return {
                "value": curr_value,
                "previous_value": prev_value,
                "description": desc,
                "last_update": last_update,
                "source": "fear_and_greed_package",
            }

        except Exception:
            return {
                "value": float(getattr(self._snapshot, "fng_value", 0.0) or 0.0),
                "previous_value": float(getattr(self._snapshot, "fng_prev", 0.0) or 0.0),
                "description": str(getattr(self._snapshot, "fng_description", "") or ""),
                "last_update": None,
                "source": "cached_fallback",
            }

    def refresh_if_needed(self, force: bool = False) -> MarketRegimeSnapshot:
        with self._lock:
            if not force and self._last_refresh_at is not None:
                age = datetime.now() - self._last_refresh_at
                if age < timedelta(minutes=self.refresh_minutes):
                    return self._snapshot

            try:
                vix_df = self.provider.fetch_vix_daily()
                oil_df = self.provider.fetch_wti_daily()
                fng_data = self._fetch_fear_and_greed_data()

                new_snapshot = evaluate_market_regime(vix_df, oil_df, fng_data=fng_data)
                self._snapshot = new_snapshot
                self._last_refresh_at = datetime.now()

            except Exception as e:
                self._snapshot.reasons.append(f"refresh 실패: {e}")

            return self._snapshot

    def get_snapshot(self) -> MarketRegimeSnapshot:
        with self._lock:
            return self._snapshot

    def allow_swing_entry(self) -> bool:
        snapshot = self.refresh_if_needed()
        return snapshot.allow_swing_entry

    def get_volatility_mode(self) -> str:
        snapshot = self.refresh_if_needed()
        return snapshot.volatility_mode

    def debug_summary(self) -> str:
        snapshot = self.refresh_if_needed()
        return (
            f"[MarketRegime] "
            f"risk={snapshot.risk_state}, "
            f"vix={snapshot.vix_close:.2f}, "
            f"oil_rsi={snapshot.wti_rsi:.2f}, "
            f"oil_reversal={snapshot.oil_reversal}, "
            f"fng={snapshot.fng_value:.2f}, "
            f"fng_desc={snapshot.fng_description}, "
            f"fng_recovery={snapshot.fng_recovery}, "
            f"swing_score={snapshot.swing_score}, "
            f"allow_swing={snapshot.allow_swing_entry}"
        )