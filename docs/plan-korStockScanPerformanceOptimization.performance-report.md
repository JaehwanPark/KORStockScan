# KORStockScan 정기 성과측정보고서

기준 시각: `2026-04-20 KST`  
기준 데이터 baseline: `2026-04-17` 고밀도 표본일 + DB 우선 스냅샷 + 장후 문서

이 문서는 장후/주간 반복 성과판정에 쓰는 기준 문서다.  
일회성 진단은 [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md), 기본계획 대비 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에서 본다.

## 1. 판정

1. 현재 성과측정의 1순위는 `손익`이 아니라 `거래수`, `퍼널`, `blocker`, `체결품질`, `missed_upside`다.
2. `2026-04-17`은 고밀도 표본일이 맞지만, baseline은 `문서 파생값`이 아니라 `스냅샷 실필드` 기준으로 다시 고정해야 한다.
3. 다음주 성과측정의 핵심 baseline은 `latency + partial/rebase 체결품질 축`과 `HOLDING missed_upside/capture_efficiency 개선`이다.

## 2. 보고 주기

| 주기 | 보고 범위 | 주 목적 | 기본 출력 |
| --- | --- | --- | --- |
| `Daily POSTCLOSE` | 당일 실행축/퍼널/체결품질/holding 품질 | 당일 go/no-go, 익일 canary 판정 | 장후 메모 + checklist 반영 |
| `Weekly POSTCLOSE (금)` | 월~금 누적 성과와 승격축 정리 | 다음주 PREOPEN 승격축 `1개` 확정 | 주간 통합판정 |
| `Milestone` | 최고손실일, 구조 변경 직후, 대규모 표본일 | 계획 재정렬 | 별도 진단 보고서 |

## 3. 측정 순서와 해석 규칙

### 3-1. 장후/주간 보고 순서

1. `거래수`
2. `퍼널`
3. `blocker`
4. `체결품질`
5. `HOLDING/청산 품질`
6. `손익`

### 3-2. 해석 규칙

1. `손익`은 마지막 결과값으로만 읽는다.
2. `NULL`, 미완료 상태, fallback 정규화 값은 손익 기준에서 제외한다.
3. `counterfactual` 수치는 직접 실현손익과 합산하지 않는다.
4. `full fill`, `partial fill`, `split-entry`, `same_symbol_repeat`는 별도 코호트로 읽는다.
5. BUY 후 미진입은 `latency/liquidity/AI threshold/overbought`로 분리 기록한다.

## 4. 현재 baseline (`2026-04-17`)

> `2026-04-20` 정합성 보정:
> `realized_pnl_krw=-223,423`는 `trade_review` 기준의 당일 실현손익이다.
> `performance_tuning.trends.recent_points`는 rolling trend이므로 당일 손익 baseline이나 rollback 기준으로 사용하지 않는다.
> `same_symbol_repeat_flag=55.1%`는 현재 원 raw 필드와 산식 추적이 끝나지 않아 hard baseline/rollback 기준에서 제외한다.

### 4-1. 거래/손익 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `total_trades` | `68` | 운영기간 중 최대 표본 |
| `completed_trades` | `65` | 손익 해석의 기본 표본 |
| `loss_trades` | `36` | 손실축 집중 구간 존재 |
| `avg_profit_rate` | `-0.25%` | 직접 손익은 악화 |
| `realized_pnl_krw` | `-223,423` | `trade_review` 기준 당일 실현손익 |

### 4-2. 퍼널/체결품질 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `budget_pass_events` | `6,634` | 엔진 평가 모수 충분 |
| `order_bundle_submitted_events` | `67` | 실제 주문 전송 표본 |
| `latency_block_events` | `6,567` | 상류 차단 병목이 큼 |
| `quote_fresh_latency_blocks` | `5,354` | stale quote보다 내부 처리 지연 비중 큼 |
| `position_rebased_after_fill_events` | `117` | rebase 관찰 밀도 높음 |
| `partial_fill_events` | `82` | split-entry/partial 품질 이슈 집중 |
| `full_fill_events` | `33` | partial과 분리 해석 필요 |
| `gatekeeper_eval_ms_p95` | `29,336ms` | gatekeeper 지연이 큼 |
| `partial_fill_completed_avg_profit_rate` | `-0.261` | partial cohort EV 악화 |

### 4-3. HOLDING/청산 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `MISSED_UPSIDE` | `19` | 승자 보유 품질 개선 여지 큼 |
| `GOOD_EXIT` | `32` | 정상 종료 표본도 충분 |
| `estimated_extra_upside_10m_krw_sum` | `1,612,548` | 직접 손익이 아니라 HOLDING 개선 여지 |
| `capture_efficiency_avg_pct` | `39.8%` | `post_sell_feedback` 기준선으로 사용 |

### 4-4. 미진입 기회비용 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `evaluated_candidates` | `194` | 차단 사례 표본 충분 |
| `MISSED_WINNER` | `157` | 기회비용 크지만 즉시 broad relax 근거로 쓰지 않음 |
| `AVOIDED_LOSER` | `29` | 차단이 전부 악은 아님 |
| `estimated_counterfactual_pnl_10m_krw_sum` | `1,896,874` | 진입 기회비용 방향성 참고용 |

## 5. 다음주 주요 성과측정 포인트

| 구간 | 기준선 | 원하는 방향 |
| --- | --- | --- |
| `latency_block_events / budget_pass_events` | `6567 / 6634` | 의미 있게 감소 |
| `quote_fresh_latency_blocks` | `5,354` | 감소 |
| `partial_fill_events` | `82` | 체결기회 훼손 없이 질 개선 |
| `partial_fill_completed_avg_profit_rate` | `-0.261` | `-0.15` 이내로 개선 |
| `exit_rules.scalp_soft_stop_pct` | `26` | 감소 |
| `missed_upside_rate` | 현재 HOLDING 기준선으로 고정 예정 | 감소 |
| `capture_efficiency_avg_pct` | `39.8%` | 증가 |
| `GOOD_EXIT` 분포 | `32`건 | 질 유지 또는 개선 |

## 6. 정기 보고서 작성 템플릿

### 6-0. 2026-04-20 운영 업데이트

#### 판정

1. `2026-04-20`의 장후 우선축은 `same-symbol 반복`이 아니라 `latency + partial/rebase`로 다시 고정한다.
2. `HOLDING`은 아직 성과확대 판단이 아니라 baseline 고정 단계다.
3. 리스크 사이즈는 긴급 하향 반영했지만, 오늘은 clean one-day 효과 판정일이 아니다.

#### 근거

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `total_trades` | `28` | 당일 거래수 |
| `completed_trades` | `24` | 손익 해석 기본 표본 |
| `realized_pnl_krw` | `-56,786` | `trade_review` 기준 당일 실현손익 |
| `budget_pass_events` | `866` | 당일 평가 모수 |
| `latency_block_events` | `838` | latency 차단 우세 |
| `order_bundle_submitted_events` | `28` | 실제 주문 전송 표본 |
| `partial_fill_events` | `31` | partial 우세 |
| `full_fill_events` | `11` | full과 분리 해석 필요 |
| `position_rebased_after_fill_events` | `44` | rebase 반복 존재 |
| `gatekeeper_eval_ms_p95` | `19,917ms` | 상류 지연 여전. `2026-04-20` 공식 p95 기준이며, 단일 샘플값 `21,619ms`는 기준선에서 제외 |
| `exit_rules.scalp_soft_stop_pct` | `18` | soft-stop 과다 |
| `partial_fill_completed_avg_profit_rate` | `-0.25` | partial cohort EV 악화 |
| `missed_upside_rate` | `42.3%` | HOLDING 개선 여지 큼 |
| `capture_efficiency_avg_pct` | `32.871%` | HOLDING baseline 고정치 |

#### 다음 액션

1. `2026-04-21 POSTCLOSE`에는 `partial/rebase` 기반 soft-stop 비중을 다시 본다.
2. 같은 슬롯에서 긴급 하향한 risk size의 full-day 효과를 clean sample로 재판정한다.
3. HOLDING 확대 여부는 `2026-04-22 POSTCLOSE`까지 보류한다.

### 6-1. Daily POSTCLOSE

1. 판정
2. 근거
3. 다음 액션

필수 포함값:

1. `거래수`, `completed_trades`
2. `AI BUY -> submitted -> filled` 퍼널
3. blocker 상위 분포
4. `full fill / partial fill / split-entry / same_symbol_repeat`
5. `MISSED_UPSIDE / GOOD_EXIT / capture_efficiency`
6. `realized_pnl_krw`는 마지막

### 6-2. Weekly POSTCLOSE

1. 주간 기준선 대비 변화
2. 승격/보류 후보 `1개`
3. regime 태그와 조건부 유효범위
4. 다음주 PREOPEN 반영축

## 7. 데이터 소스와 우선순위

### 7-1. 소스 우선순위

1. 과거 날짜 운영 판정은 `DB 우선` 조회를 기준으로 한다.
2. 수동 감사/포렌식은 `monitor_snapshots/*.json.gz`를 사용한다.
3. 평문 `*.json`은 당일 임시 산출물 또는 fallback으로만 사용한다.
4. 문서에 적힌 파생 지표는 원 raw 필드와 산식이 추적되기 전까지 rollback/life-cycle 기준으로 쓰지 않는다.

### 7-2. 리포트별 소유 지표

1. `trade_review_YYYY-MM-DD`
   - `total_trades`
   - `completed_trades`
   - `loss_trades`
   - `avg_profit_rate`
   - `realized_pnl_krw`
2. `performance_tuning_YYYY-MM-DD`
   - `budget_pass_events`
   - `order_bundle_submitted_events`
   - `latency_block_events`
   - `quote_fresh_latency_blocks`
   - `partial_fill_events`
   - `full_fill_events`
   - `position_rebased_after_fill_events`
   - `gatekeeper_eval_ms_p95`
   - `partial_fill_completed_avg_profit_rate`
   - `breakdowns.exit_rules.*`
   - `breakdowns.fill_quality_cohorts.*`
3. `post_sell_feedback_YYYY-MM-DD`
   - `MISSED_UPSIDE`
   - `GOOD_EXIT`
   - `estimated_extra_upside_10m_krw_sum`
   - `capture_efficiency_avg_pct`
4. `missed_entry_counterfactual_YYYY-MM-DD`
   - `MISSED_WINNER`
   - `AVOIDED_LOSER`
   - `estimated_counterfactual_pnl_10m_krw_sum`
5. `performance_tuning.trends.*`
   - rolling trend 전용
   - 당일 손익 baseline/rollback 기준으로 사용 금지

## 8. 대시보드-검증축 매핑 (performance-tuning)

| 검증축/판정항목 | 대시보드 지표 키 | 비고 |
| --- | --- | --- |
| `N_min` | `sections.judgment_gate.n_min`, `sections.judgment_gate.n_current` | `N_current >= N_min` 충족 여부를 화면에서 바로 판정 |
| `Δ_min + PrimaryMetric` | `sections.judgment_gate.primary_metric_name`, `sections.judgment_gate.primary_metric_value`, `sections.judgment_gate.delta_min` | 현재는 `budget_pass_to_submitted_rate`를 PrimaryMetric으로 사용 |
| `rollback: reject_rate` | `sections.judgment_gate.rollback_values.reject_rate` | 상한은 `sections.judgment_gate.rollback_limits.reject_rate_max` |
| `rollback: partial_fill_ratio` | `sections.judgment_gate.rollback_values.partial_fill_ratio` | full/partial fill 기반 비율 |
| `rollback: latency_p95` | `sections.judgment_gate.rollback_values.latency_p95` | Gatekeeper 평가 p95 기준 |
| `rollback: reentry_freq` | `sections.judgment_gate.rollback_values.reentry_freq` | rebase/submitted 비율 기반 재진입 빈도 proxy |
| `작업10 필수 관찰축` | `sections.holding_axis.holding_action_applied` | HOLDING hybrid 적용 관찰 |
| `작업10 필수 관찰축` | `sections.holding_axis.holding_force_exit_triggered` | FORCE_EXIT 트리거 관찰 |
| `작업10 필수 관찰축` | `sections.holding_axis.holding_override_rule_versions` | rule version 관찰 |
| `작업10 필수 관찰축` | `sections.holding_axis.force_exit_shadow_samples` | FORCE_EXIT shadow 표본 |
| `작업10 필수 관찰축` | `sections.holding_axis.trailing_conflict_rate` | trailing 충돌률 |

## 9. 패턴랩 정기 실행 및 DB 연계 운영

### 9-1. 실행 정책

1. `claude_scalping_pattern_lab`, `gemini_scalping_pattern_lab`은 `금요일 POSTCLOSE` 정기 실행으로 고정한다.
2. 데이터 소스 우선순위는 `DB -> 원본 파일 -> 압축 파일(.gz)`로 통일한다.
3. DB/파일 소스 불일치가 발생하면 결론 확정보다 `이벤트 복원/집계 정합성` 점검을 우선한다.

### 9-2. 자동 실행 경로

1. `deploy/install_pattern_lab_cron.sh`
2. `deploy/run_claude_scalping_pattern_lab_cron.sh`
3. `deploy/run_gemini_scalping_pattern_lab_cron.sh`
4. 로그:
   - `logs/claude_scalping_pattern_lab_cron.log`
   - `logs/gemini_scalping_pattern_lab_cron.log`

### 9-3. 주간 검증 항목

1. `trade_fact/funnel_fact/sequence_fact` 생성 성공 여부
2. `profit_valid_flag` 표본 30건 미만 경고 여부
3. `full_fill/partial_fill/split-entry` 분리 집계 유지 여부
4. 관찰축(`거래수/퍼널/blocker/체결품질/missed_upside`) 주간 변동 보고서 반영 여부

## 참고 문서

- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
