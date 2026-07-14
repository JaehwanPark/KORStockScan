"""DB-first BD_FBUY_ACCUM_PRE_V1 candidate scanner.

This module is query/report-only. It does not create broker orders, runtime
approval artifacts, threshold env changes, provider route changes, or bot
restart signals.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from src.utils.constants import DATA_DIR, POSTGRES_URL, PROJECT_ROOT


SCHEMA_VERSION = "BD_FBUY_ACCUM_PRE_V1"
ARTIFACT_DIR = DATA_DIR / "runtime" / "bd_fbuy_accum_pre"
WS_SNAPSHOT_PATH = DATA_DIR / "runtime" / "kiwoom_ws_snapshot" / "latest.json"


@dataclass(frozen=True)
class ScannerThresholds:
    low20_min_pct: float = 0.0
    low20_max_pct: float = 8.0
    ma5_near_ratio: float = 0.995
    recent_low_tolerance_ratio: float = 0.995
    foreign_inflow_min_ratio: float = 0.10
    foreign_positive_streak_min: int = 2
    volume_ratio_min: float = 0.80
    volume_ratio_max: float = 1.50
    median_volume_floor: int = 50_000
    current_volume_floor: int = 50_000
    median_value_floor: int = 500_000_000
    current_value_floor: int = 500_000_000


@dataclass(frozen=True)
class ReboundExpansionThresholds:
    low20_min_pct: float = 8.0
    low20_max_pct: float = 40.0
    ma5_near_ratio: float = 0.995
    recent_low_tolerance_ratio: float = 0.995
    foreign_inflow_min_ratio: float = 0.10
    foreign_positive_streak_min: int = 2
    volume_ratio_min: float = 1.50
    volume_ratio_max: float = 3.50
    median_volume_floor: int = 50_000
    current_volume_floor: int = 100_000
    median_value_floor: int = 500_000_000
    current_value_floor: int = 1_000_000_000


def artifact_path(target_date: str | date | None = None) -> Path:
    d = _date_text(target_date)
    return ARTIFACT_DIR / f"{SCHEMA_VERSION}_{d}.json"


def _date_text(value: str | date | None = None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normal_stock_mask(names: pd.Series) -> pd.Series:
    pattern = (
        r"(?:우|우B|우C|스팩|SPAC|ETF|ETN|리츠|인버스|레버리지|선물|합성|채권|"
        r"액티브|KODEX|TIGER|KBSTAR|SOL|ACE|HANARO|ARIRANG|KOSEF|TIMEFOLIO)"
    )
    return ~names.fillna("").str.contains(pattern, regex=True)


def _liquidity_bucket(traded_value: float, median_value: float) -> str:
    floor = min(_safe_float(traded_value), _safe_float(median_value))
    if floor >= 5_000_000_000:
        return "liquid"
    if floor >= 1_000_000_000:
        return "valid"
    if floor >= 500_000_000:
        return "thin_valid"
    return "below_floor"


def _volume_bucket(vol_ratio: float) -> str:
    v = _safe_float(vol_ratio)
    if v < 0.80 or v > 1.50:
        return "excluded"
    if v < 1.00:
        return "normal"
    if v <= 1.30:
        return "active"
    return "expanded"


def _score_foreign_inflow(min_ratio: float) -> float:
    if min_ratio >= 0.30:
        return 1.50
    if min_ratio >= 0.20:
        return 1.20
    if min_ratio >= 0.15:
        return 0.90
    if min_ratio >= 0.10:
        return 0.60
    return 0.0


def _score_persistence(streak: int) -> float:
    if streak >= 5:
        return 1.00
    if streak >= 3:
        return 0.75
    if streak >= 2:
        return 0.50
    return 0.0


def _score_bottoming(dist_low20_pct: float) -> float:
    v = _safe_float(dist_low20_pct)
    if 0 <= v <= 3:
        return 1.00
    if v <= 5:
        return 0.75
    if v <= 8:
        return 0.50
    return 0.0


def _score_volume_quality(vol_ratio: float) -> float:
    v = _safe_float(vol_ratio)
    if 0.90 <= v <= 1.20:
        return 0.75
    if 0.80 <= v < 0.90 or 1.20 < v <= 1.30:
        return 0.60
    if 1.30 < v <= 1.50:
        return 0.40
    return 0.0


def _score_liquidity(traded_value: float, median_value: float) -> float:
    floor = min(_safe_float(traded_value), _safe_float(median_value))
    if floor >= 5_000_000_000:
        return 0.75
    if floor >= 1_000_000_000:
        return 0.55
    if floor >= 500_000_000:
        return 0.35
    return 0.0


def compute_star_scores(row: dict[str, Any], live: dict[str, Any] | None = None) -> dict[str, Any]:
    qty_ratio = _safe_float(row.get("foreign_qty_medvol20_ratio"))
    amt_ratio = _safe_float(row.get("foreign_amt_medvalue20_ratio"))
    min_inflow_ratio = min(qty_ratio, amt_ratio)
    vol_ratio = _safe_float(row.get("vol_med20_ratio"))
    traded_value = _safe_float(row.get("traded_value"))
    median_value = _safe_float(row.get("med_value20"))

    parts = {
        "foreign_inflow_score": _score_foreign_inflow(min_inflow_ratio),
        "foreign_persistence_score": _score_persistence(_safe_int(row.get("foreign_positive_streak"))),
        "bottoming_score": _score_bottoming(_safe_float(row.get("dist_low20_pct"))),
        "volume_quality_score": _score_volume_quality(vol_ratio),
        "liquidity_score": _score_liquidity(traded_value, median_value),
    }
    live_bonus = 0.0
    live_penalty = 0.0
    live = live or {}
    if _safe_int(live.get("today_foreign_broker_est_net_qty")) > 0:
        live_bonus += 0.25
    if bool(live.get("price_above_vwap")) and bool(live.get("spread_ok")):
        live_bonus += 0.10
    if bool(live.get("execution_strength_overheated")) or bool(live.get("spread_bad")):
        live_penalty += 0.25

    raw = sum(parts.values()) + live_bonus - live_penalty
    star_score = max(0.0, min(5.0, round(raw, 2)))
    return {
        **parts,
        "live_bonus": round(live_bonus, 2),
        "live_penalty": round(live_penalty, 2),
        "star_score": star_score,
        "star_display": _star_display(star_score),
    }


def _star_display(score: float) -> str:
    full = int(max(0, min(5, math.floor(float(score)))))
    return "★" * full + "☆" * (5 - full)


def _prepare_candidate_frame(df: pd.DataFrame, target_date: str | date | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    work["quote_date"] = pd.to_datetime(work["quote_date"], errors="coerce")
    for col in [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "ma5",
        "foreign_net",
    ]:
        work[col] = pd.to_numeric(work.get(col), errors="coerce")
    work = work.dropna(subset=["quote_date", "stock_code", "close_price"]).sort_values(
        ["stock_code", "quote_date"]
    )
    grouped = work.groupby("stock_code", group_keys=False)
    work["low20"] = grouped["low_price"].rolling(20, min_periods=20).min().reset_index(level=0, drop=True)
    work["med_vol20"] = grouped["volume"].rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    work["traded_value"] = work["close_price"] * work["volume"]
    work["med_value20"] = (
        grouped["traded_value"].rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    )
    work["prior_low5"] = (
        grouped["low_price"].rolling(5, min_periods=3).min().shift(1).reset_index(level=0, drop=True)
    )
    work["n60"] = grouped["foreign_net"].rolling(60, min_periods=20).count().reset_index(level=0, drop=True)
    work["foreign_net_prev1"] = grouped["foreign_net"].shift(1)
    positive = (work["foreign_net"] > 0).astype(int)
    work["foreign_positive_streak"] = positive.groupby(work["stock_code"]).transform(
        lambda s: s.groupby((s != s.shift()).cumsum()).cumsum()
    )
    latest_ts = pd.Timestamp(target_date) if target_date else work["quote_date"].max()
    current = work[work["quote_date"].eq(latest_ts)].copy()
    if current.empty and target_date:
        current = work[work["quote_date"].eq(work["quote_date"].max())].copy()
    current = current[_normal_stock_mask(current["stock_name"])]
    current = current[
        (current["low20"] > 0)
        & (current["ma5"] > 0)
        & (current["med_vol20"] > 0)
        & (current["med_value20"] > 0)
        & (current["n60"] >= 20)
    ].copy()
    current["dist_low20_pct"] = (current["close_price"] - current["low20"]) / current["low20"] * 100.0
    current["dist_ma5_pct"] = (current["close_price"] - current["ma5"]) / current["ma5"] * 100.0
    current["vol_med20_ratio"] = current["volume"] / current["med_vol20"]
    current["foreign_qty_medvol20_ratio"] = current["foreign_net"] / current["med_vol20"]
    current["foreign_amt_medvalue20_ratio"] = (
        current["foreign_net"] * current["close_price"] / current["med_value20"]
    )
    return current


def filter_pass_candidates(frame: pd.DataFrame, thresholds: ScannerThresholds | None = None) -> pd.DataFrame:
    thresholds = thresholds or ScannerThresholds()
    if frame.empty:
        return frame.copy()
    mask = (
        frame["dist_low20_pct"].between(thresholds.low20_min_pct, thresholds.low20_max_pct)
        & (frame["close_price"] >= frame["ma5"] * thresholds.ma5_near_ratio)
        & (frame["low_price"] >= frame["prior_low5"] * thresholds.recent_low_tolerance_ratio)
        & (frame["foreign_positive_streak"] >= thresholds.foreign_positive_streak_min)
        & (frame["foreign_qty_medvol20_ratio"] >= thresholds.foreign_inflow_min_ratio)
        & (frame["foreign_amt_medvalue20_ratio"] >= thresholds.foreign_inflow_min_ratio)
        & (frame["vol_med20_ratio"] >= thresholds.volume_ratio_min)
        & (frame["vol_med20_ratio"] <= thresholds.volume_ratio_max)
        & (frame["med_vol20"] >= thresholds.median_volume_floor)
        & (frame["volume"] >= thresholds.current_volume_floor)
        & (frame["med_value20"] >= thresholds.median_value_floor)
        & (frame["traded_value"] >= thresholds.current_value_floor)
    )
    return frame[mask].copy()


def filter_rebound_expansion_candidates(
    frame: pd.DataFrame,
    thresholds: ReboundExpansionThresholds | None = None,
) -> pd.DataFrame:
    thresholds = thresholds or ReboundExpansionThresholds()
    if frame.empty:
        return frame.copy()
    mask = (
        frame["dist_low20_pct"].between(thresholds.low20_min_pct, thresholds.low20_max_pct)
        & (frame["close_price"] >= frame["ma5"] * thresholds.ma5_near_ratio)
        & (frame["low_price"] >= frame["prior_low5"] * thresholds.recent_low_tolerance_ratio)
        & (frame["foreign_positive_streak"] >= thresholds.foreign_positive_streak_min)
        & (frame["foreign_qty_medvol20_ratio"] >= thresholds.foreign_inflow_min_ratio)
        & (frame["foreign_amt_medvalue20_ratio"] >= thresholds.foreign_inflow_min_ratio)
        & (frame["vol_med20_ratio"] >= thresholds.volume_ratio_min)
        & (frame["vol_med20_ratio"] <= thresholds.volume_ratio_max)
        & (frame["med_vol20"] >= thresholds.median_volume_floor)
        & (frame["volume"] >= thresholds.current_volume_floor)
        & (frame["med_value20"] >= thresholds.median_value_floor)
        & (frame["traded_value"] >= thresholds.current_value_floor)
    )
    return frame[mask].copy()


def compute_rebound_expansion_scores(row: dict[str, Any], live: dict[str, Any] | None = None) -> dict[str, Any]:
    qty_ratio = _safe_float(row.get("foreign_qty_medvol20_ratio"))
    amt_ratio = _safe_float(row.get("foreign_amt_medvalue20_ratio"))
    min_inflow_ratio = min(qty_ratio, amt_ratio)
    dist_low20_pct = _safe_float(row.get("dist_low20_pct"))
    vol_ratio = _safe_float(row.get("vol_med20_ratio"))
    traded_value = _safe_float(row.get("traded_value"))
    median_value = _safe_float(row.get("med_value20"))

    rebound_position_score = 1.0 if 8 <= dist_low20_pct <= 18 else 0.75 if dist_low20_pct <= 28 else 0.45
    volume_expansion_score = 0.75 if 1.50 <= vol_ratio <= 2.20 else 0.55 if vol_ratio <= 2.80 else 0.35
    parts = {
        "foreign_inflow_score": _score_foreign_inflow(min_inflow_ratio),
        "foreign_persistence_score": _score_persistence(_safe_int(row.get("foreign_positive_streak"))),
        "rebound_position_score": rebound_position_score,
        "volume_expansion_score": volume_expansion_score,
        "liquidity_score": _score_liquidity(traded_value, median_value),
    }
    live_bonus = 0.0
    live_penalty = 0.0
    live = live or {}
    if _safe_int(live.get("today_foreign_broker_est_net_qty")) > 0:
        live_bonus += 0.25
    if bool(live.get("price_above_vwap")) and bool(live.get("spread_ok")):
        live_bonus += 0.10
    if bool(live.get("execution_strength_overheated")) or bool(live.get("spread_bad")):
        live_penalty += 0.25
    raw = sum(parts.values()) + live_bonus - live_penalty
    star_score = max(0.0, min(5.0, round(raw, 2)))
    return {
        **parts,
        "live_bonus": round(live_bonus, 2),
        "live_penalty": round(live_penalty, 2),
        "star_score": star_score,
        "star_display": _star_display(star_score),
    }


def _load_daily_quotes(db_url: str, target_date: str, lookback_days: int = 90) -> tuple[pd.DataFrame, str]:
    engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        latest_db_date = conn.execute(text("SELECT max(quote_date) FROM daily_stock_quotes")).scalar()
        anchor = min(pd.Timestamp(target_date).date(), latest_db_date) if target_date else latest_db_date
        df = pd.read_sql(
            text(
                """
                SELECT quote_date, stock_code, stock_name, open_price, high_price, low_price,
                       close_price, volume, ma5, foreign_net
                FROM daily_stock_quotes
                WHERE quote_date >= :start
                  AND quote_date <= :anchor
                  AND close_price IS NOT NULL
                  AND close_price > 0
                  AND stock_code ~ '^[0-9]{6}$'
                """
            ),
            conn,
            params={"start": pd.Timestamp(anchor) - pd.Timedelta(days=lookback_days), "anchor": anchor},
        )
    return df, str(anchor)


def _load_ws_snapshot() -> dict[str, Any]:
    try:
        payload = json.loads(WS_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def _ws_live_for_code(code: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    stocks = snapshot.get("stocks") if isinstance(snapshot, dict) else {}
    row = stocks.get(str(code)) if isinstance(stocks, dict) else None
    if not isinstance(row, dict):
        return {
            "source": "ws_snapshot",
            "source_quality": "missing_ws_snapshot",
            "today_foreign_broker_est_net_qty": 0,
        }
    now_ts = time.time()
    age_sec = max(0.0, now_ts - _safe_float(row.get("last_foreign_broker_update_ts"), 0.0))
    source_quality = "ok" if age_sec <= 180 else "stale_ws_snapshot"
    best_ask = _safe_float(row.get("best_ask"))
    best_bid = _safe_float(row.get("best_bid"))
    spread_bps = ((best_ask - best_bid) / best_bid * 10000.0) if best_ask > 0 and best_bid > 0 else 0.0
    return {
        "source": "ws_snapshot",
        "source_quality": source_quality,
        "today_foreign_broker_est_net_qty": _safe_int(row.get("foreign_broker_net_est_qty")),
        "foreign_broker_est_delta_qty": _safe_int(row.get("foreign_broker_net_est_delta_qty")),
        "ws_age_sec": round(age_sec, 1),
        "curr": _safe_int(row.get("curr")),
        "best_bid": _safe_int(best_bid),
        "best_ask": _safe_int(best_ask),
        "spread_bps": round(spread_bps, 2),
        "spread_ok": bool(spread_bps and spread_bps <= 80.0),
        "spread_bad": bool(spread_bps and spread_bps > 150.0),
    }


def _daily_db_foreign_fallback(row: dict[str, Any]) -> dict[str, Any]:
    foreign_net = _safe_int(row.get("foreign_net"))
    return {
        "source": "daily_stock_quotes",
        "source_quality": "daily_db_fallback",
        "source_note": "WS 0F foreign-broker estimate unavailable; using latest daily_stock_quotes.foreign_net as reference.",
        "today_foreign_broker_est_net_qty": foreign_net,
        "daily_foreign_net_qty": foreign_net,
        "quote_date": row.get("quote_date"),
    }


def _resolve_live_for_row(row: dict[str, Any], snapshot: dict[str, Any], *, allow_db_fallback: bool = False) -> dict[str, Any]:
    code = str(row.get("stock_code") or "")
    live = _ws_live_for_code(code, snapshot)
    if not allow_db_fallback:
        return live
    if live.get("source_quality") not in {"missing_ws_snapshot", "stale_ws_snapshot"}:
        return live
    fallback = _daily_db_foreign_fallback(row)
    fallback["fallback_from_source_quality"] = live.get("source_quality")
    return {**live, **fallback}


def _apply_live_confirmation(candidates: list[dict[str, Any]], live_intraday: bool = False) -> list[dict[str, Any]]:
    ws_snapshot = _load_ws_snapshot()
    for row in candidates:
        live = _resolve_live_for_row(row, ws_snapshot, allow_db_fallback=live_intraday)
        row["live_confirmation"] = live
        score = compute_star_scores(row, live if live_intraday else {})
        row.update(score)
        row["live_confirmed"] = _safe_int(live.get("today_foreign_broker_est_net_qty")) > 0
    return candidates


def _apply_rebound_live_confirmation(candidates: list[dict[str, Any]], live_intraday: bool = False) -> list[dict[str, Any]]:
    ws_snapshot = _load_ws_snapshot()
    for row in candidates:
        live = _resolve_live_for_row(row, ws_snapshot, allow_db_fallback=live_intraday)
        row["live_confirmation"] = live
        score = compute_rebound_expansion_scores(row, live if live_intraday else {})
        row.update(score)
        row["live_confirmed"] = _safe_int(live.get("today_foreign_broker_est_net_qty")) > 0
    return candidates


def _history_rows(df: pd.DataFrame, code: str, limit: int = 20) -> dict[str, list[dict[str, Any]]]:
    hist = df[df["stock_code"].astype(str).eq(str(code))].copy().sort_values("quote_date").tail(limit)
    if hist.empty:
        return {"price": [], "volume": [], "foreign": []}
    price = []
    volume = []
    foreign = []
    hist["ma5_calc"] = hist["close_price"].rolling(5, min_periods=1).mean()
    hist["low20_calc"] = hist["low_price"].rolling(20, min_periods=1).min()
    hist["med_vol20_calc"] = hist["volume"].rolling(20, min_periods=1).median()
    for _, r in hist.iterrows():
        d = pd.Timestamp(r["quote_date"]).date().isoformat()
        price.append(
            {
                "date": d,
                "close": round(_safe_float(r["close_price"]), 2),
                "ma5": round(_safe_float(r["ma5_calc"]), 2),
                "low20": round(_safe_float(r["low20_calc"]), 2),
            }
        )
        volume.append(
            {
                "date": d,
                "volume": _safe_int(r["volume"]),
                "med_vol20": _safe_int(r["med_vol20_calc"]),
            }
        )
        foreign.append({"date": d, "foreign_net": _safe_int(r["foreign_net"])})
    return {"price": price, "volume": volume, "foreign": foreign}


def build_report(
    target_date: str | date | None = None,
    *,
    db_url: str | None = None,
    live_intraday: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    target = _date_text(target_date)
    db_url = db_url or os.getenv("DATABASE_URL", POSTGRES_URL)
    thresholds = ScannerThresholds()
    rebound_thresholds = ReboundExpansionThresholds()
    source_df, effective_date = _load_daily_quotes(db_url, target)
    candidate_frame = _prepare_candidate_frame(source_df, effective_date)
    pass_frame = filter_pass_candidates(candidate_frame, thresholds)
    rebound_frame = filter_rebound_expansion_candidates(candidate_frame, rebound_thresholds)
    candidates: list[dict[str, Any]] = []
    for _, r in pass_frame.iterrows():
        row = {
            "stock_code": str(r["stock_code"]),
            "stock_name": str(r.get("stock_name") or ""),
            "cohort": "bottom_accumulation",
            "cohort_title": "바닥다지기 + 적정 거래량 + 외인 유입 후보",
            "quote_date": pd.Timestamp(r["quote_date"]).date().isoformat(),
            "close_price": round(_safe_float(r["close_price"]), 2),
            "low20": round(_safe_float(r["low20"]), 2),
            "ma5": round(_safe_float(r["ma5"]), 2),
            "dist_low20_pct": round(_safe_float(r["dist_low20_pct"]), 4),
            "dist_ma5_pct": round(_safe_float(r["dist_ma5_pct"]), 4),
            "volume": _safe_int(r["volume"]),
            "med_vol20": _safe_int(r["med_vol20"]),
            "vol_med20_ratio": round(_safe_float(r["vol_med20_ratio"]), 4),
            "traded_value": _safe_int(r["traded_value"]),
            "med_value20": _safe_int(r["med_value20"]),
            "foreign_net": _safe_int(r["foreign_net"]),
            "foreign_net_prev1": _safe_int(r["foreign_net_prev1"]),
            "foreign_positive_streak": _safe_int(r["foreign_positive_streak"]),
            "foreign_qty_medvol20_ratio": round(_safe_float(r["foreign_qty_medvol20_ratio"]), 6),
            "foreign_amt_medvalue20_ratio": round(_safe_float(r["foreign_amt_medvalue20_ratio"]), 6),
            "volume_bucket": _volume_bucket(_safe_float(r["vol_med20_ratio"])),
            "liquidity_bucket": _liquidity_bucket(_safe_float(r["traded_value"]), _safe_float(r["med_value20"])),
            "history": _history_rows(source_df, str(r["stock_code"])),
        }
        row.update(compute_star_scores(row))
        candidates.append(row)
    _apply_live_confirmation(candidates, live_intraday=live_intraday)
    candidates.sort(
        key=lambda x: (
            _safe_float(x.get("star_score")),
            _safe_float(x.get("foreign_inflow_score")),
            _safe_float(x.get("liquidity_score")),
        ),
        reverse=True,
    )
    rebound_candidates: list[dict[str, Any]] = []
    for _, r in rebound_frame.iterrows():
        row = {
            "stock_code": str(r["stock_code"]),
            "stock_name": str(r.get("stock_name") or ""),
            "cohort": "rebound_expansion",
            "cohort_title": "이미 반등이 시작됐고 외인이 거래량을 동반해 따라붙는 후보",
            "quote_date": pd.Timestamp(r["quote_date"]).date().isoformat(),
            "close_price": round(_safe_float(r["close_price"]), 2),
            "low20": round(_safe_float(r["low20"]), 2),
            "ma5": round(_safe_float(r["ma5"]), 2),
            "dist_low20_pct": round(_safe_float(r["dist_low20_pct"]), 4),
            "dist_ma5_pct": round(_safe_float(r["dist_ma5_pct"]), 4),
            "volume": _safe_int(r["volume"]),
            "med_vol20": _safe_int(r["med_vol20"]),
            "vol_med20_ratio": round(_safe_float(r["vol_med20_ratio"]), 4),
            "traded_value": _safe_int(r["traded_value"]),
            "med_value20": _safe_int(r["med_value20"]),
            "foreign_net": _safe_int(r["foreign_net"]),
            "foreign_net_prev1": _safe_int(r["foreign_net_prev1"]),
            "foreign_positive_streak": _safe_int(r["foreign_positive_streak"]),
            "foreign_qty_medvol20_ratio": round(_safe_float(r["foreign_qty_medvol20_ratio"]), 6),
            "foreign_amt_medvalue20_ratio": round(_safe_float(r["foreign_amt_medvalue20_ratio"]), 6),
            "volume_bucket": _volume_bucket(_safe_float(r["vol_med20_ratio"])),
            "liquidity_bucket": _liquidity_bucket(_safe_float(r["traded_value"]), _safe_float(r["med_value20"])),
            "history": _history_rows(source_df, str(r["stock_code"])),
        }
        row.update(compute_rebound_expansion_scores(row))
        rebound_candidates.append(row)
    _apply_rebound_live_confirmation(rebound_candidates, live_intraday=live_intraday)
    rebound_candidates.sort(
        key=lambda x: (
            _safe_float(x.get("star_score")),
            _safe_float(x.get("foreign_inflow_score")),
            _safe_float(x.get("liquidity_score")),
        ),
        reverse=True,
    )
    source_quality_counts: dict[str, int] = {}
    for row in [*candidates, *rebound_candidates]:
        q = str((row.get("live_confirmation") or {}).get("source_quality") or "missing")
        source_quality_counts[q] = source_quality_counts.get(q, 0) + 1
    report = {
        "schema_version": SCHEMA_VERSION,
        "target_date": target,
        "effective_db_date": effective_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "decision_authority": "query_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "thresholds": thresholds.__dict__,
        "rebound_expansion_thresholds": rebound_thresholds.__dict__,
        "summary": {
            "db_source_rows": int(len(source_df)),
            "db_candidate_frame_rows": int(len(candidate_frame)),
            "db_pass_count": int(len(candidates)),
            "rebound_expansion_count": int(len(rebound_candidates)),
            "live_confirmed_count": int(sum(1 for row in candidates if row.get("live_confirmed"))),
            "rebound_live_confirmed_count": int(sum(1 for row in rebound_candidates if row.get("live_confirmed"))),
            "source_quality_counts": source_quality_counts,
            "refresh_cadence": "10min",
            "refresh_window": "09:05~15:20",
        },
        "forbidden_runtime_uses": [
            "broker_order",
            "threshold_env_mutation",
            "provider_route_change",
            "bot_restart",
            "runtime_approval_auto_apply",
        ],
        "candidates": candidates,
        "rebound_expansion_candidates": rebound_candidates,
    }
    if write:
        path = artifact_path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    return report


def load_or_build_report(
    target_date: str | date | None = None,
    *,
    refresh: bool = False,
    live_intraday: bool = False,
    db_url: str | None = None,
) -> dict[str, Any]:
    path = artifact_path(target_date)
    if live_intraday:
        refresh = True
    if not refresh and path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return build_report(target_date, db_url=db_url, live_intraday=live_intraday, write=True)


def _ws_snapshot_received_types(value: Any) -> list[str]:
    if isinstance(value, (set, list, tuple)):
        return sorted(str(item) for item in value if item is not None and str(item))
    if value is None:
        return []
    return [str(value)] if str(value) else []


def _ws_snapshot_realtime_type_ts(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, float] = {}
    for key, raw_ts in value.items():
        if key is None:
            continue
        ts = _safe_float(raw_ts, 0.0)
        if ts > 0 and math.isfinite(ts):
            result[str(key)] = ts
    return result


def _ws_snapshot_string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    for key, raw_value in value.items():
        if key is None or raw_value is None:
            continue
        text = str(raw_value).strip()
        if text:
            result[str(key)] = text
    return result


def _ws_snapshot_age_ms(ts: Any, now_ts: float) -> Any:
    ts_value = _safe_float(ts, 0.0)
    if ts_value <= 0 or not math.isfinite(ts_value):
        return "not_available_timestamp"
    return round(max(0.0, now_ts - ts_value) * 1000.0, 3)


def _ws_snapshot_last_trade_tick(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed_keys = {
        "ts",
        "price",
        "volume",
        "strength",
        "trade_time",
        "trade_ts",
        "source",
        "real_type",
    }
    result: dict[str, Any] = {}
    for key in allowed_keys:
        if key not in value:
            continue
        item = value.get(key)
        if isinstance(item, float) and not math.isfinite(item):
            continue
        if item is None or isinstance(item, (str, int, float, bool)):
            result[key] = item
    return result


def write_ws_snapshot(realtime_data: dict[str, Any], *, now_ts: float | None = None) -> Path | None:
    """Persist a read-only WS snapshot for dashboard and source-quality consumers."""
    now_ts = now_ts or time.time()
    stocks: dict[str, Any] = {}
    for code, row in (realtime_data or {}).items():
        if not isinstance(row, dict):
            continue
        orderbook = row.get("orderbook") if isinstance(row.get("orderbook"), dict) else {}
        asks = orderbook.get("asks") or []
        bids = orderbook.get("bids") or []
        best_ask = _safe_int((asks[0] or {}).get("price")) if asks else 0
        best_bid = _safe_int((bids[0] or {}).get("price")) if bids else 0
        realtime_type_ts = _ws_snapshot_realtime_type_ts(row.get("last_realtime_type_ts"))
        last_trade_tick = _ws_snapshot_last_trade_tick(row.get("last_trade_tick"))
        stocks[str(code)] = {
            "curr": _safe_int(row.get("curr")),
            "foreign_broker_net_est_qty": _safe_int(row.get("foreign_broker_net_est_qty")),
            "foreign_broker_net_est_delta_qty": _safe_int(row.get("foreign_broker_net_est_delta_qty")),
            "last_foreign_broker_update_ts": _safe_float(row.get("last_foreign_broker_update_ts")),
            "last_ws_update_ts": _safe_float(row.get("last_ws_update_ts")),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "received_types": _ws_snapshot_received_types(row.get("received_types")),
            "last_realtime_type_ts": realtime_type_ts,
            "last_ws_item": str(row.get("last_ws_item") or ""),
            "last_ws_market_suffix": str(row.get("last_ws_market_suffix") or ""),
            "last_ws_market_route": str(row.get("last_ws_market_route") or "unknown"),
            "last_realtime_type_item": _ws_snapshot_string_map(
                row.get("last_realtime_type_item")
            ),
            "last_realtime_type_market_suffix": _ws_snapshot_string_map(
                row.get("last_realtime_type_market_suffix")
            ),
            "last_realtime_type_market_route": _ws_snapshot_string_map(
                row.get("last_realtime_type_market_route")
            ),
            "market_session_state": str(row.get("market_session_state") or ""),
            "market_session_remaining": str(row.get("market_session_remaining") or ""),
            "last_realtime_type_ages_ms": {
                real_type: _ws_snapshot_age_ms(ts, now_ts) for real_type, ts in realtime_type_ts.items()
            },
            "last_0b_ts": realtime_type_ts.get("0B", 0.0),
            "last_0b_age_ms": _ws_snapshot_age_ms(realtime_type_ts.get("0B"), now_ts),
            "last_trade_tick": last_trade_tick,
            "last_trade_tick_age_ms": _ws_snapshot_age_ms(last_trade_tick.get("ts"), now_ts),
        }
    payload = {
        "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
        "generated_at_epoch": now_ts,
        "generated_at": datetime.fromtimestamp(now_ts).isoformat(timespec="seconds"),
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
        "stocks": stocks,
    }
    try:
        WS_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = WS_SNAPSHOT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(WS_SNAPSHOT_PATH)
        return WS_SNAPSHOT_PATH
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build BD_FBUY_ACCUM_PRE_V1 DB-first candidate artifact.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", POSTGRES_URL))
    parser.add_argument("--live-intraday", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, db_url=args.db_url, live_intraday=args.live_intraday, write=True)
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"[DONE] {SCHEMA_VERSION} target_date={args.target_date} "
            f"db_pass_count={report['summary']['db_pass_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
