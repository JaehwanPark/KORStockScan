"""Swing strategy discovery simulator v1.

This module builds an aggressive sim-only swing exploration book. It is not a
real-order path and it intentionally stores rows outside recommendation_history.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
)
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema
from src.model.common_v2 import RECO_DIAGNOSTIC_PATH, RECO_PATH
from src.utils.constants import DATA_DIR, POSTGRES_URL, TRADING_RULES
from src.utils.jsonl_io import iter_jsonl


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_sim"
PIPELINE_EVENTS_DIR = Path(DATA_DIR) / "pipeline_events"

POLICY_VERSION = "swing_strategy_discovery_sim_v1"
LABEL_WEIGHT_POLICY_VERSION = "swing_lifecycle_ev_label_weight_policy_v1"
COMPOSITE_EV_POLICY_VERSION = "swing_lifecycle_composite_ev_policy_v1"
ARM_POLICY_VERSION = "bounded_8_arm_policy_v1"
DECISION_AUTHORITY = "swing_sim_exploration_only"
DEFAULT_MAX_DAILY_CANDIDATES = 50

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
        SELECT quote_date, stock_code, stock_name, open_price, high_price, low_price, close_price,
               volume, marcap, daily_return
        FROM daily_stock_quotes
        WHERE stock_code IN :codes
        ORDER BY stock_code ASC, quote_date DESC
    """).bindparams(bindparam("codes", expanding=True))
    try:
        df = pd.read_sql(query, engine, params={"codes": codes})
    except Exception:
        return {}
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
    return mode in {"SELECTED", "META_V2", "DB_FINAL_ENSEMBLE", "DB_EOD_TOP5"} or bool(row.get("selected_by_legacy_model"))


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
) -> list[dict[str, Any]]:
    if source_rows is None or source_rows.empty:
        return []
    block_reasons = block_reasons or {}
    quote_features = quote_features or {}
    rows: list[dict[str, Any]] = []
    for source in source_rows.to_dict("records"):
        code = _norm_code(source.get("code") or source.get("stock_code"))
        if not code.strip("0"):
            continue
        quote = quote_features.get(code, {})
        block_reason = block_reasons.get(code, "no_block_observed")
        position_tag = str(source.get("position_tag") or quote.get("position_tag") or "UNKNOWN")
        volatility_bucket = str(quote.get("volatility_bucket") or source.get("volatility_bucket") or "unknown")
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
                "sector": str(source.get("sector") or ""),
                "industry": str(source.get("industry") or ""),
                "theme_tags": _json_text(source.get("theme_tags") or []),
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
                    "quote_features": quote,
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


def build_arm_rows(candidates: list[dict[str, Any]], *, virtual_budget_krw: int | None = None) -> list[dict[str, Any]]:
    virtual_budget = int(virtual_budget_krw or getattr(TRADING_RULES, "SIM_VIRTUAL_BUDGET_KRW", 10_000_000))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        reference_price = _safe_float(candidate.get("_reference_price"), 0.0)
        for spec in ARM_SET:
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
                        "arm_policy_version": ARM_POLICY_VERSION,
                        "sizing_ratio": round(ratio, 4),
                        "entry_reference_price_source": "safe_pool_close_or_latest_quote",
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "runtime_effect": False,
                    },
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            )
    return rows


def persist_discovery_rows(candidates: list[dict[str, Any]], arms: list[dict[str, Any]], *, db_url: str = POSTGRES_URL) -> dict[str, int]:
    ensure_swing_strategy_discovery_schema(db_url)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    candidate_ids: dict[str, int] = {}
    with Session.begin() as session:
        for row in candidates:
            existing = (
                session.query(SwingStrategyDiscoveryCandidate)
                .filter_by(
                    source_date=pd.to_datetime(row["source_date"]).date(),
                    stock_code=row["stock_code"],
                    policy_version=row["policy_version"],
                )
                .first()
            )
            payload = {
                "source_date": pd.to_datetime(row["source_date"]).date(),
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
                session.flush()
            else:
                for key, value in payload.items():
                    setattr(existing, key, value)
            candidate_ids[row["candidate_key"]] = int(existing.id)

        for row in arms:
            candidate_id = candidate_ids.get(row["candidate_key"])
            if not candidate_id:
                continue
            existing = (
                session.query(SwingStrategyDiscoveryArm)
                .filter_by(candidate_id=candidate_id, arm_id=row["arm_id"], policy_version=row["policy_version"])
                .first()
            )
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
    return {"candidate_rows": len(candidates), "arm_rows": len(arms)}


def summarize_candidates(candidates: list[dict[str, Any]], arms: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candidate_count": len(candidates),
        "arm_count": len(arms),
        "selection_arm_counts": dict(Counter(row["selection_arm"] for row in candidates)),
        "position_tag_counts": dict(Counter(row["position_tag"] for row in candidates)),
        "block_reason_counts": dict(Counter(row["block_reason"] for row in candidates)),
        "volatility_bucket_counts": dict(Counter(row["volatility_bucket"] for row in candidates)),
        "arm_policy_counts": dict(Counter(row["arm_id"] for row in arms)),
    }


def build_swing_strategy_discovery_report(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    max_candidates: int = DEFAULT_MAX_DAILY_CANDIDATES,
    persist: bool = True,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    source_rows = load_safe_pool_rows(date_key)
    block_reasons = load_block_reason_map(date_key)
    quote_features = fetch_quote_features(source_rows.get("code", pd.Series(dtype=str)).tolist(), db_url=db_url)
    source_count = int(len(source_rows))
    quote_feature_count = int(len(quote_features))
    candidates = build_candidate_rows(
        source_rows,
        target_date=date_key,
        max_candidates=max_candidates,
        block_reasons=block_reasons,
        quote_features=quote_features,
    )
    arms = build_arm_rows(candidates)
    persist_summary = persist_discovery_rows(candidates, arms, db_url=db_url) if persist else {"candidate_rows": 0, "arm_rows": 0}
    summary = summarize_candidates(candidates, arms)
    warnings: list[str] = []
    if not candidates:
        warnings.append("safe_pool_source_empty")
    if source_count and quote_feature_count == 0:
        warnings.append("quote_features_unavailable")
    elif source_count and quote_feature_count < min(source_count, max_candidates):
        warnings.append("quote_features_partial")
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
        "mode": "sim_only_aggressive_exploration",
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
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
            "universe": "safe_pool",
            "arm_allocation": ARM_ALLOCATION,
            "diversity_v1": list(DIVERSITY_BUCKET_FIELDS),
            "v2_required_extension": list(V2_REQUIRED_FIELDS),
            "legacy_ml_role": "low_weight_feature_and_comparison_cohort",
            "max_daily_candidates": max_candidates,
        },
        "source_quality": {
            "safe_pool_source_rows": source_count,
            "quote_feature_rows": quote_feature_count,
            "quote_feature_coverage": round(quote_feature_count / source_count, 6) if source_count else 0.0,
            "warnings": warnings,
        },
        "arm_set": ARM_SET,
        "summary": summary,
        "persist_summary": persist_summary,
        "sources": {
            "diagnostic_csv": str(RECO_DIAGNOSTIC_PATH),
            "recommendation_csv": str(RECO_PATH),
            "pipeline_events": str((PIPELINE_EVENTS_DIR / f"pipeline_events_{date_key}.jsonl")),
        },
        "examples": [
            {
                key: row.get(key)
                for key in (
                    "stock_code",
                    "stock_name",
                    "selection_arm",
                    "diversity_bucket",
                    "lifecycle_exploration_score",
                    "legacy_selection_mode",
                )
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
        f"- selection_arm_counts: `{summary.get('selection_arm_counts', {})}`",
        f"- block_reason_counts: `{summary.get('block_reason_counts', {})}`",
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
    max_candidates: int = DEFAULT_MAX_DAILY_CANDIDATES,
    persist: bool = True,
) -> dict[str, Path]:
    report = build_swing_strategy_discovery_report(
        target_date,
        db_url=db_url,
        max_candidates=max_candidates,
        persist=persist,
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
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_DAILY_CANDIDATES)
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    paths = write_swing_strategy_discovery_report(
        args.target_date,
        db_url=args.db_url,
        output_dir=args.output_dir,
        max_candidates=args.max_candidates,
        persist=not args.no_persist,
    )
    print(f"[DONE] swing_strategy_discovery_sim json={paths['json']} md={paths['md']}")


if __name__ == "__main__":
    main()
