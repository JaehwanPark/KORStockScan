"""Structured daily report builder for web/API/Flutter consumption."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.trade_profit import calculate_net_realized_pnl, get_trade_cost_rate
from src.market_regime import summarize_market_regime
from src.utils.constants import DATA_DIR, POSTGRES_URL, TRADING_RULES


REPORT_DIR = DATA_DIR / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_SCHEMA_VERSION = 3
DEFAULT_REALIZED_PNL_COST_RATE = 0.0023
_ENGINE_CACHE: dict[str, Any] = {}

_MODEL_XGB_FEATURES = [
    "daily_return",
    "ma_ratio",
    "macd",
    "macd_sig",
    "vwap",
    "obv",
    "up_trend_2d",
    "dist_ma5",
    "dual_net_buy",
    "foreign_net_roll5",
    "inst_net_roll5",
    "bbb",
    "bbp",
    "atr_ratio",
    "rsi",
]

_MODEL_LGBM_FEATURES = [
    "bbp",
    "rsi",
    "rsi_slope",
    "range_ratio",
    "vol_momentum",
    "vol_change",
    "atr",
    "bbb",
    "foreign_vol_ratio",
    "inst_vol_ratio",
    "margin_rate_change",
    "margin_rate_roll5",
]


@dataclass
class _ReportContext:
    warnings: list[str]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _safe_date_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def report_path_for_date(target_date: str) -> Path:
    return REPORT_DIR / f"report_{target_date}.json"


def load_saved_daily_report(target_date: str) -> dict | None:
    path = report_path_for_date(target_date)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    schema_version = _safe_int((payload.get("meta") or {}).get("schema_version"))
    if schema_version != REPORT_SCHEMA_VERSION:
        return None
    return payload


def save_daily_report(report: dict) -> Path:
    target_date = str(report.get("date") or datetime.now().strftime("%Y-%m-%d"))
    path = report_path_for_date(target_date)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return path


def _parse_target_date(target_date: str | None) -> str:
    if not target_date:
        return datetime.now().strftime("%Y-%m-%d")
    return str(target_date).strip()


def _import_sqlalchemy():
    from sqlalchemy import create_engine, text

    return create_engine, text


def _get_engine():
    create_engine, _ = _import_sqlalchemy()
    cache_key = str(POSTGRES_URL)
    if cache_key not in _ENGINE_CACHE:
        _ENGINE_CACHE[cache_key] = create_engine(POSTGRES_URL, pool_pre_ping=True)
    return _ENGINE_CACHE[cache_key]


def _fetch_recent_db_dates(limit: int = 30) -> list[str]:
    try:
        _, text = _import_sqlalchemy()
        engine = _get_engine()
    except Exception:
        return []

    candidates: set[str] = set()
    with engine.connect() as conn:
        quote_rows = conn.execute(
            text(
                """
                SELECT quote_date
                FROM daily_stock_quotes
                GROUP BY quote_date
                ORDER BY quote_date DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).fetchall()
        rec_rows = conn.execute(
            text(
                """
                SELECT rec_date
                FROM recommendation_history
                GROUP BY rec_date
                ORDER BY rec_date DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).fetchall()

    for row in quote_rows:
        candidates.add(_safe_date_string(row[0]))
    for row in rec_rows:
        candidates.add(_safe_date_string(row[0]))
    return sorted((item for item in candidates if item), reverse=True)


def list_available_report_dates(limit: int = 30) -> list[str]:
    file_dates = {
        path.stem.replace("report_", "")
        for path in REPORT_DIR.glob("report_*.json")
        if path.is_file()
    }
    db_dates = set(_fetch_recent_db_dates(limit=limit))
    dates = sorted((item for item in (file_dates | db_dates) if item), reverse=True)
    return dates[:limit]


def _resolve_quote_date(target_date: str, ctx: _ReportContext) -> str:
    try:
        _, text = _import_sqlalchemy()
        engine = _get_engine()
        with engine.connect() as conn:
            quote_date = conn.execute(
                text(
                    """
                    SELECT MAX(quote_date)
                    FROM daily_stock_quotes
                    WHERE quote_date <= :target_date
                    """
                ),
                {"target_date": target_date},
            ).scalar()
    except Exception as exc:
        ctx.warnings.append(f"시세 기준일 조회 실패: {exc}")
        return target_date

    resolved = _safe_date_string(quote_date) or target_date
    if resolved != target_date:
        ctx.warnings.append(f"요청일 {target_date} 대신 최근 시세일 {resolved} 기준으로 리포트를 생성했습니다.")
    return resolved


def _build_market_snapshot(target_date: str, ctx: _ReportContext) -> dict:
    snapshot = {
        "quote_date": target_date,
        "model_ready": False,
        "total_valid": 0,
        "above_20ma_count": 0,
        "ma20_ratio": 0.0,
        "avg_rsi": 0.0,
        "avg_prob": 0.0,
        "avg_bull": 0.0,
        "status_text": "데이터 부족",
        "status_tone": "muted",
        "dashboard": "시장 스냅샷을 불러오지 못했습니다.",
        "psychology": "데이터 부족으로 심리 분석을 생략합니다.",
        "strategy": "리포트 데이터가 안정화될 때까지 보수적으로 대응하십시오.",
        "stocks": [],
    }

    try:
        import pandas as pd
        import numpy as np
        import joblib
        from src.utils import kiwoom_utils
        from src.model.common_v2 import calculate_all_features
        _, text = _import_sqlalchemy()
        engine = _get_engine()
    except Exception as exc:
        ctx.warnings.append(f"시장 진단 모델 로드 실패: {exc}")
        return snapshot

    try:
        quote_date = _resolve_quote_date(target_date, ctx)
        snapshot["quote_date"] = quote_date

        targets = pd.read_sql(
            text(
                """
                SELECT stock_code, stock_name, marcap, close_price, ma20, rsi
                FROM daily_stock_quotes
                WHERE quote_date = :quote_date
                ORDER BY marcap DESC NULLS LAST
                LIMIT 150
                """
            ),
            engine,
            params={"quote_date": quote_date},
        )

        if targets.empty:
            ctx.warnings.append("일봉 대상 종목이 없어 시장 진단을 생략했습니다.")
            return snapshot

        target_codes = [
            str(value).strip().zfill(6)
            for value in targets.get("stock_code", pd.Series(dtype=object)).dropna().tolist()
            if str(value).strip()
        ]
        history_by_code: dict[str, Any] = {}
        if target_codes:
            try:
                history_rows = pd.read_sql(
                    text(
                        """
                        SELECT *
                        FROM daily_stock_quotes
                        WHERE stock_code = ANY(:codes)
                          AND quote_date <= :quote_date
                        ORDER BY stock_code ASC, quote_date DESC
                        """
                    ),
                    engine,
                    params={"codes": target_codes, "quote_date": quote_date},
                )
                if not history_rows.empty:
                    history_rows["stock_code"] = history_rows["stock_code"].astype(str).str.zfill(6)
                    history_rows = history_rows.groupby("stock_code", sort=False).head(60)
                    history_by_code = {
                        str(code).zfill(6): group.sort_values("quote_date").reset_index(drop=True)
                        for code, group in history_rows.groupby("stock_code", sort=False)
                    }
            except Exception as exc:
                ctx.warnings.append(f"시장 진단 일봉 history bulk 조회 실패: {exc}")

        model_paths = {
            "m_xgb": DATA_DIR / "hybrid_xgb_model.pkl",
            "m_lgbm": DATA_DIR / "hybrid_lgbm_model.pkl",
            "b_xgb": DATA_DIR / "bull_xgb_model.pkl",
            "b_lgbm": DATA_DIR / "bull_lgbm_model.pkl",
            "meta": DATA_DIR / "stacking_meta_model.pkl",
        }
        models = {key: joblib.load(path) for key, path in model_paths.items()}
        snapshot["model_ready"] = True

        total_valid = 0
        above_20ma_count = 0
        avg_rsi_sum = 0.0
        avg_prob_sum = 0.0
        avg_bull_sum = 0.0
        stocks: list[dict[str, Any]] = []
        rename_map = {
            "Return": "daily_return",
            "MA_Ratio": "ma_ratio",
            "MACD": "macd",
            "MACD_Sig": "macd_sig",
            "VWAP": "vwap",
            "OBV": "obv",
            "Up_Trend_2D": "up_trend_2d",
            "Dist_MA5": "dist_ma5",
            "Dual_Net_Buy": "dual_net_buy",
            "Foreign_Net_Roll5": "foreign_net_roll5",
            "Inst_Net_Roll5": "inst_net_roll5",
            "BB_Width": "bbb",
            "BBB": "bbb",
            "BB_Pos": "bbp",
            "BBP": "bbp",
            "ATR_Ratio": "atr_ratio",
            "RSI": "rsi",
            "RSI_Slope": "rsi_slope",
            "Range_Ratio": "range_ratio",
            "Vol_Momentum": "vol_momentum",
            "Vol_Change": "vol_change",
            "ATR": "atr",
            "Foreign_Vol_Ratio": "foreign_vol_ratio",
            "Inst_Vol_Ratio": "inst_vol_ratio",
            "Margin_Rate_Change": "margin_rate_change",
            "Margin_Rate_Roll5": "margin_rate_roll5",
            "Foreign_Net_Accel": "foreign_net_accel",
            "Inst_Net_Accel": "inst_net_accel",
        }

        for _, row in targets.iterrows():
            code = str(row.get("stock_code", "")).strip().zfill(6)
            name = str(row.get("stock_name", "") or code)
            curr_p = _safe_float(row.get("close_price"))
            ma20 = _safe_float(row.get("ma20"))

            if not code or curr_p <= 0:
                continue

            try:
                if not kiwoom_utils.is_valid_stock(code, name, current_price=int(curr_p)):
                    continue
            except Exception:
                pass

            history = history_by_code.get(code, pd.DataFrame())
            if history.empty and not history_by_code:
                history = pd.read_sql(
                    text(
                        """
                        SELECT *
                        FROM daily_stock_quotes
                        WHERE stock_code = :code
                          AND quote_date <= :quote_date
                        ORDER BY quote_date DESC
                        LIMIT 60
                        """
                    ),
                    engine,
                    params={"code": code, "quote_date": quote_date},
                )
                if not history.empty:
                    history = history.sort_values("quote_date").reset_index(drop=True)
            if history.empty or len(history) < 30:
                continue

            total_valid += 1
            is_above_20ma = curr_p > ma20 if ma20 > 0 else False
            if is_above_20ma:
                above_20ma_count += 1

            for col in ("retail_net", "foreign_net", "inst_net", "margin_rate"):
                if col not in history.columns:
                    history[col] = 0.0

            feat = calculate_all_features(history)
            feat = feat.rename(columns={src: dst for src, dst in rename_map.items() if src in feat.columns})
            latest = feat.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
            for feature_name in _MODEL_XGB_FEATURES + _MODEL_LGBM_FEATURES + [
                "foreign_net_roll5",
                "inst_net_roll5",
                "foreign_net_accel",
                "inst_net_accel",
                "rsi",
            ]:
                if feature_name not in latest.columns:
                    latest[feature_name] = 0.0

            avg_rsi_sum += _safe_float(latest["rsi"].values[0])

            p_xgb = float(models["m_xgb"].predict_proba(latest[_MODEL_XGB_FEATURES])[0][1])
            p_lgb = float(models["m_lgbm"].predict_proba(latest[_MODEL_LGBM_FEATURES])[0][1])
            p_bxgb = float(models["b_xgb"].predict_proba(latest[_MODEL_XGB_FEATURES])[0][1])
            p_blgb = float(models["b_lgbm"].predict_proba(latest[_MODEL_LGBM_FEATURES])[0][1])
            p_final = float(
                models["meta"].predict_proba(
                    pd.DataFrame(
                        [[p_xgb, p_lgb, p_bxgb, p_blgb]],
                        columns=["XGB_Prob", "LGBM_Prob", "Bull_XGB_Prob", "Bull_LGBM_Prob"],
                    )
                )[0][1]
            )

            avg_prob_sum += p_final
            avg_bull_sum += (p_bxgb + p_blgb) / 2

            foreign_roll = _safe_float(latest.get("foreign_net_roll5", pd.Series([0])).values[0])
            inst_roll = _safe_float(latest.get("inst_net_roll5", pd.Series([0])).values[0])
            foreign_accel = _safe_float(latest.get("foreign_net_accel", pd.Series([0])).values[0])
            inst_accel = _safe_float(latest.get("inst_net_accel", pd.Series([0])).values[0])
            is_for_buy = foreign_roll > 0 and foreign_accel > 0
            is_inst_buy = inst_roll > 0 and inst_accel > 0
            qualifies = p_final >= TRADING_RULES.PROB_MAIN_PICK and (is_for_buy or is_inst_buy)

            stocks.append(
                {
                    "code": code,
                    "name": name,
                    "price": int(curr_p),
                    "price_text": f"{int(curr_p):,}원",
                    "ma20_state": "정배열" if is_above_20ma else "역배열",
                    "ma20_icon": "🟢" if is_above_20ma else "🔴",
                    "ai_prob": round(p_final * 100, 1),
                    "ai_prob_text": f"{p_final:.1%}",
                    "ai_details": {
                        "hybrid_xgb": round(p_xgb * 100, 1),
                        "hybrid_lgbm": round(p_lgb * 100, 1),
                        "bull_xgb": round(p_bxgb * 100, 1),
                        "bull_lgbm": round(p_blgb * 100, 1),
                    },
                    "supply": {
                        "foreign": "양호" if is_for_buy else "이탈",
                        "institution": "양호" if is_inst_buy else "이탈",
                    },
                    "result": "합격" if qualifies else ("수급 부재" if p_final >= TRADING_RULES.PROB_MAIN_PICK else "점수 미달"),
                    "result_tone": "good" if qualifies else ("warn" if p_final >= TRADING_RULES.PROB_MAIN_PICK else "bad"),
                }
            )

        snapshot["stocks"] = sorted(stocks, key=lambda item: item["ai_prob"], reverse=True)
        snapshot["total_valid"] = total_valid
        snapshot["above_20ma_count"] = above_20ma_count
        snapshot["ma20_ratio"] = round((above_20ma_count / total_valid * 100) if total_valid else 0.0, 1)
        snapshot["avg_rsi"] = round((avg_rsi_sum / total_valid) if total_valid else 0.0, 1)
        snapshot["avg_prob"] = round((avg_prob_sum / total_valid * 100) if total_valid else 0.0, 1)
        snapshot["avg_bull"] = round((avg_bull_sum / total_valid * 100) if total_valid else 0.0, 1)

        ma20_ratio = snapshot["ma20_ratio"]
        if ma20_ratio < 40:
            snapshot["status_text"] = "하락장"
            snapshot["status_tone"] = "bad"
            snapshot["dashboard"] = f"시총 상위 우량주 중 20일선 위에 있는 종목이 {ma20_ratio:.1f}%에 그칩니다."
            snapshot["psychology"] = (
                f"상승장 전용 모델 평균 확신도는 {snapshot['avg_bull']:.1f}%로 낮습니다. "
                "AI는 방어적 심리를 유지하는 구간으로 해석합니다."
            )
            snapshot["strategy"] = "현금 비중을 높이고, 반등 확인 전까지는 무리한 추격 매수를 피하는 편이 좋습니다."
        elif ma20_ratio >= 60:
            snapshot["status_text"] = "상승장"
            snapshot["status_tone"] = "good"
            snapshot["dashboard"] = f"시총 상위 우량주 중 20일선 위 종목 비율이 {ma20_ratio:.1f}%로 넓게 확산돼 있습니다."
            snapshot["psychology"] = (
                f"상승장 전용 모델 평균 확신도는 {snapshot['avg_bull']:.1f}%입니다. "
                "주도주 추세가 살아있는 환경으로 읽힙니다."
            )
            snapshot["strategy"] = "수급이 붙는 주도주 위주로 눌림목 스윙과 추세 추종을 병행하기 좋은 구간입니다."
        else:
            snapshot["status_text"] = "중립장"
            snapshot["status_tone"] = "warn"
            snapshot["dashboard"] = f"20일선 위 종목 비율은 {ma20_ratio:.1f}%로 애매한 중립 구간입니다."
            snapshot["psychology"] = "모델 시그널이 엇갈리는 횡보장에 가깝고, 공격과 방어를 병행해야 하는 흐름입니다."
            snapshot["strategy"] = "비중을 줄인 스캘핑이나 짧은 스윙으로 대응하면서 확실한 추세 종목만 선별하는 편이 좋습니다."

        _apply_cached_market_regime_label(snapshot, target_date)

    except Exception as exc:
        ctx.warnings.append(f"시장 진단 계산 실패: {exc}")

    return snapshot


def _estimate_realized_pnl(row: dict[str, Any]) -> float:
    buy_price = _safe_float(row.get("buy_price"))
    sell_price = _safe_float(row.get("sell_price"))
    qty = _safe_int(row.get("buy_qty"))
    profit_rate = _safe_float(row.get("profit_rate"))
    cost_rate = get_trade_cost_rate(
        _safe_float(
            getattr(TRADING_RULES, "REPORT_REALIZED_PNL_COST_RATE", getattr(TRADING_RULES, "TRADE_COST_RATE", DEFAULT_REALIZED_PNL_COST_RATE)),
            DEFAULT_REALIZED_PNL_COST_RATE,
        )
    )
    cost_basis = sell_price if sell_price > 0 else buy_price
    trading_cost = cost_basis * qty * cost_rate if cost_basis > 0 and qty > 0 else 0.0
    if buy_price > 0 and sell_price > 0 and qty > 0:
        return float(calculate_net_realized_pnl(buy_price, sell_price, qty, cost_rate=cost_rate))
    if buy_price > 0 and qty > 0:
        return (buy_price * qty * profit_rate / 100.0) - trading_cost
    return 0.0


def _load_cached_market_regime_summary(target_date: str) -> dict[str, Any] | None:
    cache_path = DATA_DIR / "cache" / "market_regime_snapshot.json"
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None

    cached_session_date = str(payload.get("cached_session_date") or payload.get("debug", {}).get("cached_session_date") or "")
    if cached_session_date != str(target_date or ""):
        return None

    summary = summarize_market_regime(payload.get("risk_state"))
    summary["allow_swing_entry"] = bool(payload.get("allow_swing_entry", False))
    summary["swing_score"] = _safe_int(payload.get("swing_score"))
    summary["swing_entry_recovery_gate_score"] = _safe_int(
        payload.get("swing_entry_recovery_gate_score", payload.get("swing_score"))
    )
    summary["market_regime_continuous_score"] = _safe_float(payload.get("market_regime_continuous_score"))
    summary["market_regime_continuous_label"] = str(payload.get("market_regime_continuous_label") or "")
    component_scores = payload.get("market_regime_component_scores", {})
    summary["market_regime_component_scores"] = component_scores if isinstance(component_scores, dict) else {}
    summary["market_regime_score_version"] = str(payload.get("market_regime_score_version") or "")
    summary["market_regime_source_quality"] = str(payload.get("market_regime_source_quality") or "")
    summary["cached_session_date"] = cached_session_date
    return summary


def _apply_cached_market_regime_label(snapshot: dict[str, Any], target_date: str) -> None:
    summary = _load_cached_market_regime_summary(target_date)
    if not summary:
        return
    risk_label = {
        "RISK_ON": "리스크온",
        "NEUTRAL": "리스크중립",
        "RISK_OFF": "리스크오프",
    }.get(str(summary["risk_state"]).upper(), "리스크 데이터 부족")
    snapshot["risk_status_text"] = risk_label
    snapshot["risk_status_tone"] = summary["status_tone"]
    snapshot["regime_code"] = summary["regime_code"]
    snapshot["risk_state"] = summary["risk_state"]
    snapshot["allow_swing_entry"] = bool(summary.get("allow_swing_entry", False))
    snapshot["swing_score"] = int(summary.get("swing_score", 0) or 0)
    snapshot["swing_entry_recovery_gate_score"] = int(summary.get("swing_entry_recovery_gate_score", 0) or 0)
    snapshot["market_regime_continuous_score"] = summary.get("market_regime_continuous_score")
    snapshot["market_regime_continuous_label"] = summary.get("market_regime_continuous_label")
    snapshot["market_regime_component_scores"] = summary.get("market_regime_component_scores") or {}
    snapshot["market_regime_score_version"] = summary.get("market_regime_score_version")
    snapshot["market_regime_source_quality"] = summary.get("market_regime_source_quality")
    snapshot["regime_source"] = "market_regime_cache"


def _trade_status(row: dict[str, Any]) -> str:
    return str(row.get("status") or "").upper()


def _is_completed_trade(row: dict[str, Any]) -> bool:
    return _trade_status(row) == "COMPLETED"


def _resolve_previous_trade_date(target_date: str, ctx: _ReportContext) -> str | None:
    try:
        _, text = _import_sqlalchemy()
        engine = _get_engine()
        with engine.connect() as conn:
            prev_date = conn.execute(
                text(
                    """
                    SELECT MAX(rec_date)
                    FROM recommendation_history
                    WHERE rec_date < :target_date
                    """
                ),
                {"target_date": target_date},
            ).scalar()
        return _safe_date_string(prev_date) or None
    except Exception as exc:
        ctx.warnings.append(f"직전 매매일 조회 실패: {exc}")
        return None


def _build_previous_day_performance(target_date: str, ctx: _ReportContext) -> dict:
    performance = {
        "date": None,
        "has_data": False,
        "summary": {
            "total_records": 0,
            "filled_records": 0,
            "completed_records": 0,
            "open_records": 0,
            "watching_records": 0,
            "expired_records": 0,
            "pending_buy_records": 0,
            "win_rate": 0.0,
            "avg_profit_rate": 0.0,
            "total_profit_rate": 0.0,
            "realized_pnl_krw": 0,
            "fill_rate": 0.0,
        },
        "strategy_breakdown": [],
        "top_winners": [],
        "top_losers": [],
        "insight": "직전 매매일 성적 데이터가 없습니다.",
    }

    prev_date = _resolve_previous_trade_date(target_date, ctx)
    performance["date"] = prev_date
    if not prev_date:
        return performance

    try:
        _, text = _import_sqlalchemy()
        engine = _get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        rec_date, stock_code, stock_name, status, strategy, trade_type,
                        buy_price, buy_qty, buy_time, sell_price, sell_time, profit_rate
                    FROM recommendation_history
                    WHERE rec_date = :rec_date
                    ORDER BY COALESCE(sell_time, buy_time) DESC NULLS LAST, stock_code
                    """
                ),
                {"rec_date": prev_date},
            ).mappings().all()
    except Exception as exc:
        ctx.warnings.append(f"직전 매매일 성적 조회 실패: {exc}")
        return performance

    if not rows:
        return performance

    items = [dict(row) for row in rows]
    total_records = len(items)
    filled = [
        row for row in items
        if row.get("buy_time") is not None or _safe_int(row.get("buy_qty")) > 0 or _trade_status(row) in {"BUY_ORDERED", "HOLDING", "SELL_ORDERED", "COMPLETED"}
    ]
    completed = [row for row in items if _is_completed_trade(row)]
    open_records = [row for row in items if _trade_status(row) in {"HOLDING", "SELL_ORDERED"}]
    watching_records = [row for row in items if _trade_status(row) == "WATCHING"]
    expired_records = [row for row in items if _trade_status(row) == "EXPIRED"]
    pending_buy = [row for row in items if _trade_status(row) == "BUY_ORDERED"]

    completed_rates = [_safe_float(row.get("profit_rate")) for row in completed]
    win_count = sum(1 for value in completed_rates if value > 0)
    avg_profit_rate = sum(completed_rates) / len(completed_rates) if completed_rates else 0.0
    total_profit_rate = sum(completed_rates) if completed_rates else 0.0
    realized_pnl = sum(_estimate_realized_pnl(row) for row in completed)

    strategy_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in items:
        strategy_map[str(row.get("strategy") or "UNKNOWN")].append(row)

    strategy_breakdown = []
    for strategy, strategy_rows in strategy_map.items():
        strat_completed = [row for row in strategy_rows if row in completed]
        strat_rates = [_safe_float(row.get("profit_rate")) for row in strat_completed]
        strat_wins = sum(1 for value in strat_rates if value > 0)
        strategy_breakdown.append(
            {
                "strategy": strategy,
                "total_records": len(strategy_rows),
                "completed_records": len(strat_completed),
                "open_records": sum(
                    1 for row in strategy_rows if str(row.get("status") or "") in {"HOLDING", "SELL_ORDERED"}
                ),
                "win_rate": round((strat_wins / len(strat_completed) * 100) if strat_completed else 0.0, 1),
                "avg_profit_rate": round((sum(strat_rates) / len(strat_rates)) if strat_rates else 0.0, 2),
                "realized_pnl_krw": int(round(sum(_estimate_realized_pnl(row) for row in strat_completed))),
            }
        )
    strategy_breakdown.sort(key=lambda item: (item["realized_pnl_krw"], item["avg_profit_rate"]), reverse=True)

    def _trade_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "code": str(row.get("stock_code") or ""),
            "name": str(row.get("stock_name") or ""),
            "strategy": str(row.get("strategy") or ""),
            "status": str(row.get("status") or ""),
            "profit_rate": round(_safe_float(row.get("profit_rate")), 2),
            "buy_price": _safe_float(row.get("buy_price")),
            "sell_price": _safe_float(row.get("sell_price")),
            "buy_qty": _safe_int(row.get("buy_qty")),
            "buy_time": str(row.get("buy_time") or ""),
            "sell_time": str(row.get("sell_time") or ""),
            "realized_pnl_krw": int(round(_estimate_realized_pnl(row))),
        }

    completed_sorted = sorted(completed, key=lambda row: _safe_float(row.get("profit_rate")), reverse=True)
    completed_sorted_asc = sorted(completed, key=lambda row: _safe_float(row.get("profit_rate")))
    top_winners = [_trade_row(row) for row in completed_sorted[:5]]
    top_losers = [_trade_row(row) for row in completed_sorted_asc[:5]]

    performance["has_data"] = True
    performance["summary"] = {
        "total_records": total_records,
        "filled_records": len(filled),
        "completed_records": len(completed),
        "open_records": len(open_records),
        "watching_records": len(watching_records),
        "expired_records": len(expired_records),
        "pending_buy_records": len(pending_buy),
        "win_rate": round((win_count / len(completed) * 100) if completed else 0.0, 1),
        "avg_profit_rate": round(avg_profit_rate, 2),
        "total_profit_rate": round(total_profit_rate, 2),
        "realized_pnl_krw": int(round(realized_pnl)),
        "fill_rate": round((len(filled) / total_records * 100) if total_records else 0.0, 1),
    }
    performance["strategy_breakdown"] = strategy_breakdown
    performance["top_winners"] = top_winners
    performance["top_losers"] = top_losers

    if performance["summary"]["completed_records"] == 0:
        performance["insight"] = "직전 매매일에는 아직 종료된 거래가 없어, 승률보다 미청산 보유 상태를 점검하는 편이 좋습니다."
    elif performance["summary"]["realized_pnl_krw"] > 0:
        performance["insight"] = (
            f"직전 매매일 실현손익은 {performance['summary']['realized_pnl_krw']:,}원, "
            f"승률은 {performance['summary']['win_rate']:.1f}%였습니다."
        )
    else:
        performance["insight"] = (
            f"직전 매매일 실현손익은 {performance['summary']['realized_pnl_krw']:,}원으로 약했습니다. "
            "손실 전략과 차단 게이트를 함께 점검해보는 편이 좋습니다."
        )

    return performance


def build_daily_report(target_date: str | None = None) -> dict:
    target_date = _parse_target_date(target_date)
    ctx = _ReportContext(warnings=[])

    market = _build_market_snapshot(target_date, ctx)
    performance = _build_previous_day_performance(target_date, ctx)

    status_text = market.get("status_text", "데이터 부족")
    tone_map = {
        "good": "text-success",
        "warn": "text-warning",
        "bad": "text-danger",
        "muted": "text-secondary",
    }

    top_candidates = (market.get("stocks") or [])[:25]
    qualified = [row for row in market.get("stocks", []) if row.get("result") == "합격"]

    report = {
        "date": target_date,
        "stats": {
            "quote_date": market.get("quote_date"),
            "ma20_ratio": market.get("ma20_ratio", 0.0),
            "avg_rsi": market.get("avg_rsi", 0.0),
            "avg_prob": market.get("avg_prob", 0.0),
            "avg_bull": market.get("avg_bull", 0.0),
            "total_valid": market.get("total_valid", 0),
            "qualified_count": len(qualified),
            "status_text": status_text,
            "color": tone_map.get(market.get("status_tone", "muted"), "text-secondary"),
            "tone": market.get("status_tone", "muted"),
            "risk_status_text": market.get("risk_status_text"),
            "risk_status_tone": market.get("risk_status_tone"),
            "risk_state": market.get("risk_state"),
            "regime_code": market.get("regime_code"),
            "allow_swing_entry": market.get("allow_swing_entry"),
            "swing_score": market.get("swing_score"),
            "swing_entry_recovery_gate_score": market.get("swing_entry_recovery_gate_score"),
            "market_regime_continuous_score": market.get("market_regime_continuous_score"),
            "market_regime_continuous_label": market.get("market_regime_continuous_label"),
            "market_regime_component_scores": market.get("market_regime_component_scores"),
            "market_regime_score_version": market.get("market_regime_score_version"),
            "market_regime_source_quality": market.get("market_regime_source_quality"),
            "regime_source": market.get("regime_source"),
        },
        "insights": {
            "dashboard": market.get("dashboard", ""),
            "psychology": market.get("psychology", ""),
            "strategy": market.get("strategy", ""),
            "execution_feedback": performance.get("insight", ""),
        },
        "performance": performance,
        "stocks": top_candidates,
        "sections": {
            "qualified_stocks": qualified[:10],
            "top_winners": performance.get("top_winners", []),
            "top_losers": performance.get("top_losers", []),
            "strategy_breakdown": performance.get("strategy_breakdown", []),
        },
        "meta": {
            "schema_version": REPORT_SCHEMA_VERSION,
            "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "warnings": ctx.warnings,
            "model_ready": bool(market.get("model_ready")),
            "report_path": str(report_path_for_date(target_date)),
        },
    }
    return report


def load_or_build_daily_report(target_date: str | None = None, *, refresh: bool = False) -> dict:
    target_date = _parse_target_date(target_date)
    if not refresh:
        loaded = load_saved_daily_report(target_date)
        if loaded:
            return loaded
    report = build_daily_report(target_date)
    save_daily_report(report)
    return report


def format_daily_report_summary(report: dict) -> str:
    stats = report.get("stats", {}) or {}
    perf = report.get("performance", {}) or {}
    perf_summary = perf.get("summary", {}) or {}
    warnings = report.get("meta", {}).get("warnings", []) or []
    lines = [
        f"📘 Daily Report ({report.get('date', '')})",
        f"- 시장 상태: {stats.get('status_text', '-')}",
        f"- 20일선 위 비율: {stats.get('ma20_ratio', 0)}%",
        f"- 평균 RSI: {stats.get('avg_rsi', 0)}",
        f"- 평균 AI 확신도: {stats.get('avg_prob', 0)}%",
        f"- 직전 매매일: {perf.get('date') or '없음'}",
        f"- 종료 거래: {perf_summary.get('completed_records', 0)}건 / 승률 {perf_summary.get('win_rate', 0)}%",
        f"- 실현손익 추정: {perf_summary.get('realized_pnl_krw', 0):,}원",
        f"- 경고: {len(warnings)}건",
    ]
    if stats.get("risk_status_text"):
        lines.insert(5, f"- 매크로 리스크: {stats.get('risk_status_text')} ({stats.get('risk_state', 'UNKNOWN')})")
    if stats.get("market_regime_continuous_score") is not None:
        lines.insert(
            6,
            "- 시장 연속 점수: "
            f"{stats.get('market_regime_continuous_score')} "
            f"({stats.get('market_regime_continuous_label') or 'UNKNOWN'})",
        )
    return "\n".join(lines)
