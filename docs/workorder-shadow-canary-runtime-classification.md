# 작업지시서: Shadow/Canary 런타임 경로와 Live Cohort 분류 기준

작성일: `2026-04-25 KST`  
대상: KORStockScan 메인 코드베이스 운영/튜닝 문서 소유자  
ApplyTarget: `main` 문서/후속 코드정리 기준  

이 문서는 체크리스트/Project/Calendar 자동관리 대상이 아닌 독립 workorder다. 목적은 `shadow/canary` 경로를 일괄 삭제하는 것이 아니라, `지속 모니터링 가치`와 `운영/코드 부채`를 함께 평가해 각 경로를 `remove / observe-only / baseline-promote / active-canary` 중 하나로 고정하고, live 전환/병렬 관찰 시 섞이면 안 되는 `cohort`도 함께 분류 기준으로 잠그는 것이다.

---

## 1. 배경

기준 문서:

1. [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)
2. [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
3. [2026-04-24-stage2-todo-checklist.md](./2026-04-24-stage2-todo-checklist.md)

현재 기준은 아래로 고정한다.

1. `Plan Rebase`의 신규/보완축 운영 원칙은 `shadow 금지`, `canary-only`, `하루 1축 live`, `baseline 승격은 근거가 닫힌 뒤 별도 정리`다.
2. 그러나 코드베이스에는 여전히 `legacy shadow`, `observe-only shadow`, `이름은 canary지만 사실상 운영 기본값으로 굳은 축`, `여전히 실험 축인 canary`가 섞여 있다.
3. 따라서 다음 액션은 무조건 삭제가 아니라, 각 경로를 동일한 평가 축으로 분류하고 후속 코드 액션까지 닫는 것이다.
4. 이 문서는 실행 checklist가 아니라 `분류 기준`, `가치 평가 규칙`, `판정표`, `후속 코드정리 기준`을 소유한다.
5. 이미 적용된 `dual_persona/watch75 shadow` 런타임 가드는 현 상태의 일부로 간주한다. 이 문서는 그 상태를 포함해 해당 축을 `remove`로 닫을지, `observe-only`로 남길지를 공식 판정하는 기준 문서다.
6. 새 `shadow/canary` 경로를 추가하거나, 기존 항목의 분류를 `remove / observe-only / baseline-promote / active-canary` 중 다른 상태로 바꾸면 같은 change set에서 이 문서의 판정표도 함께 갱신해야 한다.
7. 장후 `POSTCLOSE` 분류/정리 항목은 same-day 변경 누락을 보정하는 daily review 용도이며, 생성/상태변경 시점의 문서 갱신 의무를 대체하지 않는다.
8. 조사 범위는 `src/utils/constants.py`의 운영 토글/상수와 `src/engine/`의 실런타임 분기, 이벤트 stage, shadow 기록, canary 적용 경로로 고정한다.
9. `src/web/`, `src/template/`의 CSS `box-shadow`, 공용 `analyze_target_shadow_prompt` capability, `S15 shadow record` 같은 execution bookkeeping은 `튜닝 shadow/canary 축`에서 제외한다.
10. `cohort tag`가 live 전환, stage-disjoint 예외, rollback 판정의 단위가 된 이상 `canary flag`만 정리하고 cohort를 방치하는 상태는 허용하지 않는다. live/observe/제외 코호트는 문서 기준으로 같이 잠가야 한다.

---

## 2. 평가 축

모든 항목은 아래 공통 축으로 평가한다.

| 평가축 | 설명 | 판정 기준 |
| --- | --- | --- |
| `live 영향도` | 현재 실주문/실판단 경로에 실제 영향이 있는지 | `none`, `guarded-off`, `limited-live`, `baseline-live` |
| `튜닝 모니터링 가치` | 이후 튜닝/rollback/후속 축 선택에 남길 가치 | `High`, `Medium`, `Low` |
| `EV 판정 기여도` | 기대값/순이익 판단에 직접 기여하는 정도 | `High`, `Medium`, `Low` |
| `대체 가능성` | 동일 정보가 다른 리포트/이벤트로 충분히 대체되는지 | `Low`, `Medium`, `High` |
| `운영 부하/지연 비용` | 런타임 비용, 추가 API, 지연, 관측 오염 가능성 | `Low`, `Medium`, `High` |
| `코드 유지비` | 상수, 분기, 리포트, 테스트를 유지하는 비용 | `Low`, `Medium`, `High` |
| `향후 재개 가능성` | 이후 재사용/재개할 현실적인 가능성 | `Low`, `Medium`, `High` |

`튜닝 모니터링 가치`는 아래 등급으로만 쓴다.

### `High`

1. 다른 지표로 대체되지 않고
2. 다음 canary 선택, rollback 판정, baseline 승격 판단에 직접 쓰이며
3. 운영 비용 대비 정보가치가 높다.

### `Medium`

1. 직접 판정에는 약하지만
2. 특정 failure mode 재현, 오염 탐지, 후보 검증에는 유효하다.

### `Low`

1. 이미 다른 리포트/이벤트로 충분히 대체 가능하거나
2. 현재 운영 원칙상 다시 사용할 가능성이 낮다.

각 판정은 반드시 아래 4개를 함께 남긴다.

1. `가치 등급`
2. `왜 그렇게 보는지`
3. `등급이 올라가는 조건`
4. `등급이 내려가는 조건`

최소 공통 해석 규칙은 아래로 고정한다.

1. `EV 판정 기여도`가 낮아도 `운영 오염 탐지` 가치가 높으면 `observe-only`는 가능하다.
2. `운영 부하/지연 비용`이 높고 `대체 가능성`도 높으면 `remove` 우선이다.
3. 현재 `True`인 canary라도 이미 baseline live로 해석 중이면 `baseline-promote` 후보로 본다.
4. `baseline-promote`는 즉시 rename이 아니라, `현재는 baseline처럼 쓰지만 이름/문서/로그가 canary인 상태`를 뜻한다.

---

## 3. 분류 체계

| 분류 | 의미 | 후속 코드 액션 기준 |
| --- | --- | --- |
| `remove` | live도 아니고 모니터링 가치도 낮고, 다른 지표로 대체 가능 | 호출 제거, 상수 제거, 리포트/테스트/문서 정리 여부까지 함께 닫는다 |
| `observe-only` | live 판단에는 안 쓰지만 튜닝 모니터링 가치가 남아 있음 | 실주문/실판단 비사용을 명시하고, 어느 리포트/리뷰에서만 유지할지 고정한다 |
| `baseline-promote` | 사실상 운영 기본 경로인데 이름/분기가 아직 canary | 상수명, 로그명, 문서 용어, rollback 표현 정리 범위를 함께 닫는다 |
| `active-canary` | 아직 실험 축으로 유지해야 함 | 성공 기준, 종료 조건, OFF 조건, baseline 승격 판단 시점을 같이 둔다 |

후속 코드 액션 연결 규칙은 아래로 고정한다.

1. `remove`
   - 호출 제거 여부
   - 상수 제거 여부
   - 리포트/대시보드 정리 여부
   - 테스트 삭제/수정 여부
   - same change set으로 판정표/관련 기준문서 동시 갱신 여부
2. `observe-only`
   - live 판단 비사용 명시
   - 유지 리포트/로그 범위 명시
   - baseline 승격 금지 명시
3. `baseline-promote`
   - rename 대상 상수
   - rename 대상 로그 stage/reason
   - 문서 용어 정리 범위
   - rollback guard는 유지하되 `canary` 표현 제거 범위
4. `active-canary`
   - 현재 live/guard 상태
   - 성공 기준
   - 종료 또는 승격 조건
   - 실패 시 OFF 또는 parking 조건

### 3.1 Live Cohort 분류

`shadow/canary` 축 정리와 별도로, live 전환에 쓰이는 cohort는 아래 5개 상태로만 분류한다.

| cohort 상태 | 의미 | live 판정 사용 방식 |
| --- | --- | --- |
| `baseline-decision` | 기준선 EV/품질 판정의 주 비교모집단 | 기준선 유지 여부 판단에 직접 사용 |
| `active-canary-decision` | 현재 live canary가 실제로 바꾼 모집단 | baseline과 분리 비교, rollback 직접 연결 |
| `provisional-stage-disjoint` | 병렬 canary 예외에서 다른 조작점과 분리된 임시 cohort | hard pass/fail 금지, provisional 판정만 허용 |
| `observe-only` | 리포트/모니터링에는 남기지만 live go/no-go에는 직접 쓰지 않는 cohort | 오염 탐지/후속 설계 참고용 |
| `excluded` | fallback, stale snapshot, partial/full 혼합, initial/pyramid 혼합 등 현재 판정에서 제외할 모집단 | 손익/승인 판단 입력 금지 |

live 전환 시 cohort는 최소 아래 필드를 같이 잠근다.

1. `cohort_name`
2. `cohort_status`
3. `entry_or_exit_stage`
4. `apply_target`
5. `cohort_tag`
6. `inclusion_rule`
7. `exclusion_rule`
8. `rollback_owner`
9. `allowed_metrics`
10. `forbidden_aggregations`

cohort 분류 공통 규칙은 아래로 고정한다.

1. `baseline-decision` cohort는 `main-only`, `normal_only`, `post_fallback_deprecation`, `COMPLETED + valid profit_rate`, `full/partial 분리` 원칙을 깨면 안 된다.
2. `active-canary-decision` cohort는 반드시 ON/OFF 가능한 단일 조작점과 1:1로 연결돼야 하며, `applied/not-applied`를 raw event에서 복원할 수 있어야 한다.
3. `provisional-stage-disjoint` cohort는 별도 `cohort tag`, 별도 rollback guard, 별도 적용시점이 동시에 없으면 만들 수 없다.
4. `observe-only` cohort는 future candidate 탐색에는 쓸 수 있지만, 실현손익 pass/fail 근거로 승격하면 안 된다.
5. `excluded` cohort는 손익 왜곡 방지용이므로, 제외 사유가 줄어들었다고 즉시 baseline으로 되돌리지 않고 별도 재승인 절차를 거친다.

### 3.2 Live 전환 시 Cohort 잠금 템플릿

새 live 축 승인 또는 기존 축 replacement 시 아래 형식을 checklist/report에 같이 남긴다.

1. `baseline cohort`: 예) `main-only + normal_only + post_fallback_deprecation`
2. `candidate live cohort`: 예) `gatekeeper_fast_reuse post-change`, `soft_stop qualifying cohort`
3. `observe-only cohort`: 예) `wait6579_ev_cohort`, `hard_stop_whipsaw_aux`, `same_symbol cooldown shadow`
4. `excluded cohort`: 예) `fallback`, `partial/full mixed`, `initial/pyramid mixed`, `NULL or incomplete profit`
5. `rollback trigger owner`: 진입/보유/청산 중 어느 축이 이 cohort를 끄는지
6. `cross-contamination check`: 다른 canary가 유입 모집단을 바꿨는지 여부

판정 메모에서 위 6개 중 하나라도 비어 있으면 `cohort 미정리`로 보고 live 승인/유지 판정을 잠그지 않는다.

### 3.3 현행 Decision Cohort Inventory

아래 inventory는 `Plan Rebase`와 현행 active checklist에서 실제 판정/관찰에 쓰이면서, 최소 하나 이상에 해당하는 코호트만 잠근다.

1. `src/` 코드/리포트 빌더/스냅샷 경로가 남아 있다.
2. active checklist의 live 승인/관찰/rollback 판정에 직접 들어간다.
3. 현재 기준 문서(`Plan Rebase`, performance report, active workorder)에서 현행 영향도가 있다.

과거 문서에만 남고 현재 `src/` 흔적도 없고 active 판정에도 쓰이지 않는 historical-only cohort는 이 inventory에 올리지 않는다. 아직 상태가 비어 있는 코호트가 있으면 `전체 코호트 분류 완료`로 보지 않는다.

| cohort | cohort 상태 | 주 용도 | 유지 종료 시점/달성요건 | 기본 문서 |
| --- | --- | --- | --- | --- |
| `main-only + normal_only + post_fallback_deprecation` | `baseline-decision` | live 기준선 손익/퍼널/체결 품질 비교 | Plan Rebase 종료 전까지 유지. 새 기준선이 문서 승인되어 replacement되고 동일 메트릭/제외규칙이 승계될 때만 교체 가능 | `Plan Rebase`, 날짜별 checklist |
| `wait6579_ev_cohort` | `observe-only` | BUY recovery 후보 EV/blocked_ai_score/제출 전환 관찰 | `buy_recovery_canary` 축이 remove 또는 baseline 승격으로 닫히고, `recovery_check -> promoted -> submitted` 설명력이 다른 live/report 축으로 완전히 대체될 때 제거 가능 | `2026-04-21~22 checklist` |
| `buy_recovery_canary applied cohort` | `active-canary-decision` | `WAIT65~79` live canary 효과/rollback 판정 | 승격 조건 또는 OFF/parking 판정이 닫히는 시점까지 유지. `submitted/full/partial/COMPLETED + valid profit_rate` 기준으로 승격 또는 종료가 확정되면 제거 | `2026-04-21~23 checklist` |
| `wait6579_probe_canary_applied` | `active-canary-decision` | 소량 probe 적용 표본 분리 | probe가 종료되거나 본 canary에 통합되어 별도 applied tag가 사라질 때 제거 | `wait6579_ev_cohort`, `2026-04-21 checklist` |
| `post-restart cohort` | `active-canary-decision` | replacement 이후 same-day 제출 회복 관찰 | replacement 당일 판정이 닫히고 후속 축이 새 `post-change` cohort로 넘어가면 종료. 익일 이후 지속 baseline으로 쓰지 않음 | `2026-04-24 checklist` |
| `gatekeeper_fast_reuse post-change` | `active-canary-decision` | signature/window 형상 변경 이후 live 비교 | PREOPEN 승인/보류와 post-change 유지/롤백 판정이 닫힐 때까지 유지. baseline 승격 또는 OFF 확정 시 제거/재분류 | `2026-04-24`, `2026-04-27 checklist` |
| `soft_stop qualifying cohort` | `provisional-stage-disjoint` | 보유/청산 live 예외 canary 후보 | `soft_stop_rebound_split` 승인 또는 보류+재시각이 닫히고, qualifying rule이 live 조작점으로 승격되거나 폐기될 때 종료 | `2026-04-27 checklist` |
| `hard_stop_whipsaw_aux` | `observe-only` | severe-loss guard 보조 관찰 | 하드스탑을 보조 관찰로만 둔다는 원칙이 유지되는 동안 유지. `MISSED_UPSIDE/GOOD_EXIT/NEUTRAL`과 반등 지표가 독립 판단가치를 잃거나 hard stop 완화 의제가 공식 폐기되면 제거 | `Plan Rebase`, `2026-04-27 checklist` |
| `same_symbol_reentry` | `observe-only` | 동일종목 재진입 손실/guard 필요성 관찰 | `same_symbol_reentry_loss_count`가 독립 guard 후보성을 잃거나, soft stop/position context 축에 완전히 흡수되어 별도 재진입 cohort가 필요 없을 때 제거 | `holding_exit_observation`, `2026-04-27 checklist` |
| `trailing_continuation` | `observe-only` | upside capture 개선 후보 관찰 | `MISSED_UPSIDE rate >= 60%`, `GOOD_EXIT rate <= 30%`로 2순위 live 후보 요건을 충족해 canary로 승격되거나, 반대로 upside 개선 후보성이 약해져 후순위 폐기가 확정되면 제거/재분류 | `holding_exit_observation`, `2026-04-27 checklist` |
| `initial-only` | `observe-only` | 신규 진입만의 체결/손익/청산 품질 분리 | `1주 cap` 유지/해제 판정이 닫히고 initial/pyramid가 더 이상 다른 EV를 보이지 않아 분리 해석 가치가 사라질 때만 제거 | `2026-04-24`, `2026-04-27 checklist` |
| `pyramid-activated` | `observe-only` | 추가매수 활성 표본 분리 | `1주 cap` 및 추가매수 정책 재판정이 닫히고 별도 손익/청산 특성이 없다고 확인될 때만 제거 | `2026-04-24`, `2026-04-27 checklist` |
| `full_fill` | `observe-only` | 체결 품질 우수 표본 분리 | `partial_fill`과 EV/청산 품질 차이가 더 이상 의사결정 의미를 잃지 않는 한 유지. full/partial 합산 허용 정책으로 바뀌기 전에는 제거 금지 | `Plan Rebase`, performance/report/checklist |
| `partial_fill` | `observe-only` | partial 전용 손익/재베이스/soft-stop 악화 관찰 | partial 악화 여부가 더 이상 독립 리스크가 아니라고 확인되기 전까지 유지. full/partial 합산 정책 변경 전에는 제거 금지 | `Plan Rebase`, performance/report/checklist |

inventory 운영 규칙은 아래로 고정한다.

1. 위 표에 없는 cohort가 신규 문서/코드/리포트에 등장하면, 같은 change set에서 이 표에 추가하고 상태를 먼저 잠근다.
2. 표에 있는 cohort라도 성격이 바뀌면 `상태 변경 + why + 허용 메트릭 + 금지 집계`를 같은 턴에 같이 갱신한다.
3. `baseline-decision`, `active-canary-decision`, `provisional-stage-disjoint`는 빈 이름으로 운영하지 않는다. 임시 표현(`post-change`, `new cohort`)만 적고 상태를 안 잠그는 것은 무효다.
4. `historical-only` 문서에만 남고 `src/`/active checklist/현재 기준 리포트 어디에도 연결되지 않는 cohort는 inventory에서 제거한다. 필요하면 archive나 과거 report에서만 유지한다.
5. `observe-only` cohort는 `유지 종료 시점/달성요건` 없이 무기한 두지 않는다. 제거, 승격, 상위 축 흡수 중 하나의 종료 조건이 반드시 있어야 한다.

---

## 4. 판정표

아래 판정은 `src/` 기준 실제 런타임/리포트 경로를 기준으로 잠근다.

### 4.0 `src/engine + constants` 전수 inventory

| 축 | 분류 | live 영향도 | 비고 |
| --- | --- | --- | --- |
| `dual_persona` | `observe-only` | `guarded-off` | gatekeeper/overnight dual-persona shadow |
| `watching_shared_prompt_shadow` | `observe-only` | `guarded-off` | WATCHING shared prompt 비교 shadow |
| `watching_prompt_75_shadow` | `remove` | `guarded-off` | 제거 완료, historical 판정만 유지 |
| `hard_time_stop_shadow` | `observe-only` | `none` | 공통 hard time stop 관찰 |
| `ai_holding_shadow_band` | `observe-only` | `none` | HOLDING review/skip 경계 관찰 |
| `same_symbol_soft_stop_cooldown_shadow` | `observe-only` | `none` | same-symbol cooldown 가설 관찰 |
| `partial_only_timeout_shadow` | `observe-only` | `none` | partial-only timeout 가설 관찰 |
| `split_entry_rebase_integrity_shadow` | `observe-only` | `none` | split-entry/rebase 정합성 관찰 |
| `split_entry_immediate_recheck_shadow` | `observe-only` | `none` | partial 후 immediate recheck 관찰 |
| `strength_shadow_feedback` | `observe-only` | `none` | dynamic strength 후보 장후 평가 |
| `buy_recovery_canary` | `active-canary` | `guarded-off` | `WAIT65~79` BUY 회복축 |
| `wait6579_probe_canary` | `active-canary` | `limited-live` | 소량 실전 probe |
| `fallback_qty_canary` | `baseline-promote` | `baseline-live` | current runtime/log는 `fallback_qty_guard` |
| `latency_guard_canary` | `active-canary` | `guarded-off` | broad fallback override legacy 축 |
| `spread_relief_canary` | `active-canary` | `guarded-off` | parking 상태 |
| `ws_jitter_relief_canary` | `active-canary` | `guarded-off` | same-day 종료된 replacement 축 |
| `other_danger_relief_canary` | `active-canary` | `limited-live` | residual 완화 실험축 |
| `dynamic_strength_canary` | `baseline-promote` | `baseline-live` | current runtime/log는 `dynamic_strength_relief` |
| `partial_fill_ratio_canary` | `baseline-promote` | `baseline-live` | current config는 `partial_fill_ratio_guard` |

### 4.1 `dual_persona`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 현재 실주문 경로에서는 꺼져 있지만, historical `dual_persona_shadow_samples/conflict/veto/extra_ms`는 향후 AI 엔진 A/B 재개 여부를 판단하는 데 직접 쓸 수 있다.
  - 상향 조건: `entry_filter_quality` 이후 AI 라우팅 A/B를 다시 열거나, Gemini 대비 보수 veto/conflict를 본격 비교할 때
  - 하향 조건: AI 엔진 A/B 재개를 공식 폐기하고 historical 비교도 더 이상 쓰지 않을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
  - historical 비교 지표는 일부 대체가 어렵지만, 현재 daily tuning의 주병목 판정에는 직접 입력이 아니다.
- 운영 부하/지연 비용: `High`
  - shadow 호출이 살아 있으면 추가 API/지연 비용이 크다.
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `performance_tuning`과 대시보드에 `dual_persona_*` 메트릭과 breakdown이 이미 존재한다.
  2. 현재 `OPENAI_DUAL_PERSONA_ENABLED=False`이며 runtime guard로 신규 shadow 호출은 차단된 상태다.
  3. 현재 Plan Rebase 주병목/실주문 판정에는 직접 쓰지 않는다.
- 다음 액션:
  1. runtime submit 경로는 계속 OFF로 둔다.
  2. historical metrics/report/UI는 당장 삭제하지 않는다.
  3. AI A/B 재개가 공식 폐기되면 그때 `runtime engine wiring + report cards + tests`를 한 세트로 `remove` 후보 재판정한다.

### 4.2 `watching_prompt_75_shadow`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: `WAIT 75~79` shadow는 이미 `WAIT 65~79 buy_recovery_canary`, `wait6579_ev_cohort`, `buy_recovery prompt` 계열로 대체됐다.
  - 상향 조건: 별도 `75~79` 경계구간만 독립적으로 재검증해야 하는 새로운 질문이 생길 때
  - 하향 조건: 현재처럼 `65~79` 실전 canary와 cohort report가 운영 기준을 완전히 대체할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Low`
- 근거:
  1. 상수 주석도 이미 `remote 전용` legacy shadow 성격으로 남아 있다.
  2. rare score band라 표본 희소성이 강하고, 현재는 `wait6579_ev_cohort`와 `buy_recovery_canary`가 더 직접적인 판단축이다.
  3. runtime guard로 기본 운영에서 더 이상 타지 않는다.
- 다음 액션:
  1. `src/` runtime hook, 상수, 전용 report/check script, 전용 테스트를 같은 change set에서 제거 완료
  2. 현재 문서에서는 historical 제거 판정만 유지하고, `75 shadow`를 현행 축/재개 후보로 다루지 않는다
  3. 이후 재개가 필요하면 기존 축을 복구하지 않고 새 canary로 재정의한 뒤 본 판정표에 새 항목으로 추가한다

### 4.3 `hard_time_stop_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 실주문 개입 없이 `시간기반 강제정리` 가설의 false positive와 ghost event를 관찰하는 용도로는 아직 가치가 있다.
  - 상향 조건: `soft_stop_rebound_split`과 별도로 `time-based exit` 후보를 다시 검토할 때
  - 하향 조건: `post_sell`/`trade_review`만으로 동일 판단이 충분하고, ghost event 점검도 더 이상 필요 없을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
  - 청산 후 결과는 대체되지만, 장중 `would-have-fired` 관측은 완전 대체가 어렵다.
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 실주문에 연결되지 않고 `hard_time_stop_shadow` 이벤트만 남긴다.
  2. trade review/performance tuning UI에서 이미 관찰 지표로 쓰인다.
  3. 과거 ghost event 점검 이력이 있어 완전 삭제 전 관측 가치가 남아 있다.
- 다음 액션:
  1. 유지 범위를 `trade_review + performance_tuning 관찰`로만 명시
  2. 실주문 승격 후보로는 두지 않는다
  3. 동일 정보가 `post_sell/trade_review`로 충분히 대체되는 시점이 오면 `remove` 재판정한다

### 4.3A `watching_shared_prompt_shadow`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: WATCHING 단계에서 shared prompt와 split prompt 차이를 다시 봐야 할 때 사용할 비교 shadow다.
  - 상향 조건: AI A/B 또는 prompt split 비교를 재개할 때
  - 하향 조건: shared 경로 비교를 다시 보지 않기로 확정할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `High`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. OpenAI dual-persona engine submit 함수와 stage 기록 경로가 남아 있다.
  2. 현재는 `OPENAI_DUAL_PERSONA_ENABLED=False` 가드 아래에서 실런타임 제출이 막혀 있다.
- 다음 액션:
  1. `dual_persona`와 같이 OFF 유지
  2. prompt split 비교 의제가 사라지면 `remove` 재판정

### 4.4 `ai_holding_shadow_band`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: HOLDING AI fast reuse에서 `skip/review` 경계가 얼마나 자주 흔들리는지 보는 관측 신호로는 아직 유효하다.
  - 상향 조건: `holding reuse blocker`나 `holding AI review 지연`을 직접 튜닝 후보로 다시 올릴 때
  - 하향 조건: `holding_reuse_blockers`, `holding_sig_deltas`, `holding_reviews/skips`만으로 충분히 대체될 때
- EV 판정 기여도: `Medium`
  - 직접 손익은 아니지만 holding review 품질과 재평가 빈도를 해석하는 데 기여한다.
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `ai_holding_reuse_bypass`와 짝을 이루는 관측축으로 남아 있다.
  2. holding fast reuse를 다시 건드릴 때 band 관측이 있으면 원인귀속이 더 쉬워진다.
  3. 현재는 live 판단이 아니라 observability 성격이다.
- 다음 액션:
  1. live 판단 비사용을 문서 기준으로 고정
  2. 유지 리포트 범위는 `trade_review`와 raw holding pipeline 해석으로 제한
  3. 향후 `holding reuse` 축을 재개하지 않으면 `hard_time_stop_shadow`와 묶어 `observe-only 축 축소`를 재판정한다

### 4.4A `same_symbol_soft_stop_cooldown_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: soft stop 직후 동일 종목 재진입 cooldown이 필요한지 확인하는 관찰축이다.
  - 상향 조건: soft stop 휩쏘와 same-symbol 재진입 손실을 같이 튜닝할 때
  - 하향 조건: same-symbol cooldown live 후보를 접을 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `shadow_only=True`로 entry pipeline에만 기록하고 실주문 차단에는 연결하지 않는다.
  2. 보유/청산 cooldown 가설과 직접 연결된다.
- 다음 액션:
  1. 보유/청산 관찰축으로만 유지
  2. 재개 가능성이 사라지면 `remove` 재판정

### 4.4B `partial_only_timeout_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: partial fill만 남은 장기 체류를 timeout 후보로 봐야 하는지 확인하는 관찰축이다.
  - 상향 조건: partial-only 장기보유가 손익 훼손으로 반복 확인될 때
  - 하향 조건: `partial_fill_ratio`와 post-sell 평가만으로 충분할 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `shadow_only=True`로 holding pipeline에만 기록한다.
  2. 체결품질 가드와는 다른 `체결 후 timeout` 축이다.
- 다음 액션:
  1. partial fill 품질과 timeout 품질을 분리해 유지
  2. 표본 희소/대체 가능 시 `remove` 재판정

### 4.4C `split_entry_rebase_integrity_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: split-entry/rebase 경로 정합성 이상을 탐지하는 integrity shadow다.
  - 상향 조건: split-entry 재개나 partial fill 후 rebase 오류가 의심될 때
  - 하향 조건: split-entry 재개 계획이 없어질 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `requested_qty/cum_filled_qty/rebase_count`를 holding pipeline에 별도 기록한다.
  2. 현재는 무결성 감시지 실주문 완화가 아니다.
- 다음 액션:
  1. split-entry 재개 전까지 observability로 유지
  2. split-entry 폐기 시 `remove` 후보 재판정

### 4.4D `split_entry_immediate_recheck_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: partial 후 즉시 recheck가 필요했는지 보는 후속 shadow다.
  - 상향 조건: partial 후 확장/재베이스 타이밍 문제가 실제 손익 훼손으로 연결될 때
  - 하향 조건: split-entry 자체를 더 이상 보지 않을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `split_entry_rebase_integrity_shadow`와 짝을 이루는 후속 관찰축이다.
  2. 현재는 recheck 필요성만 기록한다.
- 다음 액션:
  1. integrity shadow와 묶어 유지/제거 판정

### 4.5 `dynamic_strength_canary` / current runtime `dynamic_strength_relief`

- 판정: `baseline-promote`
- live 영향도: `baseline-live`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 이미 baseline live 경로로 쓰이고 있어 실험 표본보다 운영 경로 설명 가치가 더 크다.
  - 상향 조건: 이후 rollback 또는 threshold 재조정이 반복되면 baseline guard로서의 모니터링 가치가 올라간다
  - 하향 조건: 더 이상 별도 guard로 보지 않고 기본 threshold 구조에 완전히 흡수될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `2026-04-24` 기준 문서에서 이미 `baseline live 107건`으로 해석했다.
  2. 현재는 `canary` 이름과 달리 baseline 경로처럼 설명된다.
- 다음 액션:
  1. 현재 runtime/log는 `dynamic_strength_relief`, 상수/env는 `SCALP_DYNAMIC_STRENGTH_RELIEF_*` 기준으로 유지한다
  2. historical `dynamic_strength_canary` 명칭은 inventory/과거 추적 문서에서만 병기한다
  3. rollback guard는 유지하되 문서/코드 용어에서는 `baseline guard` 해석으로 통일한다

### 4.6 `other_danger_relief_canary`

- 판정: `active-canary`
- live 영향도: `limited-live`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 현재 flag는 남아 있지만 same-day 효과는 약했고, baseline 승격 근거도 닫히지 않았다.
  - 상향 조건: `submitted`, `quote_fresh_latency_pass_rate`, `canary_applied`가 실제 회복을 만들 때
  - 하향 조건: 반복 관찰에도 효과가 없고 `gatekeeper_fast_reuse` 등 다음 축으로 완전히 대체될 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 문서 기준 `same-day 효과 미약`이며 장중 잠금 근거가 남아 있다.
  2. 상수는 `True`지만 baseline 승격으로 해석되지는 않았다.
  3. 현재는 운영 기본축보다 `실험 상태가 덜 닫힌 축`에 가깝다.
- 다음 액션:
  1. 성공 기준은 `submitted 회복`, `quote_fresh_latency_pass_rate 개선`, `fallback_regression=0`으로 고정
  2. 해당 기준을 충족하지 못하면 `OFF 또는 parking`으로 닫는다
  3. 충족 시에만 `baseline-promote` 재판정한다

### 4.7 `partial_fill_ratio_canary` / current config `partial_fill_ratio_guard`

- 판정: `baseline-promote`
- live 영향도: `baseline-live`
- 튜닝 모니터링 가치: `High`
  - 이유: full/partial 체결 품질은 Plan Rebase의 핵심 guard이고, 이 축은 실험이라기보다 운영 품질 가드로 굳어졌다.
  - 상향 조건: `partial_fill_ratio` rollback guard를 실제 운영 판정에서 계속 쓰는 동안
  - 하향 조건: 최소 체결비율이 기본 주문 정책에 완전히 흡수되어 독립 guard로 안 볼 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. 상수 기본값이 `True`이며 immediate fix 이후 운영 품질 가드 성격으로 남아 있다.
  2. Plan Rebase guard 표에도 `partial_fill_ratio`는 핵심 판정 축이다.
  3. `full fill`/`partial fill` 분리는 손익보다 우선 보는 기본 기준이다.
- 다음 액션:
  1. 상수/env는 `SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED` 기준으로 정리했고, 문서 분류명만 historical `partial_fill_ratio_canary`로 유지한다
  2. 문서에서 `실험 축`보다 `운영 품질 가드`로 해석을 통일
  3. 예외 override(`PRESET_TP`, `strong_absolute_override`)는 유지한다

### 4.8 `buy_recovery_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `High`
  - 이유: `WAIT 65~79` 과밀, `recovery_check/promoted/submitted`, `blocked_ai_score_share`는 BUY drought와 미진입 기회비용을 직접 해석하는 핵심 축이다.
  - 상향 조건: `main-only` 1축 live로 재승인되거나 `WAIT65~79` 과밀이 다시 1순위 병목으로 잠길 때
  - 하향 조건: `entry_filter_quality` 또는 다른 상위 필터 축이 동일 문제를 더 직접적으로 설명하고, `wait6579_ev_cohort`만으로 재판정이 충분해질 때
- EV 판정 기여도: `High`
- 대체 가능성: `Medium`
  - `wait6579_ev_cohort`와 `performance_tuning`이 많은 부분을 대체하지만, 실제 `recovery_check -> promoted -> submitted` 실전 변환은 코드축이 있어야 닫힌다.
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `Plan Rebase`는 여전히 `buy_recovery_canary`를 메인 진입 canary 축으로 명시한다.
  2. 코드에는 `AI_MAIN_BUY_RECOVERY_CANARY_*`, `watching_buy_recovery_canary`, `wait6579_probe_canary` 경로가 살아 있다.
  3. 다만 현재 기본 설정값은 `AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=False`라 항상 live-on 상태로 볼 수는 없다.
- 다음 액션:
  1. 재승인 시에는 `main live 여부`, `WAIT65~79 cohort 표본`, `blocked_ai_score_share`, `submitted/full/partial` 기준을 같은 change set의 판정 메모와 함께 잠근다.
  2. 장기간 OFF로 유지되고 `wait6579_ev_cohort`만으로도 충분해지면 `remove`가 아니라 먼저 `parking active-canary` 재판정 후 정리 범위를 닫는다.
  3. `watching_prompt_75_shadow`와 달리 이 축은 historical legacy가 아니라 재개 가능성이 높은 실전 축으로 유지한다.

### 4.8A `wait6579_probe_canary`

- 판정: `active-canary`
- live 영향도: `limited-live`
- 튜닝 모니터링 가치: `High`
  - 이유: BUY recovery가 실제 주문 품질로 이어지는지 소량 실전 표본으로 닫는 하위 probe 축이다.
  - 상향 조건: `buy_recovery_canary`가 다시 live 승인되고 promoted 표본이 누적될 때
  - 하향 조건: recovery 축 자체가 장기간 OFF거나 probe 없이도 판정이 충분할 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. 기본값이 `AI_WAIT6579_PROBE_CANARY_ENABLED=True`이며 armed 상태에서 실제 주문수량을 축소한다.
  2. `wait6579_ev_cohort`가 `wait6579_probe_canary_applied`를 직접 집계한다.
- 다음 액션:
  1. `buy_recovery_canary`의 하위 probe 축으로 묶어 관리
  2. 장기간 promoted 표본이 없으면 parking 또는 제거 재판정

### 4.8B `fallback_qty_canary` / current runtime `fallback_qty_guard`

- 판정: `baseline-promote`
- live 영향도: `baseline-live`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 명칭은 canary지만 현재는 fallback entry 수량 축소가 기본 런타임 동작처럼 쓰인다.
  - 상향 조건: fallback 진입 품질 guard로 계속 운영 판정에 쓰일 때
  - 하향 조건: fallback entry 자체를 더 이상 실전에서 쓰지 않거나 multiplier를 기본 정책으로 흡수할 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. 전용 `enabled` flag 없이 `entry_mode == fallback`에서 multiplier가 바로 적용된다.
  2. 주문 stage는 `fallback_qty_guard_applied`로 정리했지만, 상수/문서 명칭은 아직 canary 표현이 남아 있다.
- 다음 액션:
  1. 현재는 runtime/log 명칭만 `guard`로 정리됐고, inventory 분류명은 historical 추적용으로 유지한다
  2. fallback 축 자체를 접으면 함께 정리한다

### 4.9 `spread_relief_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `spread_only_required` 병목을 직접 겨냥한 첫 downstream relief 축이라 same-day replacement 흐름과 실패 이유를 복기할 때는 가치가 있다.
  - 상향 조건: `quote_fresh` 하위원인에서 다시 `spread_only_required`가 단일 우세 원인으로 잠기고, `ws_jitter/other_danger`보다 우선순위가 높아질 때
  - 하향 조건: residual 분해에서 `spread`가 후순위로 밀리고 `other_danger/ws_jitter`가 주병목으로 고정될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
  - `performance_tuning`의 `spread_relief_canary_detail`, raw `latency_canary_reason`, `quote_fresh` residual 분해로 상당 부분 대체 가능하다.
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 코드에는 `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED`와 `sniper_entry_latency.py`의 `spread_relief` 경로가 남아 있다.
  2. `2026-04-24` same-day 판정에서 `spread_only_required`가 컸지만, 이후 replacement 흐름은 `ws_jitter-only relief -> other_danger residual`로 이동했다.
  3. 현재 상수 주석도 `replacement 완료: spread-only relief는 parking 유지`로 잠겨 있다.
- 다음 액션:
  1. 현재 상태는 `parking된 active-canary`로 문서 기준을 고정하고, baseline/observe-only로 오해하지 않게 한다.
  2. 재개 시에는 `spread_only_required` 비중, `submitted 회복`, `quote_fresh_latency_pass_rate`, `fallback_regression=0`를 같은 판정 묶음으로 본다.
  3. 장기적으로 `quote_fresh` 하위원인에서 `spread`가 재부상하지 않으면 `remove` 또는 `historical note only`로 낮출지 재판정한다.

### 4.9A `ws_jitter_relief_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `2026-04-24` same-day replacement의 실제 1축이었고 why-failed 기록을 남기는 데 필요하다.
  - 상향 조건: `ws_jitter_only_required`가 다시 우세 원인으로 올라올 때
  - 하향 조건: residual 분해상 `ws_jitter`가 후순위로 밀릴 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 상수와 runtime branch는 남아 있지만 현재 `False`로 parking 상태다.
  2. same-day에 활성화 표본 0으로 종료된 이력이 있다.
- 다음 액션:
  1. parking 상태를 문서에 유지
  2. 재개는 residual 근거가 다시 나올 때만 허용

### 4.9B `latency_guard_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: broad `REJECT_DANGER -> fallback override` 경로라 현재 원인귀속 원칙과 잘 맞지 않는다.
  - 상향 조건: 세부 relief 축이 모두 실패하고 broad override를 다시 비교해야 할 때
  - 하향 조건: `spread/ws_jitter/other_danger` 세부축 체계가 굳을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Low`
- 근거:
  1. 기본값이 `False`이고 broad fallback canary 성격이다.
  2. same-day 운영은 세부 relief 축 분해 쪽으로 이동했다.
- 다음 액션:
  1. 장기간 재개 근거가 없으면 `remove` 후보로 낮추는 재판정 필요
  2. 유지하더라도 broad legacy 축으로 취급

### 4.9C `strength_shadow_feedback`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: dynamic strength 경계 표본을 장후에 후행평가하는 전용 shadow 피드백이다.
  - 상향 조건: `dynamic_strength_relief` 경계값을 재튜닝하거나 운영 해석을 다시 조정할 때
  - 하향 조건: dynamic strength가 완전 baseline이 되고 경계 표본을 더 이상 안 볼 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `shadow_candidate_recorded`와 별도 JSONL 평가 경로를 유지한다.
  2. 실주문 개입 없이 post-close evaluation만 수행한다.
- 다음 액션:
  1. `dynamic_strength_relief` 운영 해석 변경 시 유지 여부를 함께 재판정
  2. 경계 표본 가치가 낮아지면 `remove` 후보로 내린다

---

## 부록: 최소 후속 코드세트 연결

이 문서 기준의 다음 코드세트 우선순위는 아래로 고정한다.

1. `remove`
   - `watching_prompt_75_shadow`
2. `observe-only 유지 문서화`
   - `dual_persona`
   - `watching_shared_prompt_shadow`
   - `hard_time_stop_shadow`
   - `ai_holding_shadow_band`
   - `same_symbol_soft_stop_cooldown_shadow`
   - `partial_only_timeout_shadow`
   - `split_entry_rebase_integrity_shadow`
   - `split_entry_immediate_recheck_shadow`
   - `strength_shadow_feedback`
3. `baseline-promote historical/current 표기 유지`
   - `dynamic_strength_canary` (`dynamic_strength_relief`)
   - `partial_fill_ratio_canary` (`partial_fill_ratio_guard`)
   - `fallback_qty_canary` (`fallback_qty_guard`)
4. `active-canary 운영/parking 판정`
   - `buy_recovery_canary`
   - `wait6579_probe_canary`
   - `latency_guard_canary`
   - `spread_relief_canary`
   - `ws_jitter_relief_canary`
   - `other_danger_relief_canary`

이 순서를 지켜 `remove`, `observe-only`, `baseline-promote`, `active-canary`를 섞어 동시에 건드리지 않는다.
