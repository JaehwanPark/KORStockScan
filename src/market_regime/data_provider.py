import pandas as pd
import yfinance as yf


class YahooMarketDataProvider:
    VIX_TICKER = "^VIX"
    WTI_TICKER = "CL=F"
    BRENT_TICKER = "BZ=F"

    def fetch_history(self, ticker: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
        df = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.reset_index()

        rename_map = {}
        for col in df.columns:
            col_str = str(col).lower()
            rename_map[col] = col_str
        df = df.rename(columns=rename_map)

        if "date" not in df.columns and "datetime" in df.columns:
            df["date"] = df["datetime"]

        # 필요한 컬럼만 유지
        keep_cols = [c for c in ["date", "open", "high", "low", "close", "adj close", "volume"] if c in df.columns]
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