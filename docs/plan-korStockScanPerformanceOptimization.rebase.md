# KORStockScan Plan Rebase 중심 문서

기준일: `2026-05-18 KST`
역할: 현재 튜닝 원칙, 자동화체인 판정 계약, active/open 상태만 고정하는 중심축 문서다.
주의: 이 문서는 자동 파싱용 체크리스트를 소유하지 않는다. 실행 작업항목은 날짜별 `stage2 todo checklist`가 소유한다.

과거 5/4~5/8 수동 실행 맵, 종료된 latency/fallback/shadow 경과, 지나간 owner 판정 메모는 archive와 날짜별 checklist 증적으로 본다. 2026-05-13 이전 원문은 [pre-automation-renewal archive](./archive/plan-korStockScanPerformanceOptimization.rebase.pre-automation-renewal-2026-05-13.md)에 보존했다.

---

## 1. 현재 판정

1. 현재 단계는 손실 억제형 미세조정이 아니라 `기대값/순이익 극대화`를 위한 자동화체인 튜닝 단계다.
2. 중심 루프는 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution`다. 상세 산출물/소비자 계약은 [report-based-automation-traceability](./report-based-automation-traceability.md)를 따른다.
3. 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다. 원격/server 비교값은 기본 의사결정 입력에서 제외한다.
4. 실전 변경은 동일 단계 내 단일 owner canary를 기본으로 한다. stage, 조작점, cohort tag, rollback guard가 분리된 경우에만 stage-disjoint concurrent canary를 허용한다.
5. `2026-05-18` runtime env는 사용자 운영 override를 포함한다. 스캘핑은 `score65_74_recovery_probe`, pre-AI soft gate 재배치, `scalp_entry_adm_runtime_bias_p1`, `holding_exit_matrix_runtime_bias_p1`이 켜져 있고, 스윙은 one-share real canary와 gatekeeper reject cooldown이 env에 명시되어 있다. 이는 자동화체인의 무단 장중 mutation이 아니라 사용자 명시 operator override이며, threshold/provider/broker submit safety guard 우회 권한은 없다.
6. 스캘핑 live AI route는 OpenAI 고정이다. `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, Responses WS transport, numeric compact JSON hot path를 기준으로 보고, Gemini/DeepSeek fallback은 명시 env 또는 OpenAI 초기화 실패/비운영 분석 경로로만 본다.
7. 스윙은 dry-run self-improvement 체인이다. `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` lifecycle을 매 장후 감사하고, approval request는 생성할 수 있지만 별도 approval artifact 없이는 runtime env/live order 전환으로 보지 않는다.
8. sim/probe/counterfactual은 source bundle과 approval request 근거가 될 수 있지만 real execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
9. Sentinel, panic sell/buying, system error detector는 운영/attribution/source-quality 입력이다. report-only 상태에서 threshold, provider, 주문, 자동매도, bot restart를 직접 변경하지 않는다.

## 2. 용어와 판정 계약

| 표현 | 현재 의미 | 판정 |
| --- | --- | --- |
| `auto_bounded_live` | deterministic guard + AI correction guard + same-stage owner rule을 통과한 family만 다음 장전 runtime env에 반영하는 모드 | 현재 threshold apply 허용선 |
| `manifest_only` | 후보와 권고는 만들지만 runtime env를 바꾸지 않는 상태 | approval/guard 미충족 기본값 |
| `report_only` / `observe_only` | runtime 판단을 바꾸지 않고 source bundle, workorder, approval request, operator review에만 쓰는 상태 | live 변경 권한 없음 |
| `operator_runtime_override` | 사용자가 명시적으로 실적용을 지시해 runtime env와 bot restart까지 실행한 상태 | source/provenance와 rollback env를 반드시 남기며 safety guard 우회 금지 |
| `approval_required` | 자동화체인이 후보를 만들었지만 사용자/approval artifact가 필요한 상태 | artifact 없으면 env apply 금지 |
| `safety_veto` | severe loss, 주문 실패, provenance 손상, hard/protect/emergency stop 지연 같은 즉시 차단 조건 | daily-only로도 차단 가능 |
| `source_quality_blocker` | stale/missing/duplicate/provenance 결함 때문에 edge 판정이 막힌 상태 | threshold candidate 아님 |
| `instrumentation_gap` | 필요한 관찰 필드/계약이 없어 판정을 닫을 수 없는 상태 | 먼저 계측 보강 |
| `fallback_scout/main`, `fallback_single`, `latency fallback split-entry` | 과거 예외 진입/분할진입 경로 | 영구 폐기. 재개는 새 workorder와 rollback guard 필요 |
| `shadow` | 실전 주문에는 반영하지 않고 병렬 계산만 하던 검증 방식 | 신규/보완 alpha 축에서는 금지 |

자동화체인이 소비하는 새 관찰지표는 생성 시점에 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 선언해야 한다. 미선언 지표는 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅한다.

| metric role | 용도 | 금지선 |
| --- | --- | --- |
| `primary_ev` | 기대값/순이익 개선 primary 판정 | `win_rate` 또는 단순 합산으로 대체 금지 |
| `diagnostic_win_rate` | 방향성/일관성/꼬리 리스크 보조 진단 | 단독 live/canary 승인 금지 |
| `funnel_count` | 참여율, blocker, coverage, submitted drought 판단 | 손익 edge 근거로 단독 사용 금지 |
| `safety_veto` | severe loss/order/provenance safety 차단 | 기대값 개선 지표로 사용 금지 |
| `source_quality_gate` | stale/missing/duplicate/provenance 품질 gate | threshold 추천값으로 사용 금지 |
| `active_unrealized` | open sim/probe/position context | closed EV와 합산 금지 |
| `execution_quality_real_only` | real broker execution/receipt 품질 | sim/probe로 대체 금지 |
| `sim_probe_ev` | sim/probe equal-weight 기대값 관찰 | 실주문 전환 근거로 단독 사용 금지 |
| `risk_regime_state` | 패닉/시장상태처럼 매매 가능 행동의 범위를 해석하는 상태값 | approval artifact와 rollback guard 없이 주문, 청산, threshold, provider, bot 상태를 직접 변경 금지 |

## 3. 튜닝 원칙

### 3.1 성과 판정과 데이터 기준

1. 최종 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
2. 손익 판단은 `COMPLETED + valid profit_rate`만 사용한다. `NULL`, 미완료, fallback 정규화 값은 손익 기준에서 제외한다.
3. `full fill`과 `partial fill`은 합산하지 않는다. 체결 품질, 후행 청산, 손익은 각각 분리한다.
4. 비교 우선순위는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`이다. `counterfactual` 수치는 직접 실현손익과 합산하지 않는다.
5. 승률은 `diagnostic_win_rate`이며 단독 live/canary 승인 기준이 아니다. 기대값/순이익 판정은 `primary_ev`가 맡는다.
6. 단순 손익 합산은 EV가 아니다. 필드명은 `simple_sum_profit_pct`로 쓰고, EV 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나로 명명한다.
7. daily-only 수치는 incident, safety veto, freshness/source-quality, 장중 운영 trigger에는 쓸 수 있다. edge apply 승인은 rolling/cumulative 또는 `post_apply_version_window`와 함께 확인한다.
8. 원인 귀속이 불명확하면 전략 threshold를 먼저 바꾸지 않고 리포트 정합성, 이벤트 복원, 집계 품질을 먼저 점검한다.

### 3.2 자동화체인 판정 원칙

1. 장중 runtime threshold mutation은 금지한다. 적용 단위는 장후 report/calibration/AI review -> 다음 장전 runtime env -> 장후 attribution이다.
2. 조건 미달은 rollback이 아니라 `adjust_up`, `adjust_down`, `hold`, `hold_sample`, `hold_no_edge`, `freeze` calibration state로 닫는다.
3. rollback/safety revert는 hard/protect/emergency stop 지연, 주문 실패, provenance 손상, same-stage owner 충돌, severe loss guard 초과에만 쓴다.
4. AI correction과 pattern lab automation은 검토자/제안자/작업지시 layer다. deterministic guard 없이 단독 runtime apply 권한이 없다.
5. code-improvement workorder는 자동 repo 수정이 아니라 구현 지시 입력이다. `runtime_effect=false` order는 실운영 변경으로 해석하지 않는다.

### 3.3 Canary, Cohort, Live 변경 원칙

1. 동일 단계 내 live canary는 하나만 허용한다. 같은 family 안의 bounded multi-arm canary는 arm별 provenance, allocation, rollback guard가 닫힌 경우에만 허용한다.
2. canary -> live 전환은 `N_min`, primary EV 개선, rollback guard 무위반, applied/not-applied cohort 비교, cross-contamination 부재, restart/rollback 경로를 같이 닫아야 한다.
3. 신규/보완 alpha 축은 shadow-only로 열지 않는다. transport/schema, report-only decision support, counterfactual enrichment처럼 실주문/실청산 판단을 바꾸지 않는 지원축은 문서에 observe/report-only로 명시된 경우에만 허용한다.
4. sim/probe/combined/counterfactual authority는 real execution 품질, broker order enable, swing real canary 승인에 단독 사용하지 않는다.

### 3.4 문서와 실행 소유권

1. Plan Rebase는 현재 원칙과 active/open 판정만 소유한다.
2. 날짜별 checklist는 실행 작업, 절대 시각, Due/Slot/TimeWindow/Track을 소유한다.
3. report traceability와 threshold README는 자동화 산출물/consumer/apply contract를 소유한다.
4. 완료된 과거 checklist 항목은 증적이지 현재 OPEN owner가 아니다.
5. 문서 변경 후 parser 검증은 AI가 실행한다. Project/Calendar 동기화는 사용자가 표준 명령으로 수동 실행한다.

## 4. 자동화체인 기준

| 단계 | 현재 기준 | live 영향 |
| --- | --- | --- |
| `R0_collect` | pipeline event, threshold compact event, DB completed trade, monitor snapshot을 수집 | 없음 |
| `R1_daily_report` | Sentinel, panic, performance, daily threshold report를 생성 | 없음 |
| `R2_cumulative_report` | rolling/cumulative cohort와 owner baseline을 생성 | 없음 |
| `R3_manifest_only` | 후보 family와 source bundle을 만들되 env 미반영 | 없음 |
| `R4_preopen_apply_candidate` | deterministic/AI/source-quality/same-stage guard 확인 | 직접 변경 전 단계 |
| `R5_bounded_calibrated_apply` | guard 통과 family만 다음 장전 runtime env에 반영 | 있음 |
| `R6_post_apply_attribution` | selected/applied/not-applied cohort, daily EV, approval summary 제출 | 없음 |

자동화체인은 새 관찰축을 무한히 늘리는 방식이 아니라 기존 source bundle을 재사용한다. BUY 쪽은 `buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`; 보유/청산 쪽은 `holding_exit_observation`, `post_sell_feedback`, `trade_review`, `holding_exit_sentinel`; 패닉 쪽은 `panic_sell_defense`, `panic_buying`; decision-support 쪽은 `holding_exit_decision_matrix`, `statistical_action_weight`를 우선 source로 쓴다. `sentinel_followup`은 2026-05-07 단발 follow-up 기록으로 archive/reference이며 현재 자동화체인 source bundle owner가 아니다.

정리되지 못한 report-only/legacy 산출물은 `calibration_source_bundle.report_only_cleanup_audit`로 관리한다. 이 audit는 `source_quality_gate`이며 `cleanup_candidate_count`를 통해 정리 후보를 표면화하지만, `source_quality_only`라서 threshold/env/order/bot/provider 변경 권한은 없다.

`Metric Decision Contract`는 [report-based-automation-traceability](./report-based-automation-traceability.md#23-metric-decision-contract)가 소유한다. 새 report나 새 metric이 이 계약을 만족하지 못하면 threshold candidate가 아니라 source-quality/instrumentation backlog다.

## 5. 현재 런타임/관찰 축

| 영역 | 현재 상태 | 금지선 |
| --- | --- | --- |
| scalping entry | `score65_74_recovery_probe`와 `scalp_entry_adm_runtime_bias_p1`이 2026-05-18 operator override로 runtime env에 포함됐다. Entry ADM은 `BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE/NO_BUY_AI/SKIP_SOURCE_QUALITY/SKIP_PRE_SUBMIT_SAFETY` bucket과 hypothesis fallback으로 AI `BUY`를 `WAIT`/`DROP`으로 보정할 수 있다. score 50 fallback/neutral은 `blocked_ai_score`로 보류 | threshold/provider/broker submit guard 우회 금지. stale/liquidity/overbought/latency/price freshness pre-submit safety는 ADM보다 우선 |
| lifecycle decision matrix | `lifecycle_decision_matrix_runtime`은 2026-05-19 구현된 umbrella owner다. 기존 Entry ADM/Holding-Exit ADM과 sim/counterfactual source를 adapter로 감싸 `entry/submit/holding/scale_in/exit` stage별 weighted ADM policy를 만들고, selected될 때만 다음 PREOPEN env로 policy file/version/promote cap을 연결한다 | hard safety, account/order/broker guard, stale quote/price freshness/stop/qty guard 우회 금지. score bucket 고정 정책이나 score 단조 EV 가정으로 쓰지 않는다 |
| entry price | `dynamic_entry_price_resolver_p1` + `dynamic_entry_ai_price_canary_p2`; passive probe submit revalidation이 stale이면 제출 전 block | `ws_data.curr` 직접 추격, stale quote submit 금지 |
| holding/exit | `soft_stop_micro_grace`, `soft_stop_whipsaw_confirmation`, `holding_flow_override`, `holding_exit_matrix_runtime_bias_p1` 운영 override. Holding/Exit ADM은 flow AI action을 `HOLD`/`EXIT`로 보정하고 `holding_exit_matrix_avg_down_bias`/`holding_exit_matrix_pyramid_bias`로 scale-in action을 제안할 수 있다 | hard/protect/emergency/order/account/cooldown/qty safety 우회 금지 |
| scale-in/position sizing | scale-in price resolver와 dynamic qty safety 유지. `position_sizing_dynamic_formula`는 score/strategy/volatility/liquidity/spread/price band/recent loss/portfolio exposure를 입력으로 보는 별도 owner이며, 신규/추가매수 1주 cap 해제는 `position_sizing_cap_release` approval request 이후만 검토 | sim/probe 단독 실주문 cap 해제, cap 해제 자동 apply 금지 |
| sim lifecycle | sim-first lifecycle 탐색은 신규 report chain이 아니라 기존 threshold-cycle 자동화체인의 입력 범위/해석 범위다. 스캘핑 `scalp_ai_buy_all`, wait/missed-entry counterfactual, swing dry-run/probe는 모두 `actual_order_submitted=false` source로 daily/cumulative EV, runtime approval summary, code-improvement workorder에 들어간다 | real order나 real-like execution 품질로 해석 금지. 단, sim 탐색은 예수금/실주문 가능 여부/현재 selected family 때문에 후보를 좁히지 않는다 |
| swing dry-run | lifecycle audit, threshold AI review, improvement automation, runtime approval summary가 장후 생성되며 기존 threshold-cycle 자동화체인의 swing source bundle 입력이 된다 | approval artifact 없는 env/live order 전환 금지 |
| swing real canary | one-share real canary와 scale-in real canary는 별도 approval-required 축 | 스윙 전체 실주문 전환으로 해석 금지 |
| OpenAI route | main live AI route는 OpenAI, Responses WS hot path provenance 확인 | provider route 확인을 threshold/주문가/수량 변경 근거로 사용 금지 |
| Sentinel/panic | BUY/HOLD/EXIT/panic sell/panic buying은 report-only source bundle | 자동매도, TP/trailing/threshold/provider/bot restart 변경 금지 |
| System Error Detector | report-only detector와 gated filesystem maintenance detector 분리 | 전략 threshold/order 변경 금지 |

## 6. 정량 목표와 가드

| 지표/가드 | 기준 | 조치 |
| --- | --- | --- |
| `N_min` | family별 hard 판정 최소 표본 미달 | hard pass/fail 금지, `hold_sample` 또는 cap 축소 |
| `primary_ev` | family 계약의 EV primary metric | apply/승격 primary 근거 |
| `diagnostic_win_rate` | 승률/일관성 보조 지표 | 단독 apply 금지 |
| `simple_sum_profit_pct` | 단순 손익 합산 | EV로 명명/사용 금지 |
| `source_quality_gate` | stale/missing/duplicate/provenance gap | gate 미충족 시 threshold candidate 제외 |
| `execution_quality_real_only` | 실제 broker order/receipt/fill 품질 | sim/probe/combined로 대체 금지 |
| `safety_veto` | severe loss, 주문 실패, provenance 손상, stop 지연, same-stage conflict | daily-only여도 block/rollback 후보 |
| `window_policy` | `daily_only`, rolling, cumulative, post-apply version window 분리 | daily-only edge apply 금지 |
| `runtime_mutation_guard` | 장중 threshold/order/provider/bot restart 변경 금지 | 다음 장전 env 또는 별도 approval로만 처리 |

## 7. 현재 Open 상태 요약

| 워크스트림 | 현재 owner/상태 | 다음 판정 경로 |
| --- | --- | --- |
| threshold auto apply | 2026-05-18 runtime env는 preopen selected family와 사용자 운영 override가 병합되어 있다. `score65_74_recovery_probe`, pre-AI soft gate 재배치, Entry ADM runtime bias, Holding/Exit ADM runtime bias는 post-restart cohort와 장후 EV로 추적한다 | 장후 `threshold_cycle_ev`, `runtime_approval_summary`, post-apply attribution |
| lifecycle matrix runtime | `lifecycle_decision_matrix_runtime`은 Full runtime용 구조가 구현됐지만 기본 OFF이며 auto-bounded micro canary 후보로만 열린다. fixed threshold는 `hard_safety`, `baseline_prior`, `bounded_tunable`, `legacy_archive` contract에 따라 재해석한다 | postclose `lifecycle_decision_matrix`, `threshold_cycle_ev`, `runtime_approval_summary`, 다음 PREOPEN `threshold_cycle_preopen_apply`; 장중 mutation 없음 |
| entry funnel | `BUY Funnel Sentinel` + `wait6579_ev_cohort` + `score65_74_recovery_probe` + `scalp_entry_adm_runtime_bias_p1` | BUY/submitted drought와 forced WAIT/DROP은 daily/rolling/cumulative EV, blocker attribution, missed-upside/avoided-loss로 판정 |
| sim-first lifecycle threshold scope | 신규 산출물 owner가 아니라 기존 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution` 체인의 범위 규칙이다. 스캘핑과 스윙의 BUY/selection 가능 후보 전체를 `selection -> entry -> holding -> scale_in -> exit` virtual lifecycle로 넓게 실행해 최적 threshold 후보와 기능개선 workorder를 찾는다 | 실주문/예수금/cap/selected runtime family는 sim exclusion 사유가 아니라 provenance tag로만 남긴다. 별도 standalone report가 threshold-cycle consumer나 apply authority가 되지 않는다 |
| entry price quality | P1/P2 price resolver, passive probe lifecycle, submit revalidation block | `pre_submit_price_guard` family와 daily EV attribution |
| holding/exit | `soft_stop_micro_grace`, selected `soft_stop_whipsaw_confirmation`, `holding_flow_override`, `holding_exit_matrix_runtime_bias_p1` | HOLD/EXIT Sentinel, post-sell feedback, scale-in ADM bias attribution, threshold-cycle EV |
| position sizing | scale-in resolver/dynamic qty safety, 1주 cap default ON. 동적수량 산식 튜닝 owner는 `position_sizing_dynamic_formula`, cap 해제 승인 owner는 `position_sizing_cap_release`로 분리 | 산식 변경은 `notional_weighted_ev_pct` 또는 `source_quality_adjusted_ev_pct` 기준으로 별도 검토하고, 실주문 수량 확대는 approval request 기준 충족 시 사용자 승인 요청 |
| panic lifecycle | `panic_sell_defense`, `panic_buying` report-only source bundle. `panic_regime_mode`는 `NORMAL -> PANIC_DETECTED -> STABILIZING -> RECOVERY_CONFIRMED` risk-regime 해석 계층이며, V2.0 runtime 후보는 scalping `entry_pre_submit` 전용 `panic_entry_freeze_guard`다. `panic_buy_regime_mode`는 `NORMAL -> PANIC_BUY_DETECTED -> PANIC_BUY_CONTINUATION -> PANIC_BUY_EXHAUSTION -> COOLDOWN` risk-regime 해석 계층이며, V2.0 후보는 기존 보유분 TP/runner 전용 `panic_buy_runner_tp_canary`다 | code-improvement workorder와 approval summary는 `runtime_effect=false` 또는 `approval_required`로만 생성. 패닉셀 미체결 주문 cancel, holding/exit context, 강제 축소/청산과 패닉바잉 추격매수 차단, continuation trailing, exhaustion cleanup, cooldown reentry guard는 별도 owner/approval/rollback guard 없이는 열지 않는다 |
| swing lifecycle | swing dry-run recommendation, audit, AI review, improvement automation, runtime approval | approval artifact 없으면 env apply/real order 금지 |
| AI transport | OpenAI Responses WS provenance | transport incident와 strategy threshold 효과를 분리 |
| system health | System Error Detector, postclose verification, wrapper `[START]/[DONE]/[FAIL]` marker | operational incident/playbook과 strategy tuning을 분리 |
| metric contract | 새 관찰지표 onboarding 필수 계약 | 계약 미충족 시 `instrumentation_gap`/`source_quality_blocker` |

## 8. 현재 기준에서 제외되는 것

1. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`, legacy latency composite, closed shadow axes는 archive 기준 historical/reference다.
2. 과거 날짜 checklist의 `[x]` 완료 항목은 현재 owner가 아니다. 현재 owner는 이 문서 §7과 당일 checklist의 열린 항목/런타임 상태가 소유한다.
3. 운영 자동화 증적(cron, wrapper, manifest, parser, report freshness)은 전략 효과나 live 승인 근거와 분리한다.
4. `server_comparison`은 명시 플래그가 없으면 Plan Rebase 의사결정 입력에서 제외한다.
5. `combined` sim+real 진단은 운영 관찰에는 쓸 수 있지만 real execution 품질/실주문 승인에는 쓰지 않는다.
6. 새 report-only 산출물이 생겨도 source bundle consumer, metric contract, forbidden uses가 없으면 자동화체인 입력으로 보지 않는다. 단, 사용자가 별도 `operator_runtime_override`를 선언하면 산출물과 runtime env override를 분리해 기록하고, rollback env와 safety guard 우선순위를 함께 남긴다.

## 9. 델타/Q&A 라우팅

| 문서 | 무엇을 남기나 | 이 문서에서 뺀 이유 |
| --- | --- | --- |
| [plan prompt](./plan-korStockScanPerformanceOptimization.prompt.md) | 다음 세션 진입용 경량 포인터 | 중심 기준은 rebase가 소유한다 |
| [execution-delta](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 날짜형 과제 레지스터, 지나간 일정, same-day pivot, 효과 기록 | rebase에 과거 경과를 누적하지 않는다 |
| [qna](./plan-korStockScanPerformanceOptimization.qna.md) | 자동화체인 오판 방지 FAQ, metric authority, proposal/apply 구분 | 반복 정책만 보관 |
| 날짜별 checklist | 특정 시각 작업, Due/Slot/TimeWindow, 완료/미완 상태 | 자동 파싱과 Project/Calendar 소유 문서 |
| audit/report | 외부 반출본, 세부 수치 근거, 감리 관점 해설 | rebase는 승인 기준만 남김 |
| [archive](./archive/) | 종료된 관찰축, 과거 workorder, pre-renewal 원문 | 현재 active/open 판단에서 제외 |

## 10. 핵심 참조문서

| 문서 | 역할 |
| --- | --- |
| [2026-05-13-stage2-todo-checklist.md](./2026-05-13-stage2-todo-checklist.md) | 당일 장전/장중/장후 실행표와 postclose 자동 생성 항목 |
| [report-based-automation-traceability.md](./report-based-automation-traceability.md) | R0~R6 ladder, source bundle, Metric Decision Contract, 금지선 |
| [data/threshold_cycle/README.md](../data/threshold_cycle/README.md) | threshold collector/report/apply plan/runtime env 운영방법 |
| [data/report/README.md](../data/report/README.md) | 정기 report inventory와 Markdown 누락 후보 |
| [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md) | 세션 시작용 경량 포인터 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 원안 대비 변경, 날짜형 이력, 종료된 축 기록 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 반복 판단 기준과 감리 Q&A |
| [archive/closed-observation-axes-2026-05-01.md](./archive/closed-observation-axes-2026-05-01.md) | 종료된 관찰축 archive |
| [archive/plan-korStockScanPerformanceOptimization.rebase.pre-automation-renewal-2026-05-13.md](./archive/plan-korStockScanPerformanceOptimization.rebase.pre-automation-renewal-2026-05-13.md) | 자동화체인 리뉴얼 전 Rebase 원문 |
