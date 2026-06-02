import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from . import config
except ImportError:  # pragma: no cover - direct script execution
    import config
from tuning_observability_summary import write_tuning_observability_outputs

SCALPING_FEEDBACK_SOURCES = {
    "threshold_cycle_ev": ("threshold_cycle_ev", "threshold_cycle_ev"),
    "lifecycle_decision_matrix": ("lifecycle_decision_matrix", "lifecycle_decision_matrix"),
    "lifecycle_bucket_discovery": ("lifecycle_bucket_discovery", "lifecycle_bucket_discovery"),
    "runtime_approval_summary": ("runtime_approval_summary", "runtime_approval_summary"),
}


def _load_json(name: str) -> dict:
    path = config.OUTPUT_DIR / name
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_feedback_sources() -> dict:
    consumed = []
    missing = []
    for source_id, (report_name, stem) in SCALPING_FEEDBACK_SOURCES.items():
        path = config.LOCAL_REPORT_DIR / report_name / f"{stem}_{config.END_DATE}.json"
        item = {
            "source_id": source_id,
            "path": str(path),
            "runtime_effect": False,
            "decision_authority": "source_quality_only",
        }
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
            consumed.append(
                {
                    **item,
                    "status": payload.get("status") or summary.get("status"),
                    "warnings": payload.get("warnings") or summary.get("warnings") or [],
                }
            )
        else:
            missing.append({**item, "gap_type": "source_quality_gap"})
    return {
        "consumed_feedback_sources": consumed,
        "missing_feedback_sources": missing,
        "runtime_effect": False,
        "decision_authority": "source_quality_only",
    }


def _load_csv(name: str) -> pd.DataFrame:
    path = config.OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8", low_memory=False)


def _normalize_trade_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "trade_id" not in df.columns:
        return df
    out = df.copy()
    out["trade_id"] = out["trade_id"].astype("string").str.strip()
    return out


def build_summary_payload(ev_result: dict, trade_df: pd.DataFrame) -> dict:
    if not trade_df.empty:
        valid_mask = trade_df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
        valid_trades = _normalize_trade_id(trade_df[valid_mask].copy())
    else:
        valid_trades = pd.DataFrame()

    daily_stats = []
    if not valid_trades.empty and "rec_date" in valid_trades.columns:
        for rec_date, group in valid_trades.groupby("rec_date"):
            daily_stats.append(
                {
                    "date": str(rec_date),
                    "n_trades": int(len(group)),
                    "diagnostic_win_rate_pct": round((group["profit_rate"].astype(float) > 0).mean() * 100, 1),
                    "median_profit": round(float(group["profit_rate"].astype(float).median()), 3),
                    "equal_weight_avg_profit_pct": round(float(group["profit_rate"].astype(float).mean()), 3),
                    "simple_sum_profit_pct": round(float(group["profit_rate"].astype(float).sum()), 3),
                    "primary_decision_metric": "equal_weight_avg_profit_pct",
                }
            )

    observability = write_tuning_observability_outputs(
        output_dir=config.OUTPUT_DIR,
        target_date=config.END_DATE,
        analysis_start=config.START_DATE,
        analysis_end=config.END_DATE,
    )

    return {
        "meta": {
            "analysis_period": f"{config.START_DATE} ~ {config.END_DATE}",
            "generated_at": datetime.now().isoformat(),
            "total_valid_trades": int(len(valid_trades)),
            "cohorts": ["full_fill", "partial_fill", "split-entry"],
        },
        "tuning_observability": observability,
        "cohort_summary": ev_result.get("cohort_summary", []),
        "loss_patterns": ev_result.get("loss_patterns", []),
        "profit_patterns": ev_result.get("profit_patterns", []),
        "opportunity_cost": ev_result.get("opportunity_cost", []),
        "ev_backlog_titles": [row["title"] for row in ev_result.get("ev_backlog", [])],
        "daily_stats": daily_stats,
        "feedback_sources": _load_feedback_sources(),
    }


def build_cases_payload(trade_df: pd.DataFrame, seq_df: pd.DataFrame) -> dict:
    cases = {
        "feedback_sources": _load_feedback_sources(),
        "loss_split_entry": [],
        "loss_full_fill": [],
        "profit_split_entry": [],
        "profit_full_fill": [],
        "profit_partial_fill": [],
    }
    if trade_df.empty:
        return cases

    valid_mask = trade_df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
    valid_trades = _normalize_trade_id(trade_df[valid_mask].copy())
    if valid_trades.empty:
        return cases

    seq_df = _normalize_trade_id(seq_df)
    if not seq_df.empty and "trade_id" in seq_df.columns:
        valid_trades["trade_id"] = valid_trades["trade_id"].astype("string").str.strip()
        join_cols = [
            "trade_id",
            "partial_then_expand_flag",
            "multi_rebase_flag",
            "rebase_integrity_flag",
            "same_symbol_repeat_flag",
            "same_ts_multi_rebase_flag",
            "rebase_count",
        ]
        seq_view = seq_df[[col for col in join_cols if col in seq_df.columns]].drop_duplicates("trade_id")
        seq_view["trade_id"] = seq_view["trade_id"].astype("string").str.strip()
        valid_trades = valid_trades.merge(seq_view, on="trade_id", how="left")

    valid_trades["profit_rate"] = pd.to_numeric(valid_trades["profit_rate"], errors="coerce")
    loss_df = valid_trades[valid_trades["profit_rate"] <= 0].sort_values("profit_rate")
    profit_df = valid_trades[valid_trades["profit_rate"] > 0].sort_values("profit_rate", ascending=False)

    def _serialize(group: pd.DataFrame) -> list[dict]:
        rows = []
        for _, row in group.iterrows():
            item = row.to_dict()
            rows.append(item)
        return rows

    cases["loss_split_entry"] = _serialize(loss_df[loss_df["cohort"] == "split-entry"].head(5))
    cases["loss_full_fill"] = _serialize(loss_df[loss_df["cohort"] == "full_fill"].head(5))
    cases["profit_split_entry"] = _serialize(profit_df[profit_df["cohort"] == "split-entry"].head(5))
    cases["profit_full_fill"] = _serialize(profit_df[profit_df["cohort"] == "full_fill"].head(5))
    cases["profit_partial_fill"] = _serialize(profit_df[profit_df["cohort"] == "partial_fill"].head(5))
    return cases


def build_llm_payload() -> None:
    ev_result = _load_json("ev_analysis_result.json")
    trade_df = _normalize_trade_id(_load_csv("trade_fact.csv"))
    seq_df = _normalize_trade_id(_load_csv("sequence_fact.csv"))

    summary_payload = build_summary_payload(ev_result, trade_df)
    with open(config.OUTPUT_DIR / "llm_payload_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2, ensure_ascii=False)

    cases_payload = build_cases_payload(trade_df, seq_df)
    with open(config.OUTPUT_DIR / "llm_payload_cases.json", "w", encoding="utf-8") as handle:
        json.dump(cases_payload, handle, indent=2, ensure_ascii=False)

    print("LLM payload built successfully.")


if __name__ == "__main__":
    build_llm_payload()
