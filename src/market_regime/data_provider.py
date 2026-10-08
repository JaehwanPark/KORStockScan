import pandas as pd
import yfinance as yf


class CNNFearGreedProvider:
    """Package-compatible CNN projection with a consumer-owned memory cache.

    Importing fear_and_greed installs a global SQLite requests patch. The
    isolated adapter uses the same endpoint and score/rating/timestamp fields
    without importing that package or modifying any global session factory.
    """
    URL = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata'

    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self._session = None

    def get(self):
        from datetime import datetime
        from types import SimpleNamespace
        from requests_cache import CachedSession
        with self._lock:
            if self._session is None:
                self._session = CachedSession(backend='memory', expire_after=60)
            response = self._session.get(self.URL, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'})
            response.raise_for_status()
            values = response.json()['fear_and_greed']
            return SimpleNamespace(value=values['score'], description=values['rating'],
                                   last_update=datetime.fromisoformat(values['timestamp']))


class YahooMarketDataProvider:
    VIX_TICKER = "^VIX"
    WTI_TICKER = "CL=F"
    BRENT_TICKER = "BZ=F"

    @staticmethod
    def _normalize_column_name(col) -> str:
        if isinstance(col, tuple):
            parts = [
                str(part).strip()
                for part in col
                if str(part).strip() and str(part).strip().lower() != "nan"
            ]
            if not parts:
                return ""
            for part in parts:
                lowered = part.lower()
                if lowered in {
                    "date",
                    "datetime",
                    "open",
                    "high",
                    "low",
                    "close",
                    "adj close",
                    "volume",
                }:
                    return lowered
            return parts[0].lower()
        return str(col).strip().lower()

    def fetch_history(
        self, ticker: str, period: str = "3mo", interval: str = "1d"
    ) -> pd.DataFrame:
        df = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [self._normalize_column_name(col) for col in df.columns]
        else:
            df = df.rename(
                columns={col: self._normalize_column_name(col) for col in df.columns}
            )

        if "date" not in df.columns and "datetime" in df.columns:
            df["date"] = df["datetime"]

        # 필요한 컬럼만 유지
        keep_cols = [
            c
            for c in ["date", "open", "high", "low", "close", "adj close", "volume"]
            if c in df.columns
        ]
        df = df[keep_cols].copy()

        if "close" in df.columns:
            df["close"] = pd.to_numeric(df["close"], errors="coerce")

        return df.dropna(subset=["close"]) if "close" in df.columns else pd.DataFrame()

    def fetch_vix_daily(self) -> pd.DataFrame:
        return self.fetch_history(self.VIX_TICKER, period="3mo", interval="1d")

    def fetch_wti_daily(self) -> pd.DataFrame:
        return self.fetch_history(self.WTI_TICKER, period="3mo", interval="1d")

    def fetch_brent_daily(self) -> pd.DataFrame:
        return self.fetch_history(self.BRENT_TICKER, period="3mo", interval="1d")
