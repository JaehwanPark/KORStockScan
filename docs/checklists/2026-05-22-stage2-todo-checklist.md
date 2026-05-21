# 2026-05-22 Stage2 To-Do Checklist

## 오늘 목적

- Bedrock Nova Lite v1 shadow 결과를 OpenAI `gpt-5.4-mini` Tier2 호출 지점별로 비교해 정식 승격 후보 여부를 판단한다.
- Nova Lite v1 승격 판단과 별개로, Lite v2 shadow 시행 준비 여부를 닫는다.
- Micro 승격 판단은 `2026-05-21` 장후 checklist가 소유하고, `2026-05-22`에는 미완료 follow-up이 명시적으로 이관된 경우에만 다시 본다.
- latency/cost/token/cache 절감과 parse/schema 품질을 성과 판단에서 분리해 본다.
- `sim_record_id` exact join 기반 outcome-linked performance를 우선하고, 근접 매칭이나 instrumentation 이전 unmatched 표본은 source-quality gap으로만 기록한다.
- 승격 후보가 있더라도 당일 장중 provider route 변경은 금지하고, 별도 approval/workorder와 다음 PREOPEN 적용 후보로만 연결한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 스캘핑 AI route는 OpenAI 고정으로 시작한다. Bedrock shadow 결과는 장후 판단 입력이며, 장중 provider route, threshold, 주문 판단, bot restart trigger로 직접 쓰지 않는다.
- Bedrock/Nova 비교는 `decision_authority=shadow_observation_only`, `runtime_effect=false`, `broker_order_forbidden=true`, `actual_order_submitted=false` 계약을 유지한다.
- `mini` 우회 승격 검토는 `gpt-5.4-mini` Tier2 호출 지점별로 분리한다. `holding_flow`, `entry_price`, 기타 Tier2 endpoint를 합산해 단일 결론으로 닫지 않는다.
- Lite v2 shadow는 Lite v1 정식 승격 판단과 분리한다. v2 시행은 report-only 실험 설계/토글/산출물 계약만 열고, v1 또는 v2 provider route 변경으로 직접 이어지지 않는다.
- Nova Micro는 `2026-05-22` 하루치 추가 수집 후 별도 one-day decider로 OpenAI 또는 Nova Micro 중 하나를 확정한다. `defer/hold/need_more_sample` 결론은 금지한다.
- 손익은 `COMPLETED + valid profit_rate` 또는 scalp sim post-sell의 numeric `profit_rate`만 사용하고, exact `sim_record_id` join이 없는 표본은 성과 우열 근거에서 제외한다.
- 승격 결론은 `promote_candidate_requires_approval`, `keep_shadow_collecting`, `reject_provider_bypass`, `defer_source_quality_gap` 중 하나로 닫는다.
- Micro one-day 판정 산출물은 기존 `threshold_cycle_ev`, `runtime_approval_summary`, LDM, workorder 자동 apply에 연결하지 않고, 수집 종료 후 Micro shadow/duel OFF 확인을 남긴다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장후 체크리스트

- [ ] `[BedrockNovaMicroOneDayDecision0522] OpenAI vs Nova Micro one-day 성과 비교 후 엔진 확정 및 shadow OFF 확인` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:05`, `Track: AITransport`)
  - Source: [bedrock_nova_micro_one_day_decision.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_micro_one_day_decision.py), [bedrock_nova_micro_one_day_decision_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_one_day_decision/bedrock_nova_micro_one_day_decision_2026-05-22.json), [bedrock_nova_micro_one_day_decision_2026-05-22.md](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_one_day_decision/bedrock_nova_micro_one_day_decision_2026-05-22.md), [bedrock_nova_micro_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-22.jsonl), [sim_post_sell_evaluations_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-22.jsonl), [sim_post_sell_candidates_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl)
  - owner/status: `bedrock_nova_micro_one_day_engine_decision`, `temporary_one_day_decider`, `runtime_effect=false`, `decision_authority=one_day_operator_decision_artifact`
  - 실행 명령: `PYTHONPATH=. .venv/bin/python -m src.tests.bedrock_nova_micro_one_day_decision --date 2026-05-22`
  - 판정 기준: `entry/watch BUY`와 `holding continuation`을 분리하고, 각 profile에서 실제로 해당 엔진 action을 따랐다고 가정했을 때의 후행 성과를 비교한다. primary metric은 unique valid exact join 기준 `source_quality_adjusted_ev_pct`이며, 상대 엔진 대비 `>= 0.01%p` 높으면 해당 profile의 엔진 승리로 닫는다. exact join은 `entry_adm_candidate_id` 또는 `record_id -> sim_parent_record_id`이고, 모델 판단 시점 이후 청산/평가 row만 인정한다. weak join은 참고로만 표시하고 primary decision에는 넣지 않는다.
  - 1차원 판정 금지: action exact match count, parse_ok, latency, cost, token/cache 절감, `nova_minus_openai` 단순 합산, 전체 row 합산 우열만으로 winner를 정하지 않는다. `OpenAI WAIT vs Nova BUY`, `OpenAI BUY vs Nova non-BUY`, `BUY/BUY`, `OpenAI EXIT/TRIM vs Nova HOLD`, `HOLD/HOLD`, `Nova EXIT`을 분리하고, 각 bucket의 후행 `profit_rate`, MFE/MAE, missed-upside/early-exit 결과를 본 뒤 profile별 EV로 결론낸다.
  - tie-breaker: `0.01%p` 미만 차이면 BUY/entry는 MAE 노출이 낮은 엔진, holding continuation은 missed-upside 감소가 큰 엔진, 그래도 동률이면 parse/latency/cost 순으로 반드시 `winner=openai|nova_micro` 중 하나를 선택한다.
  - 적용 방식: winner가 OpenAI면 Micro shadow/duel OFF 및 기존 OpenAI 유지로 닫는다. winner가 Nova Micro면 전체 primary 전환이 아니라 `entry_watch_buy_nova_micro_v1` 또는 `holding_continuation_nova_micro_v1` profile 후보로만 기록하고, 별도 approval/workorder 없이는 global provider route를 바꾸지 않는다.
  - 금지: `defer`, `hold`, `need_more_sample`, 기존 threshold/postclose/LDM/runtime approval/workorder 자동 apply 연결, broker order submit, threshold mutation, global provider route 변경 금지.
  - 다음 액션: `winner_openai_turn_micro_shadow_off`, `winner_nova_micro_record_profile_candidate_turn_shadow_off`, `fail_missing_one_day_artifact`, `fail_primary_metric_join_contract` 중 하나로 닫는다.

- [ ] `[BedrockNovaLiteTier2PromotionReview0522] gpt-5.4-mini Tier2 호출 지점의 Nova Lite v1 one-day 라우팅 후보 확정` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:25`, `Track: AITransport`)
  - Source: [bedrock_nova_lite_one_day_decision.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_lite_one_day_decision.py), [bedrock_nova_lite_one_day_decision_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_one_day_decision/bedrock_nova_lite_one_day_decision_2026-05-22.json), [bedrock_nova_lite_one_day_decision_2026-05-22.md](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_one_day_decision/bedrock_nova_lite_one_day_decision_2026-05-22.md), [bedrock_nova_lite_shadow_report_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_2026-05-22.json), [bedrock_nova_lite_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_2026-05-22.jsonl), [sim_post_sell_evaluations_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-22.jsonl), [sim_post_sell_candidates_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl)
  - owner/status: `bedrock_nova_lite_one_day_tier2_decision`, `temporary_one_day_decider`, `runtime_effect=false`, `decision_authority=one_day_operator_decision_artifact`
  - 실행 명령: `PYTHONPATH=. .venv/bin/python -m src.tests.bedrock_nova_lite_one_day_decision --date 2026-05-22`
  - 판정 기준: `gpt-5.4-mini` Tier2 JSON 호출 지점만 대상으로 `holding_flow`, `entry_price`, `other_tier2` profile을 분리하고, valid exact join의 sample-weighted `source_quality_adjusted_ev_pct`로 OpenAI와 Lite를 비교한다. Lite가 OpenAI보다 `1.0%p` 초과로 나쁘지 않으면 Lite 우위/동률로 보며 tie-breaker도 Lite로 닫는다.
  - profile guard: valid sample이 있는 개별 profile 중 Lite가 OpenAI보다 `>1.0%p` 열위이면 Tier2 전체 Lite 라우팅 후보를 만들지 않고 OpenAI 유지로 닫는다. no-sample이면 Lite 자동 승격 금지이며 `fail_primary_metric_join_contract`로 닫는다.
  - 1차원 판정 금지: action exact match count, parse_ok, latency, cost, token/cache 절감, 전체 row action 합산, 단순 `nova_minus_openai` 점수만으로 winner를 정하지 않는다. `holding_flow`는 `OpenAI EXIT/TRIM vs Lite HOLD`, `OpenAI HOLD vs Lite TRIM/EXIT`, `HOLD/HOLD`를 분리해 후행 EV/MFE/MAE를 보고, `entry_price`는 `USE_DEFENSIVE`가 손실 회피인지 기회손실인지 별도 bucket으로 표시한다.
  - 적용 방식: winner가 Lite이면 `tier2_nova_lite_v1` 라우팅 후보를 기록하되, 실제 provider route 변경은 별도 approval/workorder 또는 명시 실행 지시 없이는 자동 적용하지 않는다. winner가 OpenAI이면 기존 OpenAI `gpt-5.4-mini`를 유지하고 Lite shadow/duel OFF 후보를 남긴다.
  - 금지: 장중 provider route 변경, `gpt-5.4-mini` 즉시 대체, entry price/order guard 변경, threshold 변경, bot restart trigger, 기존 threshold/postclose/LDM/runtime approval/workorder 자동 apply 연결 금지.
  - 다음 액션: `winner_lite_record_tier2_route_candidate_turn_shadow_off`, `winner_openai_keep_openai_turn_lite_shadow_off`, `fail_missing_one_day_artifact`, `fail_primary_metric_join_contract` 중 하나로 닫는다.

- [ ] `[BedrockNovaLiteV2ShadowImplementation0522] Nova Lite v1 대비 Lite v2 shadow 시행 준비 및 실행 여부 판단` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:45`, `Track: AITransport`)
  - Source: [bedrock_nova_lite_shadow_report_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_2026-05-22.json), [bedrock_nova_lite_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_2026-05-22.jsonl), AWS Bedrock Nova Lite v2 model availability/region/cost documentation, [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - owner/status: `bedrock_nova_lite_v2_shadow_observation`, `report_only`, `runtime_effect=false`, `decision_authority=shadow_observation_only`
  - 판정 기준: Lite v1 승격 판단과 별개로, Lite v2가 `gpt-5.4-mini` Tier2 JSON 호출 크기와 `holding_flow`/`entry_price` 응답 계약을 감당할 수 있는지 확인한다. 가능하면 v1과 동일 row schema에 `candidate_model_family=lite_v2`, `baseline_bedrock_model_id=apac.amazon.nova-lite-v1:0`, `candidate_bedrock_model_id`, `v1_v2_action_match`, `v1_v2_score_delta`, `v2_parse_ok`, `v2_latency_ms`, `v2_estimated_cost_usd`를 추가하는 report-only shadow 설계를 준비한다.
  - 시행 조건: 한국 리전 또는 운영 Bedrock profile에서 Lite v2 model id가 호출 가능하고, 비용 단가/env 토글/timeout/queue/caching 설정이 v1과 분리되어야 한다. v2 model id 또는 리전 가용성이 불명확하면 `defer_source_quality_gap`으로 닫고 v1 shadow 수집은 유지한다.
  - 금지: Lite v2 shadow를 Lite v1 정식 승격 근거와 혼합 금지, 장중 provider route 변경 금지, `gpt-5.4-mini` 즉시 대체 금지, entry price/order guard 변경 금지, threshold 변경 금지, bot restart trigger 금지, 튜닝체인 자동 apply 연결 금지.
  - 다음 액션: `start_lite_v2_shadow_report_only`, `keep_lite_v1_only`, `defer_region_or_model_gap`, `reject_lite_v2_shadow` 중 하나로 닫고, 시행 시 `target_endpoint`, `model_id`, `region/profile`, `env toggle`, `artifact path`, `sample floor`, `rollback/off switch`를 기록한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-21` postclose -> `2026-05-22`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0522] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-22`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-21.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[OpenAIWSPreopenConfirm0522] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-22`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-21.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-21.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.

- [ ] `[SwingApprovalArtifactPreopen0522] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-22`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-21.json), [threshold_cycle_ev_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-21.json)
  - 판정 기준: 사용자 승인 방침에 따라 내일 장전에는 dry-run env 전용 `swing_model_floor`, `swing_gatekeeper_reject_cooldown` 2건을 승인하고, `swing_one_share_real_canary_phase0`도 별도 real canary approval artifact로 승인한다. 두 approval은 동일 artifact 의미로 묶지 않고 dry-run env 승인과 live 1주 canary 승인을 분리 기록한다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다. 특히 dry-run 2건 승인 artifact를 real canary 승인으로 확장 해석하지 않고, real canary artifact를 dry-run env 승인으로 대체하지 않는다.
  - 다음 액션: `dry_run_approval_artifact_present_real_canary_artifact_present_separate`, `dry_run_approval_artifact_missing`, `real_canary_approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[ScalpSimOvernightPrecloseCron0522] 15:20 스캘핑 sim 오버나이트 판정 자동화 첫 운영 확인` (`Due: 2026-05-22`, `Slot: INTRADAY`, `TimeWindow: 15:20~15:30`, `Track: ScalpingLogic`)
  - Source: [run_scalp_sim_overnight_preclose.sh](/home/ubuntu/KORStockScan/deploy/run_scalp_sim_overnight_preclose.sh), [scalp_sim_overnight.py](/home/ubuntu/KORStockScan/src/engine/scalp_sim_overnight.py), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py)
  - 판정 기준: cron이 `--live-openai`로 실행되고, active 스캘핑 sim position에 대해 `scalp_sim_overnight_decision` 이벤트와 `SELL_TODAY`/`HOLD_OVERNIGHT` 후속 이벤트가 생성되는지 확인한다. report-only 산출물의 `active_undecided_count=0`, `source_quality_status=pass`, OpenAI `overnight_v1` provenance, Bedrock Nova Lite shadow row를 확인한다.
  - 금지: sim overnight action을 hard gate, 실주문, 자동매도, threshold apply, provider route 변경, bot restart 근거로 쓰지 않는다. LDM feature/source row로만 소비한다.
  - 다음 액션: `preclose_overnight_pass`, `fail_active_undecided_source_quality`, `fail_cron_or_openai`, `warning_bedrock_shadow_missing` 중 하나로 닫는다.

- [ ] `[RuntimeEnvIntradayObserve0522] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-22`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-21.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[OpenAIWSIntradaySample0522] OpenAI WS/entry_price 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-05-22`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-21.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-21.md)
  - 판정 기준: `analyze_target` WS latency/fallback과 `entry_price` transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않는다.
  - 다음 액션: 표본 부족이면 postclose provenance 보강 workorder로 분리한다.

- [ ] `[SimProbeIntradayCoverage0522] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-22`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-21.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0522] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-21.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0522] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-21.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-21.md), [code_improvement_workorder_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-21.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0522] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-21.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0522] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->
