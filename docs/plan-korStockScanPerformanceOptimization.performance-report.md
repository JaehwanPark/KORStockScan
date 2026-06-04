# KORStockScan 정기 성과측정 기준

기준 시각: `2026-06-04 KST`
역할: Plan Rebase 기간의 장후/주간 반복 성과판정 기준과 리포트 소스 우선순위를 고정한다.
현재 active/open owner와 live 변경 원칙은 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)가 소유하고, 실행 작업항목은 날짜별 `stage2 todo checklist`가 소유한다.

튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 이 기준 이전 raw/report/analytics artifact와 그 기반 성과 리포트는 archive/audit evidence이며, 현재 EV, rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 사용하지 않는다.

---

## 0. 현행화 판정

### 판정

1. 이 문서는 `2026-04-20` 전환기 성과 기준에서 멈춰 있었고, `2026-04-21 Plan Rebase` 이후의 daily checklist/report 자동화 흐름을 반영하지 못했다.
2. 누락 원인은 문서 역할이 `반복 성과 기준`에서 `과거 baseline/감사 증적`처럼 쓰이기 시작했는데, 실제 작업 owner는 날짜별 checklist와 `Plan Rebase`로 이동했기 때문이다.
3. `2026-05-04` 기준 이 문서는 active owner를 직접 소유하지 않고, `성과판정 순서`, `데이터 소스`, `리포트별 지표`, `report-only 금지선`, `정기 업데이트 트리거`만 소유한다.

### 근거

- 기존 본문 상단 기준 시각은 `2026-04-20 KST`였고, `entry_filter canary 1차 판정 후 2026-04-24 POSTCLOSE A/B 재개` 같은 만료된 전환기 문구가 남아 있었다.
- 현재 Plan Rebase 기준 entry owner는 `mechanical_momentum_latency_relief`, `dynamic_entry_price_resolver_p1`, `dynamic_entry_ai_price_canary_p2`이고, holding/exit owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`다.
- offline bundle 계열(`offline_gatekeeper_fast_reuse_bundle`, `offline_live_canary_bundle`)은 retired/removed 상태다. 과거 checklist 증적은 보존하되 현재 표준 경로로 쓰지 않는다.
- Claude/Gemini pattern lab은 별도 금요일 cron이 아니라 `deploy/run_tuning_monitoring_postclose.sh`의 POSTCLOSE monitoring report-only 체인에서 다룬다.

### 다음 액션

1. 이 문서를 바꿀 때는 `Plan Rebase`의 active owner를 복제하지 않고, 성과측정 기준과 리포트 소스만 현재화한다.
2. 새 리포트가 장후 판정 근거가 되면 [data/report/README.md](../data/report/README.md)에 canonical/Markdown 여부를 먼저 반영한다.
3. 미래 작업은 이 문서에 체크박스로 만들지 않고 날짜별 checklist에 `Due/Slot/TimeWindow/Track` 형식으로 남긴다.

## 1. 성과판정 원칙

1. 최종 목표는 손실 억제가 아니라 `기대값/순이익 극대화`다.
2. 비교 우선순위는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`이다.
3. 손익은 `COMPLETED + valid profit_rate`만 사용한다. `NULL`, 미완료, fallback 정규화 값은 손익 기준에서 제외한다.
4. `full fill`과 `partial fill`은 합산하지 않는다. `initial-only`와 `pyramid-activated`, `REVERSAL_ADD` 체결 표본도 분리한다.
5. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
6. 원인 귀속이 불명확하면 threshold를 먼저 바꾸지 않고 리포트 정합성, 이벤트 복원, 집계 품질을 먼저 확인한다.
7. `counterfactual`, `missed_upside`, `would_qty`, `would_block` 값은 기대값 개선 후보의 방향성 근거로만 보고 실현손익과 합산하지 않는다.

## 2. 현재 반복 기준선

| 기준 | 현재값 | 해석 |
| --- | --- | --- |
| 실행 기준 | `main-only` | remote/songstock 비교값은 Plan Rebase 의사결정 입력에서 제외 |
| 거래 표본 | `normal_only`, `post_fallback_deprecation` | fallback 오염 제거 후 성과판정 기본 cohort |
| 폐기 표본 | `fallback_scout/main`, `fallback_single`, `latency fallback split-entry` | 재개/observe-only runtime shadow 모두 새 workorder 없이는 금지 |
| live canary 원칙 | 동일 단계 내 `1축 canary` | entry와 holding/exit는 stage-disjoint일 때만 병렬 판정 |
| report-only 금지선 | `statistical_action_weight`, `holding_exit_decision_matrix`, threshold cycle report, pattern lab | live runtime threshold/order/exit 판단 직접 변경 금지 |

과거 `2026-04-17` 고밀도 baseline과 `2026-04-20` 감사 보정 수치는 historical reference다. 현재 rollback/live 승인 기준으로 직접 쓰지 않고, 필요 시 archive 문서와 raw snapshot을 함께 확인한다.

## 3. 보고 주기와 산출물

| 주기 | 보고 범위 | 목적 | 기준 산출물 |
| --- | --- | --- | --- |
| `Daily POSTCLOSE` | 당일 실행축, 퍼널, blocker, 체결품질, holding/exit 품질 | 다음 trading day의 유지/OFF/후속축 판단 | checklist 판정, daily threshold/action/decision reports |
| `Rolling/Cumulative` | 최근 N일/누적 cohort | daily 방향성이 우연인지 확인 | threshold cycle cumulative/rolling, statistical action weight |
| `Weekly POSTCLOSE` | 주간 누적 성과와 반복 failure type | 다음 주 report-only/observe-only 설계 우선순위 선정 | POSTCLOSE monitoring, pattern lab outputs |
| `Milestone` | 구조 변경 직후, 큰 손실일, 대규모 표본일 | Plan Rebase 재정렬 또는 rollback 판단 | 별도 audit/report |

## 4. Daily POSTCLOSE 템플릿

### 판정

1. 오늘 기대값 관점의 주된 아쉬운 유형을 `진입`, `진입가/체결`, `보유/청산`, `포지션 증감`, `런타임 안정성`, `리포트 품질` 중 하나 이상으로 분리한다.
2. live owner는 `유지`, `OFF`, `baseline 운영`, `report-only 전환`, `새 workorder 필요` 중 하나로만 닫는다.
3. 표본 부족이면 hard pass/fail을 쓰지 않고 `direction-only`와 다음 절대시각을 남긴다.

### 근거

필수 포함값:

1. `total_trades`, `completed_trades`, `COMPLETED + valid profit_rate`
2. `AI BUY -> budget_pass -> submitted -> full_fill/partial_fill -> sell_completed` 퍼널
3. blocker 상위 분포와 BUY 후 미진입 4분류
4. `full_fill`, `partial_fill`, `initial-only`, `pyramid-activated`, `REVERSAL_ADD`, `PYRAMID` 분리
5. `MISSED_UPSIDE`, `GOOD_EXIT`, `soft_stop`, `protect/trailing`, `capture_efficiency`
6. `realized_pnl_krw`는 마지막에만 제시

### 다음 액션

1. 같은 날 닫을 수 있는 판정은 같은 날 닫는다.
2. 미래 확인은 날짜별 checklist에 자동 파싱 가능한 작업항목으로 남긴다.
3. 문서 변경 후 parser 검증을 실행하고, Project/Calendar 동기화는 사용자 실행 명령으로 남긴다.

## 5. 데이터 소스 우선순위

1. 과거 날짜 운영 판정은 DB/DuckDB/Parquet 재구성값을 우선한다.
2. 수동 감사/포렌식은 `data/report/monitor_snapshots/*.json*`, `data/pipeline_events/*.jsonl*`, `data/post_sell/*.jsonl*`를 사용한다.
3. 당일 fresh 로그가 작업환경에 없으면 DB/DuckDB/Parquet, monitor snapshot, pipeline event 원본을 우선 확인하고, 누락 시 source-quality/instrumentation gap으로 분리한다.
4. 문서에 적힌 파생값은 raw 필드와 산식이 추적되기 전까지 rollback/live 승인 기준으로 쓰지 않는다.
5. generated output은 증적이지만, timestamp-only diff는 전략 변화 근거로 보지 않는다.

## 6. 리포트별 소유 지표

| 리포트 | 소유 지표 | 판정 주의 |
| --- | --- | --- |
| `trade_review_YYYY-MM-DD` | `total_trades`, `completed_trades`, `loss_trades`, `avg_profit_rate`, `realized_pnl_krw` | 손익은 마지막 결과값 |
| `performance_tuning_YYYY-MM-DD` | `budget_pass`, `submitted`, `latency_block`, blocker breakdown, fill quality, exit rules | remote 비교값 제외, full/partial 분리 |
| `holding_exit_observation_*` | exit candidate, trailing continuation, soft stop rebound, same-symbol reentry, opportunity cost | counterfactual과 realized PnL 합산 금지 |
| `statistical_action_weight_*` | `exit_only`, `avg_down_wait`, `pyramid_wait`, lower-confidence score | report-only, live threshold 직접 변경 금지 |
| `holding_exit_decision_matrix_*` | AI/flow/exit authority decision matrix | ADM ladder 승인 전 prompt/live 반영 금지 |
| `threshold_cycle_*` | daily/rolling/cumulative threshold 후보, manifest/apply plan | `ThresholdOpsTransition0506` 전 live mutation 금지 |
| `preclose_sell_target_*` | 제거된 15:00 전후 SELL_TODAY/report-only 후보 | 2026-05-10 제거. 과거 증적용 artifact로만 보존 |
| pattern lab outputs | data quality, EV improvement backlog, final review | POSTCLOSE monitoring report-only, live routing/threshold 직접 변경 금지 |

## 7. Dashboard / Performance-Tuning 매핑

| 판정항목 | 대표 지표 키 | 비고 |
| --- | --- | --- |
| entry funnel | `metrics.budget_pass_events`, `metrics.order_bundle_submitted_events` | submitted 회복 전에는 보유/청산 개선 판정도 표본 부족 가능 |
| latency/quote | `breakdowns.latency_reason_breakdown`, `latency_state_danger` | `gatekeeper_fast_reuse_ratio` 단독 승격 금지 |
| fill quality | `breakdowns.fill_quality_cohorts`, `full_fill`, `partial_fill` | full/partial 합산 결론 금지 |
| holding/exit | `sections.holding_axis`, `exit_rules.*` | hard/protect safety와 flow override 구분 |
| observation coverage | `sections.observation_axis_coverage[]` | missing key가 있으면 전략 결론보다 집계 품질 보강 우선 |
| flow bottleneck lane | `sections.flow_bottleneck_lane.nodes[]` | watch -> sell_complete 단계별 병목 위치 확인 |

## 8. Pattern Lab / Removed Offline Bundle 운영

### 판정

1. `offline_live_canary_bundle`은 retired/removed 상태이며 standby 표준 경로로 쓰지 않는다.
2. `offline_gatekeeper_fast_reuse_bundle` 전용 codebase와 legacy `gatekeeper_fast_reuse`/`entry_latency_offline` compatibility summary 생성 경로도 삭제했다.
3. `claude_scalping_pattern_lab`, `gemini_scalping_pattern_lab`은 POSTCLOSE monitoring report-only 분석랩이다.

### 근거

- EC2 서버 증설 후 로컬 offline export/analyze 경로를 사용하지 않고, 최근 운영 실행 흔적도 `2026-04-28` 이후 확인되지 않았다.
- `deploy/install_pattern_lab_cron.sh`는 dedicated Friday-only pattern lab cron 제거/폐기 스크립트다.
- 현재 표준 체인은 `deploy/run_tuning_monitoring_postclose.sh`이며, parquet/DuckDB refresh와 shadow diff 이후 Claude/Gemini pattern lab을 실행한다.
- pattern lab 출력의 `shadow-only` 또는 threshold 제안은 Plan Rebase의 신규 alpha shadow 금지선과 충돌할 수 있으므로, live 반영 전에는 별도 checklist/workorder가 필요하다.

### 다음 액션

1. pattern lab 산출물은 `data_quality`, `EV backlog`, `final review`를 분리해 읽는다.
2. 데이터 품질 경고가 있으면 전략 threshold보다 이벤트 복원/집계 정합성을 우선한다.
3. live routing, threshold mutation, 주문/청산 변경은 pattern lab 제안만으로 열지 않는다.

## 9. 정기 업데이트 규칙

1. 이 문서는 아래 상황에서만 갱신한다.
   - 성과판정 순서 또는 소스 우선순위가 바뀐 경우
   - canonical report가 추가/폐기된 경우
   - report-only와 live 적용 금지선이 바뀐 경우
   - Plan Rebase의 active owner 변화가 성과측정 기준을 바꾸는 경우
2. 날짜별 실행 결과와 개별 ticker 판정은 이 문서에 누적하지 않는다. 해당 날짜 checklist, `data/report/*`, audit/report 문서가 소유한다.
3. 문서 변경 후 parser 검증은 AI가 실행한다.
4. GitHub Project / Calendar 동기화는 아래 표준 명령을 사용자가 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 참고 문서

- [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)
- [data/report/README.md](../data/report/README.md)
- [analysis/README.md](../analysis/README.md)
- [2026-04-17-midterm-tuning-performance-report.md](/home/ubuntu/KORStockScan/docs/archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-21-plan-rebase-auditor-report.md](/home/ubuntu/KORStockScan/docs/archive/plan-rebase-transition-2026-04-20-to-2026-04-22/2026-04-21-plan-rebase-auditor-report.md)
