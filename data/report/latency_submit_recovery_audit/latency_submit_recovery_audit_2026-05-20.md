# Latency Submit Recovery Audit - 2026-05-20

## 결론

- Control state: `YELLOW`
- 막힌 단계: R3/R4. runtime semantics에 맞는 bounded recovery 후보는 220건 있지만, counterfactual label/EV gate가 부족해 다음 PREOPEN 적용은 보류한다.
- 영향: `latency_pass_events=0`, `order_bundle_submitted_events=0`은 후행 `pre_submit_price_guard` 문제가 아니라 latency classifier runtime semantics와 recovery label 부족 문제로 분리됐다.
- 조치: postclose source/report/apply-candidate 계층은 보정했다. runtime/order/provider/bot 즉시 변경은 수행하지 않았고, 2026-05-21 latency family 명시 PREOPEN apply에서도 latency env override는 생성되지 않았다.

## Before / After

| 항목 | 이전 해석 | 수정 후 해석 |
| --- | --- | --- |
| 후보 생성 | 고정 profile의 `would_pass=220`처럼 보임 | grid/quantile profile 486개를 만들고 runtime SAFE/CAUTION/recovery/hard reject를 분리 |
| runtime pass 의미 | `latency_fallback_deprecated`도 통과 가능처럼 섞임 | SAFE만 `would_pass_events`; 5/20 SAFE pass는 0 |
| recovery 후보 | 미분리 | `would_recovery_canary_events=220`, attempts 3 |
| reason split | 불충분 | `latency_fallback_deprecated=220`, `latency_state_danger=401` |
| label/EV | 후보별 미계산 | selected profile counterfactual sample 1, EV `-3.704%`, `AVOIDED_LOSER=1` |
| recommended action | apply처럼 보임 | `hold`, reason `counterfactual_joined_sample=1 below floor=3` |
| apply 결과 | 다음 PREOPEN 완화 가능처럼 보임 | `allowed_runtime_apply=false`, latency env override 없음 |
| primary owner | `pre_submit_price_guard`로 오해 가능 | `latency_classifier_runtime_profile`; price guard는 후행 가격품질 guard 유지 |

5/20 `latency_block` raw는 performance report 기준 624건이고, latency recommendation은 age/jitter/spread 숫자 필드가 복원 가능한 621건을 계산 대상으로 사용했다. 제외된 3건은 source-quality gap으로 남긴다.

## Selected Profile

```text
profile: balanced_1200_1500_0100
age<=1200, jitter<=1500, spread<=0.0100
would_safe_pass=0
would_caution_reject=220
would_recovery_canary=220
counterfactual_joined_sample=1
counterfactual_ev_pct=-3.704
missed_winner_recovered=0
avoided_loser_lost=1
stale_quote_override=0
broker_guard_bypass=0
recommended_action=hold
```

## R0~R6 결합

| 단계 | 구현/소비 상태 |
| --- | --- |
| R0 collect | `latency_block`, `latency_pass`, `order_bundle_submitted`의 동일 provenance contract를 source-quality에 등록했다. future `order_bundle_submitted`에도 `reason`, `latency_state`, `ws_age_ms`, `ws_jitter_ms`, `spread_ratio`, `quote_stale`, `signal_price`, `latest_price`, `latency_canary_*`, `policy/effective_decision`, `threshold_family`, `runtime_effect`, `actual_order_submitted`, `broker_order_forbidden`를 남기도록 보강했다. |
| R1 daily report | `daily_threshold_cycle_report`가 `latency_classifier_recommendation`을 source로 읽고 SAFE/CAUTION/recovery/hard reject, counterfactual sample/EV, stale/broker exclusion을 소비한다. |
| R2 EV/approval report | `threshold_cycle_ev_report`는 latency recommendation을 직접 읽는다. `runtime_approval_summary`는 `recommended_action=bounded_apply`일 때만 apply 후보로 보고, 5/20은 `latency_recovery_hold_by_counterfactual_ev`로 표시한다. |
| R3 manifest candidate | `latency_classifier_recommendation`은 고정 profile 선택이 아니라 grid/quantile search 후보를 만들고, 후보별 `would_pass_count`, recovery count, counterfactual EV, missed/avoided label을 계산한다. |
| R4/R5 preopen apply | 2026-05-21 latency family 명시 apply를 재생성했다. recommendation은 loaded지만 `allowed_runtime_apply=false`, `calibration_state=hold_sample`이어서 latency env override는 비어 있다. |
| R6 post-apply attribution | bounded apply가 없으므로 5/20 기준 post-apply recovery 평가는 열리지 않는다. 다음 후보는 label coverage와 positive EV가 충족될 때만 PREOPEN canary로 넘어간다. |

## 재생성 산출물

- `data/report/latency_classifier_recommendation/latency_classifier_recommendation_2026-05-20.json`
  - `profile_generation.mode=grid_quantile_search`
  - `profile_count=486`
  - `would_safe_pass_events=0`
  - `would_caution_reject_events=220`
  - `would_recovery_canary_events=220`
  - `hard_reject_events=401`
  - `counterfactual_joined_sample=1`
  - `counterfactual_ev_pct=-3.704`
  - `recommended_action=hold`
- `data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-20_postclose.json`
  - `pre_submit_price_guard.calibration_state=hold_sample`
  - reason: latency recovery 후보는 있으나 counterfactual EV/label gate 미충족. price guard 완화가 아니라 latency classifier 후보 보류로 라우팅.
- `data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json`
  - `entry_funnel.latency_submit_routing=latency_submit_recovery_hold`
  - `entry_funnel.recommended_action=hold`
- `data/report/runtime_approval_summary/runtime_approval_summary_2026-05-20.json`
  - `latency_classifier_runtime_profile.state=hold_sample`
  - `selected_auto_bounded_live=false`
  - `previous_selected_auto_bounded_live=true`
  - `allowed_runtime_apply=false`
  - `current_application=보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음`
  - reason `latency_recovery_hold_by_counterfactual_ev`
- `data/threshold_cycle/apply_plans/threshold_apply_2026-05-21.json`
  - latency recommendation loaded
  - `allowed_runtime_apply=false`
  - latency `runtime_env_overrides={}`
- `data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-20.json`
  - `status=pass`

## Source-Quality Gap

- `observation_source_quality_audit_2026-05-20.json` status는 `warning`.
- `latency_block` 624건의 5/20 historical raw는 pre-fix라 `latency_state`, `policy_decision`, `effective_decision`, `threshold_family`, `runtime_effect`, `actual_order_submitted`, `broker_order_forbidden` 결손이 남아 있다.
- 해석: `known_pre_fix_gap`. 과거 raw는 소급 수정하지 않았다.
- future instrumentation은 `latency_block`, `latency_pass`, `order_bundle_submitted` 모두 같은 contract를 쓰도록 보강했다.

## 감리 리뷰

### Must Fix

- `pre_submit_price_guard`가 latency drought primary owner처럼 보일 수 있었다.
  - 보완: EV report는 latency recommendation을 직접 소비하고, daily calibration은 latency recovery 판단을 `latency_classifier_runtime_profile`로 라우팅한다.
- `order_bundle_submitted` future event가 latency source-quality contract 일부 필드를 빠뜨릴 수 있었다.
  - 보완: submitted event에 latency state/reason/threshold/provenance 필드를 추가했다.
- 현재 must_fix: 0.

### Should Fix

- 5/20 recovery attempts는 3개이고 label join은 1개라 EV gate가 약하다. 다음 장후에는 latency_block counterfactual join coverage를 늘려야 한다.
- `runtime_approval_summary`의 기존 selected 이력과 신규 PREOPEN apply 허용이 혼동될 수 있었다.
  - 보완: latency row는 `recommended_action=bounded_apply`와 `allowed_runtime_apply=true`가 동시에 충족될 때만 `selected_auto_bounded_live=true`로 표시한다. 5/20은 `previous_selected_auto_bounded_live=true`, `selected_auto_bounded_live=false`로 분리됐다.

### Defer

- 5/20 historical raw provenance 결손은 소급 수정하지 않는다.
- bounded recovery canary 실효성은 `recommended_action=bounded_apply`가 나온 다음 post-apply window에서만 평가한다.

## Acceptance Check

- `would_pass=220` 표현은 runtime pass 의미에서 제거됐다. 5/20 runtime SAFE pass 후보는 0이다.
- `latency_fallback_deprecated` 220건은 `would_caution_reject=220` 및 `would_recovery_canary=220`으로 분리됐다.
- 후보 profile은 grid/quantile search로 생성되고, 후보별 recovery count, counterfactual EV, missed/avoided label, stale/broker exclusion, recommended action을 가진다.
- `threshold_cycle_ev`와 `runtime_approval_summary`는 `latency_pass=0`을 후행 `pre_submit_price_guard` 실패로 해석하지 않는다.
- 2026-05-21 latency family PREOPEN apply는 `recommended_action=hold` 때문에 latency env를 생성하지 않았다.
- 감리 must_fix는 2건 발견 후 보완했고 현재 0이다.
