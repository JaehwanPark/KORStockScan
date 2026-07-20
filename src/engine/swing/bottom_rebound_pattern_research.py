"""Research-only bottom rebound pattern miner.

This module reads daily quote data, finds broad historical bottom-zone signal
dates, simulates next-day anticipatory entries, and writes report artifacts.
It never writes to the database and has no runtime, order, provider, threshold,
or bot authority.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from src.utils.constants import DATA_DIR, POSTGRES_URL

REPORT_TYPE = "bottom_rebound_pattern_research"
SCHEMA_VERSION = "bottom_rebound_pattern_research_v1"
DECISION_AUTHORITY = "research_only"
REPORT_DIR = Path(DATA_DIR) / "report" / REPORT_TYPE
ENTRY_POLICIES = (
    "next_open_entry",
    "signal_close_retest_entry",
    "atr_pullback_entry",
    "open_guarded_retest_entry",
    "close_zone_limit_entry",
)
HORIZONS = (1, 3, 5, 10, 20)
FORBIDDEN_USES = [
    "runtime_env_apply",
    "broker_order_submit",
    "provider_route_change",
    "bot_restart_trigger",
    "threshold_mutation",
    "real_order_conversion_evidence",
    "standalone_buy_or_exit_decision",
]


@dataclass(frozen=True)
class ResearchConfig:
    as_of: str | None = None
    history_start: str | None = None
    min_price: float = 1000.0
    min_median_value_20d_krw: float = 500_000_000.0
    min_median_volume_20d: float = 50_000.0
    sample_floor: int = 30
    primary_horizon_days: int = 10
    cooldown_trading_days: int = 10
    signal_close_retest_discount_pct: float = 0.5
    atr_pullback_multiplier: float = 0.5
    atr_pullback_min_pct: float = 0.8
    atr_pullback_max_pct: float = 3.0
    backtest_entry_policy: str = "atr_pullback_entry"
    backtest_horizon_days: int = 10
    backtest_max_positions: int = 5
    backtest_trade_cost_pct: float = 0.23
    open_guarded_max_gap_up_pct: float = 1.0
    open_guarded_max_gap_down_pct: float = -4.0
    open_guarded_retest_discount_pct: float = 0.5
    close_zone_limit_discount_pct: float = 0.3
    enable_kiwoom_enrichment: bool = False
    kiwoom_enrichment_max_codes: int = 100
    kiwoom_enrichment_write_cache: bool = False


@dataclass(frozen=True)
class EntryResult:
    status: str
    entry_date: str | None = None
    entry_price: float | None = None
    entry_reason: str = ""
    limit_price: float | None = None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _date_text(value: str | date | datetime | pd.Timestamp | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


def _pct(value: float, base: float) -> float:
    if base <= 0:
        return 0.0
    return ((value - base) / base) * 100.0


def _normal_stock_mask(names: pd.Series) -> pd.Series:
    pattern = (
        r"(?:우|우B|우C|스팩|SPAC|ETF|ETN|리츠|인버스|레버리지|선물|합성|채권|"
        r"액티브|KODEX|TIGER|KBSTAR|SOL|ACE|HANARO|ARIRANG|KOSEF|TIMEFOLIO)"
    )
    return ~names.fillna("").astype(str).str.contains(pattern, regex=True)


def _price_at_pct(base: float, pct: float) -> float:
    return base * (1.0 + pct / 100.0)


def _as_report_number(value: Any, digits: int = 6) -> float | None:
    numeric = _safe_float(value, float("nan"))
    if not math.isfinite(numeric):
        return None
    return round(numeric, digits)


def report_paths(target_date: str, output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    base = output_dir / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_quote_frame(
    db_url: str,
    *,
    as_of: str | None = None,
    history_start: str | None = None,
) -> tuple[pd.DataFrame, str, str | None]:
    engine = create_engine(
        db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5}
    )
    with engine.connect() as conn:
        bounds = (
            conn.execute(
                text(
                    "SELECT min(quote_date) AS min_date, max(quote_date) AS max_date FROM daily_stock_quotes"
                )
            )
            .mappings()
            .one()
        )
        if bounds["max_date"] is None:
            return pd.DataFrame(), date.today().isoformat(), history_start
        effective_as_of = (
            min(pd.Timestamp(as_of).date(), bounds["max_date"])
            if as_of
            else bounds["max_date"]
        )
        effective_start = (
            max(pd.Timestamp(history_start).date(), bounds["min_date"])
            if history_start
            else bounds["min_date"]
        )
        frame = pd.read_sql(
            text("""
                SELECT quote_date, stock_code, stock_name, open_price, high_price, low_price,
                       close_price, volume, ma5, ma20, ma60, ma120, rsi, bbl, bbm, bbu, bbb,
                       bbp, vwap, atr, foreign_net, inst_net, margin_rate, marcap
                FROM daily_stock_quotes
                WHERE quote_date >= :start_date
                  AND quote_date <= :as_of
                  AND stock_code ~ '^[0-9]{6}$'
                  AND open_price > 0
                  AND high_price > 0
                  AND low_price > 0
                  AND close_price > 0
                """),
            conn,
            params={"start_date": effective_start, "as_of": effective_as_of},
        )
    return frame, effective_as_of.isoformat(), effective_start.isoformat()


def prepare_feature_frame(
    raw: pd.DataFrame, config: ResearchConfig | None = None
) -> pd.DataFrame:
    """Create signal-day features plus forward columns reserved for labeling.

    Candidate marking consumes only same-day and prior-derived columns. The
    forward columns are used later, after signal selection, to label outcomes.
    """

    config = config or ResearchConfig()
    if raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    df["quote_date"] = pd.to_datetime(df["quote_date"], errors="coerce").dt.normalize()
    df["stock_code"] = (
        df["stock_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    )
    if "stock_name" not in df.columns:
        df["stock_name"] = ""
    numeric_cols = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "ma5",
        "ma20",
        "ma60",
        "ma120",
        "rsi",
        "bbp",
        "vwap",
        "atr",
        "foreign_net",
        "inst_net",
        "margin_rate",
        "marcap",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(
        subset=[
            "quote_date",
            "stock_code",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
        ]
    )
    df = df[
        (df["open_price"] > 0)
        & (df["high_price"] > 0)
        & (df["low_price"] > 0)
        & (df["close_price"] > 0)
    ]
    df = df[_normal_stock_mask(df["stock_name"])].copy()
    df = df.sort_values(["stock_code", "quote_date"]).reset_index(drop=True)
    grouped = df.groupby("stock_code", group_keys=False)

    typical = (df["high_price"] + df["low_price"] + df["close_price"]) / 3.0
    df["traded_value"] = df["close_price"] * df["volume"].fillna(0.0)
    df["vwap20_calc"] = (typical * df["volume"]).groupby(df["stock_code"]).rolling(
        20, min_periods=5
    ).sum().reset_index(level=0, drop=True) / (
        grouped["volume"]
        .rolling(20, min_periods=5)
        .sum()
        .reset_index(level=0, drop=True)
        + 1e-9
    )
    df["vwap_effective"] = df["vwap"].where(df["vwap"] > 0, df["vwap20_calc"])

    for length in (5, 20, 60, 120):
        ma_col = f"ma{length}"
        calc_col = f"{ma_col}_calc"
        df[calc_col] = (
            grouped["close_price"]
            .rolling(length, min_periods=max(2, min(length, 5)))
            .mean()
            .reset_index(level=0, drop=True)
        )
        df[ma_col] = df[ma_col].where(df[ma_col] > 0, df[calc_col])

    df["high20"] = (
        grouped["high_price"]
        .rolling(20, min_periods=20)
        .max()
        .reset_index(level=0, drop=True)
    )
    df["high60"] = (
        grouped["high_price"]
        .rolling(60, min_periods=60)
        .max()
        .reset_index(level=0, drop=True)
    )
    df["high120"] = (
        grouped["high_price"]
        .rolling(120, min_periods=120)
        .max()
        .reset_index(level=0, drop=True)
    )
    df["low20"] = (
        grouped["low_price"]
        .rolling(20, min_periods=20)
        .min()
        .reset_index(level=0, drop=True)
    )
    df["low60"] = (
        grouped["low_price"]
        .rolling(60, min_periods=60)
        .min()
        .reset_index(level=0, drop=True)
    )
    df["median_volume20"] = (
        grouped["volume"]
        .rolling(20, min_periods=20)
        .median()
        .reset_index(level=0, drop=True)
    )
    df["median_value20"] = (
        grouped["traded_value"]
        .rolling(20, min_periods=20)
        .median()
        .reset_index(level=0, drop=True)
    )
    df["history_count"] = grouped.cumcount() + 1

    df["return_1d_pct"] = grouped["close_price"].pct_change() * 100.0
    df["return_20d_pct"] = grouped["close_price"].pct_change(20) * 100.0
    df["drawdown_high20_pct"] = (
        df["close_price"] / (df["high20"] + 1e-9) - 1.0
    ) * 100.0
    df["drawdown_high60_pct"] = (
        df["close_price"] / (df["high60"] + 1e-9) - 1.0
    ) * 100.0
    df["drawdown_high120_pct"] = (
        df["close_price"] / (df["high120"] + 1e-9) - 1.0
    ) * 100.0
    df["dist_low20_pct"] = (df["close_price"] / (df["low20"] + 1e-9) - 1.0) * 100.0
    df["dist_low60_pct"] = (df["close_price"] / (df["low60"] + 1e-9) - 1.0) * 100.0
    df["low_compression20_pct"] = (
        (df["high20"] - df["low20"]) / (df["close_price"] + 1e-9)
    ) * 100.0
    df["volume_ratio20"] = df["volume"] / (df["median_volume20"] + 1e-9)
    df["turnover_shock20"] = df["traded_value"] / (df["median_value20"] + 1e-9)
    df["vwap_distance_pct"] = (
        df["close_price"] / (df["vwap_effective"] + 1e-9) - 1.0
    ) * 100.0
    df["ma5_distance_pct"] = (df["close_price"] / (df["ma5"] + 1e-9) - 1.0) * 100.0
    df["ma20_distance_pct"] = (df["close_price"] / (df["ma20"] + 1e-9) - 1.0) * 100.0
    df["ma60_distance_pct"] = (df["close_price"] / (df["ma60"] + 1e-9) - 1.0) * 100.0
    df["ma120_distance_pct"] = (df["close_price"] / (df["ma120"] + 1e-9) - 1.0) * 100.0
    df["ma5_slope5_pct"] = grouped["ma5"].pct_change(5) * 100.0
    df["ma20_slope5_pct"] = grouped["ma20"].pct_change(5) * 100.0
    df["foreign_roll5_ratio"] = grouped["foreign_net"].rolling(
        5, min_periods=3
    ).sum().reset_index(level=0, drop=True) / (
        grouped["volume"]
        .rolling(5, min_periods=3)
        .sum()
        .reset_index(level=0, drop=True)
        + 1e-9
    )
    df["foreign_roll20_ratio"] = grouped["foreign_net"].rolling(
        20, min_periods=10
    ).sum().reset_index(level=0, drop=True) / (
        grouped["volume"]
        .rolling(20, min_periods=10)
        .sum()
        .reset_index(level=0, drop=True)
        + 1e-9
    )
    df["inst_roll5_ratio"] = grouped["inst_net"].rolling(
        5, min_periods=3
    ).sum().reset_index(level=0, drop=True) / (
        grouped["volume"]
        .rolling(5, min_periods=3)
        .sum()
        .reset_index(level=0, drop=True)
        + 1e-9
    )
    df["inst_roll20_ratio"] = grouped["inst_net"].rolling(
        20, min_periods=10
    ).sum().reset_index(level=0, drop=True) / (
        grouped["volume"]
        .rolling(20, min_periods=10)
        .sum()
        .reset_index(level=0, drop=True)
        + 1e-9
    )
    df["foreign_net_accel"] = grouped["foreign_net"].transform(
        lambda s: s.ewm(span=5, adjust=False).mean()
        - s.ewm(span=20, adjust=False).mean()
    )
    df["inst_net_accel"] = grouped["inst_net"].transform(
        lambda s: s.ewm(span=5, adjust=False).mean()
        - s.ewm(span=20, adjust=False).mean()
    )

    positive_foreign = (df["foreign_net"].fillna(0.0) > 0).astype(int)
    positive_inst = (df["inst_net"].fillna(0.0) > 0).astype(int)
    df["foreign_positive_streak"] = positive_foreign.groupby(
        df["stock_code"]
    ).transform(lambda s: s.groupby((s != s.shift()).cumsum()).cumsum())
    df["inst_positive_streak"] = positive_inst.groupby(df["stock_code"]).transform(
        lambda s: s.groupby((s != s.shift()).cumsum()).cumsum()
    )

    day_range = (df["high_price"] - df["low_price"]).abs() + 1e-9
    df["range_ratio_pct"] = day_range / (df["close_price"] + 1e-9) * 100.0
    df["body_ratio"] = (df["close_price"] - df["open_price"]).abs() / day_range
    df["lower_wick_ratio"] = (
        np.minimum(df["open_price"], df["close_price"]) - df["low_price"]
    ) / day_range
    df["atr_ratio_pct"] = df["atr"] / (df["close_price"] + 1e-9) * 100.0

    low_retest_flag = df["low_price"] <= (df["low20"] * 1.03)
    df["low_retest_count20"] = (
        low_retest_flag.astype(float)
        .groupby(df["stock_code"])
        .rolling(20, min_periods=20)
        .sum()
        .reset_index(level=0, drop=True)
    )
    if "bbp" not in df.columns:
        df["bbp"] = np.nan
    df["bbp"] = df["bbp"].fillna(0.5)
    df["rsi"] = df["rsi"].fillna(50.0)
    df["atr_ratio_pct"] = df["atr_ratio_pct"].fillna(0.0)
    by_date = df.groupby("quote_date")
    df["market_equal_weight_return_1d_pct"] = by_date["return_1d_pct"].transform("mean")
    df["market_median_return_1d_pct"] = by_date["return_1d_pct"].transform("median")
    df["market_positive_breadth_ratio"] = by_date["return_1d_pct"].transform(
        lambda s: (s > 0).mean()
    )
    df["next_quote_date"] = grouped["quote_date"].shift(-1)
    df["next_open_price"] = grouped["open_price"].shift(-1)
    df["next_high_price"] = grouped["high_price"].shift(-1)
    df["next_low_price"] = grouped["low_price"].shift(-1)
    for horizon in HORIZONS:
        df[f"future_exit_date_{horizon}d"] = grouped["quote_date"].shift(-horizon)
        df[f"future_close_{horizon}d"] = grouped["close_price"].shift(-horizon)
        df[f"future_high_max_{horizon}d"] = grouped["high_price"].transform(
            lambda s, h=horizon: s.shift(-1)
            .rolling(h, min_periods=h)
            .max()
            .shift(-(h - 1))
        )
        df[f"future_low_min_{horizon}d"] = grouped["low_price"].transform(
            lambda s, h=horizon: s.shift(-1)
            .rolling(h, min_periods=h)
            .min()
            .shift(-(h - 1))
        )
    return df.replace([np.inf, -np.inf], np.nan)


def mark_bottom_rebound_candidates(
    features: pd.DataFrame, config: ResearchConfig | None = None
) -> pd.DataFrame:
    config = config or ResearchConfig()
    if features.empty:
        return features.copy()
    df = features.copy()
    valid = (
        (df["history_count"] >= 120)
        & (df["close_price"] >= config.min_price)
        & (df["median_volume20"] >= config.min_median_volume_20d)
        & (df["median_value20"] >= config.min_median_value_20d_krw)
    )
    prior_decline = (
        (df["drawdown_high60_pct"] <= -15.0)
        | (df["drawdown_high120_pct"] <= -20.0)
        | (df["return_20d_pct"] <= -8.0)
    ) & (df["return_20d_pct"] <= 5.0)
    bottom_zone = df["dist_low60_pct"].between(0.0, 10.0) | (
        (df["bbp"] <= 0.20) & (df["dist_low60_pct"] <= 14.0)
    )
    stabilization = (
        (df["low_retest_count20"] >= 3)
        | (df["ma5_slope5_pct"] >= -1.5)
        | (df["lower_wick_ratio"] >= 0.30)
        | (df["low_compression20_pct"] <= 12.0)
    )
    not_overextended = (df["dist_low20_pct"] <= 12.0) & df["volume_ratio20"].between(
        0.40, 3.0
    )
    df["is_bottom_rebound_signal"] = (
        valid & prior_decline & bottom_zone & stabilization & not_overextended
    )
    return df


def _clip01(values: Any) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)


def _apply_backtest_rank_score(signals: pd.DataFrame) -> pd.DataFrame:
    """Rank signal-day candidates without using future label columns."""

    if signals.empty:
        return signals.copy()
    out = signals.copy()
    drawdown60 = _clip01(
        (-pd.to_numeric(out["drawdown_high60_pct"], errors="coerce") - 15.0) / 30.0
    )
    drawdown120 = _clip01(
        (-pd.to_numeric(out["drawdown_high120_pct"], errors="coerce") - 20.0) / 45.0
    )
    drawdown_score = pd.concat([drawdown60, drawdown120], axis=1).max(axis=1)
    bottom_score = _clip01(
        (10.0 - pd.to_numeric(out["dist_low60_pct"], errors="coerce")) / 10.0
    )
    retest_score = _clip01(
        pd.to_numeric(out["low_retest_count20"], errors="coerce") / 10.0
    )
    slope_score = _clip01(
        (pd.to_numeric(out["ma20_slope5_pct"], errors="coerce") + 3.0) / 6.0
    )
    wick_score = _clip01(pd.to_numeric(out["lower_wick_ratio"], errors="coerce") / 0.6)
    flow_score = _clip01(
        (pd.to_numeric(out["foreign_roll20_ratio"], errors="coerce") + 0.05) / 0.15
    )
    volume_score = _clip01(
        (3.0 - pd.to_numeric(out["volume_ratio20"], errors="coerce")) / 2.6
    )
    vwap_score = _clip01(
        (2.0 - pd.to_numeric(out["vwap_distance_pct"], errors="coerce").abs()) / 2.0
    )
    score = (
        drawdown_score * 2.0
        + bottom_score * 2.0
        + retest_score * 1.2
        + slope_score * 1.0
        + wick_score * 0.8
        + flow_score * 1.0
        + volume_score * 0.6
        + vwap_score * 0.4
    )
    out["backtest_rank_score"] = score.round(6)
    return out


def _simulate_limit_entry(
    next_quote: pd.Series, limit_price: float, reason: str
) -> EntryResult:
    open_price = _safe_float(next_quote.get("open_price"))
    low_price = _safe_float(next_quote.get("low_price"))
    high_price = _safe_float(next_quote.get("high_price"))
    quote_date = _date_text(next_quote.get("quote_date"))
    if min(open_price, low_price, high_price, limit_price) <= 0:
        return EntryResult(
            "pending_future_quotes",
            entry_reason="invalid_next_quote",
            limit_price=limit_price,
        )
    if open_price <= limit_price:
        return EntryResult(
            "entered", quote_date, open_price, f"{reason}_open_below_limit", limit_price
        )
    if low_price <= limit_price <= high_price:
        return EntryResult(
            "entered", quote_date, limit_price, f"{reason}_limit_touched", limit_price
        )
    return EntryResult(
        "expired", entry_reason=f"{reason}_not_touched", limit_price=limit_price
    )


def simulate_entry(
    policy: str,
    signal: pd.Series,
    future_quotes: pd.DataFrame,
    config: ResearchConfig | None = None,
) -> EntryResult:
    config = config or ResearchConfig()
    if future_quotes.empty:
        return EntryResult("pending_future_quotes", entry_reason="missing_next_quote")
    next_quote = future_quotes.iloc[0]
    if policy == "next_open_entry":
        entry_price = _safe_float(next_quote.get("open_price"))
        if entry_price <= 0:
            return EntryResult(
                "pending_future_quotes", entry_reason="invalid_next_open"
            )
        return EntryResult(
            "entered",
            _date_text(next_quote.get("quote_date")),
            entry_price,
            "next_open",
        )
    signal_close = _safe_float(signal.get("close_price"))
    if policy == "signal_close_retest_entry":
        limit_price = _price_at_pct(
            signal_close, -config.signal_close_retest_discount_pct
        )
        return _simulate_limit_entry(next_quote, limit_price, "signal_close_retest")
    if policy == "atr_pullback_entry":
        atr_pct = _safe_float(signal.get("atr_ratio_pct"))
        buffer_pct = min(
            config.atr_pullback_max_pct,
            max(config.atr_pullback_min_pct, atr_pct * config.atr_pullback_multiplier),
        )
        limit_price = _price_at_pct(signal_close, -buffer_pct)
        return _simulate_limit_entry(next_quote, limit_price, "atr_pullback")
    if policy == "open_guarded_retest_entry":
        next_open = _safe_float(next_quote.get("open_price"))
        gap_pct = _pct(next_open, signal_close)
        if gap_pct > config.open_guarded_max_gap_up_pct:
            return EntryResult("expired", entry_reason="open_guarded_gap_up_blocked")
        if gap_pct < config.open_guarded_max_gap_down_pct:
            return EntryResult("expired", entry_reason="open_guarded_gap_down_blocked")
        limit_price = min(
            signal_close,
            _price_at_pct(next_open, -config.open_guarded_retest_discount_pct),
        )
        return _simulate_limit_entry(next_quote, limit_price, "open_guarded_retest")
    if policy == "close_zone_limit_entry":
        limit_price = _price_at_pct(signal_close, -config.close_zone_limit_discount_pct)
        return _simulate_limit_entry(next_quote, limit_price, "close_zone_limit")
    return EntryResult("expired", entry_reason=f"unknown_entry_policy:{policy}")


def label_signal(
    signal: pd.Series,
    future_quotes: pd.DataFrame,
    *,
    config: ResearchConfig | None = None,
    entry_policies: Iterable[str] = ENTRY_POLICIES,
    horizons: Iterable[int] = HORIZONS,
) -> list[dict[str, Any]]:
    config = config or ResearchConfig()
    rows: list[dict[str, Any]] = []
    for policy in entry_policies:
        entry = simulate_entry(policy, signal, future_quotes, config)
        quotes_from_entry = (
            future_quotes[future_quotes["quote_date"] >= pd.Timestamp(entry.entry_date)]
            if entry.entry_date
            else pd.DataFrame()
        )
        for horizon in horizons:
            row = {
                "stock_code": str(signal.get("stock_code")),
                "stock_name": str(signal.get("stock_name") or ""),
                "signal_date": _date_text(signal.get("quote_date")),
                "entry_policy": policy,
                "horizon_days": int(horizon),
                "entry_status": entry.status,
                "entry_date": entry.entry_date,
                "entry_price": _as_report_number(entry.entry_price),
                "entry_reason": entry.entry_reason,
                "limit_price": _as_report_number(entry.limit_price),
            }
            if entry.status != "entered":
                row.update(
                    {
                        "label_status": (
                            "expired_entry_no_trigger"
                            if entry.status == "expired"
                            else "pending_future_quotes"
                        ),
                        "final_return_pct": None,
                        "mfe_pct": None,
                        "mae_pct": None,
                    }
                )
                rows.append(row)
                continue
            if len(quotes_from_entry) < int(horizon):
                row.update(
                    {
                        "label_status": "pending_future_quotes",
                        "final_return_pct": None,
                        "mfe_pct": None,
                        "mae_pct": None,
                    }
                )
                rows.append(row)
                continue
            window = quotes_from_entry.iloc[: int(horizon)]
            exit_quote = window.iloc[int(horizon) - 1]
            entry_price = _safe_float(entry.entry_price)
            final_return = _pct(_safe_float(exit_quote.get("close_price")), entry_price)
            mfe = max(_pct(_safe_float(v), entry_price) for v in window["high_price"])
            mae = min(_pct(_safe_float(v), entry_price) for v in window["low_price"])
            row.update(
                {
                    "label_status": "labeled",
                    "exit_date": _date_text(exit_quote.get("quote_date")),
                    "final_return_pct": round(final_return, 6),
                    "mfe_pct": round(mfe, 6),
                    "mae_pct": round(mae, 6),
                }
            )
            rows.append(row)
    return rows


def _bucket(value: Any, cuts: list[tuple[float, str]], default: str = "unknown") -> str:
    numeric = _safe_float(value, float("nan"))
    if not math.isfinite(numeric):
        return default
    for upper, label in cuts:
        if numeric <= upper:
            return label
    return cuts[-1][1] if cuts else default


def _feature_buckets(row: pd.Series) -> dict[str, str]:
    market_median = _safe_float(row.get("market_median_return_1d_pct"))
    market_breadth = _safe_float(row.get("market_positive_breadth_ratio"), 0.5)
    if market_median <= -1.0 or market_breadth <= 0.35:
        market_regime_bucket = "market_risk_off"
    elif market_median >= 1.0 or market_breadth >= 0.65:
        market_regime_bucket = "market_risk_on"
    else:
        market_regime_bucket = "market_neutral"
    foreign = _safe_float(row.get("foreign_roll20_ratio"))
    inst = _safe_float(row.get("inst_roll20_ratio"))
    if foreign > 0.0 and inst > 0.0:
        flow_combo_bucket = "dual_buy"
    elif foreign > 0.0:
        flow_combo_bucket = "foreign_buy_only"
    elif inst > 0.0:
        flow_combo_bucket = "inst_buy_only"
    else:
        flow_combo_bucket = "dual_sell_or_flat"
    return {
        "signal_year": str(_date_text(row.get("quote_date")) or "")[:4],
        "market_regime_bucket": market_regime_bucket,
        "market_breadth_bucket": _bucket(
            row.get("market_positive_breadth_ratio"),
            [
                (0.35, "breadth_weak"),
                (0.50, "breadth_soft"),
                (0.65, "breadth_balanced"),
                (999, "breadth_strong"),
            ],
        ),
        "marcap_bucket": _bucket(
            row.get("marcap"),
            [
                (100_000_000_000, "micro_cap"),
                (500_000_000_000, "small_cap"),
                (2_000_000_000_000, "mid_cap"),
                (999_000_000_000_000, "large_cap"),
            ],
        ),
        "flow_combo_bucket": flow_combo_bucket,
        "drawdown_high60_bucket": _bucket(
            row.get("drawdown_high60_pct"),
            [
                (-35, "deep_35_down"),
                (-25, "down_25_35"),
                (-15, "down_15_25"),
                (0, "down_0_15"),
                (999, "above_high"),
            ],
        ),
        "dist_low60_bucket": _bucket(
            row.get("dist_low60_pct"),
            [
                (3, "near_low_0_3"),
                (7, "near_low_3_7"),
                (14, "near_low_7_14"),
                (999, "above_low_14"),
            ],
        ),
        "vwap_distance_bucket": _bucket(
            row.get("vwap_distance_pct"),
            [
                (-5, "below_vwap_5_plus"),
                (-1, "below_vwap_1_5"),
                (1, "near_vwap"),
                (5, "above_vwap_1_5"),
                (999, "above_vwap_5_plus"),
            ],
        ),
        "volume_ratio_bucket": _bucket(
            row.get("volume_ratio20"),
            [
                (0.8, "quiet"),
                (1.2, "normal"),
                (2.0, "active"),
                (4.0, "expanded"),
                (999, "extreme"),
            ],
        ),
        "rsi_bucket": _bucket(
            row.get("rsi"),
            [
                (30, "rsi_oversold"),
                (45, "rsi_30_45"),
                (60, "rsi_45_60"),
                (999, "rsi_60_plus"),
            ],
        ),
        "bbp_bucket": _bucket(
            row.get("bbp"),
            [
                (0.1, "bbp_bottom"),
                (0.35, "bbp_low"),
                (0.65, "bbp_mid"),
                (999, "bbp_high"),
            ],
        ),
        "foreign_roll20_bucket": _bucket(
            row.get("foreign_roll20_ratio"),
            [
                (-0.05, "foreign_sell"),
                (0, "foreign_slight_sell"),
                (0.05, "foreign_slight_buy"),
                (999, "foreign_buy"),
            ],
        ),
        "inst_roll20_bucket": _bucket(
            row.get("inst_roll20_ratio"),
            [
                (-0.05, "inst_sell"),
                (0, "inst_slight_sell"),
                (0.05, "inst_slight_buy"),
                (999, "inst_buy"),
            ],
        ),
        "low_retest_bucket": _bucket(
            row.get("low_retest_count20"),
            [(1, "low_retest_0_1"), (3, "low_retest_2_3"), (999, "low_retest_4_plus")],
        ),
        "ma20_slope_bucket": _bucket(
            row.get("ma20_slope5_pct"),
            [
                (-5, "ma20_falling_fast"),
                (-1, "ma20_falling"),
                (1, "ma20_flat"),
                (999, "ma20_rising"),
            ],
        ),
        "atr_ratio_bucket": _bucket(
            row.get("atr_ratio_pct"),
            [(2, "atr_low"), (4, "atr_mid"), (7, "atr_high"), (999, "atr_extreme")],
        ),
    }


def _signal_summary_row(
    row: pd.Series, *, include_buckets: bool = True
) -> dict[str, Any]:
    payload = {
        "signal_date": _date_text(row.get("quote_date")),
        "stock_code": str(row.get("stock_code")),
        "stock_name": str(row.get("stock_name") or ""),
        "close_price": _as_report_number(row.get("close_price"), 2),
        "volume": int(_safe_float(row.get("volume"))),
        "traded_value": int(_safe_float(row.get("traded_value"))),
        "drawdown_high60_pct": _as_report_number(row.get("drawdown_high60_pct")),
        "dist_low60_pct": _as_report_number(row.get("dist_low60_pct")),
        "dist_low20_pct": _as_report_number(row.get("dist_low20_pct")),
        "low_retest_count20": _as_report_number(row.get("low_retest_count20"), 2),
        "low_compression20_pct": _as_report_number(row.get("low_compression20_pct")),
        "ma20_slope5_pct": _as_report_number(row.get("ma20_slope5_pct")),
        "vwap_distance_pct": _as_report_number(row.get("vwap_distance_pct")),
        "volume_ratio20": _as_report_number(row.get("volume_ratio20")),
        "turnover_shock20": _as_report_number(row.get("turnover_shock20")),
        "rsi": _as_report_number(row.get("rsi"), 2),
        "bbp": _as_report_number(row.get("bbp")),
        "atr_ratio_pct": _as_report_number(row.get("atr_ratio_pct")),
        "foreign_roll20_ratio": _as_report_number(row.get("foreign_roll20_ratio")),
        "inst_roll20_ratio": _as_report_number(row.get("inst_roll20_ratio")),
        "market_regime_bucket": _feature_buckets(row).get("market_regime_bucket"),
        "market_median_return_1d_pct": _as_report_number(
            row.get("market_median_return_1d_pct")
        ),
        "market_positive_breadth_ratio": _as_report_number(
            row.get("market_positive_breadth_ratio")
        ),
        "flow_combo_bucket": _feature_buckets(row).get("flow_combo_bucket"),
        "marcap": int(_safe_float(row.get("marcap"))),
        "backtest_rank_score": _as_report_number(row.get("backtest_rank_score")),
    }
    if include_buckets:
        payload.update(_feature_buckets(row))
    return payload


def _dedupe_examples(signals: pd.DataFrame, cooldown_days: int) -> pd.DataFrame:
    if signals.empty:
        return signals.copy()
    selected_indices: list[int] = []
    for _, group in signals.sort_values(["stock_code", "quote_date"]).groupby(
        "stock_code"
    ):
        last_history_count = -10_000
        for idx, row in group.iterrows():
            history_count = int(_safe_float(row.get("history_count")))
            if history_count - last_history_count >= cooldown_days:
                selected_indices.append(idx)
                last_history_count = history_count
    return signals.loc[selected_indices].copy()


def _label_frame(rows: list[dict[str, Any]] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows.copy()
    return pd.DataFrame(rows)


def _aggregate_label_rows(
    rows: list[dict[str, Any]] | pd.DataFrame,
    *,
    group_keys: list[str],
    sample_floor: int,
) -> list[dict[str, Any]]:
    frame = _label_frame(rows)
    if frame.empty:
        return []
    out: list[dict[str, Any]] = []
    for key_values, group in frame.groupby(group_keys, dropna=False):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        base = {key: value for key, value in zip(group_keys, key_values)}
        labeled = group[group["label_status"].eq("labeled")].copy()
        returns = pd.to_numeric(
            labeled.get("final_return_pct"), errors="coerce"
        ).dropna()
        mfe = pd.to_numeric(labeled.get("mfe_pct"), errors="coerce").dropna()
        mae = pd.to_numeric(labeled.get("mae_pct"), errors="coerce").dropna()
        sample_count = int(len(returns))
        total_count = int(len(group))
        equal_ev = float(returns.mean()) if sample_count else 0.0
        coverage = min(1.0, sample_count / max(1, sample_floor))
        out.append(
            {
                **base,
                "sample_count": sample_count,
                "total_row_count": total_count,
                "entry_fill_rate": (
                    round(sample_count / total_count, 6) if total_count else 0.0
                ),
                "expired_rate": (
                    round(
                        group["label_status"].eq("expired_entry_no_trigger").sum()
                        / total_count,
                        6,
                    )
                    if total_count
                    else 0.0
                ),
                "pending_future_quote_rate": (
                    round(
                        group["label_status"].eq("pending_future_quotes").sum()
                        / total_count,
                        6,
                    )
                    if total_count
                    else 0.0
                ),
                "equal_weight_avg_profit_pct": round(equal_ev, 6),
                "source_quality_adjusted_ev_pct": round(equal_ev * coverage, 6),
                "diagnostic_win_rate": (
                    round(float((returns > 0).mean()), 6) if sample_count else 0.0
                ),
                "mfe_p50_pct": (
                    _as_report_number(mfe.quantile(0.50)) if sample_count else None
                ),
                "mfe_p80_pct": (
                    _as_report_number(mfe.quantile(0.80)) if sample_count else None
                ),
                "mae_p20_pct": (
                    _as_report_number(mae.quantile(0.20)) if sample_count else None
                ),
                "mae_p10_pct": (
                    _as_report_number(mae.quantile(0.10)) if sample_count else None
                ),
            }
        )
    return sorted(
        out,
        key=lambda item: (
            int(item.get("horizon_days") or 0),
            str(item.get("entry_policy") or ""),
            _safe_float(item.get("source_quality_adjusted_ev_pct")),
            int(item.get("sample_count") or 0),
        ),
        reverse=True,
    )


def _entry_columns(
    signals: pd.DataFrame, policy: str, config: ResearchConfig
) -> pd.DataFrame:
    out = pd.DataFrame(index=signals.index)
    out["entry_policy"] = policy
    out["entry_date"] = (
        signals["next_quote_date"]
        .dt.date.astype(str)
        .where(signals["next_quote_date"].notna(), None)
    )
    next_open = pd.to_numeric(signals["next_open_price"], errors="coerce")
    next_low = pd.to_numeric(signals["next_low_price"], errors="coerce")
    next_high = pd.to_numeric(signals["next_high_price"], errors="coerce")
    has_next = next_open.gt(0) & next_low.gt(0) & next_high.gt(0)
    missing_reason = pd.Series("missing_next_quote", index=signals.index)
    if policy == "next_open_entry":
        out["entry_status"] = np.where(has_next, "entered", "pending_future_quotes")
        out["entry_price"] = next_open.where(has_next)
        out["limit_price"] = np.nan
        out["entry_reason"] = np.where(has_next, "next_open", "missing_next_quote")
        return out

    signal_close = pd.to_numeric(signals["close_price"], errors="coerce")
    if policy == "signal_close_retest_entry":
        limit_price = (
            _price_at_pct(1.0, -config.signal_close_retest_discount_pct) * signal_close
        )
        reason = "signal_close_retest"
    elif policy == "atr_pullback_entry":
        atr_pct = pd.to_numeric(signals["atr_ratio_pct"], errors="coerce").fillna(0.0)
        buffer_pct = (atr_pct * config.atr_pullback_multiplier).clip(
            lower=config.atr_pullback_min_pct,
            upper=config.atr_pullback_max_pct,
        )
        limit_price = signal_close * (1.0 - buffer_pct / 100.0)
        reason = "atr_pullback"
    elif policy == "open_guarded_retest_entry":
        gap_pct = (next_open / signal_close - 1.0) * 100.0
        gap_up_blocked = gap_pct.gt(config.open_guarded_max_gap_up_pct)
        gap_down_blocked = gap_pct.lt(config.open_guarded_max_gap_down_pct)
        gap_ok = ~(gap_up_blocked | gap_down_blocked)
        limit_price = pd.concat(
            [
                signal_close,
                next_open * (1.0 - config.open_guarded_retest_discount_pct / 100.0),
            ],
            axis=1,
        ).min(axis=1)
        reason = "open_guarded_retest"
        missing_reason = pd.Series(
            np.where(
                gap_up_blocked,
                "open_guarded_gap_up_blocked",
                np.where(
                    gap_down_blocked,
                    "open_guarded_gap_down_blocked",
                    "missing_next_quote",
                ),
            ),
            index=signals.index,
        )
        has_next = has_next & gap_ok
    elif policy == "close_zone_limit_entry":
        limit_price = signal_close * (
            1.0 - config.close_zone_limit_discount_pct / 100.0
        )
        reason = "close_zone_limit"
    else:
        out["entry_status"] = "expired"
        out["entry_price"] = np.nan
        out["limit_price"] = np.nan
        out["entry_reason"] = f"unknown_entry_policy:{policy}"
        return out

    open_fill = has_next & next_open.le(limit_price)
    limit_fill = (
        has_next & ~open_fill & next_low.le(limit_price) & next_high.ge(limit_price)
    )
    entered = open_fill | limit_fill
    out["entry_status"] = np.where(
        ~has_next, "pending_future_quotes", np.where(entered, "entered", "expired")
    )
    out["entry_price"] = np.where(
        open_fill, next_open, np.where(limit_fill, limit_price, np.nan)
    )
    out["limit_price"] = limit_price
    out["entry_reason"] = np.where(
        ~has_next,
        missing_reason,
        np.where(
            open_fill,
            f"{reason}_open_below_limit",
            np.where(limit_fill, f"{reason}_limit_touched", f"{reason}_not_touched"),
        ),
    )
    return out


def _build_labels(
    signals: pd.DataFrame, features: pd.DataFrame, config: ResearchConfig
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    examples: list[dict[str, Any]] = []
    if signals.empty:
        return pd.DataFrame(), examples
    signals = signals.sort_values(["stock_code", "quote_date"]).copy()
    bucket_frame = pd.DataFrame(
        [_feature_buckets(row) for _, row in signals.iterrows()], index=signals.index
    )
    signal_base = pd.DataFrame(
        {
            "stock_code": signals["stock_code"].astype(str),
            "stock_name": signals["stock_name"].fillna("").astype(str),
            "signal_date": signals["quote_date"].dt.date.astype(str),
            "backtest_rank_score": pd.to_numeric(
                signals.get("backtest_rank_score", 0.0), errors="coerce"
            ).fillna(0.0),
        },
        index=signals.index,
    )
    signal_base = pd.concat([signal_base, bucket_frame], axis=1)

    frames: list[pd.DataFrame] = []
    for policy in ENTRY_POLICIES:
        entry = _entry_columns(signals, policy, config)
        for horizon in HORIZONS:
            frame = pd.concat([signal_base, entry], axis=1)
            frame["horizon_days"] = int(horizon)
            has_exit = signals[f"future_close_{horizon}d"].notna()
            entered = frame["entry_status"].eq("entered")
            frame["label_status"] = np.where(
                entered & has_exit,
                "labeled",
                np.where(
                    frame["entry_status"].eq("expired"),
                    "expired_entry_no_trigger",
                    "pending_future_quotes",
                ),
            )
            entry_price = pd.to_numeric(frame["entry_price"], errors="coerce")
            final_return = (
                signals[f"future_close_{horizon}d"] / entry_price - 1.0
            ) * 100.0
            mfe = (signals[f"future_high_max_{horizon}d"] / entry_price - 1.0) * 100.0
            mae = (signals[f"future_low_min_{horizon}d"] / entry_price - 1.0) * 100.0
            frame["exit_date"] = (
                signals[f"future_exit_date_{horizon}d"]
                .dt.date.astype(str)
                .where(has_exit, None)
            )
            frame["final_return_pct"] = final_return.where(
                frame["label_status"].eq("labeled")
            ).round(6)
            frame["mfe_pct"] = mfe.where(frame["label_status"].eq("labeled")).round(6)
            frame["mae_pct"] = mae.where(frame["label_status"].eq("labeled")).round(6)
            frames.append(frame)
    labels = pd.concat(frames, ignore_index=True)
    example_signals = _dedupe_examples(signals, config.cooldown_trading_days)
    for _, signal in example_signals.head(100).iterrows():
        examples.append(_signal_summary_row(signal))
    return labels, examples


def _compound_return_pct(values: Iterable[float]) -> float:
    equity = 1.0
    for value in values:
        equity *= 1.0 + (_safe_float(value) / 100.0)
    return round((equity - 1.0) * 100.0, 6)


def _max_drawdown_pct(equity_values: Iterable[float]) -> float:
    peak = 1.0
    max_drawdown = 0.0
    for equity in equity_values:
        current = _safe_float(equity, 1.0)
        peak = max(peak, current)
        if peak > 0:
            max_drawdown = min(max_drawdown, (current / peak - 1.0) * 100.0)
    return round(max_drawdown, 6)


def _build_portfolio_backtest(
    labels: pd.DataFrame, config: ResearchConfig
) -> dict[str, Any]:
    """Closed-trade portfolio backtest using postclose signal ranking only."""

    if labels.empty:
        return {
            "config": {
                "entry_policy": config.backtest_entry_policy,
                "horizon_days": config.backtest_horizon_days,
                "max_positions": config.backtest_max_positions,
                "trade_cost_pct": config.backtest_trade_cost_pct,
            },
            "summary": {
                "trade_count": 0,
                "skipped_capacity_count": 0,
                "skipped_same_symbol_count": 0,
            },
            "equity_curve": [],
            "monthly_returns": [],
            "yearly_returns": [],
            "trades": [],
        }
    frame = labels[
        labels["entry_policy"].eq(config.backtest_entry_policy)
        & labels["horizon_days"].eq(int(config.backtest_horizon_days))
        & labels["label_status"].eq("labeled")
        & labels["entry_status"].eq("entered")
    ].copy()
    if frame.empty:
        return {
            "config": {
                "entry_policy": config.backtest_entry_policy,
                "horizon_days": config.backtest_horizon_days,
                "max_positions": config.backtest_max_positions,
                "trade_cost_pct": config.backtest_trade_cost_pct,
            },
            "summary": {
                "trade_count": 0,
                "skipped_capacity_count": 0,
                "skipped_same_symbol_count": 0,
            },
            "equity_curve": [],
            "monthly_returns": [],
            "yearly_returns": [],
            "trades": [],
        }

    frame["signal_ts"] = pd.to_datetime(frame["signal_date"], errors="coerce")
    frame["entry_ts"] = pd.to_datetime(frame["entry_date"], errors="coerce")
    frame["exit_ts"] = pd.to_datetime(frame["exit_date"], errors="coerce")
    frame["backtest_rank_score"] = pd.to_numeric(
        frame.get("backtest_rank_score"), errors="coerce"
    ).fillna(0.0)
    frame["final_return_pct"] = pd.to_numeric(
        frame["final_return_pct"], errors="coerce"
    )
    frame = frame.dropna(
        subset=["signal_ts", "entry_ts", "exit_ts", "final_return_pct"]
    )
    frame = frame.sort_values(
        ["signal_ts", "backtest_rank_score", "stock_code"],
        ascending=[True, False, True],
    )

    open_positions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    skipped_capacity_count = 0
    skipped_same_symbol_count = 0
    max_positions = max(1, int(config.backtest_max_positions))
    for _, row in frame.iterrows():
        entry_ts = row["entry_ts"]
        open_positions = [
            item for item in open_positions if item["exit_ts"] >= entry_ts
        ]
        code = str(row["stock_code"])
        if any(item["stock_code"] == code for item in open_positions):
            skipped_same_symbol_count += 1
            continue
        if len(open_positions) >= max_positions:
            skipped_capacity_count += 1
            continue
        gross_return = _safe_float(row["final_return_pct"])
        net_return = gross_return - float(config.backtest_trade_cost_pct)
        contribution_pct = net_return / max_positions
        trade = {
            "signal_date": _date_text(row["signal_ts"]),
            "entry_date": _date_text(entry_ts),
            "exit_date": _date_text(row["exit_ts"]),
            "stock_code": code,
            "stock_name": str(row.get("stock_name") or ""),
            "entry_policy": str(row["entry_policy"]),
            "horizon_days": int(row["horizon_days"]),
            "entry_price": _as_report_number(row.get("entry_price"), 2),
            "gross_return_pct": round(gross_return, 6),
            "net_return_pct": round(net_return, 6),
            "portfolio_return_contribution_pct": round(contribution_pct, 6),
            "backtest_rank_score": _as_report_number(row.get("backtest_rank_score")),
        }
        selected.append(trade)
        open_positions.append({"stock_code": code, "exit_ts": row["exit_ts"]})

    if not selected:
        return {
            "config": {
                "entry_policy": config.backtest_entry_policy,
                "horizon_days": config.backtest_horizon_days,
                "max_positions": max_positions,
                "trade_cost_pct": config.backtest_trade_cost_pct,
            },
            "summary": {
                "trade_count": 0,
                "skipped_capacity_count": skipped_capacity_count,
                "skipped_same_symbol_count": skipped_same_symbol_count,
            },
            "equity_curve": [],
            "monthly_returns": [],
            "yearly_returns": [],
            "trades": [],
        }

    trades = pd.DataFrame(selected)
    daily_contrib = (
        trades.groupby("exit_date", dropna=False)["portfolio_return_contribution_pct"]
        .sum()
        .reset_index()
        .sort_values("exit_date")
    )
    equity = 1.0
    equity_curve: list[dict[str, Any]] = []
    for _, row in daily_contrib.iterrows():
        day_return_pct = _safe_float(row["portfolio_return_contribution_pct"])
        equity *= 1.0 + day_return_pct / 100.0
        equity_curve.append(
            {
                "date": str(row["exit_date"]),
                "closed_trade_return_pct": round(day_return_pct, 6),
                "equity": round(equity, 8),
                "cumulative_return_pct": round((equity - 1.0) * 100.0, 6),
            }
        )

    trades["exit_month"] = (
        pd.to_datetime(trades["exit_date"]).dt.to_period("M").astype(str)
    )
    trades["exit_year"] = pd.to_datetime(trades["exit_date"]).dt.year.astype(str)
    monthly_returns = [
        {
            "month": key,
            "portfolio_return_pct": _compound_return_pct(
                group["portfolio_return_contribution_pct"]
            ),
        }
        for key, group in trades.groupby("exit_month")
    ]
    yearly_returns = [
        {
            "year": key,
            "portfolio_return_pct": _compound_return_pct(
                group["portfolio_return_contribution_pct"]
            ),
        }
        for key, group in trades.groupby("exit_year")
    ]
    net_returns = pd.to_numeric(trades["net_return_pct"], errors="coerce").dropna()
    summary = {
        "trade_count": int(len(trades)),
        "skipped_capacity_count": int(skipped_capacity_count),
        "skipped_same_symbol_count": int(skipped_same_symbol_count),
        "total_return_pct": round((equity - 1.0) * 100.0, 6),
        "max_drawdown_pct": _max_drawdown_pct(item["equity"] for item in equity_curve),
        "avg_trade_net_return_pct": _as_report_number(net_returns.mean()),
        "median_trade_net_return_pct": _as_report_number(net_returns.median()),
        "diagnostic_win_rate": (
            round(float((net_returns > 0).mean()), 6) if len(net_returns) else 0.0
        ),
        "first_entry_date": str(trades["entry_date"].min()),
        "last_exit_date": str(trades["exit_date"].max()),
    }
    return {
        "config": {
            "entry_policy": config.backtest_entry_policy,
            "horizon_days": config.backtest_horizon_days,
            "max_positions": max_positions,
            "trade_cost_pct": config.backtest_trade_cost_pct,
            "ranking": "signal_day_bottom_rebound_rank_score",
            "accounting": "closed_trade_compounded_slot_contribution",
        },
        "summary": summary,
        "equity_curve": equity_curve,
        "monthly_returns": monthly_returns,
        "yearly_returns": yearly_returns,
        "trades": trades.drop(columns=["exit_month", "exit_year"]).to_dict(
            orient="records"
        ),
    }


def _build_backtest_variants(
    labels: pd.DataFrame, config: ResearchConfig
) -> list[dict[str, Any]]:
    if labels.empty:
        return []
    variants = [
        ("baseline", labels),
        (
            "exclude_market_risk_off",
            labels[
                ~labels.get(
                    "market_regime_bucket", pd.Series(index=labels.index, dtype=str)
                ).eq("market_risk_off")
            ],
        ),
        (
            "require_foreign_not_sell",
            labels[
                ~labels.get(
                    "foreign_roll20_bucket", pd.Series(index=labels.index, dtype=str)
                ).eq("foreign_sell")
            ],
        ),
        (
            "exclude_risk_off_and_foreign_sell",
            labels[
                ~labels.get(
                    "market_regime_bucket", pd.Series(index=labels.index, dtype=str)
                ).eq("market_risk_off")
                & ~labels.get(
                    "foreign_roll20_bucket", pd.Series(index=labels.index, dtype=str)
                ).eq("foreign_sell")
            ],
        ),
    ]
    out: list[dict[str, Any]] = []
    for name, subset in variants:
        result = _build_portfolio_backtest(subset.copy(), config)
        summary = (
            result.get("summary") if isinstance(result.get("summary"), dict) else {}
        )
        out.append(
            {"variant": name, "summary": summary, "config": result.get("config")}
        )
    return out


def _latest_candidates(signals: pd.DataFrame, as_of: str) -> list[dict[str, Any]]:
    if signals.empty:
        return []
    current = signals[signals["quote_date"].eq(pd.Timestamp(as_of))].copy()
    current = current.sort_values(
        [
            "backtest_rank_score",
            "drawdown_high60_pct",
            "dist_low60_pct",
            "turnover_shock20",
            "foreign_roll20_ratio",
        ],
        ascending=[False, True, True, False, False],
    )
    return [_signal_summary_row(row) for _, row in current.head(100).iterrows()]


def _build_kiwoom_enrichment(
    latest_candidates: list[dict[str, Any]],
    *,
    target_date: str,
    config: ResearchConfig,
) -> dict[str, Any]:
    max_codes = max(0, int(config.kiwoom_enrichment_max_codes))
    candidate_codes = [
        str(row.get("stock_code") or "").zfill(6)
        for row in latest_candidates
        if row.get("stock_code")
    ]
    requested = candidate_codes[:max_codes]
    if not config.enable_kiwoom_enrichment:
        return {
            "enabled": False,
            "source": "kiwoom_api",
            "requested_code_count": 0,
            "mapped_code_count": 0,
            "rows_by_code": {},
            "diagnostics": {"status": "disabled"},
            "warnings": [],
        }
    if not requested:
        return {
            "enabled": True,
            "source": "kiwoom_api",
            "requested_code_count": 0,
            "mapped_code_count": 0,
            "rows_by_code": {},
            "diagnostics": {"status": "empty_candidate_set"},
            "warnings": ["kiwoom_enrichment_empty_candidate_set"],
        }
    try:
        from src.engine.swing_sector_theme_source import build_sector_theme_map

        payload = build_sector_theme_map(
            requested,
            target_date=target_date,
            allow_external=False,
            write_cache=config.kiwoom_enrichment_write_cache,
        )
    except Exception as exc:
        return {
            "enabled": True,
            "source": "kiwoom_api",
            "requested_code_count": len(requested),
            "mapped_code_count": 0,
            "rows_by_code": {},
            "diagnostics": {"status": "kiwoom_enrichment_failed", "error": str(exc)},
            "warnings": ["kiwoom_enrichment_failed"],
        }
    rows_by_code = (
        payload.get("rows_by_code")
        if isinstance(payload.get("rows_by_code"), dict)
        else {}
    )
    return {
        "enabled": True,
        "source": "kiwoom_api",
        "requested_code_count": len(requested),
        "mapped_code_count": int(payload.get("mapped_code_count") or 0),
        "sector_mapped_count": int(payload.get("sector_mapped_count") or 0),
        "theme_mapped_count": int(payload.get("theme_mapped_count") or 0),
        "rows_by_code": rows_by_code,
        "diagnostics": payload.get("diagnostics") or {},
        "warnings": payload.get("warnings") or [],
        "cache_report_type": payload.get("report_type"),
    }


def _apply_kiwoom_enrichment_to_candidates(
    candidates: list[dict[str, Any]],
    enrichment: dict[str, Any],
) -> list[dict[str, Any]]:
    rows_by_code = (
        enrichment.get("rows_by_code")
        if isinstance(enrichment.get("rows_by_code"), dict)
        else {}
    )
    if not rows_by_code:
        return candidates
    out: list[dict[str, Any]] = []
    for row in candidates:
        code = str(row.get("stock_code") or "").zfill(6)
        enrich = (
            rows_by_code.get(code) if isinstance(rows_by_code.get(code), dict) else {}
        )
        if enrich:
            row = {
                **row,
                "kiwoom_sector": enrich.get("sector") or row.get("kiwoom_sector") or "",
                "kiwoom_industry": enrich.get("industry")
                or row.get("kiwoom_industry")
                or "",
                "kiwoom_market_type": enrich.get("market_type") or "",
                "kiwoom_theme_tags": enrich.get("theme_tags") or [],
                "kiwoom_sector_source_quality": enrich.get("sector_source_quality")
                or "missing",
                "kiwoom_theme_source_quality": enrich.get("theme_source_quality")
                or "missing",
            }
        out.append(row)
    return out


def _source_quality_summary(
    *,
    raw_rows: int,
    feature_rows: int,
    signals: pd.DataFrame,
    labels: list[dict[str, Any]] | pd.DataFrame,
    config: ResearchConfig,
) -> dict[str, Any]:
    label_frame = _label_frame(labels)
    status_counts = (
        {
            str(key): int(value)
            for key, value in label_frame["label_status"]
            .value_counts(dropna=False)
            .items()
        }
        if not label_frame.empty and "label_status" in label_frame.columns
        else {}
    )
    latest_date = _date_text(signals["quote_date"].max()) if not signals.empty else None
    return {
        "implementation_status": "implemented",
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "raw_quote_rows": raw_rows,
        "feature_rows": feature_rows,
        "signal_rows": int(len(signals)),
        "unique_signal_codes": (
            int(signals["stock_code"].nunique()) if not signals.empty else 0
        ),
        "latest_signal_date": latest_date,
        "label_status_counts": status_counts,
        "sample_floor": config.sample_floor,
        "source_quality_gate": (
            "pass" if raw_rows and feature_rows else "no_source_rows"
        ),
    }


def build_research_report_from_frame(
    raw: pd.DataFrame, config: ResearchConfig | None = None
) -> dict[str, Any]:
    config = config or ResearchConfig()
    features = prepare_feature_frame(raw, config)
    features = mark_bottom_rebound_candidates(features, config)
    if features.empty:
        effective_as_of = config.as_of or date.today().isoformat()
    else:
        effective_as_of = (
            config.as_of
            or _date_text(features["quote_date"].max())
            or date.today().isoformat()
        )
    signals = _apply_backtest_rank_score(
        features[features["is_bottom_rebound_signal"].fillna(False)].copy()
    )
    labels, examples = _build_labels(signals, features, config)
    entry_policy_comparison = _aggregate_label_rows(
        labels,
        group_keys=["entry_policy", "horizon_days"],
        sample_floor=config.sample_floor,
    )
    feature_bucket_ev_tables: dict[str, list[dict[str, Any]]] = {}
    bucket_axes = [
        "signal_year",
        "market_regime_bucket",
        "market_breadth_bucket",
        "marcap_bucket",
        "flow_combo_bucket",
        "drawdown_high60_bucket",
        "dist_low60_bucket",
        "vwap_distance_bucket",
        "volume_ratio_bucket",
        "rsi_bucket",
        "bbp_bucket",
        "foreign_roll20_bucket",
        "inst_roll20_bucket",
        "low_retest_bucket",
        "ma20_slope_bucket",
        "atr_ratio_bucket",
    ]
    for axis in bucket_axes:
        feature_bucket_ev_tables[axis] = _aggregate_label_rows(
            labels,
            group_keys=["entry_policy", "horizon_days", axis],
            sample_floor=config.sample_floor,
        )[:50]

    primary_rows = [
        row
        for row in entry_policy_comparison
        if int(row.get("horizon_days") or 0) == int(config.primary_horizon_days)
        and int(row.get("sample_count") or 0) >= int(config.sample_floor)
    ]
    top_primary = max(
        primary_rows,
        key=lambda row: _safe_float(row.get("source_quality_adjusted_ev_pct")),
        default=None,
    )
    portfolio_backtest = _build_portfolio_backtest(labels, config)
    backtest_variants = _build_backtest_variants(labels, config)
    backtest_summary = (
        portfolio_backtest.get("summary")
        if isinstance(portfolio_backtest.get("summary"), dict)
        else {}
    )
    latest_candidates = _latest_candidates(signals, effective_as_of)
    kiwoom_enrichment = _build_kiwoom_enrichment(
        latest_candidates, target_date=effective_as_of, config=config
    )
    latest_candidates = _apply_kiwoom_enrichment_to_candidates(
        latest_candidates, kiwoom_enrichment
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": effective_as_of,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": DECISION_AUTHORITY,
            "window_policy": "historical_rolling_signal_day_to_forward_horizon",
            "sample_floor": config.sample_floor,
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "valid_ohlc_liquidity_history_and_future_label_maturity",
            "forbidden_uses": FORBIDDEN_USES,
            "backtest_contract": {
                "decision_authority": DECISION_AUTHORITY,
                "runtime_effect": False,
                "broker_order_forbidden": True,
                "accounting": "closed_trade_compounded_slot_contribution",
                "forbidden_uses": FORBIDDEN_USES,
            },
        },
        "config": asdict(config),
        "primary_metrics": [
            "equal_weight_avg_profit_pct",
            "source_quality_adjusted_ev_pct",
            "portfolio_total_return_pct",
            "portfolio_max_drawdown_pct",
            "diagnostic_win_rate",
            "mfe_p80_pct",
            "mae_p10_pct",
        ],
        "summary": {
            "feature_rows": int(len(features)),
            "signal_rows": int(len(signals)),
            "label_rows": int(len(labels)),
            "latest_as_of_candidate_count": int(
                len(signals[signals["quote_date"].eq(pd.Timestamp(effective_as_of))])
                if not signals.empty
                else 0
            ),
            "primary_horizon_days": config.primary_horizon_days,
            "top_primary_entry_policy": (
                top_primary.get("entry_policy") if top_primary else None
            ),
            "top_primary_source_quality_adjusted_ev_pct": (
                top_primary.get("source_quality_adjusted_ev_pct")
                if top_primary
                else None
            ),
            "backtest_trade_count": backtest_summary.get("trade_count", 0),
            "backtest_total_return_pct": backtest_summary.get("total_return_pct"),
            "backtest_max_drawdown_pct": backtest_summary.get("max_drawdown_pct"),
        },
        "source_quality_summary": _source_quality_summary(
            raw_rows=int(len(raw)),
            feature_rows=int(len(features)),
            signals=signals,
            labels=labels,
            config=config,
        ),
        "entry_policy_comparison": entry_policy_comparison,
        "portfolio_backtest": portfolio_backtest,
        "portfolio_backtest_variants": backtest_variants,
        "kiwoom_enrichment": kiwoom_enrichment,
        "feature_bucket_ev_tables": feature_bucket_ev_tables,
        "representative_historical_examples": examples[:100],
        "latest_as_of_research_only_candidates": latest_candidates,
        "scannerization_path": {
            "v1_status": "research_only",
            "v2_next_step": "convert statistically surviving feature buckets into a postclose scanner after review",
            "approval_required_before_live_use": True,
            "loose_coupling_recommendation": {
                "producer": "bottom_rebound_pattern_research",
                "artifact": "data/report/bottom_rebound_pattern_research/bottom_rebound_pattern_research_YYYY-MM-DD.json",
                "consumer": "future swing_bottom_rebound_candidate_source",
                "handoff_mode": "postclose file artifact only",
                "runtime_effect": False,
                "first_integration_stage": "swing dry-run candidate enrichment",
                "forbidden_direct_connections": [
                    "recommendation_history mutation",
                    "broker order submit",
                    "threshold env apply",
                    "bot restart",
                ],
            },
        },
        "warnings": [],
    }
    if labels.empty:
        report["warnings"].append("no_labels_built")
    if top_primary is None:
        report["warnings"].append("primary_sample_floor_not_met")
    if kiwoom_enrichment.get("warnings"):
        report["warnings"].extend(
            f"kiwoom:{warning}" for warning in kiwoom_enrichment.get("warnings") or []
        )
    return report


def build_research_report(
    *,
    db_url: str | None = None,
    config: ResearchConfig | None = None,
) -> dict[str, Any]:
    config = config or ResearchConfig()
    db_url = db_url or os.getenv("DATABASE_URL") or POSTGRES_URL
    raw, effective_as_of, effective_start = _load_quote_frame(
        db_url,
        as_of=config.as_of,
        history_start=config.history_start,
    )
    effective_config = ResearchConfig(
        **{**asdict(config), "as_of": effective_as_of, "history_start": effective_start}
    )
    return build_research_report_from_frame(raw, effective_config)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    contract = (
        report.get("metric_contract")
        if isinstance(report.get("metric_contract"), dict)
        else {}
    )
    backtest = (
        report.get("portfolio_backtest")
        if isinstance(report.get("portfolio_backtest"), dict)
        else {}
    )
    backtest_summary = (
        backtest.get("summary") if isinstance(backtest.get("summary"), dict) else {}
    )
    backtest_config = (
        backtest.get("config") if isinstance(backtest.get("config"), dict) else {}
    )
    kiwoom_enrichment = (
        report.get("kiwoom_enrichment")
        if isinstance(report.get("kiwoom_enrichment"), dict)
        else {}
    )
    lines = [
        f"# Bottom Rebound Pattern Research - {report.get('date')}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- broker_order_forbidden: `{report.get('broker_order_forbidden')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- signal_rows: `{summary.get('signal_rows')}`",
        f"- label_rows: `{summary.get('label_rows')}`",
        f"- latest_as_of_candidate_count: `{summary.get('latest_as_of_candidate_count')}`",
        f"- top_primary_entry_policy: `{summary.get('top_primary_entry_policy') or '-'}`",
        f"- top_primary_source_quality_adjusted_ev_pct: `{summary.get('top_primary_source_quality_adjusted_ev_pct')}`",
        f"- backtest_trade_count: `{summary.get('backtest_trade_count')}`",
        f"- backtest_total_return_pct: `{summary.get('backtest_total_return_pct')}`",
        f"- backtest_max_drawdown_pct: `{summary.get('backtest_max_drawdown_pct')}`",
        f"- kiwoom_enrichment_enabled: `{kiwoom_enrichment.get('enabled')}`",
        f"- kiwoom_enrichment_mapped: `{kiwoom_enrichment.get('mapped_code_count')}` / `{kiwoom_enrichment.get('requested_code_count')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Contract",
        "",
        f"- metric_role: `{contract.get('metric_role')}`",
        f"- primary_decision_metric: `{contract.get('primary_decision_metric')}`",
        f"- sample_floor: `{contract.get('sample_floor')}`",
        f"- forbidden_uses: `{contract.get('forbidden_uses')}`",
        "",
        "## Entry Policy Comparison",
        "",
        "| entry_policy | horizon | sample | fill_rate | ev | adjusted_ev | win_rate | mae_p10 | mfe_p80 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in (report.get("entry_policy_comparison") or [])[:30]:
        lines.append(
            f"| `{row.get('entry_policy')}` | `{row.get('horizon_days')}` | `{row.get('sample_count')}` | "
            f"`{row.get('entry_fill_rate')}` | `{row.get('equal_weight_avg_profit_pct')}` | "
            f"`{row.get('source_quality_adjusted_ev_pct')}` | `{row.get('diagnostic_win_rate')}` | "
            f"`{row.get('mae_p10_pct')}` | `{row.get('mfe_p80_pct')}` |"
        )
    if not report.get("entry_policy_comparison"):
        lines.append("| - | - | 0 | - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Portfolio Backtest",
            "",
            f"- entry_policy: `{backtest_config.get('entry_policy')}`",
            f"- horizon_days: `{backtest_config.get('horizon_days')}`",
            f"- max_positions: `{backtest_config.get('max_positions')}`",
            f"- trade_cost_pct: `{backtest_config.get('trade_cost_pct')}`",
            f"- trade_count: `{backtest_summary.get('trade_count')}`",
            f"- total_return_pct: `{backtest_summary.get('total_return_pct')}`",
            f"- max_drawdown_pct: `{backtest_summary.get('max_drawdown_pct')}`",
            f"- diagnostic_win_rate: `{backtest_summary.get('diagnostic_win_rate')}`",
            f"- skipped_capacity_count: `{backtest_summary.get('skipped_capacity_count')}`",
            f"- skipped_same_symbol_count: `{backtest_summary.get('skipped_same_symbol_count')}`",
            "",
            "| year | portfolio_return_pct |",
            "| --- | ---: |",
        ]
    )
    for row in backtest.get("yearly_returns") or []:
        lines.append(f"| `{row.get('year')}` | `{row.get('portfolio_return_pct')}` |")
    if not backtest.get("yearly_returns"):
        lines.append("| - | - |")
    lines.extend(
        [
            "",
            "### Backtest Variants",
            "",
            "| variant | trades | total_return | max_drawdown | win_rate |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report.get("portfolio_backtest_variants") or []:
        item = row.get("summary") if isinstance(row.get("summary"), dict) else {}
        lines.append(
            f"| `{row.get('variant')}` | `{item.get('trade_count')}` | `{item.get('total_return_pct')}` | "
            f"`{item.get('max_drawdown_pct')}` | `{item.get('diagnostic_win_rate')}` |"
        )
    if not report.get("portfolio_backtest_variants"):
        lines.append("| - | - | - | - | - |")

    latest = report.get("latest_as_of_research_only_candidates") or []
    lines.extend(
        [
            "",
            "## Latest Research-Only Candidates",
            "",
            "| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |",
            "| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in latest[:20]:
        themes = (
            row.get("kiwoom_theme_tags")
            if isinstance(row.get("kiwoom_theme_tags"), list)
            else []
        )
        theme_text = ", ".join(str(item) for item in themes[:3])
        lines.append(
            f"| `{row.get('stock_code')}` | {row.get('stock_name') or ''} | `{row.get('close_price')}` | "
            f"{row.get('kiwoom_sector') or ''} | {theme_text} | "
            f"`{row.get('market_regime_bucket')}` | `{row.get('flow_combo_bucket')}` | "
            f"`{row.get('drawdown_high60_pct')}` | `{row.get('dist_low60_pct')}` | "
            f"`{row.get('volume_ratio20')}` | `{row.get('foreign_roll20_ratio')}` |"
        )
    if not latest:
        lines.append("| - | - | - | - | - | - | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.",
            "- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.",
            "- Scannerization requires a separate workorder and approval path.",
            "",
        ]
    )
    return "\n".join(lines)


def write_research_report(
    *,
    db_url: str | None = None,
    output_dir: Path = REPORT_DIR,
    config: ResearchConfig | None = None,
) -> dict[str, Path]:
    report = build_research_report(db_url=db_url, config=config)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(str(report.get("date")), output_dir)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--history-start", default=None)
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL") or POSTGRES_URL)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--min-price", type=float, default=ResearchConfig.min_price)
    parser.add_argument(
        "--min-median-value-20d-krw",
        type=float,
        default=ResearchConfig.min_median_value_20d_krw,
    )
    parser.add_argument(
        "--min-median-volume-20d",
        type=float,
        default=ResearchConfig.min_median_volume_20d,
    )
    parser.add_argument("--sample-floor", type=int, default=ResearchConfig.sample_floor)
    parser.add_argument(
        "--primary-horizon-days", type=int, default=ResearchConfig.primary_horizon_days
    )
    parser.add_argument(
        "--backtest-entry-policy",
        default=ResearchConfig.backtest_entry_policy,
        choices=ENTRY_POLICIES,
    )
    parser.add_argument(
        "--backtest-horizon-days",
        type=int,
        default=ResearchConfig.backtest_horizon_days,
        choices=HORIZONS,
    )
    parser.add_argument(
        "--backtest-max-positions",
        type=int,
        default=ResearchConfig.backtest_max_positions,
    )
    parser.add_argument(
        "--backtest-trade-cost-pct",
        type=float,
        default=ResearchConfig.backtest_trade_cost_pct,
    )
    parser.add_argument("--enable-kiwoom-enrichment", action="store_true")
    parser.add_argument(
        "--kiwoom-enrichment-max-codes",
        type=int,
        default=ResearchConfig.kiwoom_enrichment_max_codes,
    )
    parser.add_argument("--kiwoom-enrichment-write-cache", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    config = ResearchConfig(
        as_of=args.as_of,
        history_start=args.history_start,
        min_price=args.min_price,
        min_median_value_20d_krw=args.min_median_value_20d_krw,
        min_median_volume_20d=args.min_median_volume_20d,
        sample_floor=args.sample_floor,
        primary_horizon_days=args.primary_horizon_days,
        backtest_entry_policy=args.backtest_entry_policy,
        backtest_horizon_days=args.backtest_horizon_days,
        backtest_max_positions=args.backtest_max_positions,
        backtest_trade_cost_pct=args.backtest_trade_cost_pct,
        enable_kiwoom_enrichment=args.enable_kiwoom_enrichment,
        kiwoom_enrichment_max_codes=args.kiwoom_enrichment_max_codes,
        kiwoom_enrichment_write_cache=args.kiwoom_enrichment_write_cache
        and not args.no_write,
    )
    if args.no_write:
        report = build_research_report(db_url=args.db_url, config=config)
        print(
            json.dumps(
                {
                    "date": report.get("date"),
                    "summary": report.get("summary"),
                    "kiwoom_enrichment": report.get("kiwoom_enrichment"),
                    "warnings": report.get("warnings"),
                },
                ensure_ascii=False,
                default=str,
            )
        )
        return
    paths = write_research_report(
        db_url=args.db_url, output_dir=args.output_dir, config=config
    )
    print(
        f"[DONE] bottom_rebound_pattern_research json={paths['json']} md={paths['md']}"
    )


if __name__ == "__main__":
    main()
