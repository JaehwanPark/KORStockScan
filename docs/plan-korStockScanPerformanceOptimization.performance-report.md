# KORStockScan 정기 성과측정보고서

기준 시각: `2026-04-20 KST`  
기준 데이터 baseline: `2026-04-17` 고밀도 표본일 + DB 우선 스냅샷 + 장후 문서

> 현재 활성 실행 기준은 [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)와 [2026-04-21-plan-rebase-auditor-report.md](./2026-04-21-plan-rebase-auditor-report.md)를 따른다.
> 본 문서의 `entry_filter` 표기는 감사인 원문 표현이며, 현재 실행명은 `entry_filter_quality`다.

> `2026-04-21 Plan Rebase`:
> `fallback_scout/main`과 `fallback_single`이 `partial/rebase/soft_stop` 지표를 오염시킨 것으로 확인되어, 기존 튜닝 승격 판단은 일시중단한다.
> 이후 성과판정은 `진입/보유/청산 로직 전수점검 -> 코호트 재정렬 -> 튜닝포인트 1축 재선정` 순서로 재개한다.
> AI 엔진 A/B 테스트는 `entry_filter` canary 1차 판정 완료 후 재개 여부를 별도 판정하며, 최대 기한은 `2026-04-24 POSTCLOSE`다. Plan Rebase 기간의 live 스캘핑 AI 라우팅은 Gemini로 고정하고 OpenAI dual-persona shadow도 비활성화한다.

이 문서는 장후/주간 반복 성과판정에 쓰는 기준 문서다.  
일회성 진단은 [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md), 기본계획 대비 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에서 본다.

## 1. 판정

1. 현재 성과측정의 1순위는 `손익`이 아니라 `거래수`, `퍼널`, `blocker`, `체결품질`, `missed_upside`다.
2. `2026-04-17`은 고밀도 표본일이 맞지만, baseline은 `문서 파생값`이 아니라 `스냅샷 실필드` 기준으로 다시 고정해야 한다.
3. `2026-04-21` 이후 핵심 baseline은 `fallback 오염 제거 normal-only`, `post_fallback_deprecation`, `entry_filter canary`, `HOLDING missed_upside/capture_efficiency`, `position_addition_policy 후순위 후보`로 재정렬한다.
4. 물타기/불타기/분할진입은 별도 튜닝축이 아니라 하나의 `포지션 증감 상태머신`으로 재설계해야 한다.
5. OpenAI/Gemini A/B는 독립변수 오염을 막기 위해 `entry_filter` canary 1차 판정 완료 후 재개 여부를 별도 판정한다. 최대 기한은 `2026-04-24 POSTCLOSE`다.

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

> 아래 기존 포인트는 `fallback 오염 제거 재집계` 후에만 승격/롤백 판단에 사용한다.

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

## 5-1. Plan Rebase 기준 (`2026-04-21`)

### 판정

1. 기존 `split-entry`, `partial/rebase`, `soft-stop` 통합 지표는 오염 제거 전까지 튜닝 결론으로 사용하지 않는다.
2. `fallback_scout/main`은 탐색형 분할진입이 아니라 동시 2-leg 주문이므로 실패 설계로 폐기한다.
3. `fallback_single`은 1차 응급가드 오류 표본으로 격리한다.
4. 오늘 관찰된 불타기 수익 확대는 신규 기대값 개선 후보이나, 즉시 1순위는 `entry_filter` canary로 둔다. 물타기/분할진입은 후순위 `position_addition_policy`로 재설계한다.

### 코호트

| 코호트 | 정의 | 해석 |
| --- | --- | --- |
| `normal_only` | `entry_mode=normal`, `tag=normal`, `SAFE -> ALLOW_NORMAL` | 새 baseline 후보 |
| `fallback_scout_main_contaminated` | `fallback_scout` 또는 `fallback_main` 포함 | 실패 설계 손실/오염 표본 |
| `fallback_single_contaminated` | `fallback_single` 포함 | 1차 응급가드 오류 표본 |
| `post_fallback_deprecation` | `2026-04-21 09:45 KST` 이후 표본 | 재정렬 후 운영 표본 |
| `scale_in_profit_expansion` | 불타기/추가진입으로 수익 확대 | 신규 기대값 개선 후보 |
| `avg_down_candidate` | 물타기 후보였으나 미실행 | 신규 상태머신 후보 |

### 감사인 검토용 질문

1. 현재 `진입/보유/청산` 로직표에서 누락된 상태 전이가 있는가?
2. fallback 오염 제거 코호트 정의가 감사 가능한가?
3. 다음 튜닝 1순위는 감사인 권고에 따라 `entry_filter` canary로 둔다. 단, 장후 코호트 데이터가 반대 근거를 보이면 사유를 기록한다.
4. `position_addition_policy`는 `entry_filter -> holding_exit` 이후 후순위로 두고, 추가진입 중단 -> 불타기 -> 물타기 -> soft_stop 재해석 순서로 검토한다.
5. AI 엔진 A/B 재개 여부는 `entry_filter` canary 1차 판정 완료 후, 늦어도 `2026-04-24 POSTCLOSE`에 별도 판정하는 것이 타당한가?

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
| `관찰축 커버리지 매트릭스` | `sections.observation_axis_coverage[].axis_id` / `coverage_status` / `available` / `missing_keys` | 14개 축 상태를 한 테이블에 집약; 축별 required_keys 존재 여부를 `_check_dotted_path`로 검증 |
| `관찰축: entry_funnel` | `sections.observation_axis_coverage[0]` | `direct` / `metrics.budget_pass_events` 등 필수키 보유 |
| `관찰축: latency_quote` | `sections.observation_axis_coverage[1]` | `direct` / `breakdowns.latency_reason_breakdown` 포함 |
| `관찰축: gatekeeper_fast_reuse` | `sections.observation_axis_coverage[2]` | `direct` / `breakdowns.gatekeeper_reuse_blockers` 포함 |
| `관찰축: fill_quality` | `sections.observation_axis_coverage[3]` | `direct` / `breakdowns.fill_quality_cohorts` 포함 |
| `관찰축: holding_exit` | `sections.observation_axis_coverage[4]` | `direct` / `sections.holding_axis` 포함 |
| `관찰축: dual_persona` | `sections.observation_axis_coverage[5]` | `direct` / `breakdowns.dual_persona_agreement` 등 포함 |
| `관찰축: preset_exit_sync` | `sections.observation_axis_coverage[6]` | `direct` / `breakdowns.preset_exit_sync_status` 포함 |
| `관찰축(간접): spread_relief_canary_detail` | `sections.observation_axis_coverage[7]` | `indirect` / 리포트 표시명은 `spread relief 세부 사유`, latency 지표에서 부분 추론 가능 |
| `관찰축(외부): post_sell_quality` | `sections.observation_axis_coverage[8]` | `external_report` / post_sell_feedback 리포트 링크 |
| `관찰축(외부): wait6579_ev` | `sections.observation_axis_coverage[9]` | `external_report` / wait6579_ev_cohort 리포트 링크 |
| `관찰축(외부): missed_entry_counterfactual` | `sections.observation_axis_coverage[10]` | `external_report` / missed_entry_counterfactual 리포트 링크; 성능튜닝 손익과 합산 금지 |
| `관찰축(수집미표시): initial_vs_pyramid` | `sections.observation_axis_coverage[11]` | `collected_not_displayed` / trade_review raw log 증적 |
| `관찰축(수집미표시): pyramid_zero_qty_stage1` | `sections.observation_axis_coverage[12]` | `collected_not_displayed` / raw log 증적 |
| `관찰축(수집미표시): eod_nxt_exit` | `sections.observation_axis_coverage[13]` | `collected_not_displayed` / trade raw log 증적 |
| `Flow Bottleneck Lane` | `sections.flow_bottleneck_lane.nodes[]` | 9개 노드(watch_universe→sell_complete)의 상태/지표/튜닝포인트를 가로 흐름으로 표시 |
| `Flow: watch_universe` | `sections.flow_bottleneck_lane.nodes[0]` | 감시종목 수 / strategy_rows candidates 합계 |
| `Flow: ai_decision` | `sections.flow_bottleneck_lane.nodes[1]` | AI overlap blocked / overbought blocked |
| `Flow: entry_armed` | `sections.flow_bottleneck_lane.nodes[2]` | expired_armed / budget_pass |
| `Flow: pre_submit_latency` | `sections.flow_bottleneck_lane.nodes[3]` | latency_block / quote_fresh_latency_pass_rate로 bottleneck 탐지 |
| `Flow: submitted_fill` | `sections.flow_bottleneck_lane.nodes[4]` | order_bundle_submitted / full_fill / partial_fill |
| `Flow: holding_review` | `sections.flow_bottleneck_lane.nodes[5]` | holding_reviews / holding_skips; flow 단절 anomaly 탐지 |
| `Flow: scale_in_branch` | `sections.flow_bottleneck_lane.nodes[6]` | position_rebased_after_fill / 추가매수 표본 |
| `Flow: exit_signal` | `sections.flow_bottleneck_lane.nodes[7]` | exit_signals / preset_exit_sync_mismatch |
| `Flow: sell_complete` | `sections.flow_bottleneck_lane.nodes[8]` | completed_trades / full_fill/partial_fill 평균 손익률 |

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
