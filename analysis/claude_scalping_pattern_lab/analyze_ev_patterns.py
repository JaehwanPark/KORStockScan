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
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    MIN_VALID_PROFIT_SAMPLES,
    OUTPUT_DIR,
    SERVER_LOCAL,
    SOFT_STOP_RULES,
    TOP_N_PATTERNS,
    TRAILING_TP_RULES,
)


# ── 로드 ──────────────────────────────────────────────────────────────────────

def load_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def _safe_read(name: str) -> pd.DataFrame:
        p = OUTPUT_DIR / name
        if not p.exists():
            print(f"  [WARN] {name} not found — returning empty DataFrame")
            return pd.DataFrame()
        return pd.read_csv(p, encoding="utf-8", low_memory=False)

    trade_df  = _safe_read("trade_fact.csv")
    funnel_df = _safe_read("funnel_fact.csv")
    seq_df    = _safe_read("sequence_fact.csv")
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


# ── 손익 유효 행 필터 ─────────────────────────────────────────────────────────

def valid_trades(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    mask = df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
    return df[mask].copy()


# ── 코호트별 기본 통계 ────────────────────────────────────────────────────────

def cohort_summary(df: pd.DataFrame) -> list[dict]:
    vt = valid_trades(df)
    if vt.empty:
        return []

    results = []
    for cohort, grp in vt.groupby("cohort"):
        n = len(grp)
        win = (grp["profit_rate"] > 0).sum()
        loss = (grp["profit_rate"] <= 0).sum()
        results.append({
            "cohort":          cohort,
            "n":               int(n),
            "win":             int(win),
            "loss":            int(loss),
            "win_rate":        round(win / n * 100, 1) if n > 0 else 0.0,
            "median_profit":   round(_safe_median(grp["profit_rate"]), 3),
            "mean_profit":     round(_safe_mean(grp["profit_rate"]), 3),
            "sum_profit":      round(float(grp["profit_rate"].sum()), 3),
            "sufficient":      n >= MIN_VALID_PROFIT_SAMPLES,
        })
    return results


# ── 손실 패턴 Top N ───────────────────────────────────────────────────────────

def extract_loss_patterns(df: pd.DataFrame, seq_df: pd.DataFrame) -> list[dict]:
    """
    손실 패턴을 (cohort, exit_rule, entry_mode) 기준으로 집계해 Top N을 반환.
    코호트별 혼합 금지.
    """
    vt = valid_trades(df)
    if vt.empty:
        return []

    loss_df = vt[vt["profit_rate"] <= 0].copy()
    if loss_df.empty:
        return []

    # sequence_fact join
    if not seq_df.empty:
        seq_flags = seq_df[["trade_id", "multi_rebase_flag",
                             "partial_then_expand_flag", "rebase_integrity_flag",
                             "same_symbol_repeat_flag"]].drop_duplicates("trade_id")
        loss_df = loss_df.merge(seq_flags, on="trade_id", how="left")
        for col in ["multi_rebase_flag", "partial_then_expand_flag",
                    "rebase_integrity_flag", "same_symbol_repeat_flag"]:
            if col in loss_df.columns:
                loss_df[col] = loss_df[col].fillna(False)

    patterns: list[dict] = []
    for (cohort, exit_rule), grp in loss_df.groupby(["cohort", "exit_rule"]):
        if not exit_rule:
            continue
        n = len(grp)
        contrib = round(float(grp["profit_rate"].sum()), 3)
        held_med = round(_safe_median(grp["held_sec"]), 1) if "held_sec" in grp else None

        # 선행 조건 (플래그 분포)
        preconditions: dict[str, Any] = {}
        for flag in ["multi_rebase_flag", "partial_then_expand_flag",
                     "rebase_integrity_flag", "same_symbol_repeat_flag"]:
            if flag in grp.columns:
                cnt = int(grp[flag].sum())
                if cnt > 0:
                    preconditions[flag] = {"count": cnt, "pct": round(cnt / n * 100, 1)}

        patterns.append({
            "type":            "loss",
            "cohort":          cohort,
            "exit_rule":       exit_rule,
            "n":               int(n),
            "median_profit":   round(_safe_median(grp["profit_rate"]), 3),
            "contrib_profit":  contrib,
            "median_held_sec": held_med,
            "preconditions":   preconditions,
        })

    # 기여손익(절댓값) 내림차순 Top N
    patterns.sort(key=lambda x: abs(x["contrib_profit"]), reverse=True)
    return patterns[:TOP_N_PATTERNS]


# ── 수익 패턴 Top N ───────────────────────────────────────────────────────────

def extract_profit_patterns(df: pd.DataFrame) -> list[dict]:
    vt = valid_trades(df)
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
        patterns.append({
            "type":           "profit",
            "cohort":         cohort,
            "exit_rule":      exit_rule,
            "entry_mode":     entry_mode,
            "n":              int(n),
            "median_profit":  round(_safe_median(grp["profit_rate"]), 3),
            "mean_profit":    round(_safe_mean(grp["profit_rate"]), 3),
            "contrib_profit": round(float(grp["profit_rate"].sum()), 3),
            "median_held_sec": round(_safe_median(grp["held_sec"]), 1) if "held_sec" in grp else None,
        })

    patterns.sort(key=lambda x: x["contrib_profit"], reverse=True)
    return patterns[:TOP_N_PATTERNS]


# ── 기회비용 분해 ─────────────────────────────────────────────────────────────

def decompose_opportunity_cost(funnel_df: pd.DataFrame) -> list[dict]:
    if funnel_df.empty:
        return []

    result: list[dict] = []
    for blocker, col in [
        ("latency guard miss",   "latency_block_events"),
        ("AI threshold miss",    "ai_threshold_block_events"),
        ("overbought gate miss", "overbought_block_events"),
        ("liquidity gate miss",  "liquidity_block_events"),
    ]:
        if col not in funnel_df.columns:
            continue
        total = int(funnel_df[col].sum())
        submitted = int(funnel_df["submitted_events"].sum()) if "submitted_events" in funnel_df else 1
        block_ratio = round(total / (total + submitted) * 100, 1) if (total + submitted) > 0 else 0.0
        result.append({
            "blocker":       blocker,
            "total_blocked": total,
            "block_ratio":   block_ratio,
            "days":          int(funnel_df[col].notna().sum()),
        })

    result.sort(key=lambda x: x["total_blocked"], reverse=True)
    return result[:TOP_N_PATTERNS]


# ── EV 개선 backlog 생성 ──────────────────────────────────────────────────────

_EV_TEMPLATES: dict[str, dict] = {
    "split_entry_rebase_integrity": {
        "title":          "split-entry rebase 수량 정합성 shadow 감사",
        "기대효과":       "rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함",
        "리스크":         "false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능",
        "필요표본":       "rebase_integrity_flag 케이스 20건 이상",
        "검증지표":       "cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포",
        "적용단계":       "shadow-only",
    },
    "partial_expand_immediate_recheck": {
        "title":          "partial → fallback 확대 직후 즉시 재평가 shadow",
        "기대효과":       "나쁜 포지션 확대(확대 직후 peak_profit < 0) 코호트 조기 감지",
        "리스크":         "정상 확대 패턴도 일부 차단 가능 — shadow 관찰 선행 필수",
        "필요표본":       "partial_then_expand 코호트 30건 이상",
        "검증지표":       "확대 후 90초 내 held_sec soft stop 비율 감소 여부",
        "적용단계":       "shadow-only",
    },
    "same_symbol_cooldown": {
        "title":          "동일 종목 split-entry soft-stop 재진입 cooldown shadow",
        "기대효과":       "같은 날 동일 종목 반복 손절 누수 차단",
        "리스크":         "cooldown 중 missed upside 발생 가능 — 차단 건수와 missed upside를 함께 추적해야 함",
        "필요표본":       "same_symbol_repeat_flag 케이스 10건 이상",
        "검증지표":       "same-symbol repeat soft stop 건수, cooldown 차단 후 10분 missed upside",
        "적용단계":       "shadow-only",
    },
    "partial_only_timeout": {
        "title":          "partial-only 표류 전용 timeout shadow",
        "기대효과":       "1주 partial만 남긴 채 장시간 표류하는 케이스 조기 정리",
        "리스크":         "full fill 전 짧은 대기 케이스를 오분류할 수 있음",
        "필요표본":       "partial-only 코호트 20건 이상",
        "검증지표":       "partial-only held_sec 중앙값, timeout 이후 실현손익 분포",
        "적용단계":       "shadow-only",
    },
    "latency_canary_tag_expansion": {
        "title":          "latency canary tag 완화 1축 canary 승인",
        "기대효과":       "tag_not_allowed blocker 감소로 진입 기회 확대",
        "리스크":         "bugfix-only 실표본 관찰 전 추가 완화는 해석 가능성 저하",
        "필요표본":       "bugfix-only canary_applied 건수 50건 이상 (현재 19건)",
        "검증지표":       "latency_canary_applied 증가, low_signal / tag_not_allowed 감소",
        "적용단계":       "canary",
    },
}


def build_ev_backlog(
    loss_patterns: list[dict],
    profit_patterns: list[dict],
    opp_cost: list[dict],
    seq_df: pd.DataFrame,
) -> list[dict]:
    backlog: list[dict] = []

    # 시퀀스 플래그 기반 자동 우선순위
    flag_counts: dict[str, int] = {}
    if not seq_df.empty:
        for flag in ["rebase_integrity_flag", "partial_then_expand_flag",
                     "same_symbol_repeat_flag"]:
            if flag in seq_df.columns:
                flag_counts[flag] = int(seq_df[flag].sum())

    if flag_counts.get("rebase_integrity_flag", 0) > 0:
        backlog.append(_EV_TEMPLATES["split_entry_rebase_integrity"])
    if flag_counts.get("partial_then_expand_flag", 0) > 0:
        backlog.append(_EV_TEMPLATES["partial_expand_immediate_recheck"])
    if flag_counts.get("same_symbol_repeat_flag", 0) > 0:
        backlog.append(_EV_TEMPLATES["same_symbol_cooldown"])

    # 손실 패턴 기반 추가
    for lp in loss_patterns:
        if lp.get("exit_rule") in SOFT_STOP_RULES and lp.get("cohort") == "split-entry":
            if _EV_TEMPLATES["partial_only_timeout"] not in backlog:
                backlog.append(_EV_TEMPLATES["partial_only_timeout"])
            break

    # 기회비용 기반 추가
    for oc in opp_cost:
        if oc["blocker"] == "latency guard miss" and oc["total_blocked"] > 3000:
            backlog.append(_EV_TEMPLATES["latency_canary_tag_expansion"])
            break

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
            f"- **기대효과**: {item['기대효과']}",
            f"- **리스크**: {item['리스크']}",
            f"- **필요 표본**: {item['필요표본']}",
            f"- **검증 지표**: {item['검증지표']}",
            f"- **적용 단계**: `{item['적용단계']}`",
            "",
        ]

    path = OUTPUT_DIR / "ev_improvement_backlog_for_ops.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


# ── 진입점 ────────────────────────────────────────────────────────────────────

def main() -> dict:
    print("[analyze] loading datasets …")
    trade_df, funnel_df, seq_df = load_datasets()

    print("[analyze] cohort summary …")
    coh_summary = cohort_summary(trade_df)

    print("[analyze] loss patterns …")
    loss_patterns = extract_loss_patterns(trade_df, seq_df)

    print("[analyze] profit patterns …")
    profit_patterns = extract_profit_patterns(trade_df)

    print("[analyze] opportunity cost …")
    opp_cost = decompose_opportunity_cost(funnel_df)

    print("[analyze] EV backlog …")
    backlog = build_ev_backlog(loss_patterns, profit_patterns, opp_cost, seq_df)
    write_ev_backlog_md(backlog)

    result = {
        "generated_at":    datetime.now().isoformat(),
        "cohort_summary":  coh_summary,
        "loss_patterns":   loss_patterns,
        "profit_patterns": profit_patterns,
        "opportunity_cost": opp_cost,
        "ev_backlog":      backlog,
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
