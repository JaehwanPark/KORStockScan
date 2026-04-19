# KORStockScan 정기 성과측정보고서

기준 시각: `2026-04-19 KST`  
기준 데이터 baseline: `2026-04-17` 고밀도 표본일 + 장후 문서/스냅샷

이 문서는 장후/주간 반복 성과판정에 쓰는 기준 문서다.  
일회성 진단은 [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md), 기본계획 대비 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에서 본다.

## 1. 판정

1. 현재 성과측정의 1순위는 `손익`이 아니라 `거래수`, `퍼널`, `blocker`, `체결품질`, `missed_upside`다.
2. `2026-04-17`은 실현손익 최저일이지만, 동시에 다음주 우선순위를 정할 가장 고밀도 표본일이다.
3. 다음주 성과측정의 핵심 baseline은 `split-entry soft-stop 손실축 축소`와 `HOLDING missed_upside/capture_efficiency 개선`이다.

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

### 4-1. 거래/손익 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `total_trades` | `68` | 운영기간 중 최대 표본 |
| `completed_trades` | `65` | 손익 해석의 기본 표본 |
| `loss_trades` | `36` | 손실축 집중 구간 존재 |
| `avg_profit_rate` | `-0.25%` | 직접 손익은 악화 |
| `realized_pnl_krw` | `-223,423` | 최저 실현손익일 |

### 4-2. 퍼널/체결품질 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `order_bundle_submitted_events` | `67` | 진입 실행 표본 충분 |
| `position_rebased_after_fill_events` | `117` | rebase 문제 관찰 밀도 높음 |
| `partial_fill_events` | `82` | split-entry/partial 품질 이슈 집중 |
| `same_symbol_repeat_flag` | `55.1%` | 반복 진입 오염 강함 |
| `partial_then_expand_flag` | `52.2%` | split-entry 누수의 핵심 코호트 |

### 4-3. HOLDING/청산 baseline

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| `MISSED_UPSIDE` | `19` | 승자 보유 품질 개선 여지 큼 |
| `GOOD_EXIT` | `32` | 정상 종료 표본도 충분 |
| `estimated_extra_upside_10m_krw_sum` | `1,612,548` | 직접 손익이 아니라 HOLDING 개선 여지 |
| `capture_efficiency_avg_pct` | `39.8%` | 기준선으로 사용 |

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
| `split-entry + scalp_soft_stop_pct` | `2026-04-17` 집중 손실축 | 비중 감소 |
| `same_symbol_repeat_flag` | `55.1%` | 감소 |
| `partial_fill_events` | `82` | 체결기회 훼손 없이 질 개선 |
| `missed_upside_rate` | 현재 HOLDING 기준선으로 고정 예정 | 감소 |
| `capture_efficiency_avg_pct` | `39.8%` | 증가 |
| `GOOD_EXIT` 분포 | `32`건 | 질 유지 또는 개선 |

## 6. 정기 보고서 작성 템플릿

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

## 7. 데이터 소스

1. `trade_review_YYYY-MM-DD`
2. `performance_tuning_YYYY-MM-DD`
3. `post_sell_feedback_YYYY-MM-DD`
4. `missed_entry_counterfactual_YYYY-MM-DD`
5. 날짜별 checklist와 audited validation-axis 문서

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
