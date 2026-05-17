# Gemini Scalping Pattern Lab

본 디렉토리는 스캘핑 매매 내역을 분석하여 손실/수익 패턴을 찾고 기대값 개선(EV Improvement)을 도출하기 위한 전용 코드베이스입니다.
기존 운영 코드에 영향을 주지 않도록 독립적으로 구성되었습니다.

## 실행 방법

```bash
cd analysis/gemini_scalping_pattern_lab
bash run.sh
```

## 입력 데이터
- Local pipeline: `dashboard_pipeline_events` DB 우선, 파일 fallback (`data/pipeline_events/*.jsonl`, `*.jsonl.gz`)
- Local post-sell: `data/post_sell/` (`.jsonl`, `.jsonl.gz`)
- Remote logs: 기본 제외. `PATTERN_LAB_INCLUDE_REMOTE=true`일 때만 `tmp/remote_*/` (`pipeline_events*.jsonl(.gz)`, `post_sell_evaluations*.jsonl(.gz)`)를 읽는다.

## Metric Contract

- 손익 표본은 `COMPLETED + numeric profit_rate`만 인정한다.
- JSON 산출물은 `diagnostic_win_rate_pct`, `simple_sum_profit_pct`, `equal_weight_avg_profit_pct`, `primary_decision_metric`을 생성한다.
- 모든 패턴랩 판단은 `runtime_effect=false` report-only/proposal-only 입력이며 threshold/order/provider/bot 상태를 직접 변경하지 않는다.

## 출력물 (`outputs/` 하위 생성)
- `trade_fact.csv`: 매매 기본 정보
- `funnel_fact.csv`: 퍼널 단계별 진입/차단 통계
- `sequence_fact.csv`: 매매 이벤트 시퀀스
- `ev_analysis_result.json`: 그룹핑된 패턴 통계와 metric contract
- `llm_payload_summary.json`, `llm_payload_cases.json`: AI 모델 분석용 페이로드
- `pattern_analysis_report.md`: 손실/수익 패턴 최종 리포트
- `ev_improvement_backlog.md`: 백로그
- `data_quality_report.md`: 데이터 품질 리포트
- `run_manifest.json`: 실행 메타데이터 기록
