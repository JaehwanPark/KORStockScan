# 2026-08-04 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-03` postclose -> `2026-08-04`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0804] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-04`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-03.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 결함 보완 (`2026-08-04`): target date `2026-08-04`부터 main postclose calibration candidate는 `runtime_handoff_contract_version=1`과 candidate별 handoff 계약이 모두 있어야 자동 선택된다. 구 산출물 또는 version mismatch는 `runtime_handoff_contract_missing`/`runtime_handoff_contract_version_mismatch`로 fail-closed하며, 별도 명시적 operator lock은 calibration 권한과 혼합하지 않고 기존 lock provenance로만 보존한다. 8/3 구 산출물 replay에서 entry/scale split은 차단되고 score recovery operator lock은 보존됨을 확인했다. 실제 PID/runtime env 반영은 코드리뷰 종료 후 별도 재생성·재기동 gate가 소유한다.

- [ ] `[RisingMissedScoutRuntimePreopen0804] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-04`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-03.json), [code_improvement_workorder_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-03.json), [threshold_apply_2026-08-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-04.json), [threshold_runtime_env_2026-08-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-04.json), [threshold_runtime_env_verify_2026-08-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-04.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`5`, forced_scout_with_post_sell_count=`12`, post_sell_join_coverage_pct=`1.932367`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`8`, loss_or_flat_forced_scout_count=`4`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0804] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-04`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-03.json), [threshold_apply_2026-08-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-04.json), [threshold_runtime_env_2026-08-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-04.json)
  - 판정 기준: 고정된 전일 목록을 복사하지 않고 당일 runtime manifest의 `selected_families` 전부가 runtime event provenance에 찍히는지 확인한다. apply decision이 `selected=false`인 family와 `removed_selected_families_ignored` family는 PID 반영 기대 목록에서 제외하고, sim/advisory family는 `actual_order_submitted=false`/`runtime_effect=false` 권한까지 함께 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 결함 보완 (`2026-08-04`): latency/tick 차단 반사실의 진입 기준을 executable ask, 사후 MFE/MAE 관측을 executable bid로 제한하고 mark/last-trade-only 표본은 source gap으로 제외한다. NXT post-block sampler/REST fallback/price-jump recovery는 configured·active date·current date·called·applied·reason을 분리 기록한다. launcher auto-renew는 당일 date projection 시 이전 date 결손을 `not_persisted_by_contract`로, effective date와 source를 `launcher_auto_renew`로 기록해 AI action guard와 fast-exit guard의 `active_date=missing` 오인을 제거한다. 모두 계측/귀속 변경이며 주문·threshold·provider 권한은 변경하지 않는다.
  - bounded submit 보완 (`2026-08-04`): rising-missed의 fresh trusted `eligible_wait_probe`는 최종 Entry AI와 같은 trace의 complete context에서 positive micro/tape support가 하나도 없거나, `failed_breakout/adverse` 분봉과 2개 이상 liquidity/fillability 약세 및 `score<50 + fading/weak/adverse` momentum이 동시에 확인되면 probe 제출 전 차단한다. 단일 약신호, stale/missing context, BUY 또는 비-scout 경로에는 적용하지 않는다. rollback은 `KORSTOCKSCAN_RISING_MISSED_WAIT_PROBE_QUALITY_GUARD_ENABLED=false`이며 broker/stale/account/order/quantity/cooldown/provider/cap/hard-safety owner는 변경하지 않는다.

- [ ] `[SimProbeIntradayCoverage0804] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-04`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-03.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0804] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-04`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-04.jsonl), [threshold_events_2026-08-04.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-04.jsonl), [observation_source_quality_audit_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-04.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-04 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[EntryPriceSelectionContractV20804] Exact V2 entry_price 가격선택 계약 재설계 및 동일 payload replay` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:05`, `Track: AIPrompt`)
  - Source: [ai_prompt_stage_coverage_replay_2026-08-03_entry_price.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_stage_coverage_replay/ai_prompt_stage_coverage_replay_2026-08-03_entry_price.json), [ai_stage_coverage_replay.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_stage_coverage_replay.py), [ai_prompt_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_prompt_contracts.py)
  - 현재 증거: mature Exact V2 `133`건 replay에서 Control `USE_DEFENSIVE 130`, Candidate `SKIP 87 / USE_DEFENSIVE 19 / USE_REFERENCE 17 / IMPROVE_LIMIT 7`, schema reject `3`, provider failure `0`이다. 비교 가능 `130`건의 source-quality-adjusted EV는 Control `+0.518089%`, Candidate `+0.281367%`, delta `-0.236722%p`, 신규 missed-upside `50`건으로 현 후보는 거부한다.
  - 판정 기준: 진입 매력도와 주문가격 선택을 분리하고, 주문 가능 후보에서는 exact payload에 존재하는 executable price만 선택한다. `SKIP`은 실제 setup invalidation·blocking fillability에 한정하고, defensive/reference/improve-limit별 fill 가능성·비용·10분 outcome을 venue/session별 동일 cohort로 비교한다.
  - 금지: provider/model/route, live prompt, 주문 수량, threshold, broker/stale/account/order/cooldown/hard-safety guard 변경 또는 runtime 승격.
  - 다음 액션: `candidate_quality_pass_offline_only`, `price_selection_contract_redesign_required`, `source_or_fill_join_gap`, `schema_semantic_fix_required` 중 하나로 닫는다.
  - 완료 판정 (`2026-08-04`): `price_selection_contract_redesign_required`. `decision_quality_entry_price_v2_1_conditional_selection`, 전용 response schema, exact price semantic gate를 구현하고 같은 Qwen3 32B 경로로 mature Exact V2 `133/133`건을 재실행했다. provider failure/schema reject/provider none은 모두 `0`, Candidate action은 `USE_DEFENSIVE 80 / USE_REFERENCE 48 / IMPROVE_LIMIT 5 / SKIP 0`으로 역할·스키마 결함은 닫혔다. 다만 선택가 limit-touch 반사실에서 Candidate는 Control보다 touch가 `111→115`, missed touch가 `15→13`으로 개선됐어도 10분 touch-adjusted end return이 `+0.233177%→+0.192904%`, delta `-0.040274%p`였고 KRX/NXT/PREMARKET 전 venue delta도 음수였다. Candidate가 Control보다 공격적인 가격을 `42`건 선택한 비용이 추가 touch의 이익을 상쇄하므로 live 승격 없이 Control을 유지한다. touch는 실제 체결 증거가 아니며 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`를 유지한다.

- [x] `[HoldingFlowDedicatedPairedReplay0804] holding_flow 전용 Exact V2 paired replay 생산자·소비자 연결` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:05~17:20`, `Track: AIPrompt`)
  - Source: [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py), [ai_decision_trace_2026-08-04.jsonl](/home/ubuntu/KORStockScan/data/ai_decision_trace/ai_decision_trace_2026-08-04.jsonl), [ai_prompt_paired_replay_2026-08-03_holding.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_paired_replay/ai_prompt_paired_replay_2026-08-03_holding.json)
  - 현재 증거: clean baseline 이후 확인한 exact `holding_flow` 자연호출은 `2`건이며 provider none `0`, action `EXIT 2`다. 현 holding stage paired report는 `holding_score` 중심이므로 endpoint별 성과 귀속을 분리해야 한다.
  - 판정 기준: 첫 mature row부터 동일 exact payload/hash/provider/model로 Control과 Candidate를 비교하고, HOLD/TRIM/EXIT action 분포, 확보한 추가수익, 확대 손실, peak giveback, post-decision MFE/MAE를 venue/session별로 기록한다. 표본 부족은 수집 중단이 아니라 cumulative keep-collecting으로 닫는다.
  - 금지: Bedrock Nova Lite v2→OpenAI failback route 변경, live holding/exit 승격, 자동 매도, threshold/stop/trailing/quantity/broker guard 변경.
  - 다음 액션: `paired_replay_complete_candidate_quality_pass_offline_only`, `sample_floor_keep_collecting`, `holding_flow_endpoint_attribution_gap`, `prompt_redesign_required` 중 하나로 닫는다.
  - 완료 판정 (`2026-08-04`): `sample_floor_keep_collecting`. 문자열 exact payload의 `[HOLDING_DECISION_CONTEXT]`를 canonical consumer가 직접 검증하고 venue/session을 동일 context에서 복원하도록 생산자·소비자 계약을 연결했다. clean baseline 자연호출 `2`건 중 7/31 `canonical_context_missing`은 제외 증거로 유지하고, 8/4 `108860` 1건만 exact eligible cohort로 고정했다. 캡처된 실제 OpenAI `gpt-5.4-mini` 경로로 `decision_quality_holding_flow_v2_1`을 실행해 hash/provider/schema 오류 `0`, Control `EXIT`→Candidate `EXIT`를 확인했다. 동일 KRX 30분 경로는 MFE `+1.377410%`, MAE `-1.101928%`, end return `+0.918274%`이고 60분 secured upside는 `+2.479339%`여서 단일 action collapse 판정이나 품질 승격은 금지하되, 후행 회복을 포착하지 못한 EXIT 표본을 다음 cumulative prompt redesign 입력으로 유지한다. 전용 outcome 소비자는 HOLD/TRIM/EXIT별 post-decision MFE/MAE·peak giveback을 기록하며 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`를 유지한다.

- [x] `[HoldingFlowBoundedDeferV220804] holding_flow soft-exit bounded defer V2.2 누적 replay` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:40`, `Track: AIPrompt`)
  - Source: [ai_prompt_stage_coverage_replay_2026-08-04_holding_flow.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_stage_coverage_replay/ai_prompt_stage_coverage_replay_2026-08-04_holding_flow.json), [ai_decision_outcome_labels_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-08-04.json), [ai_stage_coverage_replay.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_stage_coverage_replay.py)
  - 현재 증거: `108860`의 soft-stop `EXIT` 판단 후 30분 MFE `+1.377410%`, MAE `-1.101928%`, end return `+0.918274%`로 drawdown 후 recovery가 발생해 Control과 V2.1 모두 회복 탐색기회를 놓쳤다. 이는 무조건 HOLD 근거가 아니라 bounded recheck의 비용조정 가치를 측정할 첫 cumulative row다.
  - 판정 기준: hard/protect/emergency·broker/order/position conflict가 없는 soft-exit 표본만 대상으로 판단시점 즉시 executable bid EXIT와 30/60/90초 동일 venue/session executable bid 재평가를 비교한다. candidate는 exact payload만 사용하고 outcome 누출 없이 absorption/recovery evidence, 허용 추가 adverse, recheck horizon을 구조화한다. 첫 1건부터 cumulative ledger를 갱신하되 비용조정 defer EV, 추가 adverse, severe-tail, recovery capture를 모두 기록하고 favorable recovery만 선별하지 않는다.
  - 금지: hard/protect/emergency exit 지연, 기존 sell order 취소, live holding/exit prompt 승격, provider route·stop·trailing·수량·broker guard 변경, 완성 1분봉으로 30초 executable bid를 추정 또는 사후 조작.
  - 다음 액션: `bounded_defer_checkpoint_source_ready`, `checkpoint_source_unavailable_keep_collecting`, `candidate_quality_pass_offline_only`, `prompt_redesign_required`, `severe_tail_risk_rejected` 중 하나로 닫는다.
  - 완료 판정 (`2026-08-04`): `checkpoint_source_unavailable_keep_collecting`. exact eligible `108860` 1건을 동일 OpenAI `gpt-5.4-mini`로 1회 수동 V2.2 replay하여 provider none·최종 실패 `0`, Control `EXIT`→Candidate `EXIT`를 확인했다. 첫 응답의 `reason_codes_conflict` 1건은 계약 교정 재호출에서 해소됐다. 판단시점 executable bid `10,890원` 대비 30초 checkpoint는 실제 +39.388초의 fresh `ws_0D` bid `10,830원`(`-0.550964%`)으로 확인됐지만, +15초 허용범위 안의 60·90초 bid는 없어 완성봉 추정을 사용하지 않았다. 또한 판단 +0.422초에 1주 avg-down 주문이 제출되고 +4.438초에 `10,890원` 체결되어 보유수량 `2주`, 평단 `11,070원`으로 원본 포지션이 변했다. 따라서 순수 defer counterfactual과 비용조정 EV는 산출하지 않았고 live 승격도 금지했다. V2.2는 hard/protect/emergency·활성 매도주문을 EXIT로 유지하며 soft-exit exact row만 bounded defer 후보로 구조화하고 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`를 유지한다.

- [ ] `[PostcloseSourceQualityGateReview0804] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-04.json), [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json), [code_improvement_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-04.json), [threshold_cycle_postclose_verification_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-04.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0804] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-03.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0804] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-03.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0804] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-03.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-03.md), [code_improvement_workorder_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-03.json)
  - 판정 기준: selected_order_count=86와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0804] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-03.json), [runtime_apply_gap_audit_2026-08-03.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-03.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`268`, rollup_required_count=`268`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 267}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0804] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-04`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-03.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`15`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:14, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
