"""
EV 패턴 분석 모듈.

입력:
  - outputs/trade_fact.csv
  - outputs/funnel_fact.csv
  - outputs/sequence_fact.csv

출력:
  - outputs/ev_analysis_result.json   (분석 결과 중간 산출물)
  - outputs/ev_improvement_backlog_for_ops.md
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from analysis.claude_scalping_pattern_lab import config
from analysis.claude_scalping_pattern_lab.economic_evidence import (
    build_evidence,
    finite,
    profit_followups,
    trading_dates,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from .config import (
        MIN_VALID_PROFIT_SAMPLES,
        OUTPUT_DIR,
        TOP_N_PATTERNS,
    )
except ImportError:  # pragma: no cover - direct script execution
    from config import (
        MIN_VALID_PROFIT_SAMPLES,
        OUTPUT_DIR,
        TOP_N_PATTERNS,
    )

SCHEMA_VERSION = 3
METRIC_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "pattern_lab_source_only_existing_strategy_handoff",
    "window_policy": "daily_rolling_10_trading_days_cumulative_separate",
    "sample_floor": 0,
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": "self_hashed_main_lifecycle_real_terminal_reconciled_costs; snapshot_metrics_diagnostic_only",
    "forbidden_uses": [
        "runtime_threshold_apply_without_deterministic_guard",
        "broker_order_enable",
        "provider_route_change",
        "bot_restart",
        "single_day_live_approval",
    ],
    "runtime_effect": False,
}


# ── 로드 ──────────────────────────────────────────────────────────────────────


def load_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def _safe_read(name: str) -> pd.DataFrame:
        p = OUTPUT_DIR / name
        if not p.exists():
            print(f"  [WARN] {name} not found — returning empty DataFrame")
            return pd.DataFrame()
        return pd.read_csv(p, encoding="utf-8", low_memory=False)

    trade_df = _safe_read("trade_fact.csv")
    funnel_df = _safe_read("funnel_fact.csv")
    seq_df = _safe_read("sequence_fact.csv")
    return trade_df, funnel_df, seq_df


# ── 유틸 ──────────────────────────────────────────────────────────────────────


def _safe_median(series: pd.Series) -> float:
    s = series.dropna()
    return float(s.median()) if len(s) > 0 else 0.0


def _safe_mean(series: pd.Series) -> float:
    s = series.dropna()
    return float(s.mean()) if len(s) > 0 else 0.0


def _pct_str(val: float) -> str:
    return f"{val:+.2f}%"


def _normalize_trade_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "trade_id" not in df.columns:
        return df
    out = df.copy()
    out["trade_id"] = out["trade_id"].astype("string").str.strip()
    return out


# ── 손익 유효 행 필터 ─────────────────────────────────────────────────────────


def valid_trades(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    mask = df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
    mask &= df["profit_rate"].map(lambda v: finite(v) is not None)
    mask &= df["status"].eq("COMPLETED")
    return df[mask].copy()


# ── 코호트별 기본 통계 ────────────────────────────────────────────────────────


def cohort_summary(df: pd.DataFrame) -> list[dict]:
    vt = _normalize_trade_id(valid_trades(df))
    if vt.empty:
        return []

    results = []
    for cohort, grp in vt.groupby("cohort"):
        n = len(grp)
        win = (grp["profit_rate"] > 0).sum()
        loss = (grp["profit_rate"] <= 0).sum()
        mean_profit = round(_safe_mean(grp["profit_rate"]), 3)
        simple_sum = round(float(grp["profit_rate"].sum()), 3)
        results.append(
            {
                "cohort": cohort,
                "n": int(n),
                "win": int(win),
                "loss": int(loss),
                "diagnostic_win_rate_pct": round(win / n * 100, 1) if n > 0 else 0.0,
                "median_profit": round(_safe_median(grp["profit_rate"]), 3),
                "equal_weight_avg_profit_pct": mean_profit,
                "simple_sum_profit_pct": simple_sum,
                "primary_decision_metric": "equal_weight_avg_profit_pct",
                "sufficient": n >= MIN_VALID_PROFIT_SAMPLES,
            }
        )
    return results


# ── 손실 패턴 Top N ───────────────────────────────────────────────────────────


def extract_loss_patterns(df: pd.DataFrame, seq_df: pd.DataFrame) -> list[dict]:
    """
    손실 패턴을 (cohort, exit_rule, entry_mode) 기준으로 집계해 Top N을 반환.
    코호트별 혼합 금지.
    """
    vt = _normalize_trade_id(valid_trades(df))
    if vt.empty:
        return []

    loss_df = vt[vt["profit_rate"] <= 0].copy()
    if loss_df.empty:
        return []

    # sequence_fact join
    seq_df = _normalize_trade_id(seq_df)
    if (
        not seq_df.empty
        and {"trade_id", "date"} <= set(seq_df.columns)
        and "rec_date" in loss_df
    ):
        loss_df["trade_id"] = loss_df["trade_id"].astype("string").str.strip()
        flag_cols = [
            "multi_rebase_flag",
            "partial_then_expand_flag",
            "rebase_integrity_flag",
            "same_symbol_repeat_flag",
        ]
        keys = ["trade_id", "rec_date"]
        seq_cols = ["trade_id", "date", *[c for c in flag_cols if c in seq_df]]
        seq_flags = seq_df[seq_cols].rename(columns={"date": "rec_date"})
        seq_flags["trade_id"] = seq_flags["trade_id"].astype("string").str.strip()
        seq_flags = seq_flags.dropna(subset=keys)
        seq_flags = seq_flags[
            seq_flags["trade_id"].ne("") & seq_flags["rec_date"].ne("")
        ].drop_duplicates(keys, keep=False)
        # Prepared fields own date-bound flags. Only supplement absent fields
        # with exact-date unique evidence; never use an ID-only fallback.
        missing_cols = [c for c in flag_cols if c in seq_flags and c not in loss_df]
        if missing_cols:
            loss_df = loss_df.merge(
                seq_flags[[*keys, *missing_cols]],
                on=keys,
                how="left",
                validate="many_to_one",
            )
        for col in flag_cols:
            if col in loss_df.columns:
                loss_df[col] = loss_df[col].fillna(False)

    patterns: list[dict] = []
    for (cohort, exit_rule), grp in loss_df.groupby(["cohort", "exit_rule"]):
        if not exit_rule:
            continue
        n = len(grp)
        contrib = round(float(grp["profit_rate"].sum()), 3)
        held_med = (
            round(_safe_median(grp["held_sec"]), 1) if "held_sec" in grp else None
        )

        # 선행 조건 (플래그 분포)
        preconditions: dict[str, Any] = {}
        for flag in [
            "multi_rebase_flag",
            "partial_then_expand_flag",
            "rebase_integrity_flag",
            "same_symbol_repeat_flag",
        ]:
            if flag in grp.columns:
                cnt = int(grp[flag].sum())
                if cnt > 0:
                    preconditions[flag] = {"count": cnt, "pct": round(cnt / n * 100, 1)}

        patterns.append(
            {
                "type": "loss",
                "cohort": cohort,
                "exit_rule": exit_rule,
                "n": int(n),
                "median_profit": round(_safe_median(grp["profit_rate"]), 3),
                "equal_weight_avg_profit_pct": round(_safe_mean(grp["profit_rate"]), 3),
                "simple_sum_profit_pct": contrib,
                "contrib_profit": contrib,
                "median_held_sec": held_med,
                "preconditions": preconditions,
            }
        )

    # 기여손익(절댓값) 내림차순 Top N
    patterns.sort(key=lambda x: abs(x["contrib_profit"]), reverse=True)
    return patterns[:TOP_N_PATTERNS]


# ── 수익 패턴 Top N ───────────────────────────────────────────────────────────


def extract_profit_patterns(df: pd.DataFrame) -> list[dict]:
    vt = _normalize_trade_id(valid_trades(df))
    if vt.empty:
        return []

    profit_df = vt[vt["profit_rate"] > 0].copy()
    if profit_df.empty:
        return []

    patterns: list[dict] = []
    for (cohort, exit_rule, entry_mode), grp in profit_df.groupby(
        ["cohort", "exit_rule", "entry_mode"]
    ):
        if not exit_rule:
            continue
        n = len(grp)
        patterns.append(
            {
                "type": "profit",
                "cohort": cohort,
                "exit_rule": exit_rule,
                "entry_mode": entry_mode,
                "n": int(n),
                "median_profit": round(_safe_median(grp["profit_rate"]), 3),
                "equal_weight_avg_profit_pct": round(_safe_mean(grp["profit_rate"]), 3),
                "mean_profit": round(_safe_mean(grp["profit_rate"]), 3),
                "simple_sum_profit_pct": round(float(grp["profit_rate"].sum()), 3),
                "contrib_profit": round(float(grp["profit_rate"].sum()), 3),
                "median_held_sec": (
                    round(_safe_median(grp["held_sec"]), 1)
                    if "held_sec" in grp
                    else None
                ),
            }
        )

    patterns.sort(key=lambda x: x["contrib_profit"], reverse=True)
    return patterns[:TOP_N_PATTERNS]


# ── 기회비용 분해 ─────────────────────────────────────────────────────────────


def decompose_opportunity_cost(funnel_df: pd.DataFrame) -> list[dict]:
    if funnel_df.empty:
        return []

    result: list[dict] = []
    for blocker, col in [
        ("latency guard miss", "latency_block_events"),
        ("AI threshold miss", "ai_threshold_block_events"),
        ("overbought gate miss", "overbought_block_events"),
        ("liquidity gate miss", "liquidity_block_events"),
    ]:
        if col not in funnel_df.columns:
            continue
        values = funnel_df[col].map(finite)
        values = pd.to_numeric(values, errors="coerce")
        values = values.where(values >= 0)
        if not values.notna().any():
            continue
        total = int(values.sum())
        submitted_values = (
            pd.to_numeric(funnel_df["submitted_events"].map(finite), errors="coerce")
            if "submitted_events" in funnel_df
            else pd.Series(dtype=float)
        )
        submitted_known = (
            len(submitted_values) == len(values)
            and submitted_values.notna().all()
            and values.notna().all()
            and (submitted_values >= 0).all()
        )
        submitted = int(submitted_values.sum()) if submitted_known else 0
        block_ratio = (
            None
            if not submitted_known
            else (
                round(total / (total + submitted) * 100, 1)
                if (total + submitted) > 0
                else 0.0
            )
        )
        result.append(
            {
                "blocker": blocker,
                "total_blocked": total,
                "block_ratio": block_ratio,
                "days": int(values.notna().sum()),
                "metric_role": "funnel_count_not_missed_ev",
            }
        )

    result.sort(key=lambda x: x["total_blocked"], reverse=True)
    return result[:TOP_N_PATTERNS]


# ── EV 개선 backlog 생성 ──────────────────────────────────────────────────────

_EV_TEMPLATES: dict[str, dict] = {
    "split_entry_rebase_integrity": {
        "title": "split-entry rebase 수량 정합성 report-only 감사",
        "기대효과": "rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함",
        "리스크": "false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능",
        "필요표본": "재현 가능한 결함 증거; 경제성/승격 표본 floor 없음",
        "검증지표": "cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포",
        "적용단계": "report_only_observation",
    },
    "same_symbol_cooldown": {
        "title": "same-symbol repeat source attribution",
        "기대효과": "반복 거래의 수익과 손실을 함께 분리해 원인 관찰",
        "리스크": "반복 횟수만으로 cooldown 또는 매수 차단 불가",
        "필요표본": "재현 가능한 identity/sequence 증거; 별도 승격 floor 없음",
        "검증지표": "same_symbol_repeat_flag count; exact lifecycle net economics",
        "적용단계": "report_only_observation",
    },
    "partial_only_timeout": {
        "title": "partial fill quality source attribution",
        "기대효과": "partial/full 품질을 분리해 수익률 착시 방지",
        "리스크": "관찰만으로 timeout/수량/진입조건 변경 불가",
        "필요표본": "재현 가능한 fill identity 증거; 별도 승격 floor 없음",
        "검증지표": "partial_then_expand_flag count; exact partial/full net economics",
        "적용단계": "report_only_observation",
    },
}


def build_ev_backlog(
    loss_patterns: list[dict],
    profit_patterns: list[dict],
    opp_cost: list[dict],
    seq_df: pd.DataFrame,
    economics: dict | None = None,
) -> list[dict]:
    backlog: list[dict] = []

    # 시퀀스 플래그 기반 자동 우선순위
    flag_counts: dict[str, int] = {}
    if not seq_df.empty:
        for flag in [
            "rebase_integrity_flag",
            "partial_then_expand_flag",
            "same_symbol_repeat_flag",
        ]:
            if flag in seq_df.columns:
                flag_counts[flag] = int(seq_df[flag].sum())

    for flag, key in (
        ("rebase_integrity_flag", "split_entry_rebase_integrity"),
        ("partial_then_expand_flag", "partial_only_timeout"),
        ("same_symbol_repeat_flag", "same_symbol_cooldown"),
    ):
        if flag_counts.get(flag, 0) > 0:
            backlog.append(
                {
                    **_EV_TEMPLATES[key],
                    "diagnostic_source": {"field": flag, "count": flag_counts[flag]},
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
    # Display profit_patterns are intentionally not approval evidence. The
    # exact-cost all-outcome cohort (including losses) owns economic followups.
    if economics:
        backlog.extend(profit_followups(economics))

    return backlog


# ── ops backlog 마크다운 출력 ─────────────────────────────────────────────────


def write_ev_backlog_md(backlog: list[dict]) -> None:
    lines = [
        "# EV 개선 후보 백로그 (for Ops)",
        "",
        f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]
    for i, item in enumerate(backlog, 1):
        lines += [
            f"## {i}. {item['title']}",
            "",
            f"- **기대효과**: {item.get('기대효과', item.get('expected_effect'))}",
            f"- **리스크**: {item.get('리스크', item.get('risk'))}",
            f"- **필요 표본**: {item.get('필요표본', item.get('required_sample'))}",
            f"- **검증 지표**: {item.get('검증지표', item.get('metric'))}",
            f"- **적용 단계**: `{item.get('적용단계', item.get('apply_stage'))}`",
            "",
        ]

    path = OUTPUT_DIR / "ev_improvement_backlog_for_ops.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


# ── 진입점 ────────────────────────────────────────────────────────────────────


def main() -> dict:
    print("[analyze] loading datasets …")
    trade_df, funnel_df, seq_df = load_datasets()
    target = config.ANALYSIS_END.isoformat()
    expected = trading_dates(config.ANALYSIS_START, config.ANALYSIS_END)
    source_path = OUTPUT_DIR / "source_manifest.json"
    source = json.loads(source_path.read_text()) if source_path.exists() else {}
    covered = sorted(set(source.get("covered_dates") or []) & set(expected))
    if source.get("target_date") != target:
        covered = []
    for frame, column in (
        (trade_df, "rec_date"),
        (funnel_df, "date"),
        (seq_df, "date"),
    ):
        if not frame.empty:
            frame.drop(
                (
                    frame.index[~frame[column].isin(covered)]
                    if column in frame
                    else frame.index
                ),
                inplace=True,
            )
    economics = build_evidence(
        config.PROJECT_ROOT / "data/report/main_scalping_lifecycle_paired",
        config.ANALYSIS_START,
        config.ANALYSIS_END,
    )

    print("[analyze] cohort summary …")
    coh_summary = cohort_summary(trade_df)

    print("[analyze] loss patterns …")
    loss_patterns = extract_loss_patterns(trade_df, seq_df)

    print("[analyze] profit patterns …")
    profit_patterns = extract_profit_patterns(trade_df)

    print("[analyze] opportunity cost …")
    opp_cost = decompose_opportunity_cost(funnel_df)

    print("[analyze] EV backlog …")
    backlog = build_ev_backlog(
        loss_patterns, profit_patterns, opp_cost, seq_df, economics
    )
    write_ev_backlog_md(backlog)

    result = {
        "schema_version": SCHEMA_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_contract": METRIC_CONTRACT,
        "generated_at": datetime.now().isoformat(),
        "date": target,
        "economics": economics,
        "source_isolation": {
            "schema": "pattern_lab_date_isolation_v1",
            "target_date": target,
            "status": (
                "isolated"
                if covered or economics["sources"]
                else "missing_source_contract"
            ),
            "included_dates": sorted(set(covered) | set(economics["sources"])),
            "snapshot_included_dates": covered,
            "excluded_dates": sorted(
                set(expected) - set(covered) - set(economics["sources"])
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "snapshot_metric_role": "unverified_display_diagnostic_not_economic_approval",
        "cohort_summary": coh_summary,
        "loss_patterns": loss_patterns,
        "profit_patterns": profit_patterns,
        "opportunity_cost": opp_cost,
        "ev_backlog": backlog,
    }

    out_path = OUTPUT_DIR / "ev_analysis_result.json"
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[analyze] → {out_path}")
    print("[analyze] done.")
    return result


if __name__ == "__main__":
    main()
