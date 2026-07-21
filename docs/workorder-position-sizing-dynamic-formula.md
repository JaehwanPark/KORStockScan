# Position Sizing Dynamic Formula Workorder

기준일: `2026-07-21 KST`
owner: `position_sizing_dynamic_formula`
상태: `implemented_not_runtime_reflected`

## 1. 목적

`position_sizing_dynamic_formula`는 모든 `SCALPING/SCALP` 신규매수, Opening Rotation, Rising Missed Scout, AVG_DOWN/PYRAMID, scalping sim/counterfactual 수량의 단일 owner다. 선택 공식 `entry_type_5stage_cap25_v1`은 `10%/15%/20%/25%/25%` 5단계를 사용하고 절대 비율 상한을 25%로 고정한다. NXT·시장 판별 실패·source 결측/무효·최초 진입정보 복원 실패는 tier 1(10%)로 fail closed한다.

소스 구현은 완료됐지만 사용자의 재기동 금지에 따라 현재 프로세스에는 반영되지 않았다. 다음 명시적으로 승인된 프로세스 시작 전까지 상태는 `implemented_not_runtime_reflected`다. Report grid는 선택 공식과 `flat_10_fallback`만 비교하며 자동 runtime mutation 권한은 없다.

## 2. 입력 계약

중앙 배분기 입력은 아래 필드를 명시한다. Score·변동성·유동성은 성과 분석 feature일 수 있으나 tier 결정권은 없다.

| 입력 | 의미 | source 후보 |
| --- | --- | --- |
| `allocation_stage` | 신규/Opening/Rising/AVG_DOWN/PYRAMID/sim 단계 | runtime event |
| `reference_time` | 최초 진입 기준시각 | entry armed/buy/runtime state |
| `source_signature` | 최초 scanner source, 대소문자·중복·무효 token 정규화 대상 | scanner/runtime state |
| `effective_venue` | `KRX`/`NXT`; 불명은 fail-closed | venue resolver/runtime state |
| `budget_base_krw` | real 주문가능금액 또는 sim 10,000,000 KRW | account/broker or sim contract |
| `price_krw` | 주문 산정가격 | entry/scale-in price resolver |
| `current_position_qty` | 현재 보유수량 | account/runtime state |
| `remaining_position_qty_cap`, `stage_qty_cap`, `broker_qty_cap` | downstream 수량 상한 | position/stage/broker guard |
| `initial_formula_version`, `initial_tier` | 추가매수의 최초 진입 tier 재사용 | runtime state/reconstruction |

필수 provenance는 아래 필드를 포함한다.

- `position_sizing_formula_owner=position_sizing_dynamic_formula`
- `formula_version`
- `tier`
- `ratio`
- `tier_reason`
- `source_count`
- `reference_time`
- `venue`
- `target_budget`
- `safe_budget`
- `pre_cap_qty`
- `effective_qty`
- `min_one_share_floor_applied`
- `binding_caps`
- `actual_order_submitted`
- `budget_authority`

## 3. Source Bundle

1차 source bundle은 새 standalone 관찰축을 늘리지 않고 기존 산출물을 재사용한다.

| source | 용도 | 필수 gate |
| --- | --- | --- |
| `threshold_cycle.calibration_source_bundle.completed_by_source.real` | real-only closed EV와 downside | `COMPLETED + valid profit_rate` only |
| `buy_funnel_sentinel` | entry blocker, submitted drought, score/strategy funnel | report-only, source freshness |
| `wait6579_ev_cohort` | score 65~79 missed/probe EV | `actual_order_submitted=false` 분리 |
| `missed_entry_counterfactual` | missed upside와 candidate sizing 기회비용 | counterfactual-only |
| `scalp_sim_ev_midcheck` | sim/probe qty source와 active/open split | sim/probe 권한 분리 |
| `holding_exit_sentinel` | stop/exit pressure와 non-real split | real/non-real split pass |
| `panic_sell_defense` | recent loss/source-quality blocker | market context와 real/non-real split pass |
| `scale_in_price_guard` source metrics | spread/stale quote/scale-in price quality | execution-quality real-only guard |

## 4. Sample Floor

초기 판정은 `report_only_design`으로 시작한다.

| stage | sample floor | denominator | 판정 |
| --- | --- | --- | --- |
| `design_ready` | 0 | source contract present | 문서/스키마 검증만 가능 |
| `report_only_candidate` | 30 | real completed valid, normal-only | 산식 후보 점수화 가능 |
| `approval_required` | 60 | real completed valid + candidate provenance rows | 사용자 approval request 생성 가능 |
| `approved_live_candidate` | 100 | post-apply version window real rows | 다음 장전 apply 후보 검토 가능 |

sim/probe/counterfactual rows는 sample floor 보조 가속 입력으로만 쓰며, real denominator를 대체하지 않는다.

## 5. Primary Metric

primary metric은 아래 둘 중 하나만 사용한다.

- `notional_weighted_ev_pct`
- `source_quality_adjusted_ev_pct`

보조 진단:

- `diagnostic_win_rate`
- `submitted_count`
- `full_fill_rate`
- `order_failure_rate`
- `p10_profit_rate`
- `p90_loss_tail_pct`
- `cap_reduced_opportunity_count`
- `missed_upside_notional_krw`

금지:

- `win_rate` 단독 승인
- `simple_sum_profit_pct`를 EV로 사용
- sim/probe equal-weight EV 단독으로 실주문 확대 승인

## 6. Candidate Grid Schema (P3 적용)

`position_sizing_dynamic_formula`는 아래 2개 공식만 비교한다. 과거 7개 후보와 필드는 archive/parser 호환용으로만 읽고 현재 수량 결정권으로 사용하지 않는다.

| 후보 ID | 타입 | 설명 |
| --- | --- | --- |
| `entry_type_5stage_cap25_v1` | selected | reference time/source count/venue 5-stage allocator, max 25% |
| `flat_10_fallback` | rollback | all eligible scalping sizing at 10% with the same safety/cap composition |

후보별 metric: `real_sample_count`, `sim_probe_sample_count`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct`, `diagnostic_win_rate`, `full_fill_rate`, `partial_fill_rate`, `cancel_rate`, `late_fill_rate`, `order_failure_rate`, `min_one_share_floor_rate`, `cash_usage_pct`, `downside_p10_profit_rate`.

source-quality 결손 후보는 EV 분모에서 제외하고 `source_quality_blocked`로 닫는다.

runtime_apply_allowed=false로 시작하며 approval/preopen guard 테스트가 닫힌 뒤에만 bounded candidate를 연다.

## 6.1 Approval Artifact Schema (향후)

실주문 수량 확대 또는 산식 live 적용은 아래 artifact가 있어야 한다.

path:

```text
data/threshold_cycle/approvals/position_sizing_dynamic_formula_YYYY-MM-DD.json
```

required fields:

```json
{
  "approval_id": "position_sizing_dynamic_formula_YYYY-MM-DD",
  "approval_date": "YYYY-MM-DD",
  "owner": "position_sizing_dynamic_formula",
  "approved_by": "operator",
  "approval_scope": "candidate_grid_comparison|bounded_live_canary",
  "selected_formula_version": "entry_type_5stage_cap25_v1",
  "max_notional_krw": 3000000,
  "allowed_strategies": ["SCALPING"],
  "sample_floor_passed": false,
  "primary_metric": "notional_weighted_ev_pct",
  "primary_metric_value": null,
  "source_quality_passed": false,
  "same_stage_owner_guard_passed": false,
  "rollback_guard": {
    "order_failure_rate_max_pct": 10.0,
    "p10_profit_rate_floor_pct": -2.0,
    "severe_loss_count_max": 0,
    "receipt_provenance_required": true
  },
  "runtime_apply_allowed": false
}
```

`runtime_apply_allowed=true`는 `approval_scope=bounded_live_canary`, source-quality pass, same-stage owner guard pass, rollback guard pass가 모두 닫힌 경우에만 허용한다.

## 7. Implementation Phases

1. `P0_contract_only` - 완료 (`2026-05-14`)
   - 이 문서와 traceability/threshold README 계약 유지.
   - runtime effect 없음.
2. `P1_report_source_bundle` - 완료 (`2026-05-14`)
   - `daily_threshold_cycle_report`에 `position_sizing_dynamic_formula` metadata와 source metrics를 report-only로 추가.
   - candidate qty와 baseline qty provenance만 산출.
3. `P2_candidate_grid_archive` - 완료 (`2026-06-10`)
   - `position_sizing_cap_release` family 제거, `position_sizing_dynamic_formula` 단일 owner로 승격.
   - 7개 고정 후보 grid 생성 (`linear_10_30_current`, `linear_10_20_defensive`, `linear_15_30_aggressive`, `spread_penalized_10_30`, `liquidity_adjusted_10_30`, `recent_loss_capped_10_20`, `portfolio_exposure_capped_10_30`).
   - 후보별 metric 노출, source-quality 결손 후보 EV 분모 제외.
   - sim/probe `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false` 분리.
   - `SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED`, `SCALPING_INITIAL_ENTRY_MAX_QTY`, `SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP` env/constant/runtime parsing 삭제.
   - `runtime_apply_allowed=false`로 시작.
4. `P3_entry_type_5stage_cap25_v1` - 소스 구현 완료, runtime 미반영 (`2026-07-21`)
   - `src/engine/scalping/position_sizing_allocator.py`를 유일한 공개 수량 결정면으로 추가.
   - 일반/Opening/Rising Missed/추가매수/sim/counterfactual을 중앙 배분기로 연결.
   - Rising Missed 400,000 KRW cap과 single-order collapse, 점수 선형 및 sim 100% runtime 권한 제거.
   - 현재 프로세스는 재기동하지 않았으므로 다음 승인된 process start까지 `implemented_not_runtime_reflected` 유지.
5. `P4_runtime_approval_summary` - 미착수
   - 향후 공식 변경 조건 충족 시 approval request만 생성.
   - env override와 장중 주문 수량 변경은 생성하지 않음.
6. `P5_preopen_apply_guard` - 미착수
   - approval artifact loader와 fail-closed guard 추가.
   - 기본값은 `runtime_apply_allowed=false`.
7. `P6_bounded_live_canary` - 미착수
   - 별도 사용자 승인 뒤 다음 장전 canary로만 검토.

## 7.1 P3 구현 기록

- implemented_at: `2026-07-21 KST`
- 구현: `resolve_scalping_allocation(context)`가 tier, ratio, 예산, 95% safe budget, 최소 1주, cash/position/stage/broker cap을 한 번에 결정한다.
- KRX 경계: `09:30`, `11:30`, `13:30`, `15:20`; source count 0~5+, 중복/무효 token을 검증한다.
- NXT/unknown/reconstruction failure는 tier 1로 닫고, scale-in은 최초 tier/version을 재사용한다.
- `daily_threshold_cycle_report` candidate grid는 `entry_type_5stage_cap25_v1`과 `flat_10_fallback`만 노출한다.
- 산출물 계약: 모든 sizing event가 `formula_version`, `tier`, `ratio`, `tier_reason`, `source_count`, `reference_time`, `venue`, `target_budget`, `safe_budget`, `pre_cap_qty`, `effective_qty`, `binding_caps`를 노출한다.
- runtime 상태: source implemented, 현재 process 미재기동, `implemented_not_runtime_reflected`.
- report 권한: `allowed_runtime_apply=false`, `runtime_change=false`, `runtime_apply_allowed=false`.
- denominator: `sample_count`는 real `COMPLETED + valid profit_rate` normal-only row만 사용. sim/probe/counterfactual sizing event는 `sim_probe_sizing_event_count`와 `candidate_grid[].sim_probe_sample_count`로만 노출하며 real denominator를 대체하지 않는다.

## 7.2 Review Gate 보완 (`2026-07-21 19:56 KST`)

- 절대 안전예산보다 비싼 1주를 minimum floor가 허용하지 않도록 절대예산 cap을 floor 선행 제약으로 합성했다.
- loss-reentry, WAIT6579, scale-in 1.5x 수량 제한은 별도 수량 owner로 덮어쓰지 않고 기존 `ScalpingSizingContext`의 `stage_qty_cap`으로 재판정한다.
- `order_bundle_submitted`/`scale_in_order_submitted`에 중앙 sizing provenance를 남기고 threshold event compaction이 strategy, budget, price, cap 필드를 보존하도록 보완했다.
- `qty_source=scalping_position_sizing_allocator`는 real/sim 공통 source이므로 sim 판정에 사용하지 않는다. sim은 `actual_order_submitted=false` 또는 sim virtual budget authority로만 분리한다.
- missed-entry/WAIT6579 counterfactual row에도 동일한 formula/tier/budget/cap provenance와 `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다.
- 검증: 관련 producer/consumer 회귀 `1590 passed`, Black, compile, parser validation, `git diff --check`; unresolved finding `0`.
- runtime 상태: 봇을 재기동하지 않았으므로 `implemented_not_runtime_reflected` 유지.

## 8. Forbidden Uses

- 장중 runtime threshold/order mutation 금지.
- sim/probe/counterfactual 단독 실주문 수량 확대 금지.
- 스윙 dry-run approval을 스캘핑 수량 확대 approval로 재사용 금지.
- provider route 확인을 수량 산식 변경 근거로 사용 금지.
- bot restart를 산식 승인 근거로 사용 금지.

## 9. 테스트 기준

구현 단계에서 필요한 최소 테스트:

- 중앙 allocator 경계시각/source/NXT/fail-closed/cap 합성 테스트
- 일반/Opening/Rising Missed/scale-in/sim/counterfactual producer-consumer 테스트
- Rising Missed probe-first 총수량 보존과 broker 미호출 sim 테스트
- `daily_threshold_cycle_report` 2-formula grid/source bundle 테스트
- real/sim/probe denominator 분리 테스트
- `primary_metric` 명명/EV contract 테스트
- approval artifact missing fail-closed 테스트
- same-stage owner conflict 테스트
- rollback guard breach 테스트
- parser 검증과 `git diff --check`
