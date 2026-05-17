import json
from pathlib import Path

import pandas as pd

try:
    from . import config
except ImportError:  # pragma: no cover - direct script execution
    import config

TOP_N_PATTERNS = 5
MIN_VALID_SAMPLES = config.MIN_VALID_SAMPLES
SCHEMA_VERSION = 2
METRIC_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "main_only_completed",
    "window_policy": "rolling_10d_with_daily_guard",
    "sample_floor": MIN_VALID_SAMPLES,
    "primary_decision_metric": "equal_weight_avg_profit_pct",
    "source_quality_gate": "COMPLETED + numeric profit_rate only; local/main source by default; full/partial/split cohorts separated",
    "forbidden_uses": [
        "runtime_threshold_apply_without_deterministic_guard",
        "broker_order_enable",
        "provider_route_change",
        "bot_restart",
        "real_execution_quality_inference_from_remote_or_sim",
    ],
    "runtime_effect": False,
}


def _load_csv(name: str) -> pd.DataFrame:
    path = config.OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8", low_memory=False)


def _safe_median(series: pd.Series) -> float:
    series = series.dropna()
    return float(series.median()) if not series.empty else 0.0


def _safe_mean(series: pd.Series) -> float:
    series = series.dropna()
    return float(series.mean()) if not series.empty else 0.0


def _normalize_trade_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "trade_id" not in df.columns:
        return df
    out = df.copy()
    out["trade_id"] = out["trade_id"].astype("string").str.strip()
    return out


def _valid_trades(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    mask = df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
    out = df[mask].copy()
    if "profit_rate" in out.columns:
        out["profit_rate"] = pd.to_numeric(out["profit_rate"], errors="coerce")
    if "held_sec" in out.columns:
        out["held_sec"] = pd.to_numeric(out["held_sec"], errors="coerce")
    return out


def _normalize_sequence_flags(seq_df: pd.DataFrame) -> pd.DataFrame:
    if seq_df.empty:
        return seq_df
    seq_df = seq_df.copy()
    for col in [
        "partial_then_expand_flag",
        "multi_rebase_flag",
        "rebase_integrity_flag",
        "same_symbol_repeat_flag",
        "same_ts_multi_rebase_flag",
    ]:
        if col in seq_df.columns:
            seq_df[col] = seq_df[col].astype(str).str.lower().isin(["true", "1"])
    if "rebase_count" in seq_df.columns:
        seq_df["rebase_count"] = pd.to_numeric(seq_df["rebase_count"], errors="coerce").fillna(0)
    return seq_df


def cohort_summary(trade_df: pd.DataFrame) -> list[dict]:
    valid = _valid_trades(trade_df)
    if valid.empty or "cohort" not in valid.columns:
        return []

    rows: list[dict] = []
    for cohort, group in valid.groupby("cohort"):
        count = len(group)
        win = int((group["profit_rate"] > 0).sum())
        mean_profit = round(_safe_mean(group["profit_rate"]), 3)
        simple_sum = round(float(group["profit_rate"].sum()), 3)
        rows.append(
            {
                "cohort": str(cohort),
                "n": int(count),
                "diagnostic_win_rate_pct": round((win / count) * 100, 1) if count else 0.0,
                "median_profit": round(_safe_median(group["profit_rate"]), 3),
                "equal_weight_avg_profit_pct": mean_profit,
                "simple_sum_profit_pct": simple_sum,
                "primary_decision_metric": "equal_weight_avg_profit_pct",
                "sufficient": count >= MIN_VALID_SAMPLES,
            }
        )
    return sorted(rows, key=lambda row: row["simple_sum_profit_pct"])


def extract_loss_patterns(trade_df: pd.DataFrame, seq_df: pd.DataFrame) -> list[dict]:
    valid = _normalize_trade_id(_valid_trades(trade_df))
    if valid.empty:
        return []

    loss_df = valid[valid["profit_rate"] <= 0].copy()
    if loss_df.empty:
        return []

    seq_df = _normalize_trade_id(_normalize_sequence_flags(seq_df))
    if not seq_df.empty:
        loss_df["trade_id"] = loss_df["trade_id"].astype("string").str.strip()
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
        loss_df = loss_df.merge(seq_view, on="trade_id", how="left")

    rows: list[dict] = []
    for (cohort, exit_rule), group in loss_df.groupby(["cohort", "exit_rule"], dropna=False):
        if not exit_rule:
            continue
        preconditions = {}
        for flag in [
            "partial_then_expand_flag",
            "multi_rebase_flag",
            "rebase_integrity_flag",
            "same_symbol_repeat_flag",
            "same_ts_multi_rebase_flag",
        ]:
            if flag not in group.columns:
                continue
            count = int(group[flag].fillna(False).sum())
            if count > 0:
                preconditions[flag] = {
                    "count": count,
                    "pct": round((count / len(group)) * 100, 1),
                }
        rows.append(
            {
                "cohort": str(cohort),
                "exit_rule": str(exit_rule),
                "n": int(len(group)),
                "median_profit": round(_safe_median(group["profit_rate"]), 3),
                "mean_profit": round(_safe_mean(group["profit_rate"]), 3),
                "equal_weight_avg_profit_pct": round(_safe_mean(group["profit_rate"]), 3),
                "simple_sum_profit_pct": round(float(group["profit_rate"].sum()), 3),
                "contrib_profit": round(float(group["profit_rate"].sum()), 3),
                "median_held_sec": round(_safe_median(group["held_sec"]), 1),
                "preconditions": preconditions,
            }
        )
    rows.sort(key=lambda row: abs(row["contrib_profit"]), reverse=True)
    return rows[:TOP_N_PATTERNS]


def extract_profit_patterns(trade_df: pd.DataFrame) -> list[dict]:
    valid = _normalize_trade_id(_valid_trades(trade_df))
    if valid.empty:
        return []

    profit_df = valid[valid["profit_rate"] > 0].copy()
    if profit_df.empty:
        return []

    rows: list[dict] = []
    for (cohort, exit_rule, entry_mode), group in profit_df.groupby(
        ["cohort", "exit_rule", "entry_mode"],
        dropna=False,
    ):
        if not exit_rule:
            continue
        rows.append(
            {
                "cohort": str(cohort),
                "exit_rule": str(exit_rule),
                "entry_mode": str(entry_mode),
                "n": int(len(group)),
                "median_profit": round(_safe_median(group["profit_rate"]), 3),
                "mean_profit": round(_safe_mean(group["profit_rate"]), 3),
                "equal_weight_avg_profit_pct": round(_safe_mean(group["profit_rate"]), 3),
                "simple_sum_profit_pct": round(float(group["profit_rate"].sum()), 3),
                "contrib_profit": round(float(group["profit_rate"].sum()), 3),
                "median_held_sec": round(_safe_median(group["held_sec"]), 1),
            }
        )
    rows.sort(key=lambda row: row["contrib_profit"], reverse=True)
    return rows[:TOP_N_PATTERNS]


def decompose_opportunity_cost(funnel_df: pd.DataFrame) -> list[dict]:
    if funnel_df.empty:
        return []

    rows: list[dict] = []
    for blocker, column in [
        ("AI threshold miss", "ai_threshold_block_events"),
        ("latency guard miss", "latency_block_events"),
        ("overbought gate miss", "overbought_block_events"),
        ("liquidity gate miss", "liquidity_block_events"),
    ]:
        if column not in funnel_df.columns:
            continue
        total_blocked = int(pd.to_numeric(funnel_df[column], errors="coerce").fillna(0).sum())
        if "submitted_events" in funnel_df.columns:
            submitted = int(pd.to_numeric(funnel_df["submitted_events"], errors="coerce").fillna(0).sum())
        else:
            submitted = 0
        total = total_blocked + submitted
        rows.append(
            {
                "blocker": blocker,
                "total_blocked": total_blocked,
                "block_ratio": round((total_blocked / total) * 100, 1) if total else 0.0,
                "days": int(funnel_df["date"].nunique()) if "date" in funnel_df.columns else 0,
            }
        )
    rows.sort(key=lambda row: row["total_blocked"], reverse=True)
    return rows[:TOP_N_PATTERNS]


def build_ev_backlog(
    cohort_rows: list[dict],
    loss_patterns: list[dict],
    opportunity_cost: list[dict],
) -> list[dict]:
    backlog: list[dict] = []
    negative_cohorts = [row for row in cohort_rows if row["simple_sum_profit_pct"] < 0]
    if negative_cohorts:
        worst = negative_cohorts[0]
        backlog.append(
            {
                "title": f"{worst['cohort']} EV 누수 분리 점검",
                "적용단계": "report_only_observation",
                "기대효과": f"{worst['cohort']} 코호트의 음수 EV 원인을 분리해 전역 조정 오판을 줄인다.",
                "검증지표": f"{worst['cohort']} 거래수, 손익 중앙값, 기여손익 합 재확인",
                "필요표본": f"{MIN_VALID_SAMPLES}건 이상 또는 연속 2일 동일 패턴",
            }
        )
    if loss_patterns:
        top_loss = loss_patterns[0]
        backlog.append(
            {
                "title": f"{top_loss['cohort']} / {top_loss['exit_rule']} 손실패턴 분해",
                "적용단계": "report_only_observation",
                "기대효과": "가장 큰 음수 기여 패턴을 별도 축으로 분리해 EV 누수 원인을 좁힌다.",
                "검증지표": f"빈도={top_loss['n']}, 중앙손익={top_loss['median_profit']:+.3f}%, 기여손익={top_loss['contrib_profit']:+.3f}%",
                "필요표본": "동일 패턴 10건 이상",
            }
        )
    for item in opportunity_cost[:2]:
        stage = "canary_only_candidate_after_workorder" if item["blocker"] == "AI threshold miss" else "report_only_observation"
        backlog.append(
            {
                "title": f"{item['blocker']} EV 회수 조건 점검",
                "적용단계": stage,
                "기대효과": f"{item['blocker']} 구간에서 놓친 기대값 회수 가능성을 검증한다.",
                "검증지표": f"차단건수={item['total_blocked']}, 차단비율={item['block_ratio']}%",
                "필요표본": "장중/장후 snapshot 동시 확인",
            }
        )
    return backlog[:TOP_N_PATTERNS]


def analyze_patterns() -> None:
    trade_df = _load_csv("trade_fact.csv")
    funnel_df = _load_csv("funnel_fact.csv")
    seq_df = _load_csv("sequence_fact.csv")

    if trade_df.empty and funnel_df.empty:
        print("trade/funnel dataset not found")
        return

    result = {
        "schema_version": SCHEMA_VERSION,
        "metric_contract": METRIC_CONTRACT,
        "cohort_summary": cohort_summary(trade_df),
        "loss_patterns": extract_loss_patterns(trade_df, seq_df),
        "profit_patterns": extract_profit_patterns(trade_df),
        "opportunity_cost": decompose_opportunity_cost(funnel_df),
    }
    result["ev_backlog"] = build_ev_backlog(
        result["cohort_summary"],
        result["loss_patterns"],
        result["opportunity_cost"],
    )

    output_path = config.OUTPUT_DIR / "ev_analysis_result.json"
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("EV analysis saved to ev_analysis_result.json")


if __name__ == "__main__":
    analyze_patterns()
