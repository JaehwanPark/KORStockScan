import json
import threading
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

import numpy as np

try:
    import fear_and_greed
except ImportError:  # optional dependency
    fear_and_greed = None

from src.utils.constants import DATA_DIR, TRADING_RULES
from .data_provider import YahooMarketDataProvider
from .rules import evaluate_market_regime
from .schemas import MarketRegimeSnapshot


class MarketRegimeService:
    def __init__(self, refresh_minutes: int = 15):
        self.provider = YahooMarketDataProvider()
        self.refresh_minutes = refresh_minutes
        self._lock = threading.RLock()
        self._last_refresh_at = None
        self._tz = ZoneInfo("Asia/Seoul")
        self._cache_path = DATA_DIR / "cache" / "market_regime_snapshot.json"
        self._session_cache_date = None
        self._snapshot = self._load_snapshot_cache() or MarketRegimeSnapshot(
            timestamp=self._now(),
            reasons=["시장환경 초기 미평가 상태"]
        )
        if self._snapshot.debug.get("cached_session_date"):
            self._session_cache_date = str(self._snapshot.debug.get("cached_session_date"))

    def _now(self) -> datetime:
        return datetime.now(self._tz)

    def _market_open_time(self) -> dt_time:
        raw = getattr(TRADING_RULES, "MARKET_OPEN_TIME", "09:00:00")
        return datetime.strptime(str(raw), "%H:%M:%S").time()

    def _session_cache_ready_time(self) -> dt_time:
        base_dt = datetime.combine(self._now().date(), self._market_open_time())
        return (base_dt - timedelta(minutes=30)).time()

    def _resolve_session_date(self, now: datetime | None = None) -> str:
        current = now or self._now()
        if current.time() >= self._session_cache_ready_time():
            return current.date().isoformat()
        return (current.date() - timedelta(days=1)).isoformat()

    def _snapshot_to_payload(self, snapshot: MarketRegimeSnapshot, session_date: str) -> dict:
        payload = self._json_safe_value(dict(snapshot.__dict__))
        payload["timestamp"] = snapshot.timestamp.isoformat()
        payload["cached_session_date"] = session_date
        payload["cached_at"] = self._now().isoformat()
        return payload

    def _json_safe_value(self, value):
        if isinstance(value, dict):
            return {str(key): self._json_safe_value(inner) for key, inner in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe_value(item) for item in value]
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.ndarray):
            return [self._json_safe_value(item) for item in value.tolist()]
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def _snapshot_from_payload(self, payload: dict) -> MarketRegimeSnapshot | None:
        try:
            cleaned = dict(payload)
            ts_raw = cleaned.get("timestamp")
            cleaned["timestamp"] = datetime.fromisoformat(ts_raw) if ts_raw else self._now()
            cached_session_date = str(cleaned.pop("cached_session_date", "") or "")
            cleaned.pop("cached_at", None)
            snapshot = MarketRegimeSnapshot(**cleaned)
            if cached_session_date:
                snapshot.debug["cached_session_date"] = cached_session_date
            return snapshot
        except Exception:
            return None

    def _load_snapshot_cache(self) -> MarketRegimeSnapshot | None:
        try:
            if not self._cache_path.exists():
                return None
            with open(self._cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return self._snapshot_from_payload(payload)
        except Exception:
            return None

    def _persist_snapshot_cache(self, snapshot: MarketRegimeSnapshot, session_date: str) -> None:
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = self._snapshot_to_payload(snapshot, session_date)
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            snapshot.debug["cached_session_date"] = session_date
            self._session_cache_date = session_date
        except Exception as e:
            snapshot.reasons.append(f"cache 저장 실패: {e}")

    def _clone_snapshot_with_reason(self, snapshot: MarketRegimeSnapshot, reason: str) -> MarketRegimeSnapshot:
        cloned = self._snapshot_from_payload(self._snapshot_to_payload(snapshot, snapshot.debug.get("cached_session_date", ""))) or snapshot
        cloned.reasons = list(cloned.reasons)
        if reason not in cloned.reasons:
            cloned.reasons.append(reason)
        return cloned

    def _cached_session_snapshot(self, now: datetime | None = None) -> MarketRegimeSnapshot | None:
        current = now or self._now()
        target_session_date = self._resolve_session_date(current)
        loaded = self._load_snapshot_cache()
        if loaded and str(loaded.debug.get("cached_session_date", "")) == target_session_date:
            return loaded
        if str(self._snapshot.debug.get("cached_session_date", "")) == target_session_date:
            return self._snapshot
        return loaded

    def _fetch_fear_and_greed_data(self) -> dict:
        """
        fear-and-greed 패키지를 사용해 공포탐욕지수 조회.
        previous_value는 직전 snapshot 값을 사용한다.
        실패 시 cached 값 유지.
        """
        if fear_and_greed is None:
            return {
                "value": float(getattr(self._snapshot, "fng_value", 0.0) or 0.0),
                "previous_value": float(getattr(self._snapshot, "fng_prev", 0.0) or 0.0),
                "description": str(getattr(self._snapshot, "fng_description", "") or ""),
                "last_update": None,
                "source": "module_missing_fallback",
            }

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
            now = self._now()
            session_date = self._resolve_session_date(now)

            if not force and self._session_cache_date == session_date and now.time() >= self._session_cache_ready_time():
                return self._snapshot

            if not force and self._last_refresh_at is not None:
                age = now - self._last_refresh_at
                if age < timedelta(minutes=self.refresh_minutes):
                    return self._snapshot

            try:
                vix_df = self.provider.fetch_vix_daily()
                oil_df = self.provider.fetch_wti_daily()
                fng_data = self._fetch_fear_and_greed_data()

                missing_sources = []
                if vix_df is None or vix_df.empty:
                    missing_sources.append("VIX")
                if oil_df is None or oil_df.empty:
                    missing_sources.append("WTI")
                if missing_sources:
                    raise ValueError(f"market data incomplete: {', '.join(missing_sources)}")

                new_snapshot = evaluate_market_regime(vix_df, oil_df, fng_data=fng_data)
                self._snapshot = new_snapshot
                self._last_refresh_at = now

                if now.time() >= self._session_cache_ready_time():
                    self._persist_snapshot_cache(self._snapshot, session_date)

            except Exception as e:
                fallback = self._cached_session_snapshot(now)
                if fallback is not None:
                    self._snapshot = self._clone_snapshot_with_reason(fallback, f"refresh 실패 폴백 사용: {e}")
                else:
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
