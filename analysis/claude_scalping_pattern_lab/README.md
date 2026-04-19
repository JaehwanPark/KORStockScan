# Claude Scalping Pattern Lab

스캘핑 거래 패턴 분석 전용 독립 코드베이스.
운영 코드(`src/`, `bot_main.py`)와 완전히 분리됨.

## 분석 목적

- 누적 스캘핑 거래 데이터 기반 손실 패턴 / 수익 패턴 분해
- 미진입 기회비용 blocker별 분해
- EV 개선 후보 우선순위 도출 (shadow-only → canary → 승격)

## 디렉토리 구조

```
claude_scalping_pattern_lab/
├── config.py                  # 분석 기간, 경로, 옵션
├── prepare_dataset.py         # 데이터 준비 (CSV 3종 생성)
├── analyze_ev_patterns.py     # 패턴 분석 + EV 백로그
├── build_claude_payload.py    # Claude 투입 payload + 최종 보고서
├── run_all.sh                 # 일괄 실행 스크립트
├── prompts/
│   ├── prompt_loss_patterns.md
│   ├── prompt_profit_patterns.md
│   └── prompt_ev_prioritization.md
└── outputs/                   # 실행 후 생성
    ├── trade_fact.csv
    ├── funnel_fact.csv
    ├── sequence_fact.csv
    ├── data_quality_report.md
    ├── ev_analysis_result.json
    ├── ev_improvement_backlog_for_ops.md
    ├── claude_payload_summary.json
    ├── claude_payload_cases.json
    ├── final_review_report_for_lead_ai.md
    └── run_manifest.json
```

## 실행 방법

```bash
# 프로젝트 루트에서
bash analysis/claude_scalping_pattern_lab/run_all.sh
```

또는 단계별 실행:

```bash
cd /home/ubuntu/KORStockScan
PYTHONPATH=. .venv/bin/python analysis/claude_scalping_pattern_lab/prepare_dataset.py
PYTHONPATH=. .venv/bin/python analysis/claude_scalping_pattern_lab/analyze_ev_patterns.py
PYTHONPATH=. .venv/bin/python analysis/claude_scalping_pattern_lab/build_claude_payload.py
```

## 입력 데이터 경로

| 종류 | 경로 |
|---|---|
| trade_review 스냅샷 | `data/report/monitor_snapshots/trade_review_*.json` |
| performance_tuning 스냅샷 | `data/report/monitor_snapshots/performance_tuning_*.json` |
| pipeline events | `data/pipeline_events/pipeline_events_*.jsonl` |

## 분석 기간

`config.py`의 `ANALYSIS_START` / `ANALYSIS_END` 로 조정.
기본: `2026-04-01 ~ 2026-04-17`

## 출력 산출물

| 파일 | 설명 |
|---|---|
| `trade_fact.csv` | 거래별 손익, 코호트, 진입/청산 정보 |
| `funnel_fact.csv` | 일별 퍼널 blocker 통계 |
| `sequence_fact.csv` | 거래별 이벤트 시퀀스 플래그 |
| `data_quality_report.md` | 표본 수, 제외 건수, 정합성 플래그 분포 |
| `ev_analysis_result.json` | 분석 결과 중간 산출물 |
| `ev_improvement_backlog_for_ops.md` | EV 개선 후보 백로그 |
| `claude_payload_summary.json` | Claude 투입용 요약 통계 |
| `claude_payload_cases.json` | Claude 투입용 대표 케이스 |
| `final_review_report_for_lead_ai.md` | 최종 분석 보고서 (판정/근거/다음액션) |
| `run_manifest.json` | 실행 기록 (시각, 파일 목록, 행수) |

## 품질 게이트

- 서버별 `valid_profit_rate` 30건 미만이면 **결론 확정 금지** (`data_quality_report.md`에 명시)
- `full_fill / partial_fill / split-entry` 코호트 혼합 분석 금지
- `rebase_integrity_flag` 케이스는 손절 튜닝 전 정합성 감사 선행 필수

## 제약 사항

- `src/` 이하 운영 코드 수정 금지
- 패키지 설치/업그레이드 금지
- 봇 재기동, cron 수정 금지
- 오프라인 파일 분석만 수행
