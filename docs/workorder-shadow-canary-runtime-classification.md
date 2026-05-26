# 작업지시서: Shadow/Canary 런타임 경로와 Live Cohort 분류 기준

작성일: `2026-04-25 KST`  
마지막 갱신: `2026-05-21 KST`
대상: KORStockScan 메인 코드베이스 운영/튜닝 문서 소유자  
ApplyTarget: `main` 문서/후속 코드정리 기준  

이 문서는 체크리스트/Project/Calendar 자동관리 대상이 아닌 독립 workorder다. 목적은 `shadow/canary` 경로를 일괄 삭제하는 것이 아니라, `지속 모니터링 가치`와 `운영/코드 부채`를 함께 평가해 각 경로를 `remove / observe-only / baseline-promote / active-canary` 중 하나로 고정하고, live 전환/병렬 관찰 시 섞이면 안 되는 `cohort`도 함께 분류 기준으로 잠그는 것이다.

운영 정의:

1. `shadow`: 병렬 계산과 로그만 남기고 실주문/실판단은 바꾸지 않는 경로
2. `active-canary`: ON/OFF 가능한 단일 조작점이 제한된 live cohort에 실제 영향을 주는 경로
3. `baseline-promote`: 이름은 canary/relief라도 사실상 기본 운영경로처럼 쓰이는 상태
4. `cohort`: baseline/live/observe/excluded 모집단을 분리해 EV 해석과 rollback을 섞이지 않게 잠그는 단위
5. `운영 override`: alpha 검증보다 실전 보호/보정 목적이 앞서는 runtime 우선순위 변경. canary와 동일하게 rollback owner와 cohort를 잠가야 한다.
6. `real-canary`: 기본 dry-run 또는 sim 체계는 유지하되, 별도 승인된 극소수 모집단에만 실제 브로커 주문을 보내 execution 품질과 receipt 정합성을 수집하는 경로다. 전체 실매매 전환이나 dry-run 해제가 아니다.

현재 스냅샷:

1. entry live owner는 `mechanical_momentum_latency_relief`다. `latency_quote_fresh_composite`와 `latency_signal_quality_quote_composite`는 `observe-only/historical-reference`로 내린다.
2. 보유/청산 live owner는 `soft_stop_micro_grace`다. `soft_stop_expert_defense v2`는 `2026-04-30 12:00~15:30 KST` same-day 수집 축으로 종료했고, 다음 재승인 전 기본 OFF다. `soft_stop_rebound_split`은 historical hypothesis로, `trailing_continuation`은 2순위 후보로 유지한다.
3. `Gemini response schema registry`와 `DeepSeek retry acceptance snapshot`은 flag-off observability 묶음이다. live enable 또는 active canary가 아니다.
4. `AI cache hit/miss`는 영향도가 중간 이상일 수 있으나, 현재 structured join 필드가 부족해 `observe-only schema gap`으로 분류한다.
5. `Execution receipt binding`은 BUY/SELL 체결 truth 품질 이슈다. EV 판정 전제 품질축으로 보되, alpha canary로 분류하지 않는다.
6. `2026-05-01` 근로자의 날과 `2026-05-05` 어린이날은 KRX 휴장으로, 휴장일 Due 작업은 다음 운영일 체크리스트로 이관한다.
7. threshold 운영은 `실시간 자동변경`이 아니라 `장중 적재 -> 장후 산정 -> 다음 장전 적용`으로 고정한다. compact threshold stream이 기본 경로이며, `entry_mechanical_momentum`, `bad_entry_block`, `REVERSAL_ADD blocked funnel`, `soft_stop_micro_grace`가 현재 sample-ready family다.
8. `bad_entry_block`의 naive 차단은 금지한다. 다만 `2026-05-12` postclose 기준 `bad_entry_refined_canary`는 active live owner가 아니라 `post_sell` join readiness를 기다리는 `observe-only / report-only hold`다. entry 쪽 active canary는 `score65_74_recovery_probe`와 `dynamic_entry_ai_price_canary_p2`처럼 별도 cohort로 분리해 본다.
9. `statistical_action_weight`는 가격대/거래량/시간대별 행동 선택 통계용 `decision-support` 축이다. live 판단에는 직접 쓰지 않고 장후 threshold weight 입력과 동적 수량화 설계 근거로만 둔다.
10. 스윙은 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`가 기본이며, `swing_sim_*`/combined는 EV 후보와 승인 요청 생성에는 동급 입력으로 쓴다. 다만 broker execution 품질은 real-only라 `swing_one_share_real_canary`를 별도 approval-required real-canary 후보로 둔다.

### 2026-05-14 POSTCLOSE Snapshot Addendum

이 addendum은 `runtime_approval_summary_2026-05-14`, `threshold_cycle_ev_2026-05-14`, `pipeline_event_verbosity_2026-05-14`, `panic_sell_defense_2026-05-14` 기준의 당일 분류 보정이다. 기존 분류 체계는 바꾸지 않고, 5/14에 새 baseline 승격이나 remove 판정이 없었음을 잠근다.

| 축 | 2026-05-14 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| `soft_stop_whipsaw_confirmation` | active-canary / selected auto-bounded-live | 당일 runtime approval summary에서 유일한 selected_auto_bounded_live이며 runtime env에 반영됨 | 5/15 post-apply attribution에서 applied/not-applied cohort와 rollback guard 확인 |
| `score65_74_recovery_probe` | observe/existing-family input, 당일 runtime selected 아님 | 5/14 runtime env selected family에 없고 runtime approval summary state는 hold 계열 | 다음 preopen apply와 rolling/cumulative sample 기준으로 재판정. 수동 env override 금지 |
| `bad_entry_refined_canary` | observe-only / live OFF | runtime approval summary상 adjust_up이지만 current_application=`OFF/관찰 only` | source bundle과 post-sell join 품질이 닫힐 때까지 live 승격 금지 |
| `pipeline_event_compaction_v2_shadow` | report-only diagnostic aggregation | 기본 mode는 `off`; shadow는 raw JSONL/DB upsert를 보존하고 producer summary/parity만 생성 | V1/V2 parity 2영업일 이상 확인 전 suppress 금지 |
| `panic_entry_freeze_guard` | report-only candidate / inactive | `panic_sell_defense_2026-05-14` panic_state=`NORMAL`, candidate status=`inactive_no_panic`, allowed_runtime_apply=`false` | PANIC_SELL/confirmed risk-off 반복과 approval artifact/rollback guard가 닫힌 뒤 별도 implementation workorder로 검토 |
| `swing_runtime_approval` | approval-required dry-run, real canary 아님 | 5/14 approval request 2건, approved 0건, runtime_change=false | approval artifact 없이는 env/live order 반영 금지 |

5/14 결론은 `no_runtime_classification_change_with_snapshot_update`다. 신규 `remove`, `baseline-promote`, `active-canary` 전환은 없고, report-only/observe-only 축은 threshold/order/provider/bot restart 권한이 없다.

### 2026-05-15 POSTCLOSE Snapshot Addendum

이 addendum은 `runtime_approval_summary_2026-05-15`, `threshold_cycle_ev_2026-05-15`, `pipeline_event_verbosity_2026-05-15`, `panic_sell_defense_2026-05-15`, `panic_buying_2026-05-15` 기준의 당일 분류 보정이다. 기존 분류 체계는 바꾸지 않고, 5/15에 새 baseline 승격이나 remove 판정이 없었음을 잠근다.

| 축 | 2026-05-15 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| `soft_stop_whipsaw_confirmation` | active-canary / selected auto-bounded-live 유지 | runtime approval summary에서 유일한 scalping selected auto-bounded-live이며 당일 runtime env 적용 family다 | 5/18 PREOPEN apply에서 다음 장전 env 반영 여부를 deterministic guard로 재확인 |
| `score65_74_recovery_probe` | active-canary 후보 / 당일 runtime selected 아님 | threshold EV postclose에서 `adjust_up`, `sample_count=196`, `source_sample_count=19`이나 `threshold_relaxation_approved=false`, panic sell context 동반 | 장중 수동 threshold 변경 금지. 다음 장전 rolling/cumulative guard와 panic context를 같이 본다 |
| `bad_entry_refined_canary` | observe-only / live OFF | `adjust_up` 후보지만 current application은 `OFF/관찰 only`이고 same-stage live owner가 아니다 | post-sell join 품질과 single-owner guard가 닫히기 전 live 승격 금지 |
| `pipeline_event_compaction_v2_shadow` | report-only diagnostic aggregation | raw 1.70GB, high-volume diagnostic share 96.87%, parity not ok, suppress eligibility false | V1/V2 parity 2영업일 이상 통과 전 suppress 금지 |
| `panic_entry_freeze_guard` | report-only candidate / approval contract missing | `panic_regime_mode=PANIC_DETECTED`지만 runtime effect는 `report_only_no_mutation`; loader/env/pre-submit guard/rollback tests 미구현 | V2.0 approval contract workorder가 생기기 전 신규 BUY pre-submit freeze 적용 금지 |
| `panic_buy_runner_tp_canary` | report-only/freeze | `panic_buy_regime_mode=NORMAL`, market-wide panic-buy unconfirmed, orderbook collector coverage source-quality blocker와 approval contract missing | 기존 보유분 TP/runner 전용 owner로 유지. TP/trailing 변경 금지 |
| `swing_runtime_approval` | approval-required dry-run, real canary 아님 | `swing_model_floor`, `swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0` request가 있으나 approved 0, approval artifact missing | 승인 artifact 없이는 env/live order 반영 금지 |

5/15 결론은 `no_runtime_classification_change_with_snapshot_update`다. 신규 `remove`, `baseline-promote`, 추가 `active-canary` 전환은 없고, report-only/observe-only 축은 threshold/order/provider/bot restart 권한이 없다. `soft_stop_whipsaw_confirmation` 외의 당일 후보는 다음 장전 deterministic guard 또는 별도 approval contract가 닫히기 전까지 runtime owner가 아니다.

### 2026-05-18 POSTCLOSE Snapshot Addendum

이 addendum은 `runtime_approval_summary_2026-05-18`, `threshold_cycle_ev_2026-05-18`, `threshold_runtime_env_2026-05-18`, `scalp_entry_action_decision_matrix_2026-05-18`, `swing_runtime_approval_2026-05-18` 기준의 당일 분류 보정이다. 5/18에는 사용자 운영 override로 runtime 영향이 열린 축이 있으므로, alpha baseline 승격이 아니라 `operator override cohort`로 별도 잠근다.

| 축 | 2026-05-18 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| `score65_74_recovery_probe` | active-canary / selected auto-bounded-live | runtime env selected family에 포함됨. score 65~74 BUY 병목 확대 목적의 bounded cohort다 | post-restart/postclose attribution에서 `env loaded -> intended downstream consumer reached|intended safety block` 순서를 계속 확인 |
| `bad_entry_refined_canary` | active-canary / selected auto-bounded-live | runtime env selected family에 포함됨. post-sell/ADM 품질을 근거로 bad-entry 방어 cohort를 분리한다 | 단일 손실 표본으로 threshold를 닫지 않고 candidate/post-sell join 품질을 먼저 본다 |
| `strength_momentum_soft_gate_p1` | operator override risk-context path / baseline 아님 | pre-AI hard block을 `risk_context_only`로 낮추는 운영 override가 적용됐으나 post-restart real scalp 표본은 hold_sample | 5/19 real cohort에서 AI/counterfactual 전달과 source-quality blocker 분리를 확인 |
| `overbought_pullback_guard_p1` | operator override + pre-submit safety guard | AI 평가는 허용하되 pullback/rebreak 또는 price freshness가 없으면 broker submit 직전 차단한다 | `blocked_overbought`가 terminal pre-AI block으로 재등장하지 않는지 확인 |
| `liquidity_pre_submit_guard_p1` | operator override + pre-submit hard guard | AI/counterfactual 평가는 허용하되 저유동성은 broker submit 직전 `actual_order_submitted=false`로 닫는다 | missed-upside/avoided-loss 분석에는 포함하되 submit safety 우회 금지 |
| `scalp_entry_action_decision_matrix_advisory` | operator runtime bias active / source bundle warning | ADM runtime bias env는 켜졌으나 matrix joined_sample=`2/20`, prompt_applied_count=`0`, missing action bucket이 남음 | runtime forced WAIT/DROP, missed upside, avoided loss를 다음 장중/postclose cohort에서 분리 |
| `holding_exit_decision_matrix` | operator runtime bias active / positive action tuning not ready | holding/exit/scale-in bias env는 열렸지만 daily matrix edge와 forced action 표본은 아직 부족하다 | hard/emergency/order safety를 우회하지 않고 missed-upside/avg-down/pyramid provenance를 수집 |
| `pipeline_event_compaction_v2_shadow` | report-only diagnostic aggregation | raw event 보존을 전제로 producer summary/parity만 생성하는 instrumentation 축이다 | parity와 source link가 닫히기 전 raw suppress 또는 runtime 판단 변경 금지 |
| `swing_one_share_real_canary_phase0` | approval-bounded real-canary env retained / dry-run split 유지 | runtime env selected family에 있으나 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 기본이며 5/18 swing approval request는 0건 | 승인 artifact와 target 후보가 없으면 실주문 제출로 해석하지 않는다 |
| `swing_gatekeeper_reject_cooldown` | active selected policy tuning / source-quality 관찰 필요 | runtime env selected family에 포함됐지만 swing_runtime_approval 5/18은 requested=0, blocked=14로 닫힘 | gatekeeper accept/reject contract gap과 cooldown attribution을 분리 |

5/18 결론은 `no_baseline_promote_with_operator_override_cohorts_locked`다. 신규 `remove`와 `baseline-promote`는 없다. 사용자 운영 override 축은 실런타임 bias 영향이 있으므로 `observe-only`가 아니라 `operator override cohort`로 보되, threshold mutation/provider change/broker submit safety 우회 권한은 없다. report-only/pattern lab/source-quality 축은 runtime owner로 승격하지 않는다.

### 2026-05-19 INTRADAY/POSTCLOSE Snapshot Addendum

이 addendum은 `threshold_runtime_env_2026-05-19`, `threshold_apply_2026-05-19`, 당일 sim 확대 override, lifecycle decision matrix, sim AI budget manager, sim scale-in approval flow 기준의 분류 보정이다. 결론은 `active_shadow_none_runtime_shadow_refs_are_off_or_report_only`다.

| 축 | 2026-05-19 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| active shadow runtime | 없음 | `threshold_runtime_env_2026-05-19.json` 기준 `shadow` 문자열 0건이고 shadow env 기본값은 모두 OFF다 | 신규 shadow로 열지 않는다. 남은 shadow 참조는 OFF/historical/report-only cleanup 후보로만 관리 |
| `pipeline_event_compaction_v2_shadow` | report-only diagnostic aggregation | raw 보존/compaction parity 목적의 diagnostic 이름이다. runtime env에는 반영되지 않았다 | raw suppress나 producer 변경 전 parity/source link 확인 필요 |
| `lifecycle_decision_matrix_runtime` | umbrella ADM owner / 기본 OFF / micro-canary 후보 | `entry/submit/holding/scale_in/exit` stage별 weighted ADM policy를 만들지만 hard safety와 broker guard를 우회하지 않는다 | selected되면 다음 PREOPEN policy file/version/promote cap만 env에 쓴다 |
| `scalp_sim_candidate_window_expansion` | sim-only operator override cohort | score 55~100 WAIT/blocked 후보를 `actual_order_submitted=false`, `broker_order_forbidden=true`로 sim lifecycle에 편입한다 | real BUY 승격이나 submit guard 완화 근거로 쓰지 않고 lifecycle matrix source로만 본다 |
| `scalp_sim_ai_budget_manager` | sim-only operator override cohort | 확대된 sim holding의 OpenAI 호출량을 live/reuse/deferred/critical bypass로 attribution한다 | critical bypass 과다를 `hard_critical/soft_critical/non_critical`로 분해하는 후속 보정 후보 |
| `scalp_sim_scale_in_window_expansion` | sim-auto-approved sim-only actuator | postclose artifact is generated with `approved=true`, `approval_state=sim_auto_approved`, and `human_approval_required=false` only when the lifecycle matrix source report is readable; it can open only the next PREOPEN sim-source env window | Still a sim-only scale-in source actuator. Real scale-in, cap release, hard-safety relaxation, provider changes, and bot restart are forbidden |
| `score65_74_recovery_probe` | active operator-selected entry cohort | 5/19 runtime env에 사용자 reopen lock으로 로드됐다 | rolling/cumulative EV와 blocker attribution으로만 판정. score bucket 고정 정책 금지 |

5/19 결론은 active shadow가 없다는 점을 잠그고, 신규 sim 확대축은 `shadow`가 아니라 `sim-only cohort` 또는 `sim-auto-approved actuator`로 분류한다. 남아 있는 `hard_time_stop_shadow`, `partial_only_timeout_shadow`, `same_symbol_soft_stop_cooldown_shadow`, `dual_persona_shadow`, prompt shadow 계열은 기본 OFF 또는 historical/dashboard label이며 현재 runtime owner가 아니다.

### 2026-05-21 POSTCLOSE Snapshot Addendum

이 addendum은 `threshold_cycle_ev_2026-05-21`, `runtime_approval_summary_2026-05-21`, `lifecycle_decision_matrix_2026-05-21`, `bedrock_nova_micro_shadow_report_2026-05-21`, `threshold_cycle_postclose_verification_2026-05-21` 기준의 당일 분류 보정이다. 결론은 `no_runtime_classification_change_with_2026_05_21_snapshot`이다.

| 축 | 2026-05-21 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| `Bedrock Nova Micro bypass` | shadow observation only / `holding_continuation` 후보 분리 | Micro shadow는 `row_count=2945`, parse ok rate `0.9997`이다. `engine_decision_performance` exact/evaluated `53`건에서 OpenAI lifecycle quality score `8`, Nova `18`; 불일치 `16`건은 OpenAI `EXIT` vs Nova `HOLD`였고 Nova `6` vs OpenAI `-4`, edge count Nova `11` vs OpenAI `5`로 HOLD continuation arm은 Nova 우위다. 다만 Nova가 사실상 `HOLD`만 냈으므로 `EXIT`/loss-reduction 판단력은 미검증 | 전체 provider primary 승격이 아니라 `holding_continuation` stage-specific 후보로 다음 검토. source-quality coverage, rollback guard, approval/workorder 없이 provider route 변경 금지 |
| `Bedrock Nova Lite overnight shadow` | shadow observation only | overnight 주판정은 OpenAI `gpt-5.4-mini`이며 Lite는 동일 입력 observation/report만 남긴다. action 결정, provider route 변경, live order enable 권한 없음 | shadow JSONL/report에서 latency/cost/action drift만 누적 |
| `scalp_sim_overnight_ai_carry` | sim-only source / hard gate 아님 | 15:20 preclose runner와 LDM 소비 경로는 `decision_authority=sim_observation_only`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다 | 다음 postclose에서 decision coverage와 carry label join을 source-quality로 확인 |
| `lifecycle_decision_matrix_runtime` | selected source-bundle owner / promote 없음 | LDM은 `total_rows=40910`, `joined=39149`, policy pass `5`지만 `promote_ready_count=0`; entry/scale bucket 후보는 approval-required source-only다 | entry/scale/overnight bucket handoff를 verifier로 계속 감리하고 runtime mutation은 PREOPEN guard 이후만 허용 |
| `scalp_sim_candidate_window_expansion` | sim-only selected cohort / 160 유지 | `max_daily=160`에서 sim completed `166`, duplicate buy signal `374`, candidate window discarded `1645`, entry join rate `0.1388`; 240 상향 근거 부족 | `hold_160_until_persistent_counter_fixed`로 닫고 다음 postclose에서 재판정 |
| `scalp_sim_ai_budget_manager` | sim-only budget/provenance owner | live/reuse/deferred/critical bypass attribution은 sim lifecycle source 품질 확인용이며 provider route, BUY/submit threshold, broker guard 변경 권한 없음 | deferred/exhausted row가 LDM/source-quality consumer로 이어지는지 계속 확인 |
| postclose bot restart isolation | operations/runbook control, strategy cohort 아님 | 16:10 wrapper의 bot stop/restart 격리는 resource isolation이다. 5/21 wrapper는 daily report 단계에서 kill됐고 수동 복구로 verifier가 `pass_with_pending_done_marker`를 냈다 | 다음 postclose에서 `[DONE]` marker와 resource guard를 확인하고 daily report RSS workorder로 보완 |

5/21 결론은 신규 `remove`, `baseline-promote`, 추가 `active-canary` 전환 없음이다. Bedrock shadow, scalp sim overnight, LDM bucket attribution, runbook restart isolation은 모두 실주문/threshold/provider/bot 전략 변경 권한을 갖지 않는다.

### 2026-05-22 POSTCLOSE Snapshot Addendum

이 addendum은 `threshold_cycle_ev_2026-05-22`, `runtime_approval_summary_2026-05-22`, `runtime_apply_bridge_2026-05-22`, `bedrock_nova_micro_one_day_decision_2026-05-22`, `bedrock_nova_lite_one_day_decision_2026-05-22`, `threshold_cycle_postclose_verification_2026-05-22` 기준의 당일 분류 보정이다. 결론은 `no_baseline_promote_with_route_candidates_and_source_quality_gaps_locked`이다.

| 축 | 2026-05-22 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| `Bedrock Nova Micro one-day` | observe-only 종료 후보 / OpenAI 유지 | one-day decider winner=`openai`, next_action=`turn_micro_shadow_off_keep_openai`. `runtime_effect=false`, `broker_order_forbidden=true`, `actual_order_submitted=false`를 유지했다 | Micro shadow/duel은 OFF 후보로 닫고, provider route/threshold/order guard 변경 금지 |
| `Bedrock Nova Lite v1 Tier2` | route candidate / approval-workorder required | one-day decider winner=`lite`, route_candidate=`tier2_nova_lite_v1`. `holding_flow` exact join 82건에서 Lite source-quality adjusted EV가 OpenAI보다 `+0.0472%p` 높았다 | candidate만 보관한다. 실제 provider route 변경은 별도 approval/workorder와 rollback/off switch 전까지 금지 |
| `Bedrock Nova Lite v2` | source-quality/contract gap | 공식 model id는 확인됐지만 현재 운영 코드는 v1용 `KORSTOCKSCAN_BEDROCK_NOVA_LITE_*` 단일 env/model path라 v1/v2 비용, region/profile, timeout, queue, artifact path를 분리하지 못한다 | 2026-05-26 source-quality/contract 확인 항목으로 넘기고 즉시 shadow 시행은 보류 |
| `lifecycle_bucket_discovery` / `runtime_apply_bridge` | active automation bridge / live-auto 후보 1건 | `runtime_apply_bridge` status=`pass`, candidate_count=`2`, live_auto_apply_ready_count=`1`, runtime_mutation_performed=`false`; postclose verifier status=`pass` | 05-26 PREOPEN에서 env uptake와 post-apply attribution을 확인한다. hard safety/provider/bot/cap guard는 우회하지 않는다 |
| `swing_runtime_approval` | approval-required dry-run/real-canary split | `runtime_approval_summary` 기준 swing_requested=`3`, swing_approved=`0`; 대상은 `swing_model_floor`, `swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0` | 사용자가 approval artifact를 승인한 경우에만 다음 PREOPEN dry-run/real-canary 경로로 소비한다 |
| `scalp_sim_candidate_window_expansion` / `scalp_sim_ai_budget_manager` | sim-only selected cohort 유지 | sim split은 threshold EV 입력으로 유지되지만 broker execution 품질이나 live 전환 단독 근거가 아니다 | sim-only auto approval과 provenance 수집만 유지 |

5/22 결론은 신규 `baseline-promote`, 신규 `remove`, 실주문 전환 없음이다. Nova Lite v1은 route 후보일 뿐 현재 provider route가 바뀐 것이 아니고, Nova Lite v2는 별도 source-quality/contract gap이 닫히기 전까지 shadow 시행 후보도 아니다. lifecycle bridge live-auto 후보는 자동화체인 범위의 entry/scale 후보이며 provider route, bot restart, position cap release, broker safety를 우회하지 않는다.

### 2026-05-26 POSTCLOSE Snapshot Addendum

이 addendum은 `threshold_cycle_ev_2026-05-26`, `runtime_approval_summary_2026-05-26`, `lifecycle_bucket_discovery_2026-05-26`, `swing_model_retrain_2026-05-26`, `threshold_cycle_postclose_verification_2026-05-26` 기준의 당일 분류 보정이다. 결론은 `no_baseline_promote_with_v2_primary_override_and_model_artifact_promotion_locked`이다.

| 축 | 2026-05-26 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| `Bedrock Nova Lite v2 entry_price/holding_flow` | operator provider override / endpoint-scoped primary | 사용자 명시 override로 `entry_price`/`holding_flow`만 Nova Lite v2 primary, OpenAI failback, Nova Lite v1 shadow comparison으로 전환됐다. 이는 provider transport/provenance 범위이며 threshold/order guard/cap 변경과 분리한다 | endpoint allowlist, failback, v1 shadow row, provider audit를 계속 확인한다. 기타 Tier2 endpoint는 OpenAI 유지 |
| `Bedrock Nova Lite v1 shadow` | shadow observation only / v2 comparison baseline | v1은 v2 primary와 비교하는 shadow-only 역할로 바뀌었고 `actual_order_submitted=false`, `runtime_effect=false` provenance만 남긴다 | v1/v2 action drift, parse, latency, cost를 source-quality로만 누적한다. threshold/order/provider 확대 근거로 쓰지 않는다 |
| `lifecycle_bucket_discovery` | sim-auto source owner / 신규 live-auto 없음 | 05-26 discovery는 `candidate_count=414`, `sim_auto_approved_count=184`, `live_auto_apply_ready_count=0`, `automation_handoff_gap_count=0`, AI two-pass `parsed`다 | 신규 live-auto 후보가 없으므로 다음 PREOPEN live env 예외를 만들지 않는다. sim-auto는 sim policy/source-only로만 소비한다 |
| `code_improvement_workorder` | runtime_effect=false implementation backlog | selected order `58`, selected `implement_now=28`, selected `attach_existing_family=30`이다. 모든 selected order는 `runtime_effect=false`로 남았다 | 사용자가 Codex 구현을 지시한 경우에만 해당 workorder source/section 기준으로 구현한다. 자동 repo 수정 또는 runtime mutation 없음 |
| `swing_model_auto_retrain` | model artifact promotion only | AI Tier2 `parsed/approved`, MLflow logged, `current.json`은 `active_live_behavior=true`, `runtime_change=model_artifact_promote_only`, `swing_live_order_dry_run_required=true`다 | active model artifact와 daily recommendations 경로만 새 artifact로 본다. dry-run 해제, real-order conversion, cap release, provider/bot 변경 금지 |
| `bottom_rebound swing discovery` | not applicable / safe-pool-only sim path | bottom rebound source는 disabled/absent이고 verifier는 `bottom_rebound_sim_handoff.status=not_applicable`로 닫혔다. safe-pool sim candidate/arm은 persisted됐다 | bottom rebound source가 contract pass로 생성되는 날에만 persisted candidate/arm handoff를 재확인한다 |
| `postclose DONE marker` | operations warning / strategy cohort 아님 | wrapper status는 succeeded지만 verifier는 `pass_with_pending_done_marker`다 | 다음 postclose에서 marker completion을 확인한다. 운영 경고는 EV/strategy/provider/order/bot 변경 근거가 아니다 |

5/26 결론은 신규 `baseline-promote`, 신규 `remove`, 실주문 전환 없음이다. Nova Lite v2 primary는 사용자 명시 provider override지만 endpoint-scoped transport 변경이며, lifecycle/swing/model 산출물의 sim/source/model-only 권한과 섞지 않는다.

## 0.1 Runtime ON/OFF 스냅샷 (`2026-05-12` 기준)

이 표는 `src/utils/constants.py` 기본값과 현재 운영문서 기준의 runtime 상태를 한곳에 잠그기 위한 스냅샷이다. env override가 있으면 장전 로드 확인에서 반드시 이 표와 비교한다.

### ON: 실주문/실판단 영향 있음

| 축 | 상태 | 현재 기준 | 유지/판정 기준 |
| --- | --- | --- | --- |
| `mechanical_momentum_latency_relief` | ON, entry operating override | `SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=True` | same-day entry replacement 운영 override다. 단, score 50 fallback/neutral은 `AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True`가 우선해 `blocked_ai_score`로 보류한다. 제출 전은 진입병목 회복, 제출 후는 `full/partial` 체결 품질과 BUY 신호 적정성으로 분리 판정한다 |
| `ai_score_50_buy_hold_override` | ON, entry operating override | `AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True` | AI parse/error/neutral score 50을 신규 BUY 제출로 내려보내지 않는다. 5/6에는 avoided loser와 missed winner를 분리해 하향 재진입 복합 threshold로 대체 가능성을 본다 |
| `score65_74_recovery_probe` | ON, entry active-canary | `AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True` | AI score `65~74`, latency `DANGER` 제외, 수급/가속/micro-VWAP gate를 통과한 cohort만 bounded canary로 본다. `missed_probe_counterfactual`은 `actual_order_submitted=false`라 EV 입력일 뿐 broker execution 승인 근거는 아니다 |
| `soft_stop_micro_grace` | ON, exit active-canary | `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True`, `20초`, emergency `-2.0%` | hard stop 전환, 미체결, same-symbol 손실이 늘면 OFF. 반등 포착 개선이 유지되면 baseline-promote 후보 |
| `REVERSAL_ADD` | ON, exit active-canary | `REVERSAL_ADD_ENABLED=True` | executed가 계속 0이면 parking 금지. `pnl/hold/supply/qty/position_cap/cooldown/pending/protection` blocker를 좁혀 실행요건을 찾는다 |
| `initial_entry_qty_cap_1share` | ON, size guard restored | `SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=True`, `SCALPING_INITIAL_ENTRY_MAX_QTY=1` | 2026-05-09 후속 사용자 지시로 신규 BUY/wait6579 probe/REVERSAL_ADD/PYRAMID 1주 수량 cap은 기본 ON으로 복귀했다. 해제는 `position_sizing_cap_release` approval request와 사용자 승인 없이는 금지한다 |
| `pre_submit_price_guard` | ON, entry guard | `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True` | 비정상 저가 지정가 차단. false block이 확인될 때만 threshold 조정 |
| `dynamic_entry_price_resolver_p1` | ON, entry baseline-promote 후보 | `SCALPING_ENTRY_PRICE_RESOLVER_ENABLED=True`, `SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS=80` | `target_buy_price`는 reference로만 쓰고 실주문가는 strategy-aware resolver가 결정한다. 일반 스캘핑 `90초`, `BREAKOUT 120초`, `PULLBACK 600초`, `RESERVE 1200초` timeout 분리와 함께 본다 |
| `dynamic_entry_ai_price_canary_p2` | ON, entry active-canary | `SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True`, `entry_price_v1`, min confidence `60`, skip min `80` | submitted 직전 Tier2 AI가 `USE_DEFENSIVE | USE_REFERENCE | IMPROVE_LIMIT | SKIP` 중 하나를 고른다. AI 실패/parse fail/guard 위반은 P1 resolver로 fail-closed하고, best ask 초과나 미체결 방치가 보이면 OFF |
| `partial_fill_ratio_guard` | ON, fill-quality guard | `SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=True` | partial/full 분리 판정 유지. partial 악화가 닫히기 전 해제 금지 |
| `dynamic_vpw` | ON, entry gate | `SCALP_DYNAMIC_VPW_ENABLED=True`, `OBSERVE_ONLY=False` | 체결강도 동적 gate 적용. threshold cycle 산정 후보로 유지 |
| `dynamic_strength_relief` | ON, baseline-promote 후보 | `SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED=True` | runtime/log는 relief 기준. 이름상 canary 잔재는 후속 정리 대상 |
| `SCALPING_ENABLE_PYRAMID` | ON, add enable owner | `SCALPING_ENABLE_PYRAMID=True` | count cap이 아니라 cooldown/pending/position cap/protection으로 리스크 제한 |

### ON: observe/report-only, 실주문 변경 없음

| 축 | 상태 | 현재 기준 | live 전환 기준 |
| --- | --- | --- | --- |
| `stat_action_decision_snapshot` | observe-only ON | `STAT_ACTION_DECISION_SNAPSHOT_ENABLED=True`, `30초` rate-limit | 직접 live 전환 금지. 장후 weight/report 입력으로만 사용 |
| `statistical_action_weight` | report-only ON | 장후 행동가중치 리포트 생성 | live 적용은 별도 단일축 canary와 rollback guard가 있을 때만 가능 |
| `bad_entry_refined_canary` | observe-only ON, live OFF | `SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=False` | `record_id -> post_sell_evaluations` join readiness가 닫히기 전까지 `bad_entry_refined_candidate`는 provisional signal로만 본다 |
| `holding_exit_decision_matrix` | report-only ON | AI 보유/청산 판단 보조 매트릭스 | `ADM-1 report-only -> ADM-2 shadow prompt -> ADM-3 advisory nudge -> ADM-4 weighted live -> ADM-5 policy gate` 순서로만 전환 |
| `swing_live_order_dry_run` | dry-run ON | `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`; 스윙 live lifecycle은 실행하되 브로커 주문만 차단 | runtime threshold/logic은 승인 artifact가 있을 때 dry-run 내부에서만 반영. 실주문 허용과 별개 |
| `swing_runtime_approval` | approval request ON | hard floor + EV trade-off score로 `approval_required` 요청 생성 | 수동 approval artifact가 있어야 다음 장전 dry-run env 반영. 실주문 허용 없음 |
| `threshold_cycle` | automation ON, mutation OFF | 07:35 manifest, 16:10 collector/report | `ThresholdOpsTransition0506` 전까지 `manifest_only`; runtime threshold mutation/restart 자동화 금지 |
| `hard_time_stop_shadow` | OFF, historical/replay only | `SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=False` | 실주문 승격 후보 아님. time-based exit 의제 재개 시 새 단일축으로 정의 |
| `same_symbol_soft_stop_cooldown_shadow` | OFF, live cooldown으로 대체 | `SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED=False` | `same_symbol_loss_reentry_cooldown` live 운영가드로 전환. 복합 threshold 전환은 5/6 후속 |
| `partial_only_timeout_shadow` | OFF, historical/replay only | `SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_ENABLED=False` | partial 장기체류 손익 훼손이 반복될 때 새 report-only 항목으로 재등록 |
| `SCALP_LOSS_FALLBACK` | observe-only ON, live OFF | `SCALP_LOSS_FALLBACK_ENABLED=False`, `OBSERVE_ONLY=True` | `REVERSAL_ADD`와 충돌하지 않는 별도 owner/rollback 기준 없이는 live 금지 |

#### `holding_exit_decision_matrix` 전환 ladder

`AI decision matrix`는 계속 보고서로만 두는 축이 아니다. 다만 live 반영은 아래 순서 외에는 허용하지 않는다.

`2026-05-07 KST` 기준으로는 `ADM-2 shadow prompt` naming이 stale하다. 현재 코드 owner는 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=False` 기본 OFF 상태의 readiness plumbing이며, runtime loader / feature flag / cache-key 분리 / provenance logging은 구현됐지만 same-day live prompt enable은 아직 열지 않는다.

| 단계 | 상태 | 의미 | ON 기준 | 금지사항 |
| --- | --- | --- | --- | --- |
| `ADM-1 report-only` | 현재 ON | 장후 `holding_exit_decision_matrix_YYYY-MM-DD.json/md` 생성 | schema, `matrix_version`, `prompt_hint`, `hard_veto`, provenance 확인 | AI prompt/응답/주문 변경 금지 |
| `ADM-2 shadow prompt` | 현재 OFF (historical naming only) | 전일 matrix를 다음 장전 로드하고 shadow-only prompt context로 주입 | token budget, cache key 분리, Gemini/OpenAI/DeepSeek parity, action drift 로그 준비 | live AI 응답 채택 금지 |
| `ADM-3 advisory nudge` | 현재 OFF | matrix가 `참고 권고`로 live prompt에 들어가지만 hard override는 하지 않음 | ADM-2에서 drift가 설명 가능하고 `GOOD_EXIT/MISSED_UPSIDE/soft_stop` 악화가 없을 때 | matrix 단독 청산/추가매수 금지 |
| `ADM-4 weighted live` | 현재 OFF | AI 응답 후처리 또는 confidence weight에 제한 반영 | bucket sample floor, confidence-adjusted edge, rollback guard, single owner가 닫힐 때 | 다른 보유/청산 canary와 같은 stage에서 중복 live 금지 |
| `ADM-5 policy gate` | 현재 OFF | 특정 bucket에서 강한 veto/allow gate로 사용 | 며칠 이상 반복 표본과 hard veto 정밀도 검증, owner 승인, 즉시 OFF env 필요 | 초기 운영에서 바로 진입 금지 |

운영 규칙:

1. matrix는 장중 self-updating 금지다. 전일 장후 산정본을 다음 장전 immutable context로만 로드한다.
2. ADM-2 이상을 켜려면 별도 runtime flag가 필요하다. 현재 코드는 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED` 토글과 runtime provenance를 가지지만 기본값은 OFF다. flag OFF는 baseline cohort, flag ON은 candidate cohort로 보고 non-holding/shared prompt surface는 excluded cohort로 둔다.
3. ADM-3 이상은 `soft_stop_micro_grace`, `REVERSAL_ADD`, `bad_entry_refined_canary`와 같은 보유/청산 stage live owner 충돌 여부를 먼저 확인한다.
4. live 전환 판정은 손실 억제가 아니라 `COMPLETED + valid profit_rate`, `GOOD_EXIT/MISSED_UPSIDE`, soft stop tail, 추가매수 기회비용을 함께 본다.

### OFF 또는 guarded-off: ON 시점/기준

| 축 | 현재 OFF 근거 | ON 시점 | ON 기준 |
| --- | --- | --- | --- |
| `soft_stop_expert_defense v2` | `SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=False`; 2026-04-30 same-day 수집 종료 | 5/4 장후 이후 refined canary 결과 확인 후, 빠르면 5/6 이후 별도 checklist | v2 그대로 재가동 금지. `absorption/veto/arbitration` 중 하나의 단일 조작점, rollback guard, cohort tag, restart plan이 닫힐 때만 ON |
| `soft_stop_micro_grace_extend` | `SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_ENABLED=False` 예비 파라미터 | `soft_stop_micro_grace 20초` 표본이 비악화인데 rebound capture가 부족할 때 | hard stop/same-symbol/미체결 악화 없음, 추가 10초 유예의 would-have-improved 근거가 있어야 함 |
| `latency_quote_fresh_composite` | 2026-04-29 08:29 OFF + restart 완료 | 현 entry owner 교체가 필요할 때만 | `mechanical_momentum_latency_relief`를 OFF하고 단일축 replacement 승인, submitted 회복 목표와 rollback guard 필요 |
| `latency_signal_quality_quote_composite` | 2026-04-29 12:50 효과 미약 종료 | 재개 기본 없음 | signal>=90 경로에서 실제 pass candidate가 확인되고 현 entry owner와 충돌하지 않을 때만 재정의 |
| `latency_spread_relief` | replacement 완료 후 parking | spread-only blocker가 다시 주병목일 때 | spread blocker가 제출 전 terminal miss의 주원인이고 broad relief가 아닌 단일축 rollback 기준이 있을 때 |
| `latency_ws_jitter_relief` | 2026-04-27 미개선 종료 | ws jitter가 독립 주병목으로 재확인될 때 | quote freshness/other danger와 분리된 표본, restart/rollback plan 필요 |
| `latency_other_danger_relief` | 2026-04-27 미개선 종료 | other_danger residual이 다시 주병목일 때 | broad fallback 금지. danger reason별 단일축으로 재분해해야 함 |
| `latency_guard_canary` | broad fallback override OFF | 원칙상 재개 금지 | broad override가 아니라 신규 세분화 축으로만 재등록 |
| `latency_fallback` / `split_entry` | fallback/split-entry 폐기 확정 | 재개 계획 없음 | 재개하려면 기존 축 복구가 아니라 새 workorder, 새 cohort, 새 rollback guard 필요 |
| `generic AVG_DOWN` | runtime removed | 재개 계획 없음 | 단순 낙폭형 물타기는 EV/귀속 품질이 거칠어 재오픈 금지. scalping `AVG_DOWN` add_type은 `REVERSAL_ADD` 체결 귀속명으로만 유지 |
| `SCALPING_PYRAMID_ZERO_QTY_STAGE1` | active bugfix | `2026-05-04` 사용자 지시로 스캘핑 PYRAMID 1주 floor 기본 ON | 신규 진입 cap 확대가 아니라 `buy_qty=1 -> int(1 * 0.50)=0` 실행불능 제거다. 예수금/position cap이 1주 이상 허용할 때만 `floor_applied=True`로 1주 주문을 허용하고, `initial-only`/`pyramid-activated`는 계속 분리한다. |
| `OpenAI Responses WS` | `OPENAI_RESPONSES_WS_ENABLED=False`, transport `http` | 5/4 shadow 결과와 parity acceptance 통과 후 | request_id mismatch=0, late_discard=0, http fallback<=2%, parse_fail<=0.5%, timeout reject<=1% |
| `OpenAI dual persona` | `OPENAI_DUAL_PERSONA_ENABLED=False` | AI A/B 의제를 다시 열 때 | entry/holding owner 안정화 후, 추가 API/지연 비용과 EV 비교 cohort가 문서화될 때 |
| `OpenAI schema registry` / deterministic config | `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`, `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=False` | endpoint contract acceptance 완료 후 | schema gap 0, parse failure 기준 통과, rollback env와 endpoint별 scope 고정 |
| `swing_one_share_real_canary` | 스윙 실주문 execution 품질 수집은 아직 승인축만 정의 | `swing_runtime_approval`이 EV 후보를 만들고, 별도 사용자 승인 artifact가 존재하는 다음 장전 | `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True` 기본값을 유지한 채 승인된 극소수 후보에만 1주 실제 BUY/SELL을 허용. max 1 new/day, max 3 open, max total notional 300,000 KRW, same-symbol active 1개, phase0 scale-in 실주문 금지, broker receipt/slippage/fill quality real-only 기록 |

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

### 3.0 Canary Live 전환 기준

canary를 `기본 live owner` 또는 `운영 기본값`으로 전환하려면 아래가 같은 판정셋에 함께 닫혀야 한다.

1. `단일 조작점`: 어떤 flag/rule이 live에 영향을 줬는지 코드와 로그에서 1:1 복원 가능
2. `cohort 복원성`: `applied/not-applied`, `baseline`, `excluded`가 raw event나 compact report에서 분리 가능
3. `정량 기준`: 최소 `N_min`, 핵심 metric, `COMPLETED + valid profit_rate`, `submitted/full/partial` 등 해당 단계 지표가 문서에 고정
4. `비악화 조건`: 체결 품질, 손익, missed upside, hard/protect safety, 주문 실패가 허용 guard를 넘지 않음
5. `rollback 준비`: 즉시 OFF env 또는 restart 절차, rollback owner, 판정 시각이 문서에 존재
6. `오염 점검`: same-stage 다른 owner, stage-disjoint 다른 축, `initial/pyramid`, `full/partial`, `REVERSAL_ADD` 같은 혼입이 분리돼 있음

위 여섯 항목 중 하나라도 비면 `baseline-promote`나 `기본 live` 전환이 아니라 `active-canary 유지`, `observe-only`, `guarded-off` 중 하나로 남긴다.

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
| `real-canary-decision` | 기본 dry-run/sim 체계에서 별도 승인된 1주 이하 실제 주문 모집단 | EV는 combined에 들어갈 수 있지만, 주 목적은 broker execution/receipt/fill 품질 수집이다. 전체 live 전환 근거로 단독 사용 금지 |
| `operating-override-decision` | 운영상 same-day 또는 carry-over override가 실제 live 판단을 바꾼 모집단 | baseline과 분리 비교하되, alpha canary 성과와 합산하지 않고 override owner 기준으로 keep/OFF를 판정 |
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
2. `candidate live cohort`: 예) `other_danger relief applied cohort`, `soft_stop qualifying cohort`
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
| `buy_recovery_canary applied cohort` | `guarded-off` | `WAIT65~79` live canary 효과/rollback 판정 | 코드 경로는 회귀/재개 가능성 때문에 유지하되, Plan Rebase 단일 live canary 기간에는 OFF로 유지. 재개 시 새 승인 항목과 rollback guard 필요 | `2026-04-21~23 checklist` |
| `wait6579_probe_canary_applied` | `guarded-off` | 소량 probe 적용 표본 분리 | `soft_stop_micro_grace` live 관찰 중에는 OFF. 재개하려면 단일 live canary slot을 다시 확보하고 `submitted/full/partial` 회복 기준을 새로 문서화 | `wait6579_ev_cohort`, `2026-04-21 checklist` |
| `latency_quote_fresh_composite` | `observe-only` | 2026-04-29 이전 live였던 quote freshness 복합 residual 축의 historical/reference cohort | `2026-04-29 08:29 KST` OFF + restart 이후에는 historical/reference 및 감리 비교용으로만 유지. 재개 시 새 승인 항목과 rollback guard 필요 | `Plan Rebase`, `2026-04-29 checklist` |
| `latency_signal_quality_quote_composite` | `observe-only` | `latency_quote_fresh_composite` replacement로 same-day 시험한 예비 복합축의 post-restart cohort | `2026-04-29 12:21~12:50 KST` replacement cohort 분리와 효과 미약 판정 보존이 끝나면 historical-only로 유지. baseline/live 승격 금지 | `Plan Rebase`, `2026-04-29 checklist` |
| `mechanical_momentum_latency_relief` | `operating-override-decision` | score 70대 mechanical fallback 상태를 포함하는 현재 entry replacement live cohort | `AI score 50`은 5/4 buy-hold override로 제외한다. `submitted` 전까지는 진입병목 회복으로 보고, `submitted` 이후는 `full/partial` 체결 품질과 `HOLDING/exit_rule/COMPLETED + valid profit_rate`로 BUY 신호 적정성을 분리 판정한 뒤 keep/OFF/후속 replacement를 결정한다. hard baseline 승격과 분리한다 | `Plan Rebase`, `2026-04-29 checklist` |
| `dynamic_entry_price_resolver_p1` | `baseline-decision` | reference target과 defensive price 권한을 분리한 기본 entry price resolver cohort | `reference_target_applied/rejected`, `submitted_order_price`, timeout profile, `price_below_bid_bps`가 안정적으로 복원되고 P2 canary의 fallback baseline으로 고정될 때 유지 | `2026-05-04 checklist`, `entry price audit follow-up` |
| `dynamic_entry_ai_price_canary_p2` | `active-canary-decision` | submitted 직전 Tier2 AI가 live quote/microstructure를 보고 최종 주문가를 조정하는 entry price canary cohort | `USE_DEFENSIVE/REFERENCE/IMPROVE_LIMIT/SKIP` applied 표본과 P1 fallback 표본을 분리해 체결 품질, 미체결 방치, `COMPLETED + valid profit_rate`를 확인한 뒤 유지/종료/승격을 결정 | `2026-05-04 checklist`, `entry price audit follow-up` |
| `post-restart cohort` | `active-canary-decision` | replacement 이후 same-day 제출 회복 관찰 | replacement 당일 판정이 닫히고 후속 축이 새 `post-change` cohort로 넘어가면 종료. 익일 이후 지속 baseline으로 쓰지 않음 | `2026-04-29 checklist` |
| `soft_stop qualifying cohort` | `provisional-stage-disjoint` | 보유/청산 live 예외 canary 후보 | `soft_stop_rebound_split` 승인 또는 보류+재시각이 닫히고, qualifying rule이 live 조작점으로 승격되거나 폐기될 때 종료 | `2026-04-27 checklist` |
| `soft_stop_micro_grace` | `active-canary-decision` | soft_stop 최초 터치 후 짧은 휩쏘 확인유예 | `scalp_soft_stop_pct` 손실/반등 개선이 확인되어 baseline 승격되거나, emergency/hard_stop 악화 또는 soft_stop 지연 부작용으로 OFF 확정될 때 종료 | `2026-04-27 checklist` |
| `soft_stop_expert_defense` | `observe-only` | 2026-04-30 same-day v2 수집에서 stop arbitration/thesis veto/orderbook absorption/shadow 전략을 한 owner로 묶은 보유/청산 방어망 | 다음 재승인 전 기본 OFF. `soft_stop_absorption_*`, `soft_stop_expert_shadow`, `adverse_fill_observed`는 다음 방어망 설계 근거로만 유지하고 live 유예/청산 변경에는 쓰지 않는다 | `2026-04-30 checklist` |
| `reversal_add` | `active-canary-decision` | 유효 진입 초반 눌림을 1주 소형 추가매수로 회수하는 보유/청산 canary | `reversal_add_candidate`, `reversal_add_blocked_reason`, `reversal_add_gate_blocked`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_used`, 후속 `soft_stop/trailing/COMPLETED`로 손익/soft stop tail 개선 여부가 닫히면 유지/종료/승격 결정 | `Plan Rebase`, `2026-04-30 checklist` |
| `bad_entry_block` | `observe-only` | never-green/AI fade 불량 진입 후보를 실전 차단 전 관찰 | 2026-04-30 기준 표본 수는 충분하지만 `GOOD_EXIT` 제거 위험이 남아 단순 live block은 금지. observe 로그는 refined canary의 후보/비후보 비교군으로 유지 | `Plan Rebase`, `2026-04-30 checklist` |
| `bad_entry_refined_canary` | `observe-only` | never-green/AI fade 후보의 lifecycle join readiness 관찰 | `bad_entry_refined_candidate`는 runtime provisional signal로만 남기고, `record_id -> post_sell_evaluations` join 완료 전에는 live go/no-go에 쓰지 않는다. joined sample floor, preventable count, false-positive risk가 닫힌 뒤에만 bounded canary 재승격을 검토한다 | `2026-05-12 checklist` |
| `hard_stop_whipsaw_aux` | `observe-only` | severe-loss guard 보조 관찰 | 하드스탑을 보조 관찰로만 둔다는 원칙이 유지되는 동안 유지. `MISSED_UPSIDE/GOOD_EXIT/NEUTRAL`과 반등 지표가 독립 판단가치를 잃거나 hard stop 완화 의제가 공식 폐기되면 제거 | `Plan Rebase`, `2026-04-27 checklist` |
| `same_symbol_reentry` | `observe-only` | 동일종목 재진입 손실/guard 필요성 관찰 | `same_symbol_reentry_loss_count`가 독립 guard 후보성을 잃거나, soft stop/position context 축에 완전히 흡수되어 별도 재진입 cohort가 필요 없을 때 제거 | `holding_exit_observation`, `2026-04-27 checklist` |
| `trailing_continuation` | `observe-only` | upside capture 개선 후보 관찰 | `MISSED_UPSIDE rate >= 60%`, `GOOD_EXIT rate <= 30%`로 2순위 live 후보 요건을 충족해 canary로 승격되거나, 반대로 upside 개선 후보성이 약해져 후순위 폐기가 확정되면 제거/재분류 | `holding_exit_observation`, `2026-04-27 checklist` |
| `initial-only` | `observe-only` | 신규 진입만의 체결/손익/청산 품질 분리 | 1주 cap 유지/해제 승인 요청 여부와 무관하게 initial-only 손익/soft stop tail과 추가매수 후보의 영향을 분리한다. initial/pyramid가 더 이상 다른 EV를 보이지 않아 분리 해석 가치가 사라질 때만 제거 | `2026-04-29`, `2026-04-30 checklist`, `2026-05-11 checklist` |
| `pyramid-activated` | `observe-only` | 추가매수 활성 표본 분리 | 1주 cap 유지/해제 승인 요청 여부와 무관하게 pyramid activated 표본과 손익/청산 품질을 분리한다. 별도 특성이 없다고 확인될 때만 제거 | `2026-04-29`, `2026-04-30 checklist`, `2026-05-11 checklist` |
| `full_fill` | `observe-only` | 체결 품질 우수 표본 분리 | `partial_fill`과 EV/청산 품질 차이가 더 이상 의사결정 의미를 잃지 않는 한 유지. full/partial 합산 허용 정책으로 바뀌기 전에는 제거 금지 | `Plan Rebase`, performance/report/checklist |
| `partial_fill` | `observe-only` | partial 전용 손익/재베이스/soft-stop 악화 관찰 | partial 악화 여부가 더 이상 독립 리스크가 아니라고 확인되기 전까지 유지. full/partial 합산 정책 변경 전에는 제거 금지 | `Plan Rebase`, performance/report/checklist |
| `initial_entry_qty_cap_1share` | `active-canary-decision` | 신규 BUY 초기 수량 tail 제한과 holding/exit 원인귀속 보존 | 2026-05-09 후속 사용자 지시로 기본 ON 복귀. 해제는 `position_sizing_cap_release`가 approval request를 만들고 사용자가 승인할 때만 가능하다 | `2026-04-30 checklist`, `2026-05-11 checklist` |
| `initial_entry_qty_cap_3share_candidate` | `historical-reference` | 3주 cap 전환 승인조건 관찰 | 현재 승격 후보가 아니라 cap 정책 비교 근거로만 유지한다. 확대는 2주/3주 ladder가 아니라 cap release approval flow로만 다룬다 | `2026-04-30 checklist`, `2026-05-11 checklist` |
| `statistical_action_weight` | `observe-only` | 가격대/거래량/시간대별 `exit_only`/`avg_down_wait`/`pyramid_wait` 성과 비교 | sample-ready가 되면 threshold weight 입력으로 연결하되, 직접 live owner로 승격하지 않는다. 단순 평균이 아니라 `confidence_adjusted_score`와 `policy_hint`로만 해석하고, live 적용은 별도 단일축 canary와 rollback guard가 생길 때만 가능 | `threshold_cycle`, `2026-05-06 checklist` |
| `ai_cache_hit_miss` | `observe-only` | gatekeeper/holding AI cache hit vs miss 영향도 관찰 | structured join 필드가 `submitted/full/partial/COMPLETED`와 안정적으로 연결될 때까지 live go/no-go 입력 금지 | `2026-04-29 checklist` |
| `execution_receipt_binding_quality` | `observe-only` | WS 실제체결과 active order binding 정합성 관찰 | BUY/SELL `EXEC_IGNORED` 원인이 order number race인지 visibility 문제인지 닫힐 때까지 EV 판정 전제 품질축으로 유지 | `2026-04-29`, `2026-04-30 checklist` |
| `gemini_schema_registry_flag_off` | `observe-only` | Gemini response schema registry의 flag-off contract 관찰 | `holding_exit_v1` contract gap이 닫히고 live enable 항목이 별도 승인되기 전까지 flag-off 유지. `eod_top5_v1`은 2026-05-21 EOD TOP5 기능 제거로 registry 범위에서 제외 | `2026-04-29`, `2026-04-30 checklist`, `2026-05-21 cleanup` |
| `deepseek_retry_acceptance_flag_off` | `observe-only` | DeepSeek retry/backoff acceptance snapshot 관찰 | `api_call_lock`, retry log visibility, live-sensitive sleep guard가 문서/테스트로 닫히기 전까지 live enable 금지 | `2026-04-29`, `2026-04-30 checklist` |
| `openai_responses_ws_shadow_flag_off` | `observe-only` | OpenAI Responses WS transport parity/load/timeout/http-fallback 관찰 | `request_id mismatch=0`, `late_discard=0`, `http fallback<=2%`, `parse_fail<=0.5%`가 shadow 기준으로 닫히고 별도 entry transport canary가 승인되기 전까지 flag-off 유지 | `2026-05-04 checklist` |
| `swing_live_order_dry_run` | `observe-only` | 스윙 선정-진입-보유-추가매수-청산 live lifecycle을 실주문 없이 관찰 | `swing_sim_*`, `actual_order_submitted=false`, closed lifecycle이 `swing_runtime_approval`과 daily EV combined 입력으로 안정 연결될 때 유지. 실주문 전환과 별개 | `2026-05-11 checklist`, `time-based runbook` |
| `swing_runtime_approval` | `approval-request` | 스윙 threshold/logic 후보를 `proposal -> approval_required -> approved_live(dry-run)`로 연결 | hard floor + trade-off score 기준으로 요청 생성. approval artifact 없이는 env 반영 금지, env 반영 후에도 dry-run 유지 | `2026-05-11 checklist`, `threshold_cycle README` |
| `swing_one_share_real_canary` | `real-canary-decision` | 스윙 broker execution/receipt/fill 품질을 1주 실주문으로 수집 | 기본 OFF. `swing_runtime_approval` 이후 별도 승인 artifact가 있을 때만 phase0 시작. max 1 new/day, max 3 open, max total notional 300,000 KRW, phase0 scale-in 실주문 금지, dry-run 외 후보 실주문 0건을 rollback guard로 둔다 | `Plan Rebase`, `time-based runbook`, `2026-05-11 checklist` |
| `scalp_sim_candidate_window_expansion` | `sim-only-cohort` | WAIT/blocked 스캘핑 후보를 실제 주문 없이 virtual lifecycle에 편입 | 사용자 operator override로만 ON. `actual_order_submitted=false`, `broker_order_forbidden=true`, BUY 텔레그램 suppression 유지. real execution 품질이나 broker submit 승인 근거로 쓰지 않는다 | `Plan Rebase`, `2026-05-19 checklist`, `threshold runtime env` |
| `scalp_sim_ai_budget_manager` | `sim-only-cohort` | 확대된 sim holding의 OpenAI 호출량을 상태변화/예산/deferred로 제어 | real holding, provider route, BUY/submit threshold 변경 권한 없음. critical bypass 과다는 별도 review/checklist로 닫는다 | `Plan Rebase`, `2026-05-19 checklist`, `scalp_sim_ai_deferred_review` |
| `scalp_sim_scale_in_window_expansion` | `sim-auto-approved-sim-actuator` | Expand the sim-only additional-buy window to collect matrix `scale_in` arm samples | The postclose artifact defaults to `approved=true` with `approval_state=sim_auto_approved` only after the lifecycle matrix source report is readable; next PREOPEN env applies only sim-source policy values. Real scale-in, cap release, hard-safety relaxation, provider changes, and bot restart are forbidden | `Plan Rebase`, `report-based automation traceability`, `scalp_sim_scale_in_window_expansion_YYYY-MM-DD.json` |

inventory 운영 규칙은 아래로 고정한다.

1. 위 표에 없는 cohort가 신규 문서/코드/리포트에 등장하면, 같은 change set에서 이 표에 추가하고 상태를 먼저 잠근다.
2. 표에 있는 cohort라도 성격이 바뀌면 `상태 변경 + why + 허용 메트릭 + 금지 집계`를 같은 턴에 같이 갱신한다.
3. `baseline-decision`, `active-canary-decision`, `provisional-stage-disjoint`는 빈 이름으로 운영하지 않는다. 임시 표현(`post-change`, `new cohort`)만 적고 상태를 안 잠그는 것은 무효다.
4. `historical-only` 문서에만 남고 `src/`/active checklist/현재 기준 리포트 어디에도 연결되지 않는 cohort는 inventory에서 제거한다. 필요하면 archive나 과거 report에서만 유지한다.
5. `observe-only` cohort는 `유지 종료 시점/달성요건` 없이 무기한 두지 않는다. 제거, 승격, 상위 축 흡수 중 하나의 종료 조건이 반드시 있어야 한다.

---

### 3.4 스윙 1주 Real Canary Cohort 잠금

`swing_one_share_real_canary`는 스윙 dry-run을 해제하는 축이 아니라, sim/combined가 볼 수 없는 broker execution 품질을 real source로 채우는 극소 수량 canary다.

| 항목 | 기준 |
| --- | --- |
| baseline cohort | `swing_live_order_dry_run`, `swing_sim_*`, `actual_order_submitted=false` |
| candidate real cohort | `swing_one_share_real_canary`, `actual_order_submitted=true`, `qty=1`, `canary_qty_cap=1` |
| observe-only cohort | `swing_runtime_approval`의 `approval_required` 후보 중 real canary 미승인 후보 |
| excluded cohort | fallback diagnostic 추천, DB load gap, critical instrumentation gap, severe downside guard fail, same-stage owner conflict, phase0 scale-in/PYRAMID/AVG_DOWN 실주문 |
| inclusion rule | `swing_runtime_approval` hard floor 통과, EV trade-off score 통과, 사용자 approval artifact 존재, 장전 preopen apply 시점, 동일 종목 active real canary 없음 |
| exposure guard | phase0 기준 `max_new_entries_per_day=1`, `max_open_positions=3`, `max_total_notional_krw=300000`, `qty=1` |
| allowed metrics | broker receipt, order number binding, submit/reject, fill ratio, partial/full, slippage, cancel/timeout, sell receipt, realized PnL, combined EV contribution |
| forbidden aggregations | sim fill quality와 real fill quality 합산, 1주 real canary 성과만으로 스윙 전체 실주문 전환, scale-in 실주문 품질을 phase0 BUY/SELL 품질과 합산 |
| rollback owner | `swing_one_share_real_canary` |
| rollback trigger | approval artifact 밖 실주문 1건, qty > 1, dry-run global 해제, receipt/order number mismatch, sell failure, price guard breach, daily new/open/notional cap 초과, actual_order_submitted provenance 누락 |

운영 해석:

1. `combined`는 EV 후보와 승인 요청 생성에 계속 사용한다.
2. `real-canary`는 broker execution 품질을 채우는 데이터 수집축이다.
3. 1주 real canary가 통과해도 스윙 실주문 전체 전환은 별도 2차 계획/승인 없이는 금지한다.
4. phase0에서는 스윙 추가매수, AVG_DOWN, PYRAMID 실주문을 열지 않는다. 보유 중 real canary 포지션의 청산 SELL만 실제 주문으로 닫는다.

---

## 4. 판정표

아래 판정은 `src/` 기준 실제 런타임/리포트 경로를 기준으로 잠근다.

### 4.0 `src/engine + constants` 전수 inventory

| 축 | 분류 | live 영향도 | 비고 |
| --- | --- | --- | --- |
| `dual_persona` | `observe-only` | `guarded-off` | gatekeeper/overnight dual-persona shadow |
| `watching_shared_prompt_shadow` | `observe-only` | `guarded-off` | WATCHING shared prompt 비교 shadow |
| `watching_prompt_75_shadow` | `remove` | `guarded-off` | 제거 완료, historical 판정만 유지 |
| `hard_time_stop_shadow` | `remove/guarded-off` | `none` | 5/4 기본 OFF. historical/replay label만 유지 |
| `ai_holding_fast_reuse_band` | `telemetry` | `live fast-reuse cadence` | HOLDING review/skip 경계 telemetry. shadow-only 축 아님 |
| `same_symbol_soft_stop_cooldown_shadow` | `remove/guarded-off` | `none` | 5/4 `same_symbol_loss_reentry_cooldown` live 가드로 대체 |
| `partial_only_timeout_shadow` | `remove/guarded-off` | `none` | 5/4 기본 OFF. 재개 시 새 report-only 항목 필요 |
| `split_entry_rebase_integrity_shadow` | `remove` | `guarded-off` | split-entry 폐기 정합화로 runtime shadow 기본 OFF |
| `split_entry_immediate_recheck_shadow` | `remove` | `guarded-off` | split-entry 폐기 정합화로 runtime shadow 기본 OFF |
| `strength_shadow_feedback` | `observe-only` | `none` | dynamic strength 후보 장후 평가 |
| `buy_recovery_canary` | `active-canary` | `guarded-off` | `WAIT65~79` BUY 회복축 |
| `wait6579_probe_canary` | `active-canary` | `guarded-off` | soft_stop live canary 관찰 중 entry probe OFF |
| `fallback_qty_canary` | `remove` | `guarded-off` | historical label only, live fallback 경로와 함께 종료 |
| `latency_guard_canary` | `active-canary` | `guarded-off` | broad fallback override legacy 축 |
| `latency_quote_fresh_composite` | `observe-only` | `guarded-off` | 2026-04-29 08:29 KST OFF + restart 완료. historical/reference 축 |
| `latency_signal_quality_quote_composite` | `observe-only` | `guarded-off` | 2026-04-29 12:21~12:50 KST same-day replacement 후 효과 미약 종료 |
| `mechanical_momentum_latency_relief` | `operating-override` | `limited-live` | current entry live replacement operating override. `submitted` 전은 병목, 이후는 fill quality + BUY signal quality observation |
| `soft_stop_expert_defense` | `observe-only` | `guarded-off` | 2026-04-30 same-day v2 수집 종료. 다음 재승인 전 live 유예/청산 변경 없음 |
| `initial_entry_qty_cap_1share` | `active-canary` | `limited-live` | current initial entry size guard. 2주/3주 확대는 별도 승인 전 observe-only |
| `reversal_add` | `active-canary` | `limited-live` | valid-entry early pullback recovery. 2026-05-09 후속 사용자 지시로 1주 cap은 ON이며, 해제는 `position_sizing_cap_release` 사용자 승인 전까지 금지한다. current owner is blocker narrowing (`pnl -> hold -> gate`) |
| `bad_entry_block` | `observe-only` | `none` | never-green/AI fade 후보 분류. 표본 부족이 아니라 precision/GOOD_EXIT 예외 설계가 병목이었고, refined canary의 비교군으로 유지 |
| `bad_entry_refined_canary` | `observe-only` | `guarded-off` | `2026-05-12` postclose 기준 `candidate_records=1`, `post_sell_joined_records=0`, `preventable_bad_entry_candidate_records=0`이라 lifecycle join readiness가 닫히지 않았다. naive block 비교군과 joined evidence를 분리하는 report-only hold로 유지한다 |
| `statistical_action_weight` | `observe-only` | `none` | completed trade와 `exit_signal`/`sell_completed`/`scale_in_executed` compact stage를 묶는 장후 행동가중치 리포트. live runtime mutation 없음 |
| `stat_action_decision_snapshot` | `observe-only` | `none` | HOLDING 판단 순간의 후보/선택/차단 행동 수집 이벤트. `statistical_action_weight`의 selection-bias 보정 입력이며 기본 30초 rate-limit로 IO를 제한 |
| `ai_cache_hit_miss` | `observe-only` | `none` | structured join gap으로 보조지표 유지 |
| `execution_receipt_binding_quality` | `observe-only` | `none` | SK이노베이션 BUY/SELL `EXEC_IGNORED` 사례로 runtime truth 품질축 유지 |
| `gemini_schema_registry_flag_off` | `observe-only` | `guarded-off` | flag-off contract/load observability. live enable 아님 |
| `deepseek_retry_acceptance_flag_off` | `observe-only` | `guarded-off` | flag-off retry acceptance observability. live enable 아님 |
| `openai_responses_ws_shadow_flag_off` | `observe-only` | `guarded-off` | OpenAI Responses WS parity/timeout/fallback observability. live enable 아님 |
| `orderbook_stability_observation` | `observe-only` | `none` | FR/quote-age/print-alignment 관찰. live gate 아님 |
| `swing_live_order_dry_run` | `observe-only` | `dry-run-live` | 스윙 lifecycle은 실행하지만 브로커 주문은 차단. sim/combined EV calibration 입력 |
| `swing_runtime_approval` | `approval-request` | `dry-run-live` | EV trade-off 기준 approval request 생성. approval artifact 없이는 env 반영 없음 |
| `swing_one_share_real_canary` | `real-canary` | `approval-required guarded-off` | 스윙 broker execution 품질 수집용 1주 실주문 후보. 전체 dry-run 해제 아님 |
| `spread_relief_canary` | `active-canary` | `guarded-off` | parking 상태 |
| `ws_jitter_relief_canary` | `active-canary` | `guarded-off` | same-day 종료된 replacement 축 |
| `other_danger_relief_canary` | `active-canary` | `guarded-off` | 2026-04-27 13:00 미개선 종료 |
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

- 판정: `remove/guarded-off`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Low`
  - 이유: 신규 alpha shadow 금지 원칙과 5/4 runtime shadow purge 기준에 따라 기본 OFF로 내렸다. 과거 report/UI label은 historical 해석용으로만 남긴다.
  - 상향 조건: `soft_stop_rebound_split`과 별도로 `time-based exit` 후보를 다시 검토할 때
  - 하향 조건: `post_sell`/`trade_review`만으로 동일 판단이 충분하고, ghost event 점검도 더 이상 필요 없을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
  - 청산 후 결과는 대체되지만, 장중 `would-have-fired` 관측은 완전 대체가 어렵다.
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=False`가 기본값이다.
  2. trade review/performance tuning UI의 historical label은 과거 이벤트를 읽기 위한 backward compatibility다.
  3. 다시 보려면 shadow 재개가 아니라 새 report-only/checklist owner로 정의한다.
- 다음 액션:
  1. runtime 기본 OFF 유지
  2. 실주문 승격 후보로 두지 않는다
  3. UI/report의 historical label 정리는 `CodeDebt0506`에서 backward-compatible rename으로 처리한다

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

### 4.4 `ai_holding_fast_reuse_band`

- 판정: `telemetry`
- live 영향도: `live fast-reuse cadence`
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
  1. `ai_holding_reuse_bypass`와 짝을 이루는 fast-reuse 경계 telemetry다.
  2. holding fast reuse를 다시 건드릴 때 band 관측이 있으면 원인귀속이 더 쉬워진다.
  3. 5/4부터 stage 명칭을 `ai_holding_shadow_band`에서 `ai_holding_fast_reuse_band`로 바꿔 shadow-only 축과 분리했다.
- 다음 액션:
  1. shadow-only가 아니라 live fast-reuse telemetry로 문서 기준을 고정
  2. 유지 리포트 범위는 `trade_review`와 raw holding pipeline 해석으로 제한
  3. historical `ai_holding_shadow_band` label은 report backward compatibility로만 둔다

### 4.4A `same_symbol_soft_stop_cooldown_shadow`

- 판정: `remove/guarded-off`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Low`
  - 이유: 5/4 유안타증권 반복손실로 `same_symbol_loss_reentry_cooldown` live 운영가드가 열렸으므로 shadow 가설은 닫는다.
  - 상향 조건: soft stop 휩쏘와 same-symbol 재진입 손실을 같이 튜닝할 때
  - 하향 조건: same-symbol cooldown live 후보를 접을 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED=False`가 기본값이다.
  2. live 차단 owner는 `same_symbol_loss_reentry_cooldown`이며, 최종 형태는 5/6 복합 threshold 후보로 분리한다.
- 다음 액션:
  1. runtime 기본 OFF 유지
  2. post-loss reentry 분석은 `YuantaDowntrendReentry0504-Postclose`, `DowntrendReentryComposite0506`에서 소유한다

### 4.4A-1 `soft_stop_micro_grace`

- 판정: `active-canary-decision`
- live 영향도: `limited`
- 튜닝 모니터링 가치: `High`
  - 이유: 4월 `scalp_soft_stop_pct` 61건 중 10분 내 매도가 재상회 `57건(93.4%)`, +0.5% 이상 반등 `43건(70.5%)`라 soft stop 직후 휩쏘 완화의 직접 조작점이다.
  - 상향 조건: `soft_stop_micro_grace` 적용 표본에서 `scalp_soft_stop_pct` 손실 tail이 줄고, hard stop 전환/미체결/동일종목 재진입 손실이 증가하지 않을 때
  - 하향 조건: `scalp_hard_stop_pct` 또는 emergency break가 늘거나, grace 후 더 나쁜 가격 청산이 반복될 때
- EV 판정 기여도: `High`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. `whipsaw confirmation`은 AI/호가 재확인을 추가해 entry latency와 유사한 지연/누락을 다시 만들 수 있어 1차 live 조작점에서 제외했다.
  2. `SCALP_SOFT_STOP_MICRO_GRACE_SEC=20`, `SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0`, hard stop `-2.5%`로 유예 폭을 제한했다.
- 다음 액션:
  1. `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill/partial_fill`을 분리 관찰
  2. hard stop 전환이나 grace 후 악화가 확인되면 canary OFF

### 4.4A-2 `reversal_add`

- 판정: `active-canary-decision`
- live 영향도: `limited-live`
- 튜닝 모니터링 가치: `High`
  - 이유: `micro grace 20초`는 손절 시점 지연에 그친다. `reversal_add`는 진입 판단이 틀리지 않았고 초반 눌림만 과도한 케이스를 1주 추가매수로 회수하는 별도 전략 가설이다.
  - 상향 조건: `reversal_add_used` cohort에서 `COMPLETED + valid profit_rate`가 baseline 대비 비악화이고, `scalp_soft_stop_pct` 전환율과 hard stop 전환이 늘지 않을 때
  - 하향 조건: `reversal_add_used` 후 soft stop/hard stop으로 이어지거나, cohort 평균 손익이 `<= -0.30%`일 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. 기존 `evaluate_scalping_reversal_add()`는 AI 회복, 저점 미갱신, 매수압/틱가속/micro VWAP 조건을 이미 갖고 있어 새 진입축이 아니라 보유 중 회수축으로 제한할 수 있다.
  2. `REVERSAL_ADD_SIZE_RATIO=0.33`이 0주가 될 수 있으므로 `REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=True`로 최소 1주 floor를 허용한다.
  3. 추가매수 체결 후에는 `soft_stop_micro_grace` 상태를 초기화해 기존 손절 유예 상태가 새 평단 판단을 오염시키지 않게 한다.
- 다음 액션:
  1. `reversal_add_candidate`, `reversal_add_blocked_reason`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_used`, 후속 `soft_stop/trailing/COMPLETED`를 분리한다.
  2. 내일 오전 1건이라도 체결되면 anchor case로 고정하고, 체결이 없으면 `zero_qty/position_at_cap/supply_conditions_not_met/ai_not_recovering` 중 병목을 닫는다.

### 4.4A-3 `bad_entry_block`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `High`
  - 이유: soft stop이 많은 종목을 무조건 더 버티거나 물타기할 수는 없다. never-green, 낮은 peak, 낮은 AI 상태로 60초 이상 손실이 지속되는 표본은 애초에 막아야 할 불량 진입 후보일 수 있다.
  - 상향 조건: `bad_entry_block_observed` 표본이 10건 이상이고 후속 `soft_stop/hard_stop` 전환이 높으며 `GOOD_EXIT/MISSED_UPSIDE` 놓침 위험이 낮을 때
  - 하향 조건: observe 후보가 이후 자주 회복하거나 `MISSED_UPSIDE`로 끝나 live block이 기회비용을 키울 가능성이 확인될 때
- EV 판정 기여도: `High`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. 초기 조건은 `held_sec>=60`, `profit_rate<=-0.70%`, `peak_profit<=+0.20%`, `current_ai_score<=45`로 제한한다.
  2. 내일은 `bad_entry_block_observed`만 남기고 주문 차단/청산 변경은 하지 않는다.
  3. feature는 `buy_pressure_10t`, `tick_acceleration_ratio`, `large_sell_print_detected`, `curr_vs_micro_vwap_bp`를 같이 남겨 `불량 진입`과 `일시 눌림`을 분리한다.
- 다음 액션:
  1. 후속 `soft_stop/hard_stop/GOOD_EXIT/MISSED_UPSIDE`와 연결 가능한 형태로만 해석한다.
  2. live block 승격은 별도 날짜 checklist에서 단일축 canary로만 연다.

### 4.4B `partial_only_timeout_shadow`

- 판정: `remove/guarded-off`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Low`
  - 이유: 신규 alpha shadow 금지 원칙에 따라 기본 OFF로 내렸다. partial 장기체류가 다시 문제화되면 report-only feature로 새로 연다.
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

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: split-entry 재개 의제가 현재 기준문서에서 닫혔고, same-day 판정축에서도 복귀 후보가 아니다.
  - 상향 조건: 없음. 재개가 필요하면 새 workorder와 새 cohort로 다시 정의해야 한다.
  - 하향 조건: historical runtime shadow까지 완전히 삭제할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Low`
- 근거:
  1. `latency fallback split-entry`는 `Plan Rebase`에서 영구 폐기 축으로 잠겼다.
  2. runtime shadow는 재개 없는 상태에서 현재 판정에 기여하지 않아 기본 OFF가 맞다.
- 다음 액션:
  1. runtime emit은 기본 OFF로 두고 historical audit helper만 남긴다
  2. 재개 검토가 다시 생기면 새 판정축으로 다시 등록한다

### 4.4D `split_entry_immediate_recheck_shadow`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: parent split-entry 축 자체가 폐기됐으므로 후속 recheck shadow도 운영 가치가 없다.
  - 상향 조건: 없음. split-entry 재개 정의가 새로 생길 때만 별도 재등록한다.
  - 하향 조건: historical helper까지 삭제할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Low`
- 근거:
  1. `split_entry_rebase_integrity_shadow`의 하위 후속 관찰축이라 독립 유지 이유가 없다.
  2. 현재는 historical test fixture 외 live 판정 연결점이 없다.
- 다음 액션:
  1. integrity shadow와 같이 기본 OFF/remove로 묶는다

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
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `2026-04-27 11:31 KST` raw 분해에서는 가장 직접적인 same-day pivot이었지만, `13:00` offline 판정에서 제출 회복 비율 개선을 만들지 못해 현재는 OFF 상태다.
  - 상향 조건: `submitted`, `quote_fresh_latency_pass_rate`, `latency_state_danger` 감소, `canary_applied`가 실제 회복을 만들 때
  - 하향 조건: 반복 관찰에도 효과가 없고 `entry_filter_quality` 또는 다른 명시적 latency 하위원인 축으로 완전히 대체될 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `2026-04-27 11:31 KST` raw 재집계 기준 `latency_block=3196`, `latency_state_danger=3000`, `other_danger=1218`, `low_signal=1079/1427`라 병목 직접성이 높다.
  2. `SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE`를 `90.0 -> 85.0`으로 낮춰 same-day pivot 했지만, `13:00` 기준 `budget_pass_to_submitted_rate=0.2%`가 그대로여서 축을 종료했다.
  3. 현재는 `latency_block` 직접 사유를 건드린 이력이 남아 있어 inventory에는 유지하지만, live owner는 아니다.
- 다음 액션:
  1. 현재 상태는 `13:00 미개선 종료 후 OFF`로 잠근다.
  2. 재개는 `other_danger`가 다시 1순위 direct residual로 올라오고 새 rollback guard가 문서화될 때만 허용한다.

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
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `High`
  - 이유: BUY recovery가 실제 주문 품질로 이어지는지 소량 실전 표본으로 닫는 하위 probe 축이다.
  - 상향 조건: `buy_recovery_canary`가 다시 live 승인되고 promoted 표본이 누적될 때
  - 하향 조건: recovery 축 자체가 장기간 OFF거나, 다른 live canary 관찰 중 단일축 원칙을 깨는 경우
- EV 판정 기여도: `Medium`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. 2026-04-27 `soft_stop_micro_grace` live 관찰 중에는 단일축 원칙 때문에 `AI_WAIT6579_PROBE_CANARY_ENABLED=False`로 잠근다.
  2. `wait6579_ev_cohort`가 `wait6579_probe_canary_applied`를 직접 집계한다.
- 다음 액션:
  1. `buy_recovery_canary`의 하위 probe 축으로 묶되 현재 live에서는 OFF 유지
  2. 장기간 promoted 표본이 없으면 parking 또는 제거 재판정

### 4.8B `fallback_qty_canary` / current runtime `fallback_qty_guard`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: fallback entry 자체가 폐기돼 multiplier guard는 더 이상 실전 조작점이 아니다.
  - 상향 조건: 없음. fallback entry 재개가 새 문서/가드와 함께 승인될 때만 재정의한다.
  - 하향 조건: historical 상수/로그 흔적까지 삭제할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Low`
- 근거:
  1. `entry_mode == fallback` 실전 경로가 hard-off면 `fallback_qty_guard`도 실행되지 않는다.
  2. 남는 의미는 과거 로그 해석용 historical label뿐이다.
- 다음 액션:
  1. 문서 분류는 remove로 고정하고, 잔존 로그는 historical-only로만 설명한다
  2. live runtime에서는 `fallback_qty_guard` 분기 자체를 유지하지 않는다

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
  - 이유: `2026-04-27 13:00` 기준 `ws_jitter_too_high=1852`가 `other_danger` 다음 직접 잔여 원인이라, 오늘 `15:00` 전 관찰 가능한 다음 독립축으로 가장 빠르게 교체 가능하다.
  - 상향 조건: `submitted`, `quote_fresh_latency_pass_rate`, `latency_state_danger` 감소, `ws_jitter_relief_canary_applied`가 실제 회복을 만들 때
  - 하향 조건: residual 분해상 `ws_jitter`가 후순위로 밀릴 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 상수와 runtime branch가 이미 존재하고 회귀 테스트도 있어, same-day `기존 축 OFF -> restart.flag -> 새 축 ON` 교체가 가능하다.
  2. `2026-04-24`에는 활성화 표본 0으로 종료됐지만, `2026-04-27 13:00`에는 raw danger breakdown에서 `ws_jitter_too_high`가 다시 큰 잔여 원인으로 남았다.
- 다음 액션:
  1. `2026-04-27 15:00` 미개선으로 OFF 상태를 유지한다.
  2. 재개는 `ws_jitter`가 다시 단일 우세 원인으로 올라오고 복합축보다 직접성이 높을 때만 허용한다.

### 4.9A-1 `latency_quote_fresh_composite`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `2026-04-29 08:29 KST` OFF + restart가 확정됐고 현재는 live owner가 아니지만, `quote_fresh_composite_canary_applied` historical cohort와 `composite_no_recovery` 근거는 replacement 축 선택의 reference로 남는다.
  - 상향 조건: 동일 단계 live 축이 비워지고, 새 승인 항목에서 `signal/ws_age/ws_jitter/spread/quote_stale` 묶음 전체를 다시 1축으로 재승인할 때
  - 하향 조건: historical/reference 비교도 더 이상 쓰지 않고 완전히 archive로 내릴 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `Plan Rebase`와 `2026-04-29 checklist`에서 현재 entry live 축은 `mechanical_momentum_latency_relief`로 고정됐다.
  2. `latency_quote_fresh_composite`는 제출 회복 hard baseline을 만들지 못했고, OFF 값과 restart provenance까지 확보됐다.
- 다음 액션:
  1. 장중/번들 판정에서는 historical/reference 축으로만 집계한다.
  2. 재개 없이는 baseline/live 승격 후보로 취급하지 않는다.

### 4.9A-2 `latency_signal_quality_quote_composite`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: same-day replacement로 실제 켰던 축이라 `post-restart cohort` 분리는 남길 가치가 있지만, `budget_pass=972`, `submitted=0`, 후보 통과 0건으로 현재 live owner는 아니다.
  - 상향 조건: future replacement 후보가 다시 `high AI score + quote freshness` 쪽으로 좁혀지고, 새 승인 항목에서 same-day 재승인될 때
  - 하향 조건: `signal>=90` 계열 예비 복합축을 완전히 폐기하고 historical cohort도 더 이상 쓰지 않을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Low`
- 근거:
  1. `2026-04-29 12:21~12:50 KST` replacement 이후 `low_signal=770`, `quote_stale=76`, 통과 후보 0건으로 효과 미약 종료가 문서화됐다.
  2. AI score 50/70 mechanical fallback 상태를 열지 못해 제출 drought 완화 직접성이 낮았다.
- 다음 액션:
  1. `post-restart cohort`의 historical comparison과 실패 근거만 유지한다.
  2. 새 문서 승인 없이 live 재개 후보로 읽지 않게 `observe-only`로 고정한다.

### 4.9A-3 `mechanical_momentum_latency_relief`

- 판정: `operating-override-decision`
- live 영향도: `limited-live`
- 튜닝 모니터링 가치: `High`
  - 이유: `latency_quote_fresh_composite`와 `latency_signal_quality_quote_composite`를 닫은 뒤, AI 50/70 mechanical fallback 상태까지 포함해 제출 drought를 직접 완화하는 현재 entry live replacement 축이다.
  - 상향 조건: `mechanical_momentum_relief_canary_applied` cohort에서 `submitted` 회복이 유지되고, 제출 이후 `full/partial` 체결 품질과 `HOLDING/exit_rule/COMPLETED + valid profit_rate` 기준 BUY 신호 적정성이 비악화로 확인될 때
  - 하향 조건: post-restart cohort에서 `budget_pass >= 150`인데 `submitted <= 2`, `pre_submit_price_guard_block_rate > 2.0%`, `normal_slippage_exceeded` 반복, 또는 일간 canary 손익이 NAV 대비 `<= -0.35%`일 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `2026-04-29 12:50 KST` 운영 override로 `latency_signal_quality_quote_composite=False`, `mechanical_momentum_latency_relief=True` replacement가 반영됐다.
  2. same-day counterfactual 기준 약 `91`건 후보가 확인돼, mechanical fallback 표본을 완전히 버리지 않는 현재 가장 직접적인 제출 회복 축이었다. 단, `2026-05-04` 유안타증권 반복손실 이후 `AI score 50`은 신규 BUY 보류 override가 우선한다.
  3. `2026-04-29 12:57 KST` restart 후 main PID `30566 -> 35539` 교체 provenance가 확보됐다.
- 다음 액션:
  1. `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`까지는 entry 병목 회복으로, `full/partial`, `HOLDING/exit_rule`, `COMPLETED + valid profit_rate`, `fallback_regression=0`는 BUY 신호 품질 관찰로 post-restart cohort를 분리한다.
  2. baseline 승격 전까지는 same-day 운영 override 1축으로만 유지한다. 문서상 `active canary`와 혼용하지 않는다.

### 4.9A-4 `orderbook_stability_observation`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `FR_10s`, `quote_age_p50/p90`, `print_quote_alignment`는 quote freshness 복합축의 세부 품질을 설명할 수 있지만, 현재 entry 병목 해소 전에는 추가 차단으로 쓰면 submitted 회복을 더 늦출 수 있다.
  - 상향 조건: entry 병목이 해소되고, `unstable_quote_observed=True` 표본이 submitted/fill/COMPLETED + valid profit_rate에서 명확히 악화될 때
  - 하향 조건: unstable 표본과 체결품질/손익 간 차이가 없거나 기존 `ws_age/ws_jitter/spread_ratio`로 충분히 대체될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `orderbook_stability_observed`는 `ENTRY_PIPELINE` 관찰 이벤트로만 남기며 주문 판단, canary flag, threshold, fallback/scout 경로를 변경하지 않는다.
  2. canary 승격은 현재 entry canary가 submitted 회복과 baseline `N_min`을 충족한 뒤 별도 checklist에서만 검토한다.
  3. 1차 canary 후보는 `BYPASS`가 아니라 `unstable_quote_position_cap` 또는 `unstable_quote_frequency_cap`이며, `scout-only`는 폐기된 fallback/scout 원칙과 충돌하므로 제외한다.
- 다음 액션:
  1. offline bundle summary에서 `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted/fill/latency_danger`를 본다.
  2. live gate 승격 전까지는 분석 지표로만 유지한다.

### 4.9A-5 `initial_entry_qty_cap_1share` / `initial_entry_qty_cap_2share_historical` / `initial_entry_qty_cap_3share_candidate`

- 판정: `1share=active-canary-decision`, `2share=historical-reference`, `3share=historical-reference`
- live 영향도: `1share=limited-live`, `2share=none`, `3share=none`
- 튜닝 모니터링 가치: `High`
  - 이유: `2026-05-09` 후속 사용자 지시로 신규 BUY, wait6579 probe, REVERSAL_ADD/AVG_DOWN, PYRAMID의 1주 수량 cap은 기본 ON으로 복귀했다. 해제는 완벽한 spot이 아니라 EV 중심 trade-off 기준의 `position_sizing_cap_release` approval request와 사용자 승인이 있을 때만 가능하다. `2주/3주 cap`은 더 이상 직접 승격 후보가 아니라 historical reference로만 유지한다.
  - 상향 조건: cap 유지 cohort와 cap opportunity가 combined EV에서 충분히 설명되고, `position_sizing_cap_release`가 승인 요청을 만들 때
  - 하향 조건: 1주 cap이 missed upside/opportunity cost를 크게 만들지 않거나, 수량 확대 후보에서 soft stop/partial/order_failed/protection 지연 risk가 커질 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. `2026-04-29` full-day 기준 `initial_entry_qty_cap_applied=38`, `ADD_BLOCKED reason=zero_qty=0`, `completed_valid_count=17`, `completed_valid_avg_profit_rate=+0.0535%`, `pyramid_activated=3`이 확인됐다.
  2. `2026-05-09` 후속 사용자 지시로 현재 기본값은 `KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=True`, `KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_MAX_QTY=1`이다.
- 다음 액션:
  1. `initial-only`, `pyramid-activated`, `full_fill`, `partial_fill`, `soft_stop`, `order_failed`를 계속 분리한다.
  2. 수량 cap 해제는 기존 `2주/3주 cap` 후보 승격이 아니라 `position_sizing_cap_release` approval request와 사용자 승인으로만 검토한다.

### 4.9A-6 `ai_cache_hit_miss`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: holding cache hit/miss는 호출량과 decision freshness에 영향을 줄 수 있지만, 현재 structured field가 `submitted/full/partial/COMPLETED`와 안정적으로 조인되지 않는다.
  - 상향 조건: gatekeeper/holding cache hit/miss가 raw event에 canonical field로 남고, `submitted`, `soft_stop`, `COMPLETED + valid profit_rate`와 조인 가능한 schema가 생길 때
  - 하향 조건: cache miss/hit 차이가 호출비용 외 EV/청산 품질과 무관하다고 확인될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `2026-04-29` 기준 `AI 보유감시` 로그는 `MISS=2260`, `HIT=67`로 관측량은 충분했다.
  2. 그러나 pipeline event에는 `gatekeeper_cache`/`ai_cache`가 제출/체결/손익과 직접 조인되는 structured field로 남아 있지 않아 live go/no-go 근거로 쓸 수 없다.
- 다음 액션:
  1. cache 축은 영향도 0이 아니라 `schema gap`으로 둔다.
  2. canary가 아니라 structured logging 보강 후보로만 유지한다.

### 4.9A-7 `execution_receipt_binding_quality`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `High`
  - 이유: WS 실제체결이 들어왔는데 active order binding이 실패하면 보유/청산 판단보다 먼저 runtime truth가 흔들린다.
  - 상향 조건: BUY/SELL `EXEC_IGNORED`가 반복되고, 계좌동기화가 HOLDING/COMPLETED 복구를 대신하는 빈도가 늘 때
  - 하향 조건: order number binding race가 해결되고 정기 계좌동기화 의존도가 낮아졌을 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `SK이노베이션(096770)`은 `2026-04-29 13:28:19 BUY`, `15:06:28 SELL` 모두 WS 실제체결이 있었지만 `[EXEC_IGNORED] no matching active order`로 빠졌다.
  2. 정기 계좌동기화가 `BROKER_RECOVER -> HOLDING`, 이후 `잔고 없음 -> COMPLETED`를 대신 수행했다.
  3. 사용자는 단절 리스크 때문에 HTS에서 수동 매도했고, 실제 체결 기준 수익률은 비용 반영 약 `+4.2%`였다.
- 다음 액션:
  1. 이 축은 alpha canary가 아니라 `EV 판정 전제 품질축`으로 유지한다.
  2. `ORDER_NOTICE_BOUND -> WS 실제체결 -> active order binding` 경로를 BUY/SELL로 분리해 추적한다.

### 4.9A-8 `gemini_schema_registry_flag_off` / `deepseek_retry_acceptance_flag_off`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 둘 다 live enable이 아니라 flag-off load/contract/log visibility 묶음이다. 기본 live 동작을 바꾸지 않지만, 이후 AI engine enable acceptance의 전제다.
  - 상향 조건: Gemini schema registry가 endpoint별 response_schema ingress와 fallback/test matrix를 갖추고, DeepSeek retry acceptance가 `api_call_lock`/rate-limit/server-error 경로에서 충분히 관찰될 때
  - 하향 조건: live enable 계획이 폐기되거나 기존 text fallback만으로 충분하다고 확정될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. Gemini `holding_exit_v1` enum/normalization contract는 live enable 전 필수 정합성 항목으로 남아 있다. `eod_top5_v1`은 2026-05-21 EOD TOP5 기능 제거로 더 이상 live enable 후보가 아니다.
  2. DeepSeek context-aware backoff guard는 준비됐지만, retry acceptance 문서화와 로그 확인 전에는 enable 불가다.
- 다음 액션:
  1. flag 기본값 OFF를 유지한다.
  2. `GeminiSchemaContractCarry0430`, `DeepSeekAcceptanceCarry0430`, `DeepSeekInterfaceGap0430`에서 contract/test/log visibility만 닫는다.

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
   - `hard_time_stop_shadow`
   - `same_symbol_soft_stop_cooldown_shadow`
   - `partial_only_timeout_shadow`
2. `observe-only 유지 문서화`
   - `dual_persona`
   - `watching_shared_prompt_shadow`
   - `strength_shadow_feedback`
3. `telemetry 유지 문서화`
   - `ai_holding_fast_reuse_band`
4. `baseline-promote historical/current 표기 유지`
   - `dynamic_strength_canary` (`dynamic_strength_relief`)
   - `partial_fill_ratio_canary` (`partial_fill_ratio_guard`)
4. `active-canary 운영/parking 판정`
  - `buy_recovery_canary`
  - `wait6579_probe_canary`
  - `latency_guard_canary`
  - `mechanical_momentum_latency_relief`
  - `spread_relief_canary`
  - `ws_jitter_relief_canary`
  - `other_danger_relief_canary`
5. `sim-only cohort / sim-auto-approved actuator`
  - `scalp_sim_candidate_window_expansion`
  - `scalp_sim_ai_budget_manager`
  - `scalp_sim_scale_in_window_expansion`

이 순서를 지켜 `remove`, `observe-only`, `baseline-promote`, `active-canary`를 섞어 동시에 건드리지 않는다.
