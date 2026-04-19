"""
Claude 투입용 JSON 패키지 빌더.

입력:
  - outputs/trade_fact.csv
  - outputs/sequence_fact.csv
  - outputs/ev_analysis_result.json

출력:
  - outputs/claude_payload_summary.json   (요약 통계)
  - outputs/claude_payload_cases.json     (대표 케이스)
  - outputs/final_review_report_for_lead_ai.md
  - outputs/run_manifest.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    MIN_VALID_PROFIT_SAMPLES,
    OUTPUT_DIR,
    SOFT_STOP_RULES,
    TOP_N_PATTERNS,
    TRAILING_TP_RULES,
)

LAB_DIR = Path(__file__).resolve().parent


# ── 로드 ──────────────────────────────────────────────────────────────────────

def _load_json(name: str) -> dict:
    p = OUTPUT_DIR / name
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _load_csv(name: str) -> pd.DataFrame:
    p = OUTPUT_DIR / name
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8", low_memory=False)


# ── 요약 통계 payload ─────────────────────────────────────────────────────────

def build_summary_payload(ev_result: dict, trade_df: pd.DataFrame) -> dict:
    # 유효 거래 필터
    if not trade_df.empty:
        valid_mask = trade_df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
        vt = trade_df[valid_mask]
    else:
        vt = pd.DataFrame()

    # 일별 거래 현황
    daily_stats: list[dict] = []
    if not vt.empty and "rec_date" in vt.columns:
        for dt, grp in vt.groupby("rec_date"):
            daily_stats.append({
                "date":          str(dt),
                "n_trades":      int(len(grp)),
                "win_rate":      round((grp["profit_rate"] > 0).mean() * 100, 1),
                "median_profit": round(float(grp["profit_rate"].median()), 3),
                "sum_profit":    round(float(grp["profit_rate"].sum()), 3),
            })

    # 코호트별 통계
    cohort_stats = ev_result.get("cohort_summary", [])
    for cs in cohort_stats:
        srv_valid = vt[vt["cohort"] == cs["cohort"]].shape[0] if not vt.empty else 0
        cs["sample_sufficient"] = srv_valid >= MIN_VALID_PROFIT_SAMPLES

    payload: dict = {
        "meta": {
            "analysis_period": f"{ANALYSIS_START} ~ {ANALYSIS_END}",
            "generated_at":    datetime.now().isoformat(),
            "total_valid_trades": int(len(vt)),
            "cohorts":         ["full_fill", "partial_fill", "split-entry"],
        },
        "cohort_summary":   cohort_stats,
        "loss_patterns":    ev_result.get("loss_patterns", []),
        "profit_patterns":  ev_result.get("profit_patterns", []),
        "opportunity_cost": ev_result.get("opportunity_cost", []),
        "ev_backlog_titles": [b["title"] for b in ev_result.get("ev_backlog", [])],
        "daily_stats":      daily_stats,
        "instructions": {
            "rule_1": "full_fill / partial_fill / split-entry 혼합 해석 금지",
            "rule_2": "전역 손절 강화 같은 단일축 일반화 결론 금지",
            "rule_3": "운영 코드 즉시 변경 지시 금지",
            "output_required": [
                "손실 패턴 Top 5",
                "수익 패턴 Top 5",
                "기회비용 회수 후보 Top 5",
                "EV 개선 우선순위 (shadow-only → canary → 승격 순)",
            ],
        },
    }
    return payload


# ── 대표 케이스 payload ───────────────────────────────────────────────────────

def build_cases_payload(
    trade_df: pd.DataFrame,
    seq_df: pd.DataFrame,
) -> dict:
    cases: dict[str, list[dict]] = {
        "loss_split_entry":  [],
        "loss_full_fill":    [],
        "profit_split_entry": [],
        "profit_full_fill":  [],
        "integrity_flagged": [],
    }

    if trade_df.empty:
        return cases

    valid_mask = trade_df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
    vt = trade_df[valid_mask].copy()
    if vt.empty:
        return cases

    # seq_df join
    if not seq_df.empty:
        seq_key = seq_df[["trade_id", "multi_rebase_flag", "partial_then_expand_flag",
                           "rebase_integrity_flag", "same_symbol_repeat_flag",
                           "rebase_count"]].drop_duplicates("trade_id")
        vt = vt.merge(seq_key, on="trade_id", how="left")

    def _row_to_case(row: pd.Series) -> dict:
        d: dict = {
            "trade_id":   int(row.get("trade_id", 0)),
            "symbol":     str(row.get("symbol", "")),
            "name":       str(row.get("name", "")),
            "cohort":     str(row.get("cohort", "")),
            "entry_mode": str(row.get("entry_mode", "")),
            "exit_rule":  str(row.get("exit_rule", "")),
            "profit_rate": float(row.get("profit_rate", 0.0)),
            "held_sec":   row.get("held_sec"),
            "rec_date":   str(row.get("rec_date", "")),
        }
        for flag in ["multi_rebase_flag", "partial_then_expand_flag",
                     "rebase_integrity_flag", "same_symbol_repeat_flag"]:
            if flag in row.index:
                d[flag] = bool(row[flag]) if pd.notna(row[flag]) else False
        if "rebase_count" in row.index:
            d["rebase_count"] = int(row["rebase_count"]) if pd.notna(row["rebase_count"]) else 0
        return d

    # 손실 케이스
    loss_df = vt[vt["profit_rate"] <= 0].sort_values("profit_rate")
    for _, row in loss_df[loss_df.get("cohort", pd.Series()) == "split-entry"].head(5).iterrows():
        cases["loss_split_entry"].append(_row_to_case(row))
    for _, row in loss_df[loss_df.get("cohort", pd.Series()) == "full_fill"].head(5).iterrows():
        cases["loss_full_fill"].append(_row_to_case(row))

    # 수익 케이스
    profit_df = vt[vt["profit_rate"] > 0].sort_values("profit_rate", ascending=False)
    for _, row in profit_df[profit_df.get("cohort", pd.Series()) == "split-entry"].head(5).iterrows():
        cases["profit_split_entry"].append(_row_to_case(row))
    for _, row in profit_df[profit_df.get("cohort", pd.Series()) == "full_fill"].head(5).iterrows():
        cases["profit_full_fill"].append(_row_to_case(row))

    # 정합성 플래그 케이스
    if "rebase_integrity_flag" in vt.columns:
        flag_df = vt[vt["rebase_integrity_flag"].astype(str).str.lower().isin(["true", "1"])]
        for _, row in flag_df.head(10).iterrows():
            cases["integrity_flagged"].append(_row_to_case(row))

    return cases


# ── 최종 리뷰 보고서 (for lead AI) ───────────────────────────────────────────

def write_final_review_report(
    ev_result: dict,
    trade_df: pd.DataFrame,
    seq_df: pd.DataFrame,
) -> None:
    loss_patterns  = ev_result.get("loss_patterns", [])
    profit_patterns = ev_result.get("profit_patterns", [])
    opp_cost       = ev_result.get("opportunity_cost", [])
    backlog        = ev_result.get("ev_backlog", [])
    coh_summary    = ev_result.get("cohort_summary", [])

    # 표본 부족 서버 목록
    insufficient_note = ""
    if not trade_df.empty:
        valid_mask = trade_df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
        n_valid = int(valid_mask.sum())
        if n_valid < MIN_VALID_PROFIT_SAMPLES:
            insufficient_note = (
                f"\n> ⚠️ **표본 부족**: valid_profit_rate={n_valid}건 < {MIN_VALID_PROFIT_SAMPLES}. "
                "결론 확정 금지, 후속 수집 제안만 작성.\n"
            )

    lines = [
        "# 스캘핑 패턴 분석 최종 리뷰 보고서 (for Lead AI)",
        "",
        f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"분석 기간: {ANALYSIS_START} ~ {ANALYSIS_END}",
    ]
    if insufficient_note:
        lines.append(insufficient_note)

    lines += [
        "",
        "---",
        "",
        "## 1. 판정",
        "",
    ]

    # 코호트별 판정
    if coh_summary:
        lines.append("### 1-1. 코호트별 손익 요약")
        lines.append("")
        lines.append("| 코호트 | 거래수 | 승률 | 손익 중앙값 | 기여손익 합 | 표본충분 |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for cs in coh_summary:
            suf = "✓" if cs.get("sufficient") or cs.get("sample_sufficient") else "⚠️부족"
            lines.append(
                f"| {cs['cohort']} | {cs['n']} | {cs['win_rate']}% "
                f"| {cs['median_profit']:+.3f}% | {cs['sum_profit']:+.3f}% | {suf} |"
            )
        lines.append("")

    # 손실 패턴
    lines += ["### 1-2. 손실 패턴 Top 5", ""]
    if not loss_patterns:
        lines.append("- 분석 대상 없음")
    for i, lp in enumerate(loss_patterns, 1):
        pre = ", ".join(
            f"{k}={v['count']}건({v['pct']}%)"
            for k, v in lp.get("preconditions", {}).items()
        ) or "없음"
        lines += [
            f"**#{i}** — 코호트: `{lp['cohort']}` / 청산규칙: `{lp['exit_rule']}`",
            f"- 빈도: {lp['n']}건 | 손익 중앙값: {lp['median_profit']:+.3f}% | 기여손익: {lp['contrib_profit']:+.3f}%",
            f"- 보유시간 중앙값: {lp.get('median_held_sec', '-')}초",
            f"- 선행 조건: {pre}",
            "",
        ]

    # 수익 패턴
    lines += ["### 1-3. 수익 패턴 Top 5", ""]
    if not profit_patterns:
        lines.append("- 분석 대상 없음")
    for i, pp in enumerate(profit_patterns, 1):
        lines += [
            f"**#{i}** — 코호트: `{pp['cohort']}` / 청산규칙: `{pp['exit_rule']}` / 진입모드: `{pp['entry_mode']}`",
            f"- 빈도: {pp['n']}건 | 손익 중앙값: {pp['median_profit']:+.3f}% | 기여손익: {pp['contrib_profit']:+.3f}%",
            "",
        ]

    # 기회비용
    lines += ["### 1-4. 기회비용 회수 후보 Top 5", ""]
    if not opp_cost:
        lines.append("- 데이터 없음")
    for i, oc in enumerate(opp_cost, 1):
        lines += [
            f"**#{i}** — `{oc['blocker']}`",
            f"- 차단 건수 합계: {oc['total_blocked']}건 | 차단 비율: {oc['block_ratio']}% | 관찰 일수: {oc['days']}일",
            "",
        ]

    # 리스크
    lines += [
        "---",
        "",
        "## 2. 근거",
        "",
        "### 2-1. split-entry 코호트 핵심 위험",
        "",
    ]

    if not seq_df.empty:
        def _seq_stat(col: str) -> int:
            return int(seq_df[col].sum()) if col in seq_df.columns else 0
        lines += [
            f"- rebase_integrity_flag: {_seq_stat('rebase_integrity_flag')}건",
            f"- partial_then_expand_flag: {_seq_stat('partial_then_expand_flag')}건",
            f"- same_symbol_repeat_flag: {_seq_stat('same_symbol_repeat_flag')}건",
            f"- same_ts_multi_rebase_flag: {_seq_stat('same_ts_multi_rebase_flag')}건",
        ]
    else:
        lines.append("- sequence_fact 없음")

    lines += [
        "",
        "### 2-2. 전역 손절 강화 비권고 이유",
        "",
        "- 오늘 손절 표본에는 AI score 58~69처럼 낮지 않은 값도 포함됨.",
        "- 문제의 핵심은 `틱 급변 + 확대 타이밍`이며, 전역 강화는 승자도 함께 절단함.",
        "- 코호트 분리 없이 단일 임계값 강화 시 full_fill 수익 코호트에 부정적 영향.",
        "",
    ]

    # 다음 액션
    lines += [
        "---",
        "",
        "## 3. 다음 액션",
        "",
        "### 3-1. EV 개선 우선순위 (shadow-only 선행)",
        "",
    ]
    shadow_items = [b for b in backlog if b.get("적용단계") == "shadow-only"]
    canary_items = [b for b in backlog if b.get("적용단계") == "canary"]
    hold_items   = [b for b in backlog if b.get("적용단계") == "hold"]

    lines.append("**shadow-only (즉시 시작 가능):**")
    lines.append("")
    for b in shadow_items:
        lines.append(f"- `{b['title']}` — 검증지표: {b['검증지표']}")
    if not shadow_items:
        lines.append("- 없음")

    lines += ["", "**canary (shadow 결과 확인 후):**", ""]
    for b in canary_items:
        lines.append(f"- `{b['title']}` — 필요표본: {b['필요표본']}")
    if not canary_items:
        lines.append("- 없음")

    lines += ["", "**승격 후보 (canary 통과 후):**", ""]
    for b in hold_items:
        lines.append(f"- `{b['title']}`")
    if not hold_items:
        lines.append("- 없음")

    lines += [
        "",
        "### 3-2. 금지 사항",
        "",
        "- `full_fill / partial_fill / split-entry` 혼합 결론 금지",
        "- 운영 코드 즉시 변경 지시 금지",
        "- 전역 soft_stop 강화 같은 단일축 일반화 결론 금지",
        "",
        "---",
        "",
        "## 4. 참고 문서",
        "",
        "- [data_quality_report.md](data_quality_report.md)",
        "- [ev_improvement_backlog_for_ops.md](ev_improvement_backlog_for_ops.md)",
        "- [claude_payload_summary.json](claude_payload_summary.json)",
        "- [claude_payload_cases.json](claude_payload_cases.json)",
    ]

    path = OUTPUT_DIR / "final_review_report_for_lead_ai.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


# ── run_manifest ──────────────────────────────────────────────────────────────

def write_run_manifest(trade_df: pd.DataFrame, funnel_df: pd.DataFrame, seq_df: pd.DataFrame) -> None:
    manifest = {
        "run_at":  datetime.now().isoformat(),
        "version": "1.0.0",
        "inputs":  [],
        "outputs": [],
    }

    for fname, df in [
        ("trade_fact.csv", trade_df),
        ("funnel_fact.csv", funnel_df),
        ("sequence_fact.csv", seq_df),
    ]:
        p = OUTPUT_DIR / fname
        manifest["inputs"].append({
            "file":  fname,
            "rows":  int(len(df)) if not df.empty else 0,
            "exists": p.exists(),
        })

    for fname in [
        "data_quality_report.md",
        "ev_analysis_result.json",
        "ev_improvement_backlog_for_ops.md",
        "claude_payload_summary.json",
        "claude_payload_cases.json",
        "final_review_report_for_lead_ai.md",
        "run_manifest.json",
    ]:
        p = OUTPUT_DIR / fname
        manifest["outputs"].append({"file": fname, "exists": p.exists()})

    path = OUTPUT_DIR / "run_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {path}")


# ── 진입점 ────────────────────────────────────────────────────────────────────

def main() -> None:
    print("[payload] loading datasets …")
    ev_result = _load_json("ev_analysis_result.json")
    trade_df  = _load_csv("trade_fact.csv")
    seq_df    = _load_csv("sequence_fact.csv")
    funnel_df = _load_csv("funnel_fact.csv")

    print("[payload] building summary payload …")
    summary = build_summary_payload(ev_result, trade_df)
    (OUTPUT_DIR / "claude_payload_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("[payload] building cases payload …")
    cases = build_cases_payload(trade_df, seq_df)
    (OUTPUT_DIR / "claude_payload_cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("[payload] writing final review report …")
    write_final_review_report(ev_result, trade_df, seq_df)

    print("[payload] writing run manifest …")
    write_run_manifest(trade_df, funnel_df, seq_df)

    print("[payload] done.")


if __name__ == "__main__":
    main()
