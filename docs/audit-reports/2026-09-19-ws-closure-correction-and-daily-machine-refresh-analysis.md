# WS 종결 정정·Daily machine refresh 결과 분석

작성일: 2026-09-19 KST. 이번 점검은 기존 코드와 산출물의 bounded read, 문서 종결 판정 정정, 재생성 임시 산출물 정리까지다. `daily_threshold_cycle_report --refresh-machine-evaluation-only`를 다시 실행하거나 정책·provider·주문·봇을 변경하지 않았다.

## 결론

WS scanner 선택 경제성은 완료가 아니다. 현재 비용 후 EV·일별 순익이 null인 직접 원인은 표본 수가 아니라 **candidate로 새로 들어올 capacity-pruned 후보가 compact AI, entry recipe, 요청 수량, guard와 terminal을 자연 생산하지 않는 producer reachability 결손**이다. 기존 구현은 양쪽 입력이 이미 있을 때의 비교, 결손 시 fail-closed policy, PREOPEN/후행 hash 전달을 검증했지만 이 입력을 만드는 경로를 검증하지 못했다. 이전 WS0–WS5 완료 표시는 철회하고 기존 `CodeImprovementWorkorderReview0918`를 유일한 OPEN 코드 owner로 유지한다.

## 재검토 근거

- `scanner_lookup_attention_resource.execution_inputs()`는 sealed compact source projection에서 exact `(source_date, scanner_promotion_id, stock_code)` 자연 판정과 owner replay만 읽는다.
- `selection_execution_book()`은 baseline 또는 candidate에 필요한 어느 한 종목이라도 입력이 없으면 `original_unselected_entry_recipe_quantity_guard_missing`으로 비교를 중단한다.
- live scanner는 capacity prune을 compact/entry 실행 전 수행한다. promoted 후보만 이후 `scanner_promotion_id`와 runtime target을 갖고 compact/entry 경로로 넘어간다. prune event에 ID만 추가해도 AI 판정·수량·guard·terminal은 생기지 않는다.
- source 2026-09-17 결과는 complete partition 결손 5건, unselected 실행 입력 결손 1건, execution pair 0건이다. primary baseline/candidate EV, paired EV delta, net PnL과 일별 순익 차이는 모두 null이다.
- snapshot proxy는 complete partition 15건, 8일, paired generation 6건이며 incoming snapshot EV는 -1.155944%다. execution EV가 아니므로 결손을 대신할 수 없다.
- 실제 완료 관측 5건의 전체 notional EV는 +0.24074898%, candidate-control 차이는 +0.02975044%p지만 candidate 1건 대 control 4건의 비인과 관측치이고 broker-reconciled cost가 아니다. promotion 근거가 아니다.

### 열린 closure

prospective source 계약은 장중 주문과 추가 provider 호출 없이 탈락 후보의 source-only compact 판정, entry recipe, 요청 수량, guard, terminal 또는 동등하게 검증된 실행 모델 입력을 보존해야 한다. exact `scanner_promotion_id`로 양측 selection에 join되고 최소 한 changed-selection 자연 generation이 `execution_inputs` 양측에 도달한 뒤에야 경제 비교 단계로 넘어간다. 역사 결손은 합성하지 않는다.

## `daily_threshold_cycle_report --refresh-machine-evaluation-only`

이 명령은 튜너가 아니다. 기존 `threshold_cycle_<date>.json`과 exact-date `microstructure_reaction_context_<date>.json`을 읽고 다음 두 diagnostic handoff만 원자 교체한다.

1. `calibration_source_bundle.source_metrics.microstructure_reaction_context`
2. `scanner_lookup_attention_selection`

기존 파일 stat을 다시 확인하는 CAS guard가 있으며 replay, calibration candidate 재계산, provider 호출, policy write, EV 재계산과 runtime apply는 하지 않는다. CLI도 반환 summary를 출력하지 않는다. 따라서 이 명령의 성공은 최신 diagnostic link와 scanner policy hash 전달 성공을 뜻하며 EV 개선 탐색이나 정책 승격 성공을 뜻하지 않는다.

현재 daily report의 refresh 시각은 `2026-09-19T09:19:28.064360`이다. scanner handoff는 source section `02afcf30577e8fa290e00fe9d62e1e624adcb8ce2217dbfaec418a010ece49d2`, policy `5cb82631ef6674c80a5154737ccdca70b6d6ac75fad0194d2cc883e5ef45bf51`, `source_gap`, `allowed_runtime_apply=false`를 전달한다.

## Daily 전체 경제성 현황

17개 family 중 검증된 개선은 0건이고 paired comparable도 0건이다.

| 상태 | 수 | 해석 |
| --- | ---: | --- |
| `incumbent_preserved_identical_policy` | 9 | 서로 다른 정책 비교가 아니다. 시간이 지나도 자동으로 비교가 되지 않는다. |
| `source_gap` | 5 | 필요한 원천/terminal/cost 계약 수리가 먼저다. 과거 결손은 기다려도 복구되지 않는다. |
| `insufficient_sample` | 1 | `position_sizing_dynamic_formula`; 동일 계약의 유효 실제 표본이 자연 축적되면 해소 가능하다. |
| `pending_maturity` | 1 | `entry_split_order_plan`; 이미 제출된 주문의 terminal 성숙으로 해소될 수 있다. |
| `skipped_no_applicable_fill` | 1 | `scale_in_split_order_plan`; 실제 적용 가능한 fill이 생겨야 한다. 단순 시간 경과만으로는 부족하다. |

Daily의 `actual_net_profit_improvement`는 null이고 `runtime_effect=false`다. 동일 정책 9건을 개선 비교로 세거나 source gap/no-fill을 순익 0으로 바꾸면 안 된다.

## Microstructure handoff의 구조 결손

machine source에는 verified capture 3,342건이 있으나 전부 `full_round_trip_cost_missing`으로 경제 평가에서 제외됐고 1,166건은 invalid capture에도 해당한다. cost-adjusted outcome과 case는 0건이며 actual completed EV, actual net profit, causal model delta EV가 모두 null이다.

KRX regular는 관측 micro-window가 일부 존재하지만 BLOCK 526건, ENTER_NOW 5건, RECHECK 270건이 source gap이다. KRX/NXT aftermarket 989건과 PREMARKET 501건은 모두 micro-window source gap이다. 이미 지나간 window와 비용 receipt는 시간 경과로 생성되지 않는다. producer/lineage를 고친 이후의 prospective 자료만 유효해질 수 있다.

## 정리와 보존

active 관련 프로세스가 없음을 확인한 뒤 WS 재생성 임시 디렉터리의 중간 로그·중복 덤프 34개를 삭제해 39,089,649 bytes를 회수했다. deployment, 보호 입력 manifest, selected-release 검증, cron route, strict, handoff, docs parser receipt 8개만 남겼다. current report/policy, selected release, rollback·감사 evidence와 현재 source는 삭제하지 않았다.

## 코드 재리뷰와 검증

현행 compact 통합이 standalone entry replay CLI와 `--require-policy-publication`을 phased `ai_action_outcome_calibration`으로 대체했지만 wrapper 회귀 테스트 일부가 옛 명령을 계속 검사하고 있었다. production code는 바꾸지 않고 테스트를 현재 prepare→evaluate→finalize→handoff 계약과 low-price PREOPEN 선행 consumer에 맞췄다. scanner selection, microstructure handoff와 wrapper 대상 검증은 `177 passed, 1 warning`이다. warning은 `pandas_ta`의 pandas copy-on-write deprecation이며 이번 변경과 무관하다.

## 배포 상태

선택 release는 `compact-economic-optimized-reviewed-20260919-411ec0efd`, commit `411ec0efdf993ec11e36b3fc79b78a5a7a36a6e1`이며 WS evaluator 구현 commit을 포함한다. `actual_pid_consumed=false`이고 bot 재기동·조기 PREOPEN·주문은 없었다. 새 runtime code를 만들지 않았으므로 이번 정정으로 별도 release를 중복 생성하지 않는다. 배포 receipt는 evaluator와 fail-closed consumer 경로의 배포만 증명하며 구조적 경제성 종결을 증명하지 않는다.
