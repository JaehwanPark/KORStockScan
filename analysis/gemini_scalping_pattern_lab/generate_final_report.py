import datetime
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from . import config
except ImportError:  # pragma: no cover - direct script execution
    import config
from tuning_observability_summary import write_tuning_observability_outputs


def _load_json(name: str) -> dict:
    path = config.OUTPUT_DIR / name
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_csv(name: str) -> pd.DataFrame:
    path = config.OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8", low_memory=False)


def _write_pattern_report(ev_result: dict, observability: dict) -> None:
    loss_patterns = ev_result.get("loss_patterns", [])
    profit_patterns = ev_result.get("profit_patterns", [])
    opportunity_cost = ev_result.get("opportunity_cost", [])

    lines = [
        "# Gemini EV Pattern Analysis Report",
        "",
        "## 1. EV 관점 핵심 판정",
        "",
        "- 목적: EV 성과를 극대화하기 위한 튜닝 포인트를 코호트/패턴/기회비용 기준으로 점검한다.",
        "- 보조 관찰축: Plan Rebase 이후 `WAIT65~79`, `blocked_ai_score`, `gatekeeper latency`, `submitted` 단절을 함께 본다.",
        "",
        "## 2. Plan Rebase 관찰축 요약",
        "",
        f"- `WAIT65~79 total_candidates={observability['buy_recovery_canary']['total_candidates']}`",
        f"- `recovery_check={observability['buy_recovery_canary']['recovery_check_candidates']}`, `promoted={observability['buy_recovery_canary']['recovery_promoted_candidates']}`, `submitted={observability['buy_recovery_canary']['submitted_candidates']}`",
        f"- `blocked_ai_score_share={observability['buy_recovery_canary']['blocked_ai_score_share_pct']:.1f}%`, `gatekeeper_eval_ms_p95={observability['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms`",
        "",
        "## 3. 손실 패턴 (Top 5)",
        "",
    ]

    if not loss_patterns:
        lines.append("- 분석 대상 없음")
    for index, row in enumerate(loss_patterns, 1):
        lines.append(f"### {index}. {row['cohort']} / {row['exit_rule']}")
        lines.append(
            f"- 판정: 음수 EV 기여 패턴"
        )
        lines.append(
            f"- 근거: 발생 {row['n']}건, 중앙손익 {row['median_profit']:+.3f}%, 평균손익 {row['mean_profit']:+.3f}%, 기여손익 {row['contrib_profit']:+.3f}%"
        )
        lines.append(
            "- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 report-only로 분리 점검"
        )
        lines.append("")

    lines += ["## 4. 수익 패턴 (Top 5)", ""]
    if not profit_patterns:
        lines.append("- 분석 대상 없음")
    for index, row in enumerate(profit_patterns, 1):
        lines.append(f"### {index}. {row['cohort']} / {row['exit_rule']} / {row['entry_mode']}")
        lines.append("- 판정: 양수 EV 기여 패턴")
        lines.append(
            f"- 근거: 발생 {row['n']}건, 중앙손익 {row['median_profit']:+.3f}%, 평균손익 {row['mean_profit']:+.3f}%, 기여손익 {row['contrib_profit']:+.3f}%"
        )
        lines.append("- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선")
        lines.append("")

    lines += ["## 5. 기회비용 분해", ""]
    if not opportunity_cost:
        lines.append("- 데이터 없음")
    for index, row in enumerate(opportunity_cost, 1):
        lines.append(f"### {index}. {row['blocker']}")
        lines.append(
            f"- 판정: EV 회수 우선 후보"
        )
        lines.append(
            f"- 근거: 차단건수 {row['total_blocked']}건, 차단비율 {row['block_ratio']}%, 관찰일수 {row['days']}일"
        )
        lines.append("- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속")
        lines.append("")

    (config.OUTPUT_DIR / "pattern_analysis_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _write_ev_backlog(ev_result: dict, observability: dict) -> None:
    backlog = list(ev_result.get("ev_backlog", []))
    backlog.append(
        {
            "title": "WAIT65~79 -> submitted 단절 원인 점검",
            "적용단계": "observability",
            "기대효과": "EV가 남아 있는 recovery 후보가 실제 제출로 이어지지 않는 병목을 분리한다.",
            "검증지표": (
                f"promoted={observability['buy_recovery_canary']['recovery_promoted_candidates']}, "
                f"submitted={observability['buy_recovery_canary']['submitted_candidates']}"
            ),
            "필요표본": "HOLDING 발생 이후 재관찰",
        }
    )
    backlog.append(
        {
            "title": "gatekeeper latency 경로 분해(lock/model/quote_fresh)",
            "적용단계": "observability",
            "기대효과": "latency가 EV 회수 병목인지 성능 문제인지 구간별로 분해한다.",
            "검증지표": (
                f"gatekeeper_eval_ms_p95={observability['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms, "
                f"quote_fresh_latency_blocks={observability['entry_funnel']['quote_fresh_latency_blocks']}"
            ),
            "필요표본": "장전/장후 snapshot 누적",
        }
    )

    lines = ["# EV Improvement Backlog", ""]
    for index, row in enumerate(backlog, 1):
        lines.append(f"{index}. {row['title']}")
        lines.append(f"   - 적용단계: {row['적용단계']}")
        lines.append(f"   - 기대효과: {row['기대효과']}")
        lines.append(f"   - 검증지표: {row['검증지표']}")
        lines.append(f"   - 필요표본: {row['필요표본']}")
        lines.append("")

    (config.OUTPUT_DIR / "ev_improvement_backlog.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _write_final_review(ev_result: dict, trade_df: pd.DataFrame, seq_df: pd.DataFrame, observability: dict) -> None:
    loss_patterns = ev_result.get("loss_patterns", [])
    profit_patterns = ev_result.get("profit_patterns", [])
    opportunity_cost = ev_result.get("opportunity_cost", [])
    backlog = ev_result.get("ev_backlog", [])
    cohort_rows = ev_result.get("cohort_summary", [])

    insufficient_note = ""
    if not trade_df.empty:
        valid_mask = trade_df["profit_valid_flag"].astype(str).str.lower().isin(["true", "1"])
        valid_count = int(valid_mask.sum())
        if valid_count < config.MIN_VALID_SAMPLES:
            insufficient_note = (
                f"> 표본 부족: valid_profit_rate={valid_count}건 < {config.MIN_VALID_SAMPLES}. "
                "결론 확정 대신 방향성만 기록한다."
            )

    lines = [
        "# Gemini Scalping Pattern Lab Final Review",
        "",
        f"- generated_at: `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- analysis_period: `{config.START_DATE} ~ {config.END_DATE}`",
        "",
        "## 1. 판정",
        "",
    ]
    if insufficient_note:
        lines += [insufficient_note, ""]

    lines += ["### 1-1. 코호트별 EV 요약", ""]
    if cohort_rows:
        lines.append("| 코호트 | 거래수 | 승률 | 손익 중앙값 | 손익 평균값 | 기여손익 합 | 표본충분 |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for row in cohort_rows:
            sufficient = "✓" if row.get("sufficient") else "⚠️부족"
            lines.append(
            f"| {row['cohort']} | {row['n']} | {row.get('diagnostic_win_rate_pct', 0.0)}% | "
            f"{row['median_profit']:+.3f}% | {row.get('equal_weight_avg_profit_pct', row.get('mean_profit', 0.0)):+.3f}% | "
            f"{row.get('simple_sum_profit_pct', row.get('contrib_profit', 0.0)):+.3f}% | {sufficient} |"
            )
    else:
        lines.append("- 분석 대상 없음")
    lines.append("")

    lines += ["### 1-2. Plan Rebase 관찰축 요약", ""]
    lines += [
        f"- `WAIT65~79 total_candidates={observability['buy_recovery_canary']['total_candidates']}`, "
        f"`recovery_check={observability['buy_recovery_canary']['recovery_check_candidates']}`, "
        f"`promoted={observability['buy_recovery_canary']['recovery_promoted_candidates']}`, "
        f"`submitted={observability['buy_recovery_canary']['submitted_candidates']}`",
        f"- `blocked_ai_score_share={observability['buy_recovery_canary']['blocked_ai_score_share_pct']:.1f}%`, "
        f"`budget_pass_to_submitted_rate={observability['entry_funnel']['budget_pass_to_submitted_rate']:.1f}%`, "
        f"`gatekeeper_eval_ms_p95={observability['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms`",
        "",
    ]
    for item in observability.get("priority_findings", []):
        lines.append(f"- `{item['label']}`: {item['judgment']} — {item['why']}")
    lines.append("")

    lines += ["### 1-3. 손실 패턴 Top 5", ""]
    if not loss_patterns:
        lines.append("- 분석 대상 없음")
    for index, row in enumerate(loss_patterns, 1):
        preconditions = ", ".join(
            f"{key}={value['count']}건({value['pct']}%)"
            for key, value in row.get("preconditions", {}).items()
        ) or "없음"
        lines += [
            f"**#{index}** — 코호트: `{row['cohort']}` / 청산규칙: `{row['exit_rule']}`",
            f"- 빈도: {row['n']}건 | 중앙손익: {row['median_profit']:+.3f}% | 평균손익: {row['mean_profit']:+.3f}% | 기여손익: {row['contrib_profit']:+.3f}%",
            f"- 보유시간 중앙값: {row['median_held_sec']}초",
            f"- 선행 조건: {preconditions}",
            "",
        ]

    lines += ["### 1-4. 수익 패턴 Top 5", ""]
    if not profit_patterns:
        lines.append("- 분석 대상 없음")
    for index, row in enumerate(profit_patterns, 1):
        lines += [
            f"**#{index}** — 코호트: `{row['cohort']}` / 청산규칙: `{row['exit_rule']}` / 진입모드: `{row['entry_mode']}`",
            f"- 빈도: {row['n']}건 | 중앙손익: {row['median_profit']:+.3f}% | 평균손익: {row['mean_profit']:+.3f}% | 기여손익: {row['contrib_profit']:+.3f}%",
            "",
        ]

    lines += ["### 1-5. 기회비용 회수 후보 Top 5", ""]
    if not opportunity_cost:
        lines.append("- 데이터 없음")
    for index, row in enumerate(opportunity_cost, 1):
        lines += [
            f"**#{index}** — `{row['blocker']}`",
            f"- 차단 건수 합계: {row['total_blocked']}건 | 차단 비율: {row['block_ratio']}% | 관찰 일수: {row['days']}일",
            "",
        ]

    lines += [
        "---",
        "",
        "## 2. 근거",
        "",
        "### 2-1. 코호트 분리 이유",
        "",
        "- `full_fill`, `partial_fill`, `split-entry`는 손익 구조가 달라 합치면 EV 해석이 왜곡된다.",
        "- Plan Rebase 관찰축은 EV 패턴의 원인을 설명하는 보조 증거로만 사용한다.",
        "- 따라서 report의 중심은 실현 EV, 패턴 기여손익, 기회비용 순으로 유지한다.",
        "",
        "### 2-2. sequence_fact 관찰",
        "",
    ]
    if not seq_df.empty:
        for column in [
            "rebase_integrity_flag",
            "partial_then_expand_flag",
            "same_symbol_repeat_flag",
            "same_ts_multi_rebase_flag",
        ]:
            if column in seq_df.columns:
                count = int(seq_df[column].astype(str).str.lower().isin(["true", "1"]).sum())
                lines.append(f"- {column}: {count}건")
    else:
        lines.append("- sequence_fact 없음")

    lines += [
        "",
        "## 3. 다음 액션",
        "",
        "### 3-1. EV 개선 우선순위",
        "",
    ]
    for item in backlog:
        lines.append(f"- `{item['title']}`")
        if item.get("검증지표"):
            lines.append(f"  검증지표: {item['검증지표']}")
    if not backlog:
        lines.append("- 없음")

    lines += [
        "",
        "### 3-2. Plan Rebase 연계 관찰",
        "",
        "- HOLDING 발생 이후에는 `post_sell_feedback`과 `trade_review`를 함께 묶어 EV 해석을 보강한다.",
        "- `WAIT65~79 -> submitted`가 끊겨 있으면 threshold 완화보다 제출 병목 원인 분리가 우선이다.",
        "- `gatekeeper latency`는 EV 회수 실패 원인인지 성능 병목인지 분해 후 축 우선순위를 정한다.",
        "",
    ]

    (config.OUTPUT_DIR / "final_review_report_for_lead_ai.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def generate() -> None:
    ev_result = _load_json("ev_analysis_result.json")
    observability = write_tuning_observability_outputs(
        output_dir=config.OUTPUT_DIR,
        target_date=config.END_DATE,
        analysis_start=config.START_DATE,
        analysis_end=config.END_DATE,
    )
    trade_df = _load_csv("trade_fact.csv")
    seq_df = _load_csv("sequence_fact.csv")

    _write_pattern_report(ev_result, observability)
    _write_ev_backlog(ev_result, observability)
    _write_final_review(ev_result, trade_df, seq_df, observability)

    manifest_path = config.OUTPUT_DIR / "run_manifest.json"
    manifest = _load_json("run_manifest.json")
    manifest["executed_at"] = datetime.datetime.now().isoformat()
    manifest["inputs_processed"] = [
        "data/pipeline_events/",
        "data/post_sell/",
        "data/report/monitor_snapshots/",
        "tmp/remote_*",
    ]
    manifest["outputs_generated"] = [
        "trade_fact.csv",
        "funnel_fact.csv",
        "sequence_fact.csv",
        "ev_analysis_result.json",
        "llm_payload_summary.json",
        "llm_payload_cases.json",
        "pattern_analysis_report.md",
        "ev_improvement_backlog.md",
        "final_review_report_for_lead_ai.md",
        "tuning_observability_summary.json",
        "tuning_observability_summary.md",
    ]
    with open(config.OUTPUT_DIR / "run_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    generate()
