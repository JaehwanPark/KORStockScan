# 2026-07-27 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.
- 신규 다중분봉 AI 문맥은 다음 `PREMARKET_KRX_LIKE`에서 한 번 최종 검증한다. PASS이면 검증 완료 시점부터 PREMARKET·KRX 정규장·NXT 전 장의 전체 스캘핑 종목과 모든 적용 가능한 live AI endpoint에 전면 적용하고, FAIL이면 적용하지 않는다.
- 다중분봉 전면 적용 후 현행 prompt/model/provider를 새 exact 입력 control로 고정하고, 별도 `decision_quality_v1` outcome-label·오판 baseline·paired replay 루프를 시작한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- PREMARKET 최종검증 PASS는 전 장 전면 승격 권한이다. 이후 KRX/NXT별 추가 승격 gate를 두지 않으며, 각 live 호출은 해당 venue/session의 원천만 사용하고 다른 장의 값으로 보간하지 않는다.
- 다중분봉 live 승격 검증은 global runtime hook/env mapping, rollback, exact payload/trace, `provider!=none`, 필수 비교필드 `MISMATCH=0`, review finding 0건을 확인한다.
- 승격 방식은 canary, 세션 제한, 일부 종목/cohort, 일부 AI endpoint, 호출비율 제한이 아닌 전 장 전면 적용이다. PREMARKET 검증이 PASS한 뒤에는 축소 적용 상태를 만들지 않는다.
- `baseline_v1`은 보호용 input-preflight, `exact_v2`는 입력 정확성 gate, `decision_quality_v1`은 판단 개선 offline loop다. 입력 전면 적용과 Prompt V2 승격을 하나의 runtime 변경으로 묶지 않는다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 사용자 지시 실행 체크리스트

- [ ] `[MultiTimeframeAIContextPremarketFinalValidation0727] 신규 다중분봉 AI 문맥 PREMARKET 최종검증 및 전 장 전면 승격 판정` (`Due: 2026-07-27`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:40`, `Track: ScalpingLogic`)
  - Source: [market_context_observation.py](/home/ubuntu/KORStockScan/src/engine/scalping/market_context_observation.py), [multi_timeframe_context.py](/home/ubuntu/KORStockScan/src/engine/scalping/multi_timeframe_context.py), [entry_candle_context.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_candle_context.py), [holding_decision_context.py](/home/ubuntu/KORStockScan/src/engine/scalping/holding_decision_context.py), [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py), [ai_multi_timeframe_context_promotion.py](/home/ubuntu/KORStockScan/src/engine/automation/ai_multi_timeframe_context_promotion.py), [entry_context_intraday_probe.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_context_intraday_probe.py), [ai_decision_trace.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_trace.py), [ai_input_external_validation_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/ai_input_external_validation/ai_input_external_validation_2026-07-24.json), [ai_input_external_validation_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_input_external_validation/ai_input_external_validation_2026-07-27.json), [ai_multi_timeframe_context_review_2026-07-27.json](/home/ubuntu/KORStockScan/data/runtime/ai_multi_timeframe_context_review_2026-07-27.json), [ai_multi_timeframe_context_promotion_2026-07-27.json](/home/ubuntu/KORStockScan/data/runtime/ai_multi_timeframe_context_promotion_2026-07-27.json), [threshold_runtime_env_2026-07-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-27.json)
  - 목표 문맥: 세션 시작 정렬 완성 3/5/15분 OHLCV, 완성 1분봉 기반 session VWAP, 5/15분 opening range, 전일 고가·저가·종가, KOSPI/KOSDAQ 및 업종 상대 문맥이다. 형성 중 봉은 거래량·VWAP·다중분봉에서 제외한다. 이 파생값은 `input_bundle_version=scalping_multi_timeframe_context_v1`으로 관리하되 신규 병렬 payload를 만들지 않고 entry-side `entry_candle_context_v1`과 holding/scale-in/exit/overnight-side `holding_decision_context_v1`에 각각 stage projection으로 추가한다.
  - 판정 기준: review finding=`0`, 관련 tests/compile/diff=`pass`가 선행한다. PREMARKET 당일 증거는 `005930_NX/096770_NX/100090_NX`의 NXT route exact payload `request_capture_status=captured`, 응답 provenance `provider!=none`, 고정 표본별 exact request와 core endpoint별 `analyze_target`·`entry_price`·`holding_score`·`holding_flow` actual exact request가 각각 1건 이상, completed-bar-only, payload/API 내부변환 mismatch=`0`이어야 한다. KRX source 증거는 2026-07-24 골든 `005930/096770/100090`의 같은 symbol/venue/session 기준 외부 비교 필수 필드 `MISMATCH=0`과 source match=`pass`를 사용한다. 당일 KRX 정규장 exact/source 검증은 승격 전 존재할 수 없는 값으로 PREMARKET을 차단하지 않고 09:20 post-apply 필수 검증으로 넘긴다.
  - 승격 범위: 최종검증 PASS 즉시 전체 스캘핑 종목과 모든 활성 장 세션(`PREMARKET_KRX_LIKE`, `KRX_REGULAR`, `NXT_REGULAR_OVERLAP`, `NXT_AFTERMARKET`)의 적용 가능한 모든 live scalping AI endpoint에 신규 문맥을 전면 연결한다. PASS 전에는 source bundle만 생성하고 AI model payload에서는 제외한다. PASS artifact를 기록한 같은 단일 promotion transaction에서 `KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED=true`, `KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE=2026-07-27`, `entry_candle_context_v1` master와 PREMARKET/KRX/NXT cohort keys, `holding_decision_context_v1` master와 PREMARKET/KRX/NXT cohort 및 holding_score/holding_flow/overnight stage keys를 모두 활성화한다. `analyze_target`, `entry_price`, `holding_score`, `holding_flow`, `overnight`, `realtime_report`를 포함하며 canary·세션 제한·부분 cohort·endpoint 일부·호출비율 제한은 사용하지 않는다.
  - 불변 경계: 각 호출은 해당 venue/session의 source를 사용한다. provider route, threshold, 주문가·수량, broker/account/order/cooldown, hard/protect/emergency safety, bot state는 변경하지 않는다.
  - 차단 기준: forming bar 혼입, source-quality conflict, provider none, schema/semantic reject, payload/response hash 누락, global runtime hook/env/rollback/post-apply hook 누락이면 PREMARKET 최종검증을 FAIL로 닫는다. PASS 이후에는 KRX/NXT별 추가 승격 판정을 요구하지 않는다.
  - 다음 액션: `promoted_all_market_sessions_full`, `blocked_source_quality`, `blocked_provider_or_schema`, `blocked_route_isolation`, `blocked_runtime_hook_missing`, `blocked_review_or_env`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[MultiTimeframeAIContextAllMarketFirstObservation0727] 전 장 첫 AI payload 반영·격리·rollback 상태 확인` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 08:40~20:00`, `Track: ScalpingLogic`)
  - Source: [ai_multi_timeframe_context_promotion.py](/home/ubuntu/KORStockScan/src/engine/automation/ai_multi_timeframe_context_promotion.py), [pipeline_events_2026-07-27.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-27.jsonl), [ai_decision_trace_2026-07-27.jsonl](/home/ubuntu/KORStockScan/data/ai_decision_trace/ai_decision_trace_2026-07-27.jsonl), [ai_decision_requests_2026-07-27.jsonl](/home/ubuntu/KORStockScan/data/ai_decision_requests/ai_decision_requests_2026-07-27.jsonl), [threshold_runtime_env_2026-07-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-27.json)
  - 판정 기준: PREMARKET 결과가 `promoted_all_market_sessions_full`이면 runtime env/config의 global 활성화를 확인한다. 이후 각 venue/session과 endpoint에서 발생한 첫 자연 표본의 신규 문맥, completed-bar-only, exact request/response hash, `provider!=none`, effective venue/session, broker/market-data route 계약, 기존 hard safety 우선순위를 확인한다. 자연 발생하지 않은 endpoint와 session은 비활성이나 부분 적용으로 보지 않고 각각 `pending_natural_endpoints`, `pending_natural_sessions`로 둔다. 09:20부터는 `005930/096770/100090` 당일 KRX 정규장 source match와 exact payload/core endpoint 계약을 추가로 필수 확인한다.
  - rollback: 신규 문맥 누락·왜곡, source-quality blocked/conflict, provider none, semantic reject, cross-venue 오염, 신규 문맥 경로의 exception, 기존 guard 우선순위 변화 또는 09:20 이후 당일 KRX 필수 검증 실패가 확인되면 신규 문맥만 비활성화하고 주문·threshold·provider·bot·hard safety를 변경하지 않는다.
  - 다음 액션: `all_market_first_observation_pass`, `global_runtime_full_pending_natural_endpoint`, `rolled_back_context_only`, `promotion_not_authorized`, `observation_missing`, `route_or_guard_violation` 중 하나로 닫는다.

- [ ] `[AIDecisionQualityControlFreeze0727] 다중분봉 전면 적용 직후 현행 AI control manifest 고정` (`Due: 2026-07-27`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:00`, `Track: AIPrompt`)
  - Source: [ai_decision_trace.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_trace.py), [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py), [ai_prompt_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_prompt_contracts.py), [ai_decision_quality_control_2026-07-27.json](/home/ubuntu/KORStockScan/data/runtime/ai_decision_quality_control_2026-07-27.json)
  - 판정 기준: `input_preflight_mode=exact_v2`, entry-side `context_schema=entry_candle_context_v1`, holding/exit-side `context_schema=holding_decision_context_v1`, 공통 `input_bundle_version=scalping_multi_timeframe_context_v1`, stage별 current prompt version/hash, provider/model/model-id, temperature/reasoning budget, response schema를 control manifest에 고정한다. 다중분봉 전면 적용 외 prompt/model/provider/threshold/order 변경은 0건이어야 한다.
  - cohort: primary decision-quality 표본은 `replay_exact=true`, `request_capture_status=captured`, 같은 canonical context schema와 input bundle version, exact snapshot/payload hash, fresh conflict-free venue/session source를 갖춘 전면 적용 이후 자연 호출만 사용한다. Entry와 holding/exit paired cohort는 서로 합치지 않는다. `baseline_v1` proxy와 전면 적용 이전 payload는 discovery/reference cohort로 분리한다.
  - 다음 액션: `control_manifest_frozen_collect_exact_samples`, `control_manifest_gap_fix_required`, `exact_v2_not_ready_no_quality_baseline`, `promotion_failed_no_control_reset` 중 하나로 닫는다.

- [ ] `[AIDecisionOutcomeMaturityAndControlBaseline0727] 단계별 outcome 성숙·현행 AI 오판 기준선 생성` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 22:00~22:30`, `Track: AIPrompt`)
  - Source: [ai_decision_outcomes_2026-07-27.jsonl](/home/ubuntu/KORStockScan/data/ai_decision_outcomes/ai_decision_outcomes_2026-07-27.jsonl), [ai_decision_outcome_labels_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-07-27.json), [ai_decision_quality_baseline_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_decision_quality_baseline/ai_decision_quality_baseline_2026-07-27.json)
  - 구현 상태: pending 1/3/5/10/20/30/60분 label을 exact venue/session 가격 관측과 실제 주문·체결 correlation으로 성숙시키고 post-probe/scale-in/holding/exit/overnight stage outcome, realized/counterfactual 분리, 공통 오류 taxonomy를 생성하는 offline producer가 구현됐다. 당일 자연 표본과 horizon 성숙 전에는 `partial_horizons_keep_maturing`으로 유지한다.
  - 판정 기준: entry는 MFE/MAE와 target/adverse first-hit, post-probe는 잔량 submit/no-submit incremental path, scale-in은 추가 진입 이후 return/downside, holding은 secured upside와 enlarged loss, exit은 realized PnL·peak giveback·post-sell MFE/MAE, overnight는 next-session gap/MFE/MAE를 venue/session별로 성숙시킨다. Primary baseline horizon은 entry/entry-price/post-probe `10m`, scale-in `20m`, holding/exit `30m`, overnight `60m`로 고정한다. scale-in의 진정한 add/no-add incremental EV와 net profit은 notional·fill counterfactual join 전까지 `not_available`이며 realized와 counterfactual을 합치지 않는다.
  - 오류 taxonomy: `false_drop`, `false_wait`, `false_buy`, `bad_scale_support`, `bad_exit_defer`, `early_exit_support`, `unsupported_confidence`를 연속 outcome 값과 함께 집계한다.
  - 다음 액션: `control_error_baseline_ready`, `mature_label_producer_implementation_required`, `partial_horizons_keep_maturing`, `correlation_or_source_quality_gap` 중 하나로 닫는다.

- [ ] `[AIPromptV2PairedReplayReadiness0727] stage별 Prompt V2 동일 payload paired replay 착수 판정` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 22:30~23:00`, `Track: AIPrompt`)
  - Source: [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py), [ai_prompt_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_prompt_contracts.py), [ai_decision_quality_baseline_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_decision_quality_baseline/ai_decision_quality_baseline_2026-07-27.json), [ai_prompt_paired_replay_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_paired_replay/ai_prompt_paired_replay_2026-07-27.json)
  - 후보 계약: stage별 Prompt V2는 `edge_state=EDGE|NO_EDGE|INSUFFICIENT_DATA`, expected upside/downside, `trend`, `liquidity`, `tape`, `risk`, `uncertainty`, canonical reason codes를 반환한다. 형성봉과 완성봉, BBO/tape 시간 정합성, source 결손을 명시하고 score 단독 BUY/EXIT를 금지한다.
  - paired cohort: 동일 eligible trace ID·exact payload hash를 control prompt와 candidate prompt에 각각 재생한다. provider/model/temperature/reasoning budget은 동일하게 고정하며 outcome은 입력하지 않고 평가 join에만 사용한다. 후보는 주문·runtime 권한이 없다.
  - primary 판정: venue별 `source_quality_adjusted_ev_pct`, net profit, missed-upside, adverse-first BUY, incremental scale-in EV, harmful exit defer, early exit giveback, loss tail을 control 대비 비교한다. parse 성공률·latency는 보조 운영 지표다.
  - 다음 액션: `paired_replay_ready_build_stage_candidate`, `sample_floor_keep_collecting`, `mature_label_or_control_gap`, `candidate_rejected_no_runtime_apply` 중 하나로 닫는다.

- [ ] `[KRXOpenAPIAuthPreopen0727] 공식 KRX Open API 인증키 설정 및 KOSPI/KOSDAQ 일봉 smoke 확인` (`Due: 2026-07-27`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: RuntimeStability`)
  - Source: [KRX Open API 서비스 목록](https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd), [유가증권 일별매매정보](https://openapi.krx.co.kr/contents/OPP/USES/service/OPPUSES002_S2.cmd?BO_ID=JvJFzlAENzZlPBDNGAWC), [코스닥 일별매매정보](https://openapi.krx.co.kr/contents/OPP/USES/service/OPPUSES002_S2.cmd?BO_ID=hZjGpkllgCBCWqeTsYFj), [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py)
  - 사용자 과업: KRX Open API에서 두 일별매매정보 API의 이용신청·인증키 발급을 완료하고 실행 환경에 `KRX_OPEN_API_AUTH_KEY`를 secret으로 설정한다. 키 값이나 `AUTH_KEY` header는 문서, 명령 출력, trace, report에 남기지 않는다.
  - 판정 기준: `stk_bydd_trd`와 `ksq_bydd_trd`가 대상일 `basDd`에 대해 각각 정상 JSON을 반환하고 report `source_meta.krx.status=pass`, `auth_configured=true`, `auth_value_recorded=false`, `legacy_mdc_endpoint_called=false`를 기록해야 한다.
  - fallback: 키 미설정·승인대기·endpoint 장애는 `source_unavailable_reasoned`로 닫고 Naver 일봉 OHLC만 secondary 비교한다. 일봉 volume은 `NOT_COMPARABLE`이며 MDC `getJsonData.cmd`의 `HTTP 400 LOGOUT` 재시도로 우회하지 않는다.
  - 다음 액션: `krx_open_api_ready`, `auth_issue_pending_source_unavailable`, `endpoint_failure_use_reasoned_fallback`, `secret_persistence_violation_fix_required` 중 하나로 닫는다.

- [ ] `[ScannerAsyncEvalCommitRuntimeActivation0727] scanner_async_eval_commit_v1 별도 승인·우아한 재기동·전 venue 귀속` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: operator-approved`, `Track: RuntimeStability`)
  - Source: [hot_path_ai_dispatcher.py](/home/ubuntu/KORStockScan/src/engine/ai/hot_path_ai_dispatcher.py), [scanner_async_eval.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_async_eval.py), [scanner_runtime_scheduler.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_runtime_scheduler.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [scanner_scheduler_replay.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_scheduler_replay.py)
  - 현재 상태: `implemented_not_runtime_reflected`(scanner WATCHING/analyze_target 핵심 bridge). 시장자료 준비 worker 1개와 loaded OpenAI key 수 이내 AI dispatcher, generation별 중복 병합, deadline 이후 observation-only 폐기, main-thread generation·venue·source·fresh quote·position/order/cooldown 재검증이 구현됐다. holding score/flow, pre-submit retry, entry-price, gatekeeper의 공용 dispatcher 이관은 남아 있으므로 코드 소유 activation gate가 `async_v1` 요청을 `deadline_v1`로 fail-closed 처리한다. 현재 PID와 startup mode는 변경하지 않는다.
  - 적용 기준: 계획에 명시된 전체 hot-path endpoint의 dispatcher 이관과 endpoint별 state/version commit guard를 완료한 뒤 review finding 0건, targeted test·compile·parser·diff PASS, 16-symbol stress PASS와 `deadline_v1`의 PREMARKET→KRX→NXT 전체 운영주기 안전성·order/receipt/fast-exit cadence 비악화 확인, 현재 broker 보유·미체결 snapshot/reconciliation PASS가 모두 필요하다. 그 다음 코드 activation gate를 리뷰로 해제하고 사용자의 별도 재기동 승인을 받아 `KORSTOCKSCAN_SCANNER_SCHEDULER_MODE=async_v1`로 우아하게 재기동한다. KRX·PREMARKET_KRX_LIKE·NXT 결과는 분리 귀속한다.
  - rollback: stale/superseded generation broker 도달, 중복 submit, worker의 DB/runtime truth 또는 broker mutation, hard exit/receipt 지연, 가격·수량 불변식 위반, venue/source 혼입, `provider=none` 또는 failback 계약 위반 시 `async_v1 -> deadline_v1`로 되돌린다.
  - 다음 액션: `complete_hot_path_endpoint_migration`, `implemented_not_runtime_reflected`, `async_v1_runtime_attribution_started`, `async_v1_full_cycle_pass`, `rollback_to_deadline_v1` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-24` postclose -> `2026-07-27`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0727] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-27`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-24.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0727] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-27`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-24.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-24.json), [code_improvement_workorder_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-24.json), [threshold_apply_2026-07-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-27.json), [threshold_runtime_env_2026-07-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-27.json), [threshold_runtime_env_verify_2026-07-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-27.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`2`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0727] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-24.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0727] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-24.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0727] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-27.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-27.jsonl), [threshold_events_2026-07-27.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-27.jsonl), [observation_source_quality_audit_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-27.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-27 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

- [ ] `[AIInputExternalValidationKRX0920] KRX 09:20 완성분 AI 입력·외부값 동시 캡처` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:25`, `Track: ScalpingLogic`)
  - Source: [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py), [entry_context_intraday_probe.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_context_intraday_probe.py), [ai_input_external_validation_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_input_external_validation/ai_input_external_validation_2026-07-27.json)
  - 판정 기준: `005930`, `096770`, `100090`의 동일 venue/session/수정주가/완성봉을 캡처하고 인증형 KRX Open API 일봉 primary 또는 사유가 명시된 Naver OHLC fallback, 비교 가능한 필수 필드 `MISMATCH=0`, endpoint 실제 호출 `provider!=none`, 응답 의미계약 통과를 확인한다.
  - 금지: 검증 결과를 라이브 AI prompt, threshold, provider route, 주문, bot 재시작 또는 live promotion에 연결하지 않는다. `runtime_effect=false`, `actual_order_submitted=false`를 유지한다.
  - 다음 액션: `external_match_pass`, `source_unavailable_reasoned`, `basis_not_comparable`, `mismatch_investigate_no_runtime_apply`, `provider_or_schema_fail` 중 하나로 닫는다.

- [ ] `[AIInputExternalValidationKRX1030] KRX 10:30 완성분 AI 입력·외부값 동시 캡처` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 10:30~10:35`, `Track: ScalpingLogic`)
  - Source: [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py), [entry_context_intraday_probe.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_context_intraday_probe.py), [ai_input_external_validation_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_input_external_validation/ai_input_external_validation_2026-07-27.json)
  - 판정 기준: `005930`, `096770`, `100090`의 동일 venue/session/수정주가/완성봉을 캡처하고 비교 가능한 필수 필드 `MISMATCH=0`, endpoint 실제 호출 `provider!=none`, 응답 의미계약 통과를 확인한다.
  - 금지: 검증 결과를 라이브 AI prompt, threshold, provider route, 주문, bot 재시작 또는 live promotion에 연결하지 않는다. `runtime_effect=false`, `actual_order_submitted=false`를 유지한다.
  - 다음 액션: `external_match_pass`, `source_unavailable_reasoned`, `basis_not_comparable`, `mismatch_investigate_no_runtime_apply`, `provider_or_schema_fail` 중 하나로 닫는다.

- [ ] `[AIInputExternalValidationKRX1430] KRX 14:30 완성분 AI 입력·외부값 동시 캡처` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 14:30~14:35`, `Track: ScalpingLogic`)
  - Source: [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py), [entry_context_intraday_probe.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_context_intraday_probe.py), [ai_input_external_validation_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_input_external_validation/ai_input_external_validation_2026-07-27.json)
  - 판정 기준: `005930`, `096770`, `100090`의 동일 venue/session/수정주가/완성봉을 캡처하고 비교 가능한 필수 필드 `MISMATCH=0`, endpoint 실제 호출 `provider!=none`, 응답 의미계약 통과를 확인한다.
  - 금지: 검증 결과를 라이브 AI prompt, threshold, provider route, 주문, bot 재시작 또는 live promotion에 연결하지 않는다. `runtime_effect=false`, `actual_order_submitted=false`를 유지한다.
  - 다음 액션: `external_match_pass`, `source_unavailable_reasoned`, `basis_not_comparable`, `mismatch_investigate_no_runtime_apply`, `provider_or_schema_fail` 중 하나로 닫는다.

- [ ] `[AIInputExternalValidationNXT1610] NXT 16:10 완성분 시장분리 AI 입력·외부값 동시 캡처` (`Due: 2026-07-27`, `Slot: INTRADAY`, `TimeWindow: 16:10~16:15`, `Track: ScalpingLogic`)
  - Source: [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py), [entry_context_intraday_probe.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_context_intraday_probe.py), [ai_input_external_validation_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/ai_input_external_validation/ai_input_external_validation_2026-07-27.json)
  - 판정 기준: `005930_NX`를 NXT venue/session으로 명시해 캡처하고 Kiwoom 원응답→정규화→AI payload 내부 변환을 검증한다. 네이버 KRX+NXT 통합값은 KRX/NXT 단독값과 엄격 비교하지 않고 `NOT_COMPARABLE` 사유를 남긴다.
  - 금지: 통합값을 NXT 단독값으로 간주하거나 검증 결과를 라이브 AI prompt, threshold, provider route, 주문, bot 재시작 또는 live promotion에 연결하지 않는다.
  - 다음 액션: `internal_transform_match`, `external_basis_not_comparable`, `source_unavailable_reasoned`, `market_route_conflict`, `provider_or_schema_fail` 중 하나로 닫는다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0727] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-27.json), [threshold_cycle_ev_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-27.json), [code_improvement_workorder_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-27.json), [threshold_cycle_postclose_verification_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-27.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0727] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-24.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0727] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-24.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0727] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-24.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-24.md), [code_improvement_workorder_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-24.json)
  - 판정 기준: selected_order_count=182와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0727] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-24.json), [runtime_apply_gap_audit_2026-07-24.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-24.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`101`, rollup_required_count=`101`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 100}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0727] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-24.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-24.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
