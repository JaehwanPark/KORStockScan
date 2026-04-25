# 작업지시서: 성능튜닝 모니터 관찰축 커버리지 + 플로우 병목 표시 추가 (DeepSeek 전용)

작성일: 2026-04-24 KST  
대상: DeepSeek AI (코딩 에이전트)  
범위: 통합대시보드 `performance-tuning` 탭의 관찰축 표시/검증 보강 및 진입부터 청산까지의 병목 흐름 표시  
ApplyTarget: `main` 코드베이스 문서/리포트/UI만. 실거래 주문 로직 변경 금지.

---

## 1. 판정

1. 현재 `performance-tuning` 탭은 핵심 관찰축 상당수를 보여주지만, 코드베이스에 붙여 둔 관찰축/보조축 전체를 한 화면에서 커버리지로 설명하지 않는다.
2. 다음 액션은 live canary가 아니라 `관찰축 커버리지 매트릭스`와 `진입 -> 보유 -> 청산 Flow Bottleneck Lane`을 리포트/API/UI에 추가하는 코드베이스 수정이다.
3. 이 작업은 주문 제출, 매수/매도 판단, canary flag, threshold를 바꾸면 안 된다.
4. 목표는 사용자가 `직접 표시 / 간접 표시 / 수집됨-미표시 / 별도 리포트 / 폐기-보관 후보`를 한 화면에서 구분하게 만드는 것이다.
5. 신규 섹션은 기존 성능튜닝 관찰지표를 대체하지 않는다. 기존 카드/표/리스트는 그대로 유지하고, 커버리지 섹션은 현재 표시 지표가 어떤 관찰축을 담당하는지 설명하는 `메타 색인`으로만 추가한다.
6. Flow Bottleneck Lane은 사용자가 별도 개인문서로 조율하던 `감시 -> AI 판단 -> 주문자격 -> 주문제출/체결 -> HOLDING -> 청산` 흐름을 대시보드 안에서 직접 보게 하는 운영 기능이다. 단, 개인문서를 Source로 삼지 않고 본 작업지시서의 독립 명세를 기준으로 구현한다.

---

## 2. 기준 문서와 Source/Section

1. Source: `docs/plan-korStockScanPerformanceOptimization.rebase.md`
   - Section: `§1~§6`
   - 사용 원칙: `main-only`, `normal_only`, `post_fallback_deprecation`, `COMPLETED + valid profit_rate`, `full/partial 분리`, `1축 canary`, `shadow 금지`
2. Source: `docs/2026-04-24-stage2-todo-checklist.md`
   - Section: `오늘 목적`, `오늘 강제 규칙`
   - 사용 원칙: `spread relief canary` 주병목 검증축, 신규 BUY `1주 cap`, `initial-only`와 `pyramid-activated` 분리
3. Source: `docs/plan-korStockScanPerformanceOptimization.performance-report.md`
   - Section: `§8 대시보드-검증축 매핑 (performance-tuning)`
   - 사용 원칙: 대시보드에 표시되는 검증축과 실제 snapshot/report key를 문서화한다.
4. 금지 Source: `docs/personal-decision-flow-notes.md`
   - 개인문서는 다른 문서의 판정 근거/Source로 참조하지 않는다.

---

## 3. 절대 제약

1. 실거래 로직 변경 금지.
2. `src/utils/constants.py`의 canary/env 기본값 변경 금지.
3. `sniper_entry_latency`, `sniper_state_handlers`의 주문/게이트 판단 로직 변경 금지.
4. 손익 집계는 기존과 동일하게 `COMPLETED + valid profit_rate`만 사용한다.
5. `full fill`과 `partial fill`은 합치지 않는다.
6. `wait6579_ev_cohort`, `missed_entry_counterfactual`, `post_sell_feedback` 값을 `performance_tuning` 손익값과 합산하지 않는다.
7. 신규 패키지 설치 금지. 필요한 경우 사용자 승인 전까지 표준 라이브러리/기존 의존성만 사용한다.
8. 개인문서 링크를 API/대시보드/체크리스트 Source로 노출하지 않는다.

## 3-A. 작업 가속 강제 규칙

1. 작업지시서 수행 중 관찰 결과를 해석할 수 있으면 `same-day 즉시 판정`을 기본으로 한다. `장후 보자`, `익일 보자`, `다음 장전에 보자`는 기본 응답이 아니다.
2. same-day에 닫지 못한다고 판단할 경우 아래 4문항을 같은 턴에 모두 답해야 한다.
   - `지금 닫을 수 없는 이유는 무엇인가`
   - `추가 데이터가 필요한가, 아니면 코드베이스 수정이 필요한가`
   - `단일 조작점/rollback guard/restart 절차가 same-day 가능한가`
   - `불가하면 막힌 조건과 다음 절대시각은 무엇인가`
3. 위 4문항 중 하나라도 비어 있으면 `장후/익일 이관` 판정은 무효다.
4. PREOPEN은 전일 준비가 끝난 carry-over 승인 슬롯만 허용한다. same-day에 분해 가능한 후보를 `다음 장전 검토`로 넘기지 않는다.
5. DeepSeek는 이 작업지시서 범위에서도 가능한 판단을 늦추지 말고, `이미 수집된 데이터로 닫히는가`와 `코드수정이 필요하면 same-day 착수 가능한가`를 먼저 본다.

---

## 4. 구현 목표

`/dashboard?tab=performance-tuning` 또는 `/performance-tuning` 화면에 `관찰축 커버리지` 섹션과 `Flow Bottleneck Lane` 섹션을 추가한다.

기존 표시 지표는 아래처럼 유지한다. 삭제, 이름 변경, 계산식 변경은 이번 범위가 아니다.

| 표시군 | 현재 대표 지표/섹션 | 처리 원칙 |
| --- | --- | --- |
| 상단 metric cards | `cards`, `holding_reviews`, `gatekeeper_decisions`, `dual_persona_shadow_samples` | 그대로 유지 |
| 스캘핑 퍼널/체결 품질 | `budget_pass_events`, `order_bundle_submitted_events`, `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `expired_armed_events`, `full_fill_completed_avg_profit_rate`, `partial_fill_completed_avg_profit_rate` | 그대로 유지 |
| latency 분해 | `breakdowns.latency_reason_breakdown`, `breakdowns.latency_danger_reason_breakdown` | 그대로 유지 |
| 체결 cohort | `breakdowns.fill_quality_cohorts`, `full_fill_events`, `partial_fill_events` | 그대로 유지, full/partial 합산 금지 |
| preset/AI overlap | `breakdowns.preset_exit_sync_status`, `breakdowns.ai_overlap_blocked_stages`, `ai_overlap_overbought_blocked_events` | 그대로 유지 |
| post-sell KPI | `post_sell_kpi_cards` | 기존 별도 리포트 연결 유지 |
| 전략/성과 rows | `strategy_rows` | 그대로 유지 |
| 스윙/시장요약 | `sections.swing_daily_summary` | 그대로 유지 |
| 조정 관찰 포인트 | `watch_items` | 그대로 유지 |
| 판정 gate/rollback | `sections.judgment_gate` | 그대로 유지 |
| HOLDING 필수 관찰축 | `sections.holding_axis` | 그대로 유지 |
| 보유/Gatekeeper reuse | `breakdowns.holding_ai_cache_modes`, `breakdowns.holding_reuse_blockers`, `breakdowns.holding_sig_deltas`, `breakdowns.gatekeeper_cache_modes`, `breakdowns.gatekeeper_reuse_blockers`, `breakdowns.gatekeeper_sig_deltas`, `breakdowns.gatekeeper_actions` | 그대로 유지 |
| Dual Persona | `dual_persona_*`, `breakdowns.dual_persona_*` | 그대로 유지 |
| slow top lists | `sections.top_holding_slow`, `sections.top_gatekeeper_slow`, `sections.top_dual_persona_slow` | 그대로 유지 |

각 row는 아래 필드를 가진다.

1. `axis_id`: 안정적인 영문 ID. 예: `entry_funnel`, `latency_quote`, `wait6579_ev`, `missed_entry_counterfactual`
2. `axis_name`: 한국어 표시명
3. `coverage_status`: `direct`, `indirect`, `external_report`, `collected_not_displayed`, `deprecated_archive` 중 하나
4. `source_snapshot`: `performance_tuning`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `post_sell_feedback`, `trade_review`, `raw_log`, `archived` 등
5. `dashboard_location`: 현재 화면에서 어디에 보이는지. 미표시이면 `-`
6. `decision_use`: 어떤 판정에 쓰는지. 예: `제출병목`, `체결품질`, `기회비용`, `HOLDING/청산`, `canary rollback`
7. `required_keys`: 핵심 metric/breakdown key 목록
8. `gap_action`: 직접 표시가 아니면 보완 액션. 예: `별도 리포트 링크`, `추후 탭 분리`, `raw 증적 유지`
9. `owner_doc`: 기준 문서. 개인문서 금지.
10. `available`: `required_keys`가 현재 report dict에 모두 존재하면 `true`, 일부 없으면 `false`
11. `missing_keys`: `available=false`일 때 누락된 key 목록
12. `reuse_mode`: `existing_metric`, `existing_breakdown`, `existing_section`, `external_report_pointer`, `raw_log_pointer`, `archive_pointer` 중 하나

`direct` 또는 `indirect` row에서 `available=false`가 나오면 정상 완료가 아니다. 이 경우 DeepSeek는 지표를 새로 조용히 만들지 말고, `missing_keys`와 기존 리포트 생성 경로의 연결 끊김 여부를 먼저 보고해야 한다.

---

## 5. Flow Bottleneck Lane 요구사항

### 5-1. 목적

성능튜닝 모니터 상단 또는 `관찰축 커버리지` 바로 위에, 진입부터 청산까지의 횡방향 흐름을 한 줄로 표시한다. 각 노드는 현재 병목/이상치/관측대기 상태를 badge로 보여주고, 해당 노드의 튜닝포인트와 근거 지표를 바로 확인할 수 있어야 한다.

이 기능의 목표는 사용자가 별도 문서 없이도 오늘의 주병목이 어디인지, 다음 튜닝 후보가 어느 구간인지, 제출축이 풀린 뒤 HOLDING/청산으로 검증 초점이 이동했는지를 한 화면에서 판단하게 하는 것이다.

### 5-2. 필수 노드

최소 아래 노드를 횡방향으로 표시한다.

| node_id | 표시명 | 단계 | 기존 재사용 지표 | 병목/이상치 예시 |
| --- | --- | --- | --- | --- |
| `watch_universe` | 감시/후보 | ENTRY upstream | `strategy_rows`, `swing_daily_summary.metrics.candidates` | 후보 부족, regime 부적합 |
| `ai_decision` | AI BUY 판단 | ENTRY upstream | `strategy_rows`, `ai_overlap_blocked_events`, `ai_overlap_overbought_blocked_events` | AI threshold miss, overbought gate miss |
| `entry_armed` | 주문 자격 | ENTRY midstream | `expired_armed_events`, `budget_pass_events` | entry_armed 만료, 예산/수량 차단 |
| `pre_submit_latency` | 제출 전 latency/quote | ENTRY downstream | `latency_block_events`, `latency_pass_events`, `quote_fresh_latency_pass_rate`, `latency_reason_breakdown` | latency guard miss, spread/quote freshness 병목 |
| `submitted_fill` | 주문 제출/체결 | EXECUTION | `order_bundle_submitted_events`, `full_fill_events`, `partial_fill_events`, `fill_quality_cohorts` | submitted 단절, partial fill 악화 |
| `holding_review` | HOLDING 리뷰 | HOLDING | `holding_reviews`, `holding_skips`, `holding_axis`, `holding_reuse_blockers` | AI 리뷰 지연, reuse bypass 증가, action 미적용 |
| `scale_in_branch` | 추가매수/피라미드 분기 | HOLDING branch | `position_rebased_after_fill_events`, raw `ADD_BLOCKED`/`ADD_ORDER_SENT` pointer | zero_qty, floor_applied 관측대기, pyramid 원인 혼입 |
| `exit_signal` | 청산 신호 | EXIT | `exit_signals`, `exit_rules`, `preset_exit_sync_status` | soft_stop/trailing 충돌, preset mismatch |
| `sell_complete` | 매도/청산 완료 | EXIT completion | `post_sell_kpi_cards`, `COMPLETED + valid profit_rate`, `full/partial` 분리 결과 | sell_fail, missed_upside, capture_efficiency 악화 |

### 5-3. 노드 필드

`sections.flow_bottleneck_lane`을 추가하고 각 node row는 아래 필드를 가진다.

1. `node_id`
2. `node_name`
3. `stage_group`: `ENTRY`, `EXECUTION`, `HOLDING`, `EXIT`
4. `status`: `ok`, `watch`, `bottleneck`, `anomaly`, `waiting`, `not_applicable`
5. `primary_metric`: 대표 metric key
6. `primary_value`: 대표 metric 값
7. `supporting_metrics`: 보조 metric key/value 목록
8. `tuning_point`: 현재 조정 후보. 없으면 `-`
9. `evidence_keys`: dotted path 목록
10. `missing_keys`: 연결 끊김 또는 미생성 key 목록
11. `next_action`: 다음 판단 또는 parking 사유

### 5-4. 상태 판정 규칙

상태 판정은 간단한 rule 기반으로 시작한다. 임의 AI 판단이나 새 모델 호출을 넣지 않는다.

1. `pre_submit_latency`
   - `latency_block_events > 0`이고 `quote_fresh_latency_pass_rate`가 낮으면 `bottleneck`
   - `budget_pass_events > 0`인데 `order_bundle_submitted_events = 0`이면 `bottleneck`
2. `submitted_fill`
   - `order_bundle_submitted_events = 0`이면 `waiting`
   - `partial_fill_events`가 `full_fill_events`보다 과도하게 높으면 `watch`
3. `holding_review`
   - `holding_reviews = 0`이고 submitted/fill도 0이면 `waiting`
   - submitted/fill이 있는데 `holding_reviews = 0`이면 `anomaly`
4. `scale_in_branch`
   - raw log pointer만 있고 same-day 실로그가 없으면 `waiting`
   - `ADD_BLOCKED reason=zero_qty`가 반복되면 `bottleneck`
5. `exit_signal`
   - `preset_exit_sync_mismatch_events > 0`이면 `watch` 또는 `anomaly`
   - `exit_signals = 0`이고 holding 표본이 없으면 `waiting`
6. `sell_complete`
   - 손익 판단은 `COMPLETED + valid profit_rate`만 사용한다.
   - `post_sell` missed_upside/capture 지표는 기회비용 참고이며 실현손익과 합산하지 않는다.

정확한 threshold는 하드코딩 최소화한다. 처음에는 `0/존재/비율 악화` 중심으로 표시하고, 문서화된 Plan Rebase guard(`loss_cap`, `latency_p95`, `partial_fill_ratio`, `fallback_regression`)만 명시적으로 사용한다.

### 5-5. UI 요구사항

1. Flow는 좌에서 우로 이어지는 lane으로 표시한다.
2. 데스크톱에서는 한 줄 가로 스크롤 또는 wrapping lane을 허용한다.
3. 모바일에서는 카드형 세로 스택으로 깨지지 않게 표시한다.
4. 각 노드는 `status` badge와 `primary_metric`을 보여준다.
5. 노드 클릭/확장 없이도 `tuning_point`와 `next_action`이 보이게 한다.
6. 기존 `strategy_rows`, `watch_items`, `judgment_gate`, `holding_axis` 섹션은 유지한다. Flow는 이를 대체하지 않고 요약 네비게이션 역할을 한다.

### 5-6. 기존 지표 재사용 원칙

Flow node는 반드시 기존 `performance_tuning` report dict의 값을 우선 재사용한다.

1. 신규 원본 파싱을 추가하지 않는다.
2. 같은 의미의 중복 집계를 새로 만들지 않는다.
3. 외부 리포트가 필요한 노드는 `external_report_pointer`로 표시한다.
4. raw log가 필요한 노드는 `raw_log_pointer`로 표시하고, 실시간 수치가 없으면 `waiting` 또는 `collected_not_displayed`로 둔다.
5. `missing_keys`가 있는 노드는 정상처럼 녹색 표시하지 않는다.

---

## 6. 필수 커버리지 목록

최소 아래 축을 매트릭스에 포함한다.

| axis_id | axis_name | 기대 coverage_status | source_snapshot | required_keys 예시 |
| --- | --- | --- | --- | --- |
| `entry_funnel` | 진입/제출 퍼널 | `direct` | `performance_tuning` | `budget_pass_events`, `order_bundle_submitted_events`, `budget_pass_to_submitted_rate` |
| `latency_quote` | latency/quote fresh | `direct` | `performance_tuning` | `latency_block_events`, `latency_pass_events`, `quote_fresh_latency_pass_rate`, `breakdowns.latency_reason_breakdown` |
| `gatekeeper_fast_reuse` | Gatekeeper fast reuse | `direct` | `performance_tuning` | `gatekeeper_fast_reuse_ratio`, `gatekeeper_eval_ms_p95`, `breakdowns.gatekeeper_reuse_blockers`, `breakdowns.gatekeeper_sig_deltas` |
| `fill_quality` | full/partial 체결품질 | `direct` | `performance_tuning` | `full_fill_events`, `partial_fill_events`, `breakdowns.fill_quality_cohorts` |
| `holding_exit` | 보유/청산 축 | `direct` | `performance_tuning` | `holding_reviews`, `holding_skips`, `sections.holding_axis`, `breakdowns.exit_rules` |
| `post_sell_quality` | 청산 후 missed_upside/good_exit | `external_report` | `post_sell_feedback` | `MISSED_UPSIDE`, `GOOD_EXIT`, `capture_efficiency_avg_pct` |
| `wait6579_ev` | WAIT65~79 BUY recovery EV | `external_report` | `wait6579_ev_cohort` | `recovery_check`, `promoted`, `budget_pass`, `latency_block`, `submitted` |
| `missed_entry_counterfactual` | 미진입 기회비용 | `external_report` | `missed_entry_counterfactual` | `MISSED_WINNER`, `AVOIDED_LOSER`, `estimated_counterfactual_pnl_10m_krw_sum` |
| `spread_relief_canary_detail` | spread relief 세부 사유 | `indirect` 또는 `collected_not_displayed` | `performance_tuning`/`raw_log` | `spread_only_required`, `low_signal`, `quote_stale`, `latency_canary_reason` |
| `initial_vs_pyramid` | initial-only vs pyramid-activated | `collected_not_displayed` | `trade_review`/`raw_log` | `initial_entry`, `pyramid_activated`, `position_rebased_after_fill` |
| `pyramid_zero_qty_stage1` | PYRAMID zero_qty Stage 1 | `collected_not_displayed` | `raw_log` | `template_qty`, `cap_qty`, `floor_applied`, `reason=zero_qty` |
| `eod_nxt_exit` | EOD/NXT 청산 운영축 | `collected_not_displayed` | `trade_review`/`raw_log` | `exit_rule`, `sell_order_status`, `sell_fail_reason`, `is_nxt` |
| `dual_persona` | Dual Persona 보조축 | `direct` | `performance_tuning` | `dual_persona_shadow_samples`, `dual_persona_conflict_ratio`, `breakdowns.dual_persona_*` |
| `preset_exit_sync` | preset exit sync | `direct` | `performance_tuning` | `preset_exit_sync_ok_events`, `preset_exit_sync_mismatch_events`, `breakdowns.preset_exit_sync_status` |

---

## 7. 파일 단위 작업지시

### 7-1. `src/engine/sniper_performance_tuning_report.py`

1. `sections.observation_axis_coverage`를 추가한다.
2. 커버리지 row 생성은 별도 함수로 분리한다.
   - 제안 함수명: `_build_observation_axis_coverage(metrics: dict, breakdowns: dict) -> list[dict]`
3. 함수는 현재 metric 존재 여부에 따라 `direct` 축의 `available` 여부를 계산한다.
4. `external_report`와 `collected_not_displayed` 축은 값 로딩을 강제하지 말고, source와 gap_action을 명확히 표시한다.
5. 기존 `metrics`, `breakdowns`, `sections` schema key를 제거하거나 이름 변경하지 않는다.
6. `PERFORMANCE_TUNING_SCHEMA_VERSION`을 올릴지 여부를 판단한다.
   - API/스냅샷 구조에 `sections` 신규 key가 추가되므로 schema version bump가 타당하다.
   - bump 시 저장 snapshot 호환 경로가 깨지지 않도록 `_load_saved_performance_tuning_snapshot` 동작을 확인한다.
7. `direct`/`indirect` 축은 반드시 기존 `metrics`, `breakdowns`, `sections` 값을 재사용한다.
   - 새 집계를 추가해 같은 의미의 중복 지표를 만들지 않는다.
   - `required_keys` 경로 확인 helper를 두고 `available`/`missing_keys`를 계산한다.
   - 예: `metrics.budget_pass_events`, `breakdowns.latency_reason_breakdown`, `sections.holding_axis`처럼 dotted path를 검증한다.
8. 생성되지 않거나 연결이 끊긴 지표가 있으면 `meta.warnings` 또는 커버리지 row의 `missing_keys`에 노출한다.
   - `direct` row가 누락인데 화면에서 정상처럼 보이면 안 된다.
   - 누락을 0으로 정규화해서 숨기지 않는다.
9. `sections.flow_bottleneck_lane`을 추가한다.
   - 제안 함수명: `_build_flow_bottleneck_lane(report_like: dict) -> list[dict]` 또는 metrics/breakdowns/sections 인자 기반 함수
   - flow node도 existing metric/breakdown/section 재사용 원칙을 따른다.
   - `missing_keys`가 있으면 node `status`를 `anomaly` 또는 `waiting`으로 두고 `meta.warnings`에 요약한다.

### 7-2. `src/web/app.py`

1. `/performance-tuning` 템플릿에 `관찰축 커버리지` 섹션을 추가한다.
2. 컬럼은 최소 `관찰축`, `상태`, `Source`, `대시보드 위치`, `판정 용도`, `보완 액션`을 표시한다.
3. 상태 badge를 구분한다.
   - `direct`: 직접 표시
   - `indirect`: 간접 표시
   - `external_report`: 별도 리포트
   - `collected_not_displayed`: 수집/미표시
   - `deprecated_archive`: 보관/폐기 후보
4. 모바일에서도 행이 깨지지 않도록 기존 카드/리스트 스타일을 재사용한다.
5. `/api/performance-tuning`은 별도 변경 없이 report dict에 포함된 `sections.observation_axis_coverage`를 내려야 한다.
6. 기존 화면 섹션은 삭제하지 않는다.
   - `cards`, `watch_items`, `strategy_rows`, `post_sell_kpi_cards`, `swing_daily_summary`, `judgment_gate`, `holding_axis`, `top_*_slow` 렌더링을 유지한다.
   - 신규 섹션은 `조정 관찰 포인트`와 `판정 gate` 주변 또는 그 아래에 추가하되, 기존 섹션 순서를 깨지 않는다.
7. `/performance-tuning` 템플릿에 `진입 -> 청산 흐름 병목` 또는 동등한 제목의 Flow Bottleneck Lane 섹션을 추가한다.
   - 관찰축 커버리지보다 위에 두는 것을 권장한다.
   - 각 node는 `node_name`, `status`, `primary_metric`, `primary_value`, `tuning_point`, `next_action`을 표시한다.
   - 노드 순서는 `watch_universe -> ai_decision -> entry_armed -> pre_submit_latency -> submitted_fill -> holding_review -> scale_in_branch -> exit_signal -> sell_complete`로 고정한다.

### 7-3. `docs/plan-korStockScanPerformanceOptimization.performance-report.md`

1. `§8 대시보드-검증축 매핑 (performance-tuning)`에 `observation_axis_coverage` 매핑을 추가한다.
2. 위 `필수 커버리지 목록`을 문서 표로 반영한다.
3. 개인문서(`personal-decision-flow-notes.md`)를 Source로 참조하지 않는다.
4. `external_report` 축은 성능튜닝 화면의 손익/EV 값과 직접 합산하지 않는다고 명시한다.
5. `sections.flow_bottleneck_lane` 매핑을 추가한다.
6. Flow node별 기존 metric/breakdown/section 재사용 관계를 표로 문서화한다.

### 7-4. 테스트 파일

아래 중 기존 파일이 있으면 수정하고, 없으면 신규 작성한다.

1. `src/tests/test_performance_tuning_report.py`
   - `sections.observation_axis_coverage`가 존재하는지 검증한다.
   - 필수 `axis_id`가 모두 포함되는지 검증한다.
   - `direct`/`indirect` row의 `required_keys`가 실제 report dict에 존재하면 `available=true`가 되는지 검증한다.
   - 일부러 없는 dotted path를 넣은 테스트 fixture에서는 `available=false`와 `missing_keys`가 노출되는지 검증한다.
   - 기존 `metrics`, `breakdowns`, `sections` 핵심 key가 제거되지 않았는지 검증한다.
   - `sections.flow_bottleneck_lane`이 존재하고 필수 `node_id`가 순서대로 포함되는지 검증한다.
   - `budget_pass_events > 0`이고 `order_bundle_submitted_events = 0`인 fixture에서 `pre_submit_latency` 또는 `submitted_fill`이 `bottleneck`/`waiting`으로 표시되는지 검증한다.
   - `submitted/fill` 표본이 있는데 `holding_reviews = 0`인 fixture에서 `holding_review`가 `anomaly`로 표시되는지 검증한다.
   - `full_fill`/`partial_fill` 관련 기존 테스트가 있으면 훼손하지 않는다.
2. `src/tests/test_web_performance_tuning.py` 또는 유사 웹 테스트
   - HTML에 `관찰축 커버리지`와 주요 axis label이 렌더링되는지 검증한다.
   - HTML에 `진입 -> 청산 흐름 병목` 또는 Flow 섹션 제목과 `entry_armed`, `submitted`, `HOLDING`, `청산` 계열 label이 렌더링되는지 검증한다.
   - API 응답에 `sections.observation_axis_coverage`가 포함되는지 검증한다.
   - API 응답에 `sections.flow_bottleneck_lane`이 포함되는지 검증한다.
   - 기존 표시 문구(`스캘핑 퍼널/체결 품질`, `조정 관찰 포인트`, `HOLDING 필수 관찰축`, `Gatekeeper 재사용 차단 사유`)가 계속 렌더링되는지 검증한다.

---

## 8. 완료 기준

1. `/api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS` 응답에 `sections.observation_axis_coverage`가 포함된다.
2. `/api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS` 응답에 `sections.flow_bottleneck_lane`이 포함된다.
3. `/performance-tuning` 및 통합대시보드 성능튜닝 탭에서 `관찰축 커버리지` 섹션과 `진입 -> 청산 흐름 병목` 섹션이 보인다.
4. 최소 커버리지 목록의 모든 `axis_id`가 API와 화면에 포함된다.
5. Flow의 모든 필수 `node_id`가 API와 화면에 순서대로 포함된다.
6. 기존 핵심 지표가 사라지지 않는다.
   - `budget_pass_to_submitted_rate`
   - `quote_fresh_latency_pass_rate`
   - `gatekeeper_eval_ms_p95`
   - `full_fill_events`
   - `partial_fill_events`
   - `sections.holding_axis`
7. 기존 표시군이 사라지지 않는다.
   - `cards`
   - `watch_items`
   - `strategy_rows`
   - `post_sell_kpi_cards`
   - `sections.swing_daily_summary`
   - `sections.judgment_gate`
   - `sections.holding_axis`
   - `sections.top_holding_slow`
   - `sections.top_gatekeeper_slow`
   - `sections.top_dual_persona_slow`
8. `direct`/`indirect` row 중 `available=false`가 있으면 완료가 아니라 연결 끊김 보고로 제출한다.
9. Flow node 중 `missing_keys`가 있으면 완료가 아니라 연결 끊김 또는 관측대기 보고로 제출한다.
10. 실거래 로직 파일의 판단/주문 로직 diff가 없어야 한다.
11. 문서 `§8`이 신규 매트릭스와 Flow node 매핑과 일치한다.

---

## 9. 테스트 계획

필수 테스트:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_performance_tuning_report.py
```

웹 테스트가 있는 경우:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_web_performance_tuning.py
```

현재 저장소 테스트명이 다르면, 관련 테스트를 `rg -n "performance_tuning|performance-tuning|observation_axis" src/tests -S`로 확인한 뒤 가장 가까운 테스트 파일을 실행한다.

수동 API 스모크:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sniper_performance_tuning_report --help
curl -fsS 'http://127.0.0.1:8000/api/performance-tuning?date=2026-04-24&since=08:20:00' | jq '.sections.observation_axis_coverage'
curl -fsS 'http://127.0.0.1:8000/api/performance-tuning?date=2026-04-24&since=08:20:00' | jq '.sections.flow_bottleneck_lane'
```

주의: 로컬 서버 포트/실행 방식이 다르면 프로젝트 표준 Flask 실행 경로를 사용한다. 포트 변경을 코드에 하드코딩하지 않는다.

---

## 10. DeepSeek 제출 형식 (강제)

최종 답변은 아래 순서만 사용한다.

1. 판정
2. 근거
3. 다음 액션

반드시 포함한다.

1. 변경 파일 목록
2. 추가된 `axis_id` 전체 목록
3. 추가된 flow `node_id` 전체 목록과 현재 status 요약
4. 기존 표시 지표 보존 확인 목록
5. `available=false` 또는 `missing_keys` 발생 여부
6. 현재 주병목 node와 근거 metric
7. 실행한 테스트 명령과 결과
8. 실거래 로직 변경 없음 확인
9. 문서 업데이트 위치

---

## 11. 금지 사항 요약

1. live canary 추가/변경 금지.
2. threshold/env 기본값 변경 금지.
3. 주문 제출/청산/추가매수 로직 변경 금지.
4. 개인문서를 기준 Source로 참조 금지.
5. `external_report` 축을 성능튜닝 손익과 합산 금지.
