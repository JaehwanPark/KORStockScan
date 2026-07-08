"""Swing strategy discovery simulator v1.

This module builds an aggressive sim-only swing exploration book. It is not a
real-order path and it intentionally stores rows outside recommendation_history.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from sqlalchemy import bindparam, create_engine, text, tuple_
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
)
from src.engine.swing_sector_theme_source import build_sector_theme_map
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema
from src.model.common_v2 import RECO_DIAGNOSTIC_PATH, RECO_PATH
from src.utils.constants import DATA_DIR, POSTGRES_URL, TRADING_RULES
from src.utils.jsonl_io import iter_jsonl


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_sim"
PIPELINE_EVENTS_DIR = Path(DATA_DIR) / "pipeline_events"
BOTTOM_REBOUND_SOURCE_DIR = Path(DATA_DIR) / "report" / "swing_bottom_rebound_candidate_source"
THRESHOLD_APPLY_PLAN_DIR = Path(DATA_DIR) / "threshold_cycle" / "apply_plans"

POLICY_VERSION = "swing_strategy_discovery_sim_v1"
LABEL_WEIGHT_POLICY_VERSION = "swing_lifecycle_ev_label_weight_policy_v1"
COMPOSITE_EV_POLICY_VERSION = "swing_lifecycle_composite_ev_policy_v1"
ARM_POLICY_VERSION = "bounded_8_arm_policy_v1"
BOTTOM_REBOUND_ARM_POLICY_VERSION = "bottom_rebound_anticipatory_3_arm_policy_v1"
DECISION_AUTHORITY = "swing_sim_exploration_only"
DEFAULT_MAX_DAILY_CANDIDATES = 50
ACTIVE_PRIORITY_MAX_DAILY_CANDIDATES = 80

ARM_ALLOCATION = {
    "lifecycle_rank": 0.60,
    "diversity_exploration": 0.30,
    "legacy_ml": 0.10,
}

DIVERSITY_BUCKET_FIELDS = ("position_tag", "block_reason", "volatility_bucket")
V2_REQUIRED_FIELDS = ("sector", "industry", "theme_tags", "theme_source")

ARM_SET = [
    {
        "arm_id": "arm01_next_open_equal_fixed5d",
        "entry_policy": "next_open_entry",
        "sizing_policy": "equal_notional",
        "exit_policy": "fixed_5d",
    },
    {
        "arm_id": "arm02_next_open_vol_fixed10d",
        "entry_policy": "next_open_entry",
        "sizing_policy": "volatility_adjusted",
        "exit_policy": "fixed_10d",
    },
    {
        "arm_id": "arm03_pullback_equal_fixed10d",
        "entry_policy": "pullback_limit_entry",
        "sizing_policy": "equal_notional",
        "exit_policy": "fixed_10d",
    },
    {
        "arm_id": "arm04_pullback_risk_mae_time",
        "entry_policy": "pullback_limit_entry",
        "sizing_policy": "risk_capped",
        "exit_policy": "mae_stop_time_stop",
    },
    {
        "arm_id": "arm05_breakout_conf_trailing",
        "entry_policy": "breakout_confirm_entry",
        "sizing_policy": "confidence_weighted",
        "exit_policy": "trailing_after_mfe",
    },
    {
        "arm_id": "arm06_gap_fade_risk_fixed5d",
        "entry_policy": "gap_fade_entry",
        "sizing_policy": "risk_capped",
        "exit_policy": "fixed_5d",
    },
    {
        "arm_id": "arm07_pullback_vol_scale_recovery",
        "entry_policy": "pullback_limit_entry",
        "sizing_policy": "volatility_adjusted",
        "exit_policy": "scale_in_recovery",
    },
    {
        "arm_id": "arm08_breakout_risk_mae_time",
        "entry_policy": "breakout_confirm_entry",
        "sizing_policy": "risk_capped",
        "exit_policy": "mae_stop_time_stop",
    },
]

BOTTOM_REBOUND_ARM_SET = [
    {
        "arm_id": "br_arm01_next_open_equal_fixed10d",
        "entry_policy": "bottom_rebound_next_open_entry",
        "sizing_policy": "equal_notional",
        "exit_policy": "fixed_10d",
    },
    {
        "arm_id": "br_arm02_signal_close_retest_limit_fixed10d",
        "entry_policy": "bottom_rebound_signal_close_retest_limit_entry",
        "sizing_policy": "risk_capped",
        "exit_policy": "fixed_10d",
    },
    {
        "arm_id": "br_arm03_atr_pullback_limit_mae_time",
        "entry_policy": "bottom_rebound_atr_pullback_limit_entry",
        "sizing_policy": "volatility_adjusted",
        "exit_policy": "mae_stop_time_stop",
    },
]


def _date_text(value: str | date | datetime | pd.Timestamp | None) -> str:
    if value is None:
        return str(pd.Timestamp.now(tz="Asia/Seoul").date())
    return str(pd.to_datetime(value).date())


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "") or pd.isna(value):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "") or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def _is_present(value: Any) -> bool:
    try:
        if value in (None, "") or pd.isna(value):
            return False
    except Exception:
        if value in (None, ""):
            return False
    text = str(value).strip().lower()
    if text in {"", "nan", "none", "null", "false", "0"}:
        return False
    return bool(value)


def _norm_code(value: Any) -> str:
    return str(value or "").replace(".0", "").strip().zfill(6)


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def _load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    if "code" in df.columns:
        df["code"] = df["code"].map(_norm_code)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    return df


def load_safe_pool_rows(
    target_date: str,
    *,
    diagnostic_path: str | Path = RECO_DIAGNOSTIC_PATH,
    recommendation_path: str | Path = RECO_PATH,
) -> pd.DataFrame:
    """Load the latest safe-pool rows at or before target_date."""
    target_ts = pd.to_datetime(target_date).normalize()
    df = _load_csv(diagnostic_path)
    if df.empty:
        df = _load_csv(recommendation_path)
    if df.empty:
        return df
    if "date" in df.columns:
        eligible_dates = df.loc[df["date"] <= target_ts, "date"].dropna()
        if eligible_dates.empty:
            return df.iloc[0:0].copy()
        df = df[df["date"] == eligible_dates.max()].copy()
    if "hybrid_mean" not in df.columns:
        df["hybrid_mean"] = pd.to_numeric(df.get("prob", 0), errors="coerce").fillna(0.0)
    if "meta_score" not in df.columns:
        df["meta_score"] = pd.to_numeric(df.get("score", 0), errors="coerce").fillna(0.0)
    if "floor_used" not in df.columns:
        df["floor_used"] = 0.0
    safe_mask = pd.to_numeric(df["hybrid_mean"], errors="coerce").fillna(0.0) >= pd.to_numeric(
        df["floor_used"], errors="coerce"
    ).fillna(0.0)
    if safe_mask.any():
        df = df[safe_mask].copy()
    return df.reset_index(drop=True)


def _bottom_rebound_source_path(target_date: str) -> Path:
    return BOTTOM_REBOUND_SOURCE_DIR / f"swing_bottom_rebound_candidate_source_{target_date}.json"


def load_bottom_rebound_source_rows(target_date: str, *, source_path: str | Path | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = Path(source_path) if source_path else _bottom_rebound_source_path(target_date)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return pd.DataFrame(), {"path": str(path), "status": "missing", "loaded_rows": 0}
    except Exception as exc:
        return pd.DataFrame(), {"path": str(path), "status": "invalid_json", "loaded_rows": 0, "error": str(exc)}
    if not isinstance(payload, dict):
        return pd.DataFrame(), {"path": str(path), "status": "invalid_payload", "loaded_rows": 0}
    contract_ok = (
        payload.get("decision_authority") == "swing_sim_candidate_source_only"
        and payload.get("runtime_effect") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
    )
    if not contract_ok:
        return pd.DataFrame(), {"path": str(path), "status": "blocked_contract", "loaded_rows": 0}
    rows: list[dict[str, Any]] = []
    for candidate in payload.get("candidate_rows") or []:
        if not isinstance(candidate, dict):
            continue
        code = _norm_code(candidate.get("stock_code"))
        if not code.strip("0"):
            continue
        diagnostic = candidate.get("diagnostic_features") if isinstance(candidate.get("diagnostic_features"), dict) else {}
        source_features = candidate.get("source_features") if isinstance(candidate.get("source_features"), dict) else {}
        score = _safe_float(candidate.get("lifecycle_exploration_score"), 0.0)
        rows.append(
            {
                "date": target_date,
                "code": code,
                "name": str(candidate.get("stock_name") or ""),
                "hybrid_mean": max(0.0, min(1.0, score / 10.0)),
                "prob": max(0.0, min(1.0, score / 10.0)),
                "floor_used": 0.0,
                "score_rank": _safe_int(candidate.get("candidate_rank"), 999),
                "selection_mode": "BOTTOM_REBOUND_SOURCE_ONLY",
                "meta_score": round(score * 10.0, 6),
                "position_tag": "BOTTOM",
                "volatility_bucket": "bottom_rebound",
                "sector": str(diagnostic.get("kiwoom_sector") or ""),
                "industry": str(diagnostic.get("kiwoom_sector") or ""),
                "theme_tags": diagnostic.get("kiwoom_theme_tags") or [],
                "bottom_rebound_source_present": True,
                "bottom_rebound_candidate_id": candidate.get("candidate_id"),
                "bottom_rebound_candidate_rank": candidate.get("candidate_rank"),
                "bottom_rebound_source_quality_adjusted_ev_pct": candidate.get("source_quality_adjusted_ev_pct"),
                "bottom_rebound_recommended_entry_policy": candidate.get("recommended_sim_entry_policy"),
                "bottom_rebound_source_features": source_features,
            }
        )
    frame = pd.DataFrame(rows)
    return frame, {
        "path": str(path),
        "status": "ok",
        "loaded_rows": int(len(frame)),
        "source_report_date": payload.get("date"),
        "policy_version": payload.get("policy_version"),
    }


def _selected_swing_policy_file_from_apply_plan(target_date: str) -> str:
    path = THRESHOLD_APPLY_PLAN_DIR / f"threshold_apply_{_date_text(target_date)}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def walk(value: Any) -> str:
        if isinstance(value, dict):
            family = str(value.get("family") or "")
            if family == "swing_sim_auto_approval" and value.get("selected") is not False:
                recommended = value.get("recommended_values") if isinstance(value.get("recommended_values"), dict) else {}
                policy_file = str(recommended.get("policy_file") or value.get("policy_file") or "").strip()
                if policy_file:
                    return policy_file
            for child in value.values():
                found = walk(child)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = walk(item)
                if found:
                    return found
        return ""

    return walk(payload)


def _load_active_arm_priority_policies(
    policy_file: str | Path | None = None,
    *,
    target_date: str | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    resolved = str(policy_file or os.environ.get("KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE") or "").strip()
    if not resolved and target_date:
        resolved = _selected_swing_policy_file_from_apply_plan(target_date)
    if not resolved:
        return {}, {"status": "disabled", "path": ""}
    path = Path(resolved)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}, {"status": "missing_or_invalid", "path": str(path)}
    if not isinstance(payload, dict) or payload.get("schema_version") != "swing_sim_policy_catalog_v1":
        return {}, {"status": "schema_invalid", "path": str(path)}
    policies: dict[str, dict[str, Any]] = {}
    bucket_policies: dict[str, dict[str, Any]] = {}
    inactive_count = 0
    for item in payload.get("active_arm_priority_policies") or []:
        if not isinstance(item, dict):
            continue
        arm_id = str(item.get("priority_arm_id") or "").strip()
        bucket_id = str(item.get("priority_bucket_id") or "").strip()
        status = str(item.get("status") or "").strip()
        if status != "active":
            inactive_count += 1
            continue
        if arm_id:
            policies[arm_id] = item
        elif bucket_id:
            bucket_policies[bucket_id] = item
            policies[f"bucket:{bucket_id}"] = item
    return policies, {
        "status": "ok" if policies else "empty",
        "path": str(path),
        "active_policy_count": len(policies),
        "active_bucket_policy_count": len(bucket_policies),
        "inactive_policy_count": inactive_count,
    }


def merge_optional_source_rows(safe_pool_rows: pd.DataFrame, bottom_rows: pd.DataFrame) -> pd.DataFrame:
    if bottom_rows.empty:
        return safe_pool_rows.copy()
    if safe_pool_rows.empty:
        return bottom_rows.copy().reset_index(drop=True)
    safe = safe_pool_rows.copy()
    bottom = bottom_rows.copy()
    safe["code"] = safe["code"].map(_norm_code)
    bottom["code"] = bottom["code"].map(_norm_code)
    bottom_by_code = {str(row["code"]): row for row in bottom.to_dict("records")}
    merged_records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in safe.to_dict("records"):
        code = _norm_code(row.get("code"))
        extra = bottom_by_code.get(code)
        if extra:
            row = {
                **row,
                "bottom_rebound_source_present": _is_present(extra.get("bottom_rebound_source_present")),
                "bottom_rebound_candidate_id": extra.get("bottom_rebound_candidate_id"),
                "bottom_rebound_candidate_rank": extra.get("bottom_rebound_candidate_rank"),
                "bottom_rebound_source_quality_adjusted_ev_pct": extra.get("bottom_rebound_source_quality_adjusted_ev_pct"),
                "bottom_rebound_recommended_entry_policy": extra.get("bottom_rebound_recommended_entry_policy"),
                "bottom_rebound_source_features": extra.get("bottom_rebound_source_features"),
            }
        merged_records.append(row)
        seen.add(code)
    for row in bottom.to_dict("records"):
        code = _norm_code(row.get("code"))
        if code not in seen:
            merged_records.append(row)
            seen.add(code)
    return pd.DataFrame(merged_records).reset_index(drop=True)


def load_block_reason_map(target_date: str, *, event_path: Path | None = None) -> dict[str, str]:
    path = event_path or (PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl")
    priority = {
        "blocked_gatekeeper_reject": 40,
        "blocked_swing_gap": 30,
        "blocked_swing_score_vpw": 20,
        "swing_probe_entry_candidate": 10,
    }
    best: dict[str, tuple[int, str]] = {}
    for event in iter_jsonl(path):
        stage = str(event.get("stage") or event.get("event_type") or "")
        if stage not in priority:
            continue
        code = _norm_code(event.get("stock_code") or event.get("code") or (event.get("fields") or {}).get("stock_code"))
        if not code.strip("0"):
            continue
        rank = priority[stage]
        if code not in best or rank > best[code][0]:
            best[code] = (rank, stage)
    return {code: stage for code, (_, stage) in best.items()}


def fetch_quote_features(codes: Iterable[str], *, db_url: str = POSTGRES_URL, lookback: int = 60) -> dict[str, dict[str, Any]]:
    codes = sorted({_norm_code(code) for code in codes if _norm_code(code).strip("0")})
    if not codes:
        return {}
    engine = create_engine(db_url)
    query = text("""
        WITH ranked_quotes AS (
            SELECT
                quote_date,
                stock_code,
                stock_name,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                marcap,
                daily_return,
                ROW_NUMBER() OVER (
                    PARTITION BY stock_code
                    ORDER BY quote_date DESC
                ) AS rn
            FROM daily_stock_quotes
            WHERE stock_code IN :codes
        )
        SELECT quote_date, stock_code, stock_name, open_price, high_price, low_price, close_price,
               volume, marcap, daily_return
        FROM ranked_quotes
        WHERE rn <= :lookback
        ORDER BY stock_code ASC, quote_date DESC
    """).bindparams(bindparam("codes", expanding=True), bindparam("lookback"))
    try:
        df = pd.read_sql(query, engine, params={"codes": codes, "lookback": max(1, int(lookback))})
    except Exception:
        return {}
    finally:
        if hasattr(engine, "dispose"):
            engine.dispose()
    if df.empty:
        return {}
    df["stock_code"] = df["stock_code"].map(_norm_code)
    out: dict[str, dict[str, Any]] = {}
    for code, group in df.groupby("stock_code"):
        latest_first = group.head(lookback).copy()
        chronological = latest_first.sort_values("quote_date")
        close = pd.to_numeric(chronological["close_price"], errors="coerce")
        high = pd.to_numeric(chronological["high_price"], errors="coerce")
        low = pd.to_numeric(chronological["low_price"], errors="coerce")
        latest = chronological.iloc[-1]
        current = _safe_float(latest.get("close_price"), 0.0)
        low60 = _safe_float(low.min(), current)
        high60 = _safe_float(high.max(), current)
        position_ratio = (current - low60) / max(1e-9, high60 - low60) if current > 0 else 0.5
        if position_ratio >= 0.80:
            position_tag = "BREAKOUT"
        elif position_ratio <= 0.30:
            position_tag = "BOTTOM"
        else:
            position_tag = "MIDDLE"
        returns = pd.to_numeric(chronological.get("daily_return"), errors="coerce")
        if returns.isna().all():
            returns = close.pct_change() * 100.0
        vol = _safe_float(returns.tail(20).std(), 0.0)
        if vol >= 3.0:
            vol_bucket = "high"
        elif vol >= 1.2:
            vol_bucket = "mid"
        else:
            vol_bucket = "low"
        out[code] = {
            "stock_name": latest.get("stock_name"),
            "reference_price": current,
            "position_tag": position_tag,
            "position_ratio_60d": round(position_ratio, 4),
            "volatility_20d_pct": round(vol, 4),
            "volatility_bucket": vol_bucket,
            "marcap": _safe_float(latest.get("marcap"), 0.0),
            "volume": _safe_float(latest.get("volume"), 0.0),
        }
    return out


def _position_score(position_tag: str) -> float:
    return {"BREAKOUT": 0.85, "MIDDLE": 0.65, "BOTTOM": 0.75}.get(position_tag, 0.55)


def _volatility_score(bucket: str) -> float:
    return {"low": 0.55, "mid": 0.85, "high": 0.70}.get(bucket, 0.60)


def _block_exploration_score(reason: str) -> float:
    return {
        "blocked_gatekeeper_reject": 0.85,
        "blocked_swing_score_vpw": 0.80,
        "blocked_swing_gap": 0.65,
        "swing_probe_entry_candidate": 0.70,
        "no_block_observed": 0.55,
    }.get(reason, 0.55)


def _lifecycle_bootstrap_score(row: dict[str, Any], quote: dict[str, Any], block_reason: str) -> float:
    # Legacy model remains deliberately low weight. The rest of the score keeps
    # diversity and action provenance visible before closed lifecycle labels exist.
    hybrid = max(0.0, min(1.0, _safe_float(row.get("hybrid_mean"), 0.0)))
    rank = max(1, _safe_int(row.get("score_rank"), 999))
    rank_score = max(0.0, min(1.0, 1.0 - ((rank - 1) / 100.0)))
    score = (
        0.20 * hybrid
        + 0.10 * rank_score
        + 0.25 * _position_score(str(quote.get("position_tag") or row.get("position_tag") or ""))
        + 0.20 * _volatility_score(str(quote.get("volatility_bucket") or ""))
        + 0.25 * _block_exploration_score(block_reason)
    )
    return round(score, 6)


def _selection_mode(row: dict[str, Any]) -> str:
    return str(row.get("selection_mode") or "").strip().upper()


def _is_legacy_selected(row: dict[str, Any]) -> bool:
    mode = _selection_mode(row)
    return mode in {"SELECTED", "META_V2", "DB_FINAL_ENSEMBLE"} or bool(row.get("selected_by_legacy_model"))


def _pick_type(row: dict[str, Any]) -> str:
    mode = _selection_mode(row)
    if mode in {"SELECTED", "META_V2"}:
        return "MAIN"
    if mode and mode not in {"DIAGNOSTIC_ONLY", "FALLBACK_DIAGNOSTIC", "EMPTY"}:
        return "RUNNER"
    return "DIAGNOSTIC"


def build_candidate_rows(
    source_rows: pd.DataFrame,
    *,
    target_date: str,
    max_candidates: int = DEFAULT_MAX_DAILY_CANDIDATES,
    block_reasons: dict[str, str] | None = None,
    quote_features: dict[str, dict[str, Any]] | None = None,
    sector_theme_map: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if source_rows is None or source_rows.empty:
        return []
    block_reasons = block_reasons or {}
    quote_features = quote_features or {}
    sector_theme_map = sector_theme_map or {}
    rows: list[dict[str, Any]] = []
    for source in source_rows.to_dict("records"):
        code = _norm_code(source.get("code") or source.get("stock_code"))
        if not code.strip("0"):
            continue
        quote = quote_features.get(code, {})
        sector_theme = sector_theme_map.get(code, {})
        block_reason = block_reasons.get(code, "no_block_observed")
        position_tag = str(source.get("position_tag") or quote.get("position_tag") or "UNKNOWN")
        volatility_bucket = str(quote.get("volatility_bucket") or source.get("volatility_bucket") or "unknown")
        source_family_bucket = "bottom_rebound" if _is_present(source.get("bottom_rebound_source_present")) else "safe_pool"
        diversity_bucket = "|".join([position_tag, block_reason, volatility_bucket])
        score = _lifecycle_bootstrap_score(source, quote, block_reason)
        rows.append(
            {
                "candidate_key": code,
                "source_date": target_date,
                "stock_code": code,
                "stock_name": str(source.get("name") or source.get("stock_name") or quote.get("stock_name") or ""),
                "policy_version": POLICY_VERSION,
                "selection_arm": "",
                "diversity_bucket": diversity_bucket,
                "position_tag": position_tag,
                "block_reason": block_reason,
                "volatility_bucket": volatility_bucket,
                "source_family_bucket": source_family_bucket,
                "sector": str(sector_theme.get("sector") or source.get("sector") or ""),
                "industry": str(sector_theme.get("industry") or source.get("industry") or ""),
                "theme_tags": _json_text(sector_theme.get("theme_tags") or source.get("theme_tags") or []),
                "legacy_model_prob": _safe_float(source.get("prob", source.get("hybrid_mean")), 0.0),
                "legacy_model_rank": _safe_int(source.get("score_rank"), 999),
                "legacy_selection_mode": _selection_mode(source),
                "legacy_pick_type": _pick_type(source),
                "legacy_meta_score": _safe_float(source.get("meta_score", source.get("score")), 0.0),
                "legacy_hybrid_mean": _safe_float(source.get("hybrid_mean", source.get("prob")), 0.0),
                "lifecycle_exploration_score": score,
                "source_features": {
                    "label_weight_policy_version": LABEL_WEIGHT_POLICY_VERSION,
                    "composite_ev_policy_version": COMPOSITE_EV_POLICY_VERSION,
                    "arm_allocation": ARM_ALLOCATION,
                    "v2_required_fields": V2_REQUIRED_FIELDS,
                    "legacy_ml_role": "feature_and_comparison_cohort_only",
                    "source_family_bucket": source_family_bucket,
                    "quote_features": quote,
                    "sector_theme": {
                        "theme_source": sector_theme.get("theme_source") or "source_row_or_missing",
                        "theme_source_quality": sector_theme.get("theme_source_quality") or "source_row_or_missing",
                    },
                    "bottom_rebound_source": {
                        "present": _is_present(source.get("bottom_rebound_source_present")),
                        "candidate_id": source.get("bottom_rebound_candidate_id"),
                        "candidate_rank": source.get("bottom_rebound_candidate_rank"),
                        "source_quality_adjusted_ev_pct": source.get("bottom_rebound_source_quality_adjusted_ev_pct"),
                        "recommended_entry_policy": source.get("bottom_rebound_recommended_entry_policy"),
                        "entry_context": (
                            {
                                "setup_type": "anticipatory_bottom_rebound_swing",
                                "confirmation_policy": "do_not_require_breakout_confirmation",
                                "primary_ai_focus": [
                                    "invalidation_quality",
                                    "downside_tail",
                                    "liquidity",
                                    "low_retest_quality",
                                    "volume_and_flow_stabilization",
                                ],
                                "forbidden_interpretation": [
                                    "reject_only_because_price_has_not_broken_out",
                                    "treat_as_momentum_chase_setup",
                                ],
                            }
                            if _is_present(source.get("bottom_rebound_source_present"))
                            else {}
                        ),
                    },
                    "raw_source": {k: str(v) for k, v in source.items() if k in {"date", "bull_regime", "floor_used", "safe_pool_count", "candidate_count"}},
                },
                "decision_authority": DECISION_AUTHORITY,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
                "_legacy_selected": _is_legacy_selected(source),
                "_reference_price": _safe_float(source.get("close") or quote.get("reference_price"), 0.0),
            }
        )
    return allocate_candidate_arms(rows, max_candidates=max_candidates)


def _allocation_counts(total: int) -> dict[str, int]:
    if total <= 0:
        return {key: 0 for key in ARM_ALLOCATION}
    lifecycle = max(1, int(round(total * ARM_ALLOCATION["lifecycle_rank"])))
    diversity = max(0, int(round(total * ARM_ALLOCATION["diversity_exploration"])))
    legacy = max(0, total - lifecycle - diversity)
    return {"lifecycle_rank": lifecycle, "diversity_exploration": diversity, "legacy_ml": legacy}


def allocate_candidate_arms(rows: list[dict[str, Any]], *, max_candidates: int) -> list[dict[str, Any]]:
    if not rows:
        return []
    limit = max(1, min(max_candidates, len(rows)))
    counts = _allocation_counts(limit)
    by_code = {row["stock_code"]: row for row in rows}
    selected: dict[str, str] = {}

    ranked = sorted(rows, key=lambda item: item["lifecycle_exploration_score"], reverse=True)
    for row in ranked:
        if len([arm for arm in selected.values() if arm == "lifecycle_rank"]) >= counts["lifecycle_rank"]:
            break
        selected.setdefault(row["stock_code"], "lifecycle_rank")

    bucket_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ranked:
        if row["stock_code"] not in selected:
            bucket_rows[row["diversity_bucket"]].append(row)
    bucket_keys = sorted(bucket_rows)
    while len([arm for arm in selected.values() if arm == "diversity_exploration"]) < counts["diversity_exploration"]:
        progressed = False
        for key in bucket_keys:
            while bucket_rows[key]:
                row = bucket_rows[key].pop(0)
                if row["stock_code"] in selected:
                    continue
                selected[row["stock_code"]] = "diversity_exploration"
                progressed = True
                break
            if len([arm for arm in selected.values() if arm == "diversity_exploration"]) >= counts["diversity_exploration"]:
                break
        if not progressed:
            break

    legacy_rows = [row for row in ranked if row.get("_legacy_selected") and row["stock_code"] not in selected]
    for row in legacy_rows:
        if len([arm for arm in selected.values() if arm == "legacy_ml"]) >= counts["legacy_ml"]:
            break
        selected[row["stock_code"]] = "legacy_ml"

    for row in ranked:
        if len(selected) >= limit:
            break
        selected.setdefault(row["stock_code"], "lifecycle_rank")

    out = []
    for code, arm in selected.items():
        item = dict(by_code[code])
        item["selection_arm"] = arm
        item.pop("_legacy_selected", None)
        out.append(item)
    return sorted(out, key=lambda item: (item["selection_arm"], -item["lifecycle_exploration_score"], item["stock_code"]))


def _sizing_ratio(sizing_policy: str, candidate: dict[str, Any]) -> float:
    score = _safe_float(candidate.get("lifecycle_exploration_score"), 0.0)
    vol = str(candidate.get("volatility_bucket") or "")
    if sizing_policy == "equal_notional":
        return 0.10
    if sizing_policy == "volatility_adjusted":
        return {"high": 0.06, "mid": 0.10, "low": 0.12}.get(vol, 0.08)
    if sizing_policy == "confidence_weighted":
        return max(0.04, min(0.14, 0.04 + score * 0.10))
    if sizing_policy == "risk_capped":
        return 0.05 if vol == "high" else 0.08
    return 0.05


def _is_bottom_rebound_candidate(candidate: dict[str, Any]) -> bool:
    source_features = candidate.get("source_features") if isinstance(candidate.get("source_features"), dict) else {}
    bottom = source_features.get("bottom_rebound_source") if isinstance(source_features.get("bottom_rebound_source"), dict) else {}
    return _is_present(bottom.get("present")) or str(candidate.get("source_family_bucket") or "") == "bottom_rebound"


def _arm_set_for_candidate(candidate: dict[str, Any]) -> tuple[list[dict[str, str]], str, dict[str, Any]]:
    if _is_bottom_rebound_candidate(candidate):
        return (
            BOTTOM_REBOUND_ARM_SET,
            BOTTOM_REBOUND_ARM_POLICY_VERSION,
            {
                "setup_type": "anticipatory_bottom_rebound_swing",
                "entry_context_contract": {
                    "do_not_require_breakout_confirmation": True,
                    "judge_invalidation_downside_tail_liquidity_and_retest_quality": True,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "broker_order_forbidden": True,
                },
            },
        )
    return ARM_SET, ARM_POLICY_VERSION, {}


def build_arm_rows(
    candidates: list[dict[str, Any]],
    *,
    virtual_budget_krw: int | None = None,
    active_arm_priority_policies: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    virtual_budget = int(virtual_budget_krw or getattr(TRADING_RULES, "SIM_VIRTUAL_BUDGET_KRW", 10_000_000))
    active_arm_priority_policies = active_arm_priority_policies or {}
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        reference_price = _safe_float(candidate.get("_reference_price"), 0.0)
        arm_set, arm_policy_version, context = _arm_set_for_candidate(candidate)
        for spec in arm_set:
            priority_policy = active_arm_priority_policies.get(str(spec.get("arm_id") or ""))
            priority_fields = {}
            if isinstance(priority_policy, dict):
                priority_fields = {
                    "swing_active_arm_priority": True,
                    "priority_policy_id": priority_policy.get("priority_policy_id"),
                    "priority_arm_id": priority_policy.get("priority_arm_id"),
                    "priority_status": priority_policy.get("status"),
                    "priority_source": priority_policy.get("priority_source"),
                    "priority_source_report_date": priority_policy.get("source_report_date"),
                }
            ratio = _sizing_ratio(spec["sizing_policy"], candidate)
            notional = int(virtual_budget * ratio)
            qty = int(notional // reference_price) if reference_price > 0 else 0
            rows.append(
                {
                    "candidate_key": candidate["candidate_key"],
                    "source_date": candidate["source_date"],
                    "stock_code": candidate["stock_code"],
                    "policy_version": POLICY_VERSION,
                    "arm_id": spec["arm_id"],
                    "entry_policy": spec["entry_policy"],
                    "sizing_policy": spec["sizing_policy"],
                    "exit_policy": spec["exit_policy"],
                    "status": "PENDING_ENTRY",
                    "virtual_entry_price": reference_price or None,
                    "virtual_qty": max(0, qty),
                    "virtual_notional_krw": int(max(0, qty) * reference_price) if reference_price > 0 else 0,
                    "arm_features": {
                        "arm_policy_version": arm_policy_version,
                        "sizing_ratio": round(ratio, 4),
                        "entry_reference_price_source": "safe_pool_close_or_latest_quote",
                        "bottom_rebound_entry_context": context,
                        **priority_fields,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                    **priority_fields,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
    return rows


def persist_discovery_rows(candidates: list[dict[str, Any]], arms: list[dict[str, Any]], *, db_url: str = POSTGRES_URL) -> dict[str, int]:
    ensure_swing_strategy_discovery_schema(db_url)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    candidate_ids: dict[str, int] = {}
    try:
        with Session.begin() as session:
            candidate_lookup_keys = [
                (
                    pd.to_datetime(row["source_date"]).date(),
                    row["stock_code"],
                    row["policy_version"],
                )
                for row in candidates
            ]
            existing_candidates = (
                session.query(SwingStrategyDiscoveryCandidate)
                .filter(
                    tuple_(
                        SwingStrategyDiscoveryCandidate.source_date,
                        SwingStrategyDiscoveryCandidate.stock_code,
                        SwingStrategyDiscoveryCandidate.policy_version,
                    ).in_(candidate_lookup_keys)
                )
                .all()
                if candidate_lookup_keys
                else []
            )
            existing_candidate_map = {
                (item.source_date, item.stock_code, item.policy_version): item
                for item in existing_candidates
            }
            for row in candidates:
                lookup_key = (
                    pd.to_datetime(row["source_date"]).date(),
                    row["stock_code"],
                    row["policy_version"],
                )
                existing = existing_candidate_map.get(lookup_key)
                payload = {
                    "source_date": lookup_key[0],
                    "stock_code": row["stock_code"],
                    "stock_name": row["stock_name"],
                    "policy_version": row["policy_version"],
                    "selection_arm": row["selection_arm"],
                    "diversity_bucket": row["diversity_bucket"],
                    "position_tag": row["position_tag"],
                    "block_reason": row["block_reason"],
                    "volatility_bucket": row["volatility_bucket"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "theme_tags": row["theme_tags"],
                    "legacy_model_prob": row["legacy_model_prob"],
                    "legacy_model_rank": row["legacy_model_rank"],
                    "legacy_selection_mode": row["legacy_selection_mode"],
                    "legacy_pick_type": row["legacy_pick_type"],
                    "legacy_meta_score": row["legacy_meta_score"],
                    "legacy_hybrid_mean": row["legacy_hybrid_mean"],
                    "lifecycle_exploration_score": row["lifecycle_exploration_score"],
                    "source_features": _json_text(row["source_features"]),
                    "decision_authority": DECISION_AUTHORITY,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                    "updated_at": datetime.now(),
                }
                if existing is None:
                    existing = SwingStrategyDiscoveryCandidate(**payload)
                    session.add(existing)
                    existing_candidate_map[lookup_key] = existing
                else:
                    for key, value in payload.items():
                        setattr(existing, key, value)
            session.flush()
            for row in candidates:
                lookup_key = (
                    pd.to_datetime(row["source_date"]).date(),
                    row["stock_code"],
                    row["policy_version"],
                )
                candidate_ids[row["candidate_key"]] = int(existing_candidate_map[lookup_key].id)

            arm_lookup_keys = [
                (
                    candidate_ids[row["candidate_key"]],
                    row["arm_id"],
                    row["policy_version"],
                )
                for row in arms
                if row["candidate_key"] in candidate_ids
            ]
            existing_arms = (
                session.query(SwingStrategyDiscoveryArm)
                .filter(
                    tuple_(
                        SwingStrategyDiscoveryArm.candidate_id,
                        SwingStrategyDiscoveryArm.arm_id,
                        SwingStrategyDiscoveryArm.policy_version,
                    ).in_(arm_lookup_keys)
                )
                .all()
                if arm_lookup_keys
                else []
            )
            existing_arm_map = {
                (item.candidate_id, item.arm_id, item.policy_version): item
                for item in existing_arms
            }
            for row in arms:
                candidate_id = candidate_ids.get(row["candidate_key"])
                if not candidate_id:
                    continue
                existing = existing_arm_map.get((candidate_id, row["arm_id"], row["policy_version"]))
                payload = {
                    "candidate_id": candidate_id,
                    "source_date": pd.to_datetime(row["source_date"]).date(),
                    "stock_code": row["stock_code"],
                    "policy_version": row["policy_version"],
                    "arm_id": row["arm_id"],
                    "entry_policy": row["entry_policy"],
                    "sizing_policy": row["sizing_policy"],
                    "exit_policy": row["exit_policy"],
                    "status": row["status"],
                    "virtual_entry_price": row["virtual_entry_price"],
                    "virtual_qty": row["virtual_qty"],
                    "virtual_notional_krw": row["virtual_notional_krw"],
                    "arm_features": _json_text(row["arm_features"]),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                    "updated_at": datetime.now(),
                }
                if existing is None:
                    session.add(SwingStrategyDiscoveryArm(**payload))
                else:
                    for key, value in payload.items():
                        setattr(existing, key, value)
    finally:
        if hasattr(engine, "dispose"):
            engine.dispose()
    return {"candidate_rows": len(candidates), "arm_rows": len(arms)}


def summarize_candidates(candidates: list[dict[str, Any]], arms: list[dict[str, Any]]) -> dict[str, Any]:
    bottom_candidate_count = sum(1 for row in candidates if _is_bottom_rebound_candidate(row))
    bottom_codes = {row["stock_code"] for row in candidates if _is_bottom_rebound_candidate(row)}
    bottom_arm_count = sum(1 for row in arms if row.get("stock_code") in bottom_codes)
    return {
        "candidate_count": len(candidates),
        "arm_count": len(arms),
        "selection_arm_counts": dict(Counter(row["selection_arm"] for row in candidates)),
        "position_tag_counts": dict(Counter(row["position_tag"] for row in candidates)),
        "block_reason_counts": dict(Counter(row["block_reason"] for row in candidates)),
        "volatility_bucket_counts": dict(Counter(row["volatility_bucket"] for row in candidates)),
        "source_family_bucket_counts": dict(Counter(row.get("source_family_bucket", "safe_pool") for row in candidates)),
        "bottom_rebound_selected_candidate_count": bottom_candidate_count,
        "bottom_rebound_arm_count": bottom_arm_count,
        "arm_policy_counts": dict(Counter(row["arm_id"] for row in arms)),
    }


def build_swing_strategy_discovery_report(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    max_candidates: int | None = None,
    persist: bool = True,
    include_bottom_rebound_source: bool = False,
    bottom_rebound_source_path: str | Path | None = None,
    swing_sim_policy_file: str | Path | None = None,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    active_arm_policies, active_arm_policy_diag = _load_active_arm_priority_policies(
        swing_sim_policy_file,
        target_date=date_key,
    )
    effective_max_candidates = (
        max_candidates
        if max_candidates is not None
        else ACTIVE_PRIORITY_MAX_DAILY_CANDIDATES
        if active_arm_policies
        else DEFAULT_MAX_DAILY_CANDIDATES
    )
    safe_pool_rows = load_safe_pool_rows(date_key)
    bottom_rebound_rows, bottom_rebound_diag = (
        load_bottom_rebound_source_rows(date_key, source_path=bottom_rebound_source_path)
        if include_bottom_rebound_source
        else (pd.DataFrame(), {"status": "disabled", "loaded_rows": 0, "path": str(bottom_rebound_source_path or _bottom_rebound_source_path(date_key))})
    )
    source_rows = merge_optional_source_rows(safe_pool_rows, bottom_rebound_rows) if include_bottom_rebound_source else safe_pool_rows
    block_reasons = load_block_reason_map(date_key)
    quote_features = fetch_quote_features(source_rows.get("code", pd.Series(dtype=str)).tolist(), db_url=db_url)
    codes = source_rows.get("code", pd.Series(dtype=str)).tolist()
    sector_theme_payload = build_sector_theme_map(codes, target_date=date_key, allow_external=True)
    sector_theme_map = sector_theme_payload.get("rows_by_code") if isinstance(sector_theme_payload.get("rows_by_code"), dict) else {}
    source_count = int(len(source_rows))
    safe_pool_count = int(len(safe_pool_rows))
    bottom_rebound_count = int(len(bottom_rebound_rows))
    quote_feature_count = int(len(quote_features))
    sector_theme_mapped = int(sector_theme_payload.get("mapped_code_count") or 0)
    sector_theme_missing = int(sector_theme_payload.get("missing_count") or 0)
    sector_mapped = int(sector_theme_payload.get("sector_mapped_count") or 0)
    sector_missing = int(sector_theme_payload.get("sector_missing_count") or 0)
    theme_mapped = int(sector_theme_payload.get("theme_mapped_count") or 0)
    theme_missing = int(sector_theme_payload.get("theme_missing_count") or 0)
    candidates = build_candidate_rows(
        source_rows,
        target_date=date_key,
        max_candidates=effective_max_candidates,
        block_reasons=block_reasons,
        quote_features=quote_features,
        sector_theme_map=sector_theme_map,
    )
    arms = build_arm_rows(candidates, active_arm_priority_policies=active_arm_policies)
    persist_summary = persist_discovery_rows(candidates, arms, db_url=db_url) if persist else {"candidate_rows": 0, "arm_rows": 0}
    summary = summarize_candidates(candidates, arms)
    active_priority_arm_count = sum(1 for item in arms if bool(item.get("swing_active_arm_priority")))
    summary["active_arm_priority_policy_count"] = len(active_arm_policies)
    summary["active_arm_priority_arm_count"] = active_priority_arm_count
    summary["effective_max_daily_candidates"] = effective_max_candidates
    summary["bottom_rebound_persisted_candidate_count"] = (
        summary["bottom_rebound_selected_candidate_count"] if persist_summary.get("candidate_rows") else 0
    )
    summary["bottom_rebound_persisted_arm_count"] = (
        summary["bottom_rebound_arm_count"] if persist_summary.get("arm_rows") else 0
    )
    warnings: list[str] = []
    if not candidates:
        warnings.append("safe_pool_source_empty")
    elif safe_pool_count == 0 and bottom_rebound_count > 0:
        warnings.append("safe_pool_empty_bottom_rebound_source_used")
    if include_bottom_rebound_source and bottom_rebound_diag.get("status") != "ok":
        warnings.append(f"bottom_rebound_source:{bottom_rebound_diag.get('status')}")
    if (
        include_bottom_rebound_source
        and bottom_rebound_diag.get("status") == "ok"
        and summary.get("bottom_rebound_selected_candidate_count", 0) > 0
        and persist
        and (persist_summary.get("candidate_rows", 0) <= 0 or persist_summary.get("arm_rows", 0) <= 0)
    ):
        warnings.append("bottom_rebound_persist_missing")
    if source_count and quote_feature_count == 0:
        warnings.append("quote_features_unavailable")
    elif source_count and quote_feature_count < min(source_count, effective_max_candidates):
        warnings.append("quote_features_partial")
    for warning in sector_theme_payload.get("warnings") or []:
        warnings.append(f"sector_theme:{warning}")
    return {
        "schema_version": 1,
        "report_type": "swing_strategy_discovery_sim",
        "date": date_key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "family": "swing_strategy_discovery_sim",
        "policy_version": POLICY_VERSION,
        "label_weight_policy_version": LABEL_WEIGHT_POLICY_VERSION,
        "composite_ev_policy_version": COMPOSITE_EV_POLICY_VERSION,
        "arm_policy_version": ARM_POLICY_VERSION,
        "bottom_rebound_arm_policy_version": BOTTOM_REBOUND_ARM_POLICY_VERSION,
        "mode": "sim_only_aggressive_exploration",
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "broker_order_submit",
            "real_execution_quality_claim",
            "runtime_threshold_apply",
            "recommendation_history_replacement",
            "telegram_buy_alert",
        ],
        "storage_contract": {
            "source_of_truth": "db",
            "tables": [
                "swing_strategy_discovery_candidates",
                "swing_strategy_discovery_arms",
                "swing_strategy_discovery_labels",
            ],
            "report_artifact_only": True,
        },
        "selection_policy": {
            "universe": "safe_pool_plus_optional_bottom_rebound_source"
            if include_bottom_rebound_source
            else "safe_pool",
            "arm_allocation": ARM_ALLOCATION,
            "diversity_v1": list(DIVERSITY_BUCKET_FIELDS),
            "v2_required_extension": list(V2_REQUIRED_FIELDS),
            "legacy_ml_role": "low_weight_feature_and_comparison_cohort",
            "bottom_rebound_source_role": "optional_sim_only_candidate_source",
            "max_daily_candidates": effective_max_candidates,
            "effective_max_daily_candidates": effective_max_candidates,
        },
        "source_quality": {
            "safe_pool_source_rows": safe_pool_count,
            "bottom_rebound_source_rows": bottom_rebound_count,
            "combined_source_rows": source_count,
            "bottom_rebound_source": bottom_rebound_diag,
            "active_arm_priority_policy": active_arm_policy_diag,
            "quote_feature_rows": quote_feature_count,
            "quote_feature_coverage": round(quote_feature_count / source_count, 6) if source_count else 0.0,
            "sector_theme_mapped_rows": sector_theme_mapped,
            "sector_theme_missing_rows": sector_theme_missing,
            "sector_theme_coverage": round(sector_theme_mapped / source_count, 6) if source_count else 0.0,
            "sector_mapped_rows": sector_mapped,
            "sector_missing_rows": sector_missing,
            "sector_coverage": round(sector_mapped / source_count, 6) if source_count else 0.0,
            "theme_mapped_rows": theme_mapped,
            "theme_missing_rows": theme_missing,
            "theme_coverage": round(theme_mapped / source_count, 6) if source_count else 0.0,
            "sector_theme_cache": str((Path(DATA_DIR) / "runtime" / "swing_strategy_discovery" / f"sector_theme_map_{date_key}.json")),
            "warnings": warnings,
        },
        "arm_set": ARM_SET,
        "bottom_rebound_arm_set": BOTTOM_REBOUND_ARM_SET,
        "summary": summary,
        "persist_summary": persist_summary,
        "sources": {
            "diagnostic_csv": str(RECO_DIAGNOSTIC_PATH),
            "recommendation_csv": str(RECO_PATH),
            "pipeline_events": str((PIPELINE_EVENTS_DIR / f"pipeline_events_{date_key}.jsonl")),
            "sector_theme_map": str((Path(DATA_DIR) / "runtime" / "swing_strategy_discovery" / f"sector_theme_map_{date_key}.json")),
            "bottom_rebound_candidate_source": str(bottom_rebound_diag.get("path") or ""),
            "swing_sim_policy_catalog": str(active_arm_policy_diag.get("path") or ""),
        },
        "examples": [
            {
                **{
                    key: row.get(key)
                    for key in (
                        "stock_code",
                        "stock_name",
                        "selection_arm",
                        "diversity_bucket",
                        "source_family_bucket",
                        "lifecycle_exploration_score",
                        "legacy_selection_mode",
                    )
                },
                "bottom_rebound_source": (
                    (row.get("source_features") or {}).get("bottom_rebound_source")
                    if isinstance(row.get("source_features"), dict)
                    else {}
                ),
            }
            for row in candidates[:20]
        ],
        "warnings": warnings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    source_quality = report.get("source_quality") or {}
    lines = [
        f"# Swing Strategy Discovery Sim - {report.get('date')}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- policy_version: `{report.get('policy_version')}`",
        f"- mode: `{report.get('mode')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- candidate_count: `{summary.get('candidate_count', 0)}`",
        f"- arm_count: `{summary.get('arm_count', 0)}`",
        f"- bottom_rebound_selected_candidate_count: `{summary.get('bottom_rebound_selected_candidate_count', 0)}`",
        f"- bottom_rebound_arm_count: `{summary.get('bottom_rebound_arm_count', 0)}`",
        f"- bottom_rebound_persisted_candidate_count: `{summary.get('bottom_rebound_persisted_candidate_count', 0)}`",
        f"- bottom_rebound_persisted_arm_count: `{summary.get('bottom_rebound_persisted_arm_count', 0)}`",
        f"- active_arm_priority_policy_count: `{summary.get('active_arm_priority_policy_count', 0)}`",
        f"- active_arm_priority_arm_count: `{summary.get('active_arm_priority_arm_count', 0)}`",
        f"- effective_max_daily_candidates: `{summary.get('effective_max_daily_candidates', 0)}`",
        f"- selection_arm_counts: `{summary.get('selection_arm_counts', {})}`",
        f"- block_reason_counts: `{summary.get('block_reason_counts', {})}`",
        f"- source_family_bucket_counts: `{summary.get('source_family_bucket_counts', {})}`",
        f"- quote_feature_coverage: `{source_quality.get('quote_feature_coverage', 0.0)}`",
        f"- warnings: `{report.get('warnings', [])}`",
        "",
        "## Arm Set",
        "",
        "| arm_id | entry | sizing | exit |",
        "| --- | --- | --- | --- |",
    ]
    for arm in report.get("arm_set") or []:
        lines.append(
            f"| `{arm.get('arm_id')}` | `{arm.get('entry_policy')}` | `{arm.get('sizing_policy')}` | `{arm.get('exit_policy')}` |"
        )
    for arm in report.get("bottom_rebound_arm_set") or []:
        lines.append(
            f"| `{arm.get('arm_id')}` | `{arm.get('entry_policy')}` | `{arm.get('sizing_policy')}` | `{arm.get('exit_policy')}` |"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- DB tables are the source of truth; this Markdown/JSON is an audit artifact.",
            "- `actual_order_submitted=false`, `broker_order_forbidden=true`, and `runtime_effect=false` are mandatory.",
            "- Legacy ML is a low-weight feature/cohort, not the final selector.",
            "- Sector/theme fields are collected in v1 and reserved as required v2 extension inputs.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_swing_strategy_discovery_report(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    output_dir: Path = REPORT_DIR,
    max_candidates: int | None = None,
    persist: bool = True,
    include_bottom_rebound_source: bool = False,
    bottom_rebound_source_path: str | Path | None = None,
    swing_sim_policy_file: str | Path | None = None,
) -> dict[str, Path]:
    report = build_swing_strategy_discovery_report(
        target_date,
        db_url=db_url,
        max_candidates=max_candidates,
        persist=persist,
        include_bottom_rebound_source=include_bottom_rebound_source,
        bottom_rebound_source_path=bottom_rebound_source_path,
        swing_sim_policy_file=swing_sim_policy_file,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    date_key = _date_text(target_date)
    json_path = output_dir / f"swing_strategy_discovery_sim_{date_key}.json"
    md_path = output_dir / f"swing_strategy_discovery_sim_{date_key}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--db-url", default=POSTGRES_URL)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--include-bottom-rebound-source", action="store_true")
    parser.add_argument("--bottom-rebound-source-path", type=Path, default=None)
    parser.add_argument("--swing-sim-policy-file", type=Path, default=None)
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    paths = write_swing_strategy_discovery_report(
        args.target_date,
        db_url=args.db_url,
        output_dir=args.output_dir,
        max_candidates=args.max_candidates,
        persist=not args.no_persist,
        include_bottom_rebound_source=args.include_bottom_rebound_source,
        bottom_rebound_source_path=args.bottom_rebound_source_path,
        swing_sim_policy_file=args.swing_sim_policy_file,
    )
    print(f"[DONE] swing_strategy_discovery_sim json={paths['json']} md={paths['md']}")


if __name__ == "__main__":
    main()
