# Threshold Cycle Operations

작성 기준: `2026-05-22 KST`

이 디렉토리는 threshold 후보 수집, 장후 calibration, 장전 bounded runtime env apply, daily EV 리포트를 저장한다. 현재 원칙은 완전 무인 `auto_bounded_live` apply이며, 장중 runtime threshold 자동 변경은 계속 금지한다.

report 기반 자동화의 전체 추적성은 [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)를 기준으로 본다. 이 문서는 산출물별 producer/consumer와 현재 apply 단계만 설명하고, 미래 작업 owner는 날짜별 checklist가 소유한다.

적용 범위는 스캘핑 전용이 아니다. 이 README는 스캘핑과 스윙이 공통 threshold-cycle, daily EV, preopen runtime env, code-improvement workorder 체인에 들어오는 부분의 산출물 정의다. 스캘핑 `scalp_ai_buy_all` live simulator는 `scalp_sim_*` pipeline event와 quote-based completed rows를 만들며, report는 `real`/`sim`/`combined`를 분리 표시한다. `combined`는 diagnostic-only이며 실매매 동급 calibration, broker execution 품질, 실주문 전환 근거로 사용하지 않는다. 스윙 전용 `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` lifecycle 산출물은 `swing_lifecycle_audit`/`swing_improvement_automation`/`swing_runtime_approval`/`swing_sim_auto_approval` artifact를 함께 기준으로 본다. 일반 스윙 dry-run env 반영은 hard floor/source-quality와 parsed AI Tier2 review가 닫힌 `dry_run_auto_apply_ready`일 때 pre-final auto approval로 다음 장전 env에 반영한다. Tier2 missing/unavailable/parse-rejected는 fail-closed다. 반영 후에도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`와 브로커 주문 차단은 유지된다. broker execution 품질 수집용 `swing_one_share_real_canary_phase0`와 `swing_scale_in_real_canary_phase0`는 parsed AI Tier2 review와 source report hard floor/source-quality/allowlist/cap 통과 시 phase0 자동승인으로 다음 장전 env에 반영될 수 있다. 사용자 승인은 final full live conversion, bounded cap 초과 cap release, provider/bot 변경, hard/protect/emergency safety 완화에만 남긴다.

## 운영 흐름

| 시점 | wrapper | 역할 | 산출물 |
|---|---|---|---|
| runtime | `src.utils.pipeline_event_logger` | threshold 후보 stage를 compact stream에 적재 | `threshold_events_YYYY-MM-DD.jsonl` |
| POSTCLOSE 16:10 | `deploy/run_threshold_cycle_postclose.sh` | raw pipeline event를 family partition으로 backfill하고 장후 report, AI correction, ADM/lifecycle matrix, lifecycle AI context attribution/context, scalping/swing automation, latency classifier 추천, daily EV report를 생성 | `date=YYYY-MM-DD/family=*/part-*.jsonl`, `data/report/threshold_cycle_YYYY-MM-DD.json`, 파생 `statistical_action_weight`, `scalp_entry_action_decision_matrix`, `lifecycle_decision_matrix`, `lifecycle_ai_context_attribution`, `lifecycle_ai_context`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative` JSON/MD, `threshold_cycle_ai_review_YYYY-MM-DD_postclose.{json,md}`, `latency_classifier_recommendation_YYYY-MM-DD.{json,md}`, `scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}`, `swing_improvement_automation_YYYY-MM-DD.{json,md}`, `swing_runtime_approval_YYYY-MM-DD.{json,md}`, `swing_pattern_lab_automation_YYYY-MM-DD.{json,md}`, `threshold_cycle_ev_YYYY-MM-DD.{json,md}`, `runtime_approval_summary_YYYY-MM-DD.{json,md}`, `runtime_apply_gap_audit_YYYY-MM-DD.{json,md}`, `data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_YYYY-MM-DD.status.json` |
| PREOPEN 07:35 | `deploy/run_threshold_cycle_preopen.sh` | 최신 threshold report와 AI correction guard를 읽어 auto bounded runtime env 생성 | `apply_plans/threshold_apply_YYYY-MM-DD.json`, `runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}`, `data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_YYYY-MM-DD.status.json` |

cron completion detector는 wrapper log의 terminal marker를 source of truth로 본다. Threshold cycle postclose wrapper는 같은 `target_date`를 포함해 `[START]`, `[DONE]`, `[FAIL]` marker를 남겨야 하며, 완료 marker는 `[DONE] threshold-cycle postclose target_date=YYYY-MM-DD`다. artifact가 생성됐지만 marker가 없으면 threshold/runtime 실패가 아니라 wrapper/log 계약 결함으로 분류하고 marker 계약을 먼저 보강한다. `2026-05-22`부터 `12:05` intraday calibration cron은 제거됐고, intraday phase artifact는 명시 수동 forensic/legacy override가 있을 때만 생성한다.

`artifact_freshness`는 `.json` artifact가 존재하더라도 generic JSON parse 검증을 먼저 수행한다. 깨진 JSON은 one-shot fresh로 통과하지 않으며, critical artifact는 fail로 닫는다. `threshold_cycle_preopen_status`와 `threshold_cycle_postclose_status`는 `status=succeeded`만 pass로 보며, lock skip/running/failed는 조용한 성공이 아니라 status artifact warning/fail 입력으로 남긴다.

## 현재 적용 정책

- `THRESHOLD_CYCLE_APPLY_MODE` 기본값은 `auto_bounded_live`다.
- `threshold_cycle_preopen_apply`는 `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`, `auto_bounded_live`를 허용한다. `auto_bounded_live`는 승인 대기 없이 deterministic guard + AI correction guard를 통과한 family만 장전 runtime env 파일로 반영한다.
- apply plan은 자동 적용 후보/차단 사유/safety guard/calibration trigger context를 남기는 source of truth artifact다.
- 목표 미달은 rollback이 아니라 다음 manifest의 `calibration_state=adjust_up|adjust_down|hold|hold_sample|hold_no_edge|freeze`로 처리한다.
- sample 부족은 live 전면 금지가 아니라 `cap 축소`, `hold_sample`, `max_step_per_day 축소` 중 하나로 처리한다.
- `safety_revert_required=true`는 hard/protect/emergency stop 지연, 주문 실패, receipt/provenance 손상, same-stage owner 충돌, severe loss guard 초과에만 쓴다.
- 실제 env 반영은 다음 장전 1회 bounded apply로 자동 수행한다. 코드 hot mutation은 하지 않고, `src/run_bot.sh`가 당일 `runtime_env/threshold_runtime_env_YYYY-MM-DD.env`를 기동 시 source한다.
- scheduled calibration artifact는 매일 장후 1회 생성한다. 장중 intraday phase는 명시 수동 forensic/legacy override가 있을 때만 실행하며, canonical postclose threshold report를 덮어쓰지 않고 next-preopen apply 필수 단계가 아니다.
- postclose 제출물은 `threshold_cycle_ev_YYYY-MM-DD.{json,md}` daily EV 리포트로 통일한다. 스윙은 예외적으로 `swing_runtime_approval`의 요청을 daily EV와 preopen apply manifest에 노출한다. 일반 swing dry-run runtime 요청은 parsed AI Tier2 + deterministic guard가 닫힌 `dry_run_auto_apply_ready`일 때 approval artifact 없이 env를 쓸 수 있으며, Tier2 실패는 fail-closed다. phase0 `swing_one_share_real_canary_phase0`와 `swing_scale_in_real_canary_phase0`는 parsed AI Tier2 + source report auto approval로 env를 쓸 수 있다.
- `lifecycle_decision_matrix_runtime`은 ADM 확장 umbrella family다. 기본 OFF이며 selected될 때만 다음 PREOPEN env에 policy file/version/promote cap을 쓴다. hard safety와 broker/account/order guard는 항상 우선한다.
- `market_regime_continuous_thresholds`는 daily report/cache의 0~100 시장국면 연속 점수를 threshold-cycle source bundle에 등록하는 1차 family다. `allowed_runtime_apply=false`, `runtime_effect=false`로 시작하며 ADM/LDM `risk_context` feature와 label별 EV 진단 외에는 쓰지 않는다.
- 기존 fixed threshold는 role contract로 처리한다. broker/stale/price freshness/stop/account/order/qty/cooldown은 `hard_safety`, `BUY_SCORE_THRESHOLD`와 entry score cutoff/VPW/strength/momentum은 `baseline_prior`, score65_74/soft stop/holding/scale-in price guard는 `bounded_tunable`, latency DANGER/stale/broker submit 차단은 `hard_safety_submit_quality`, fallback/legacy latency/shadow 축은 `legacy_archive`다.
- `BUY Funnel Sentinel`은 `submitted/ai < 20.0%` 또는 `submitted/budget <= 10.0%`이고 각각 `ai_confirmed unique >=20`, `budget_pass unique >=3` floor를 만족하면 `SUBMIT_DROUGHT_CRITICAL`로 강제 표면화한다. 이 상태는 `operator_action_required=false`이며 postclose code-improvement workorder와 LDM `submit_bucket_attribution`에 자동 handoff한다. `threshold_cycle_ev`, `runtime_approval_summary`, postclose verifier가 이 handoff를 소비하지 못하면 `buy_funnel_submit_drought_handoff_missing`으로 실패한다. 단, threshold/order/provider/bot restart나 broker/stale/account/order/qty/cooldown guard 우회는 자동 수행하지 않는다.
- `runtime_apply_gap_audit`는 `runtime_approval_summary` 이후, 다음 checklist와 postclose verifier 이전에 실행한다. discovery/bridge/runtime summary/workorder/preopen/post-apply attribution의 생산/소비 drift를 후보별 ledger로 닫고, positive EV + source-quality pass 후보가 source-only에 묻히면 FAIL 또는 Codex 작업지시로 표면화한다. 내부 AI reviewer prompt는 영어와 `gpt-5.4` 이상 strict JSON schema를 사용하고, 사용자-facing Markdown은 한글이다. 산출물 자체는 `runtime_effect=false`, `allowed_runtime_apply=false`이며 runtime mutation executor가 아니다.
- 스윙 entry 병목은 `swing_lifecycle_audit.swing_entry_bottleneck`이 소유한다. `SWING_ENTRY_DROUGHT_CRITICAL`이면 `swing_improvement_automation`이 `order_swing_entry_bottleneck_auto_resolution`을 만들고, Swing LDM과 `swing_lifecycle_bucket_discovery`가 `next_route=code_improvement_workorder` source-only 후보로 표면화한다. `build_code_improvement_workorder`는 이 order를 selection limit과 무관하게 강제 포함하고, postclose verifier는 downstream 누락을 `swing_entry_bottleneck_handoff_missing`으로 fail 처리한다. 이 계약은 `operator_action_required=false`, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`다.
- `latency_classifier_runtime_profile`은 더 이상 CAUTION을 제출 차단으로 소유하지 않는다. runtime `EntryPolicy`는 slippage check 이후 `SAFE`와 `CAUTION`을 normal submit으로 보내고, `DANGER`, stale quote, broker/account/order/qty/cooldown guard만 차단한다. `latency_classifier_recommendation`은 DANGER/stale/broker submit 품질 감사와 counterfactual 근거 확인용 report로 유지하며, adaptive latency env apply는 `allowed_runtime_apply=false`가 기본이다.

## 주요 경로

| 경로 | 의미 |
|---|---|
| `threshold_events_YYYY-MM-DD.jsonl` | runtime compact event stream |
| `snapshots/pipeline_events_YYYY-MM-DD_*.jsonl` | POSTCLOSE collector가 live append 중인 raw 파일 대신 읽는 immutable source snapshot |
| `date=YYYY-MM-DD/family=*/part-*.jsonl` | family별 report 입력 partition |
| `checkpoints/YYYY-MM-DD.json` | incremental backfill resume/checkpoint |
| `apply_plans/threshold_apply_YYYY-MM-DD.json` | 장전 apply plan artifact |
| `runtime_env/threshold_runtime_env_YYYY-MM-DD.env` | 봇 기동 시 source되는 bounded runtime env override |
| `runtime_env/threshold_runtime_env_YYYY-MM-DD.json` | runtime env override와 selected family provenance |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | 장후 canonical threshold report |
| `data/report/report_YYYY-MM-DD.json` | daily market report. `market_regime_continuous_score`, label, component scores, legacy gate score를 threshold-cycle source bundle과 ADM/LDM risk context에 제공 |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | action weight 파생 artifact |
| `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.{json,md}` | Entry ADM action matrix artifact. direct ADM env 또는 lifecycle adapter source |
| `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_YYYY-MM-DD.{json,md}` | 개별 후보 lifecycle row, fixed threshold contract, stage별 weighted ADM policy artifact. selected family가 될 때만 다음 PREOPEN policy env로 소비 |
| `data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_YYYY-MM-DD.{json,md}` | lifecycle AI context가 AI action/EV에 기여했는지 postclose에서 stage별로 집계하는 feedback artifact. context contribution은 bounded auxiliary weight로만 LDM에 반영 |
| `data/report/lifecycle_ai_context/lifecycle_ai_context_YYYY-MM-DD.{json,md}` | LDM/ADM/source-quality/attribution을 OpenAI entry/holding/exit prompt용 context로 압축하는 context-only artifact. real order gate/provider/bot restart 근거 아님 |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | AI decision-support matrix 파생 artifact |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | 누적/rolling cohort 기반 threshold cycle 파생 artifact |
| `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_postclose.{json,md}` | scheduled AI correction proposal + deterministic guard 파생 artifact. `_intraday` review는 manual forensic/legacy manifest-only source이며 runtime apply source가 아니다 |
| `data/report/latency_classifier_recommendation/latency_classifier_recommendation_YYYY-MM-DD.{json,md}` | 전일 `latency_block`의 age/jitter/spread profile을 평가한다. `SAFE`와 `CAUTION`은 slippage check 이후 normal submit semantics로 보며, `DANGER`/stale/broker safety 차단과 counterfactual EV, missed/avoided label, stale/broker exclusion을 기록한다. adaptive latency env apply는 기본 차단이며, 제출 고갈은 `BUY Funnel Sentinel`의 `SUBMIT_DROUGHT_CRITICAL`이 별도 incident로 표면화한다 |
| `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}` | Gemini/Claude pattern lab 기반 improvement order 및 auto family 후보 artifact. runtime/code 직접 변경 없음 |
| `data/runtime/scalp_live_simulator_state.json` | 스캘핑 live simulator open sim 포지션 복원 상태. threshold report 입력은 이 파일이 아니라 `scalp_sim_*` pipeline events를 기준으로 한다 |
| `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.{json,md}` | 스윙 선정-DB 적재-진입-보유-추가매수-청산 lifecycle audit artifact. runtime/code 직접 변경 없음 |
| `data/report/swing_threshold_ai_review/swing_threshold_ai_review_YYYY-MM-DD.{json,md}` | 스윙 threshold/logic proposal-only review artifact. 기본 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none`이라 OpenAI 호출 없이 생성하며, 명시적으로 `openai`를 준 경우에만 AI review를 수행한다. deterministic guard와 수동 workorder가 최종 source of truth |
| `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.{json,md}` | 스윙 lifecycle 기반 improvement order 및 auto family 후보 artifact. 모든 order는 `runtime_effect=false`, family candidate는 `allowed_runtime_apply=false`로 시작 |
| `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.{json,md}` | 스윙 hard floor + EV trade-off score 기반 요청과 blocked reason. 일반 dry-run runtime 후보는 parsed AI Tier2 review 통과 시 `dry_run_auto_apply_ready` pre-final auto approval로 다음 PREOPEN에 소비될 수 있다. Phase0 one-share/scale-in real canary 요청은 parsed AI Tier2 review와 source-quality/cap/allowlist 통과 시 `auto_approved_real_canary`로 다음 PREOPEN에 소비될 수 있다. Final full-live/cap/provider/bot/safety 변경은 user approval 전용이다 |
| `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.{json,md}` | 스윙 safe pool 후보는 8개 arm, bottom rebound source 후보는 전용 anticipatory 3-arm으로 확장하는 source-only artifact |
| `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.{json,md}` | discovery arm의 `1d/5d/10d/policy_exit` label과 `PENDING_ENTRY/ENTERED/EXITED/EXPIRED` 상태 전개 artifact |
| `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.{json,md}` | discovery arm별/정책별/sector-theme별 source-only EV, surviving arm, avoid bucket artifact. runtime env apply 권한 없음 |
| `data/runtime/swing_strategy_discovery/sector_theme_map_YYYY-MM-DD.json` | discovery candidate의 sector/theme enrichment cache. 섹터/업종은 수동 reference(`KORSTOCKSCAN_SWING_SECTOR_MANUAL_FILE` 또는 `docs/reference/data_5126_YYYYMMDD.xlsx`), 테마는 키움 `ka90001 qry_tp=2` 기준으로 기록하며 실패 시 fallback/missing source-quality로 남긴다 |
| `data/threshold_cycle/sim_auto_approvals/swing_sim_auto_approval_YYYY-MM-DD.json` | Swing LDM과 bottom rebound sim-only 승격 결과를 단일 control-tower artifact로 합치는 source-only approval |
| `data/threshold_cycle/swing_sim_policies/swing_sim_policy_catalog_YYYY-MM-DD.json` | 다음 PREOPEN swing sim policy input catalog. 실주문/runtime threshold 변경 권한 없음 |
| `data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_YYYY-MM-DD.json` | `scalp_sim_scale_in_window_expansion` sim-auto artifact. It defaults to `approved=true`, `approval_state=sim_auto_approved`, and `human_approval_required=false` only when the lifecycle matrix source report is readable. Missing source closes as `source_quality_blocked`; preopen may apply only next PREOPEN sim-source env values. Real scale-in, cap release, hard-safety relaxation, provider changes, and bot restart are forbidden |
| `data/threshold_cycle/approvals/swing_runtime_approvals_YYYY-MM-DD.json` | Final-stage user approval artifact. Pre-final dry-run and bounded real-canary auto approvals do not require this artifact, but final full-live conversion, cap release beyond bounded limits, provider/bot changes, and hard/protect/emergency safety relaxation do |
| `data/threshold_cycle/approvals/swing_one_share_real_canary_YYYY-MM-DD.json` | 스윙 초기 BUY/SELL 1주 real canary 전용 optional narrowing artifact. Phase0 auto approval은 parsed AI Tier2가 통과한 source report allowlist/cap을 기본으로 쓰며, 이 artifact가 있으면 종목 allowlist와 cap을 더 좁힐 수 있다 |
| `data/threshold_cycle/approvals/swing_scale_in_real_canary_YYYY-MM-DD.json` | 승인된 real swing holding의 AVG_DOWN/PYRAMID 1주 추가매수 real canary 전용 optional narrowing artifact. Phase0 auto approval은 parsed AI Tier2가 통과한 source report arm/cap을 기본으로 쓰며, 이 artifact가 있으면 arm과 cap을 더 좁힐 수 있다 |
| `data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_YYYY-MM-DD.{json,md}` | DeepSeek 스윙 pattern lab 기반 automation artifact. fresh single-day 조건 미충족 시 warning만 남기고 order로 승격하지 않음 |
| `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}` | 완전 무인 반영 이후 daily EV 성과 제출 artifact |
| `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.{json,md}` | 스캘핑 selected family, 스윙 approval request, panic approval 후보를 묶은 read-only 요약 artifact. runtime mutation 권한 없음 |
| `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.{json,md}` | runtime uptake gap watchdog. 후보별 ledger, retry queue, Codex 작업지시, AI reasoning review를 남기며 runtime mutation 권한 없음 |

## 누적/rolling threshold cycle report

`threshold_cycle_cumulative` artifact는 daily report를 대체하지 않는다. 역할은 `daily`, `rolling`, `cumulative`가 같은 방향을 가리키는지 확인해 threshold 후보의 지속성을 보는 report-only 입력이다.

기본 구간:

- cumulative: `2026-04-21` 이후 `post_fallback_deprecation` 구간
- rolling: 최근 `5/10/20` calendar-day window
- completed 손익 기준: `COMPLETED + valid profit_rate`
- cohort: `all_completed_valid`, `normal_only`, `initial_only`, `pyramid_activated`, `reversal_add_activated`

금지선:

- 누적 평균 단독으로 live threshold mutation을 수행하지 않는다.
- full/partial fill split이 없는 누적 손익은 hard 승인 근거로 쓰지 않는다.
- `main_only`/runtime flag cohort/source provenance가 비어 있으면 방향성 판정으로 격하한다.
- 누적/rolling은 추천값 확정이 아니라 방향성과 step size 산정에만 사용한다.

## bounded calibration loop

`threshold_cycle_YYYY-MM-DD.json`은 기존 `apply_candidate_list` 외에 다음 섹션을 가진다.

- `calibration_candidates`: family별 `threshold_version`, target env keys, current/recommended/applied values, bounds, `max_step_per_day`, sample floor, confidence, `calibration_state`, `safety_revert_required`를 담는다.
- `sample_window`/`window_policy`: family별로 당일 데이터와 4월 이후 누적/rolling 데이터의 역할을 분리한다. 당일 운영 상태로 판단할 family와 누적 지속성이 필요한 family를 섞지 않는다.
- `calibration_source_bundle`: `data/report`의 기존 보유/청산 리포트 경로와 soft-stop tail/defer cost/trailing/safety 요약을 담는다.
- `trade_lifecycle_attribution`: `record_id` 기준으로 진입 주문/취소, 보유 중 후보 신호, 청산 rule/source, 장후 `post_sell_evaluations`를 join해 전중후 유형을 닫는다. runtime stage는 provisional signal이고, 최종 유형은 post-sell outcome이 붙은 뒤 family view로 제공한다.
- `post_apply_attribution`: threshold version별 applied/not-applied cohort key와 GOOD_EXIT/MISSED_UPSIDE/soft-stop tail/defer cost/safety breach metric 정의를 담는다.
- `safety_guard_pack`: 원복 후보를 safety breach로만 제한한다.
- `calibration_trigger_pack`: 목표 미달, 표본 부족, 방향성 불일치의 다음 calibration action을 담는다.

bounded calibration family는 아래 묶음이 중심이다. 목적은 완벽한 threshold spot 탐색이 아니라 efficient trade-off 지점의 bounded live canary와 자동 calibration이다.

1. `lifecycle_decision_matrix_runtime`: Entry ADM, Holding/Exit ADM, submit, scale-in adapter를 감싼 umbrella weighted ADM runtime 후보. selected 시에도 hard safety 우회 없이 policy file/version/promote cap만 다음 PREOPEN env로 전달한다.
2. `score65_74_recovery_probe`: family id는 유지하지만 current runtime floor는 score60이다. broad score threshold 완화가 아니라 score60~74, latency DANGER 제외, 수급/가속/micro-VWAP 유지, 1주/5만원 cap 후보
3. `latency_classifier_runtime_profile`: 전일 latency_block의 age/jitter/spread를 감사하되 CAUTION submit 차단은 제거한다. `SAFE`/`CAUTION`은 slippage check 이후 normal submit, `DANGER`/stale/broker safety만 차단으로 본다.
4. `bad_entry_refined_canary`: naive hard block 재개가 아니라 soft-stop tail/defer cost 감소 후보. `bad_entry_refined_candidate`는 runtime provisional signal이며, 최종 유형은 장후 `post_sell_evaluations`가 `record_id`로 join된 뒤 lifecycle attribution으로만 닫는다.
5. `soft_stop_whipsaw_confirmation`
6. `holding_flow_ofi_smoothing`
7. `protect_trailing_smoothing`
8. `holding_exit_decision_matrix_advisory`: SAW `candidate_weight_source`가 만든 non-`no_clear_edge` matrix bucket만 advisory canary 후보
9. `trailing_continuation`: GOOD_EXIT 훼손 리스크가 커서 1차 loop에서는 `freeze/report_only_calibration`만 허용
10. `market_regime_continuous_thresholds`: `market_regime_continuous_score` label threshold와 component weight를 rolling 10d source bundle에 등록한다. 1차 개발은 manifest-only/context-only이며, `KORSTOCKSCAN_MARKET_REGIME_*` env 반영은 별도 2차 review 전까지 금지한다.

### Lifecycle Decision Matrix와 fixed threshold

`lifecycle_decision_matrix`는 score bucket별 고정 정책이 아니라 개별 sim/real/probe 후보의 lifecycle row를 stage별 matrix로 만든다. runtime feature와 사후 label을 분리하고, `stage_ev_composite_pct`와 confidence를 산출해 `BUY_DEFENSIVE`, `WAIT_REQUOTE`, `DROP`, `ALLOW_SUBMIT`, `HOLD`, `EXIT`, `AVG_DOWN_BIAS`, `PYRAMID_BIAS`, `NO_CHANGE` 중 stage별 허용 action만 제안한다. `entry_bucket_attribution`, `submit_bucket_attribution`, `scale_in_bucket_attribution`은 source-only bucket EV/contract gap, runtime approval candidate, code-improvement workorder를 만들며, `threshold_cycle_ev`/`runtime_approval_summary`/`code_improvement_workorder`로 전달되지 않으면 postclose verifier가 fail-closed한다.

`producer_gap_discovery`는 postclose source-only missing producer 발굴 단계다. `sim_post_sell_evaluations`, LDM/discovery, swing strategy discovery EV, Swing LDM/bucket/audit 산출물을 읽어 stop recovery, missed fill recovery, swing label/source handoff, scale-in counterfactual gap 후보를 결정론으로 만든 뒤 OpenAI two-pass AI review가 priority, 구현요건, acceptance test를 보강한다. AI unavailable/parse reject/audit fail은 fail-closed이며, high-priority `code_improvement_orders`는 `build_code_improvement_workorder` selected order에 강제 포함된다. 이 산출물은 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`이고 실주문 enable, threshold mutation, provider change, bot restart, cap release, entry/exit override에 사용할 수 없다.

fixed threshold의 runtime 우선순위는 `hard safety veto -> account/order/broker guard -> lifecycle matrix runtime policy -> 기존 ADM adapter -> baseline fixed threshold fallback`이다. `baseline_prior`로 전환된 score/strength/momentum threshold는 후보 생성과 feature 역할만 하고 단독으로 BUY/WAIT/DROP을 확정하지 않는다. `bounded_tunable` 값은 matrix가 추천할 수 있지만 기존 bounds, max step, sample floor, source-quality gate를 통과해 다음 PREOPEN에만 반영된다.

soft-stop balanced 기준은 완벽한 승률이 아니라 trade-off 기준이다. GOOD_EXIT 훼손은 `+10%p`까지 허용하고, soft-stop 손실 tail 감소 또는 MISSED_UPSIDE 감소가 있으면 유지 또는 완만 조정 대상으로 본다.

`pre_submit_price_guard`는 entry price owner 내부 attribution family다. `WAIT+score>=75+DANGER+1주 cap+USE_DEFENSIVE` 표본은 broad score 완화나 fallback 재개가 아니라 `passive_probe` lifecycle로 태그한다. runtime은 방어가가 best bid보다 과도하게 낮으면 bid-1tick까지 보정하고, passive probe timeout은 30초로 줄이며, submit revalidation age와 cancel request/confirm provenance를 compact event에 남긴다. 이 표본은 `pre_submit_price_guard` report와 daily EV에서 미체결/취소 비용을 평가하는 입력이며, 새 관찰축으로 분리하지 않는다.

### Latency classifier runtime profile

`latency_classifier_runtime_profile`은 실매매 submit 직전 latency 품질 감사 owner다. runtime path는 `EntryPolicy`를 평가하되 CAUTION은 slippage check 이후 normal submit으로 단순화했고, `DANGER`, hard safety, stale quote, broker/account/order/qty/cooldown guard를 우회하지 않는다. 제출 고갈 자체는 `BUY Funnel Sentinel`의 `SUBMIT_DROUGHT_CRITICAL` incident가 소유한다.

적용 경로:

1. R0 수집: `latency_block`, `latency_pass`, `order_bundle_submitted`는 `reason`, `latency_state`, `policy_decision`, `effective_decision`, `ws_age_ms`, `ws_jitter_ms`, `spread_ratio`, `quote_stale`, `signal_price`, `latest_price`, `latency_canary_applied`, `latency_canary_reason`, `threshold_family`, `runtime_effect`, `actual_order_submitted`, `broker_order_forbidden`를 남긴다.
2. R1/R2 분석: `latency_classifier_recommendation`이 `SAFE/CAUTION normal submit semantics`, `DANGER/stale/broker hard reject`를 분리하고, `missed_entry_counterfactual` label로 latency 차단이 실제 손실 회피를 증명하는지 계산한다.
3. R3 후보: candidate의 primary metric은 `counterfactual_ev_pct_after_runtime_semantics`다. `quote_stale=true`, broker guard 우회 필요 후보, label sample 부족, negative EV는 `hold|reject`로 닫는다.
4. R4/R5 적용: `threshold_cycle_preopen_apply`는 latency adaptive env를 기본 생성하지 않는다. 과거 recovery/caution env key가 남아 있어도 CAUTION submit 차단 복구 후보로 해석하지 않고, 별도 workorder와 counterfactual proof 없이는 `allowed_runtime_apply=false`로 둔다.
5. R6 피드백: 다음 postclose에서 predicted recovery와 실제 `latency_pass`, `order_bundle_submitted`, 후행 fill/exit outcome을 비교한다.

`pre_submit_price_guard`는 이 결과를 daily EV에 함께 노출할 수 있지만, `latency_pass_events=0`의 primary owner가 아니다. price guard는 quote/price 품질을 보는 후행 safety layer로 유지한다.

## AI correction proposal layer

`threshold_cycle_ai_review` artifact는 AI를 검토자뿐 아니라 이상치 수정안 제안자로 쓰기 위한 보조 layer다. deterministic `calibration_candidates`가 source of truth이며, AI correction은 후보 위에 아래 필드를 덧붙인다.

- `ai_proposed_value`
- `ai_proposed_state`
- `ai_anomaly_route`
- `ai_required_evidence`
- `guard_accepted`
- `guard_reject_reason`

AI가 제안할 수 있는 범위는 `adjust_up|adjust_down|hold|hold_sample|freeze`, family bounds 안의 후보값, 이상치 routing(`threshold_candidate|incident|instrumentation_gap|normal_drift`), sample window(`daily_intraday|rolling_5d|rolling_10d|cumulative`)까지다. AI 단독 env/code/runtime 직접 변경, 장중 threshold mutation, safety guard 우회, `safety_revert_required` 강제 변경, 단일 사례 live enable 확정은 금지한다.

실행 방식은 세 가지다. `daily_threshold_cycle_report` 직접 실행 기본값은 provider를 호출하지 않고 deterministic calibration과 `ai_status=unavailable` artifact를 남긴다. postclose cron wrapper는 `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai`를 기본으로 넣어 장후 AI correction proposal 생성을 자동 시도한다. OpenAI correction은 Responses API와 `threshold_ai_correction_v1` strict JSON schema를 사용하며, 모델은 `GPT_THRESHOLD_CORRECTION_MODEL=gpt-5.5`, fallback은 `GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS=gpt-5.4,gpt-5.4-mini`다. 운영상 AI 호출을 끄려면 wrapper/cron env에서 `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=none`을 지정하고, 이미 생성된 strict JSON 응답을 검증할 때는 `THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON=PATH` 또는 `--ai-correction-response-json PATH`를 사용한다. Gemini provider는 수동 fallback/비교용으로 남긴다.

비용 guard는 AI 사용 확대 전 필수 조건이다. AI input은 full blob을 직접 싣지 않고 source metrics top-N summary, artifact path, full hash로 참조한다. `ai_input_context_chars`, `ai_input_context_hash`, section별 budget, token usage, elapsed_ms, output_chars, estimated cost field를 `threshold_cycle_ai_review`에 기록한다. 가격 계약은 운영 env `KORSTOCKSCAN_THRESHOLD_AI_INPUT_COST_PER_1M_USD`, `KORSTOCKSCAN_THRESHOLD_AI_OUTPUT_COST_PER_1M_USD`가 있을 때만 USD로 계산하고, 없으면 `cost_estimate_status=missing_price_contract`로 남긴다.

중복 호출 방지는 `--reuse-ai-review-if-valid`가 담당한다. wrapper 기본값은 `THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID=true`이며, 같은 date/phase/schema/input_context_hash의 parsed artifact가 있으면 provider를 다시 호출하지 않고 기존 review를 재사용한다. 재사용 artifact는 `ai_provider_status.status=reused_valid_artifact`, `new_provider_call=false`, `estimated_incremental_cost_usd=0.0`으로 남긴다.

cron wrapper에서 provider가 `openai`인 경우 `ai_status=unavailable|parse_rejected`는 조용히 통과시키지 않는다. `THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS`만큼 재시도하고, 장중 calibration은 최종 실패 시 `[FAIL] threshold-cycle calibration`으로 종료한다. 장후 postclose는 재시도 후에도 실패하면 `threshold_cycle_postclose_verification`이 runtime-applicable candidate 목록과 함께 `fail`을 반환한다. preopen apply는 postclose AI review가 존재하지만 unavailable이면 intraday parsed artifact로 fallback하지 않고 fail-closed한다.

OpenAI correction prompt는 영어 control instruction, 한국어 시장용어 glossary, 원문 enum/raw label 보존 규칙을 포함한다. `BUY/WAIT/DROP/HOLD/TRIM/EXIT/SELL_TODAY`, family id, ticker, field name은 번역하지 않는다. 이 contract는 correction proposal 품질과 schema 안정성을 위한 것이며, AI에게 runtime/env/code 변경 권한을 주지 않는다.

deterministic guard는 AI 제안을 그대로 적용하지 않는다.

- 값 제안은 family bounds와 `max_step_per_day` 안으로 clamp한다.
- `sample_window/window_policy`와 맞지 않으면 reject 또는 `hold_sample`로 둔다.
- `soft_stop_whipsaw_confirmation`, `bad_entry_refined_canary`, `scale_in_price_guard`처럼 rolling/cumulative가 필요한 family는 단일 당일 이상치만으로 live 후보를 승격하지 않는다.
- `holding_flow_ofi_smoothing`처럼 daily_intraday family는 장중 anomaly correction 후보가 될 수 있지만 runtime mutation은 금지하고 다음 장전 apply 후보로만 넘긴다.
- `score65_74_recovery_probe`, `protect_trailing_smoothing`, `scale_in_price_guard`처럼 rolling/cumulative primary를 가진 family는 daily source가 있더라도 `window_policy_resolution.primary_sample_count` 기준으로 후보 상태를 재평가한다.
- AI API/parse 실패 시 deterministic calibration artifact는 정상 생성되고 `ai_status=unavailable|parse_rejected`, family item은 `ai_review_state=unavailable`로 남는다. 단, wrapper/verification/apply guard는 이 상태를 runtime apply 가능 후보의 pass 조건으로 보지 않는다.

## calibration window policy

family별 기준 window는 다르게 적용한다.

| family | primary window | 보조 window | 해석 |
|---|---|---|---|
| `soft_stop_whipsaw_confirmation` | `rolling_10d` | `daily`, `cumulative_since_2026-04-21` | soft-stop late rebound는 단일 당일 사례로 live enable하지 않고 반복성/지속성을 본다. |
| `holding_flow_ofi_smoothing` | `daily_intraday` | `rolling_5d` | defer cost/HOLD_DEFER_DANGER는 장중 운영 상태가 빠르게 변하므로 당일 artifact를 우선하되 재발성만 rolling으로 본다. |
| `protect_trailing_smoothing` | `rolling_10d` | `daily`, `rolling_20d` | 단일 tick/단일 종목이 아니라 반복 이탈과 safety guard를 본다. |
| `trailing_continuation` | `rolling_10d` | `daily`, `rolling_20d` | GOOD_EXIT 훼손 리스크 때문에 당일 단독 live apply를 금지한다. |
| `score65_74_recovery_probe` | `rolling_5d` | `daily_intraday`, `cumulative_since_2026-04-21` | BUY drought는 당일 병목을 trigger로 쓰되 EV/close 우위와 false-positive risk는 rolling/cumulative 전용 표본으로 확인한다. 당일만으로 회수축 부활 또는 live/bounded canary 승격을 확정하지 않는다. family id는 artifact 호환을 위해 유지하지만 현 runtime floor는 score60이며, 전일 `panic_sell_defense.panic_detected` 또는 `panic_state in {PANIC_SELL, RECOVERY_WATCH}`이고 effective score60~74 표본이 sample floor의 70% 이상, EV/close 우위와 submitted drought guard를 통과하면 `panic_adjusted_ready` 후보가 될 수 있다. 최종 승격은 window policy guard를 통과해야 한다. |
| `latency_classifier_runtime_profile` | `same_day_postclose_latency_block_events` | `missed_entry_counterfactual`, 다음날 post-apply attribution | 당일 latency drought는 DANGER/stale/broker safety 감사 trigger로 사용한다. CAUTION은 normal submit semantics이므로 recovery 후보가 아니며, live 반영은 별도 proof/workorder 없이는 금지한다. |
| `bad_entry_refined_canary` | `rolling_10d` | `daily`, `cumulative_since_2026-04-21` | loser classifier 과적합을 피하기 위해 누적/rolling tail, 당일 safety, 장후 post-sell outcome join을 같이 본다. runtime 후보만으로 배드엔트리 확정 라벨을 붙이지 않는다. |
| `holding_exit_decision_matrix_advisory` | `latest_report` | `rolling_bucket_context` | 최신 matrix edge가 있어야 하며 bucket confidence는 SAW rolling context를 참조한다. |
| `scale_in_price_guard` | `rolling_10d` | `cumulative_since_2026-04-21`, `daily` | 물타기/불타기는 체결 표본이 희소하므로 당일만으로 guard 값을 정하지 않는다. |
| `market_regime_continuous_thresholds` | `rolling_10d` | `daily`, `rolling_5d` | VIX/Fear & Greed/국내 breadth/WTI pullback relief/local model 연속 점수를 risk-context feature로 검증한다. sample floor는 valid market cache + daily report 10일이며, 1차에서는 `allowed_runtime_apply=false`로 manifest-only 후보만 만든다. |

`threshold_cycle_cumulative`는 `threshold_snapshot_by_window`와 별도로 `calibration_source_bundle_by_window`를 생성한다. pipeline snapshot denominator가 비어 있어도 기존 source report의 rolling/cumulative metric이 있으면 `window_policy_resolution.primary_source_sample_count`로 소비한다. 이때 snapshot과 source denominator가 다르면 `window_policy_audit.rolling_source_snapshot_mismatch`로 표시해 report rendering/source alignment 보강 대상으로 남긴다.

새 관찰축 추가는 기본 금지다. follow-up이 어려운 신규 observe/report axis를 늘리지 않고 BUY 쪽 `buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`, 보유/청산 쪽 `holding_exit_observation`, `post_sell_feedback`, `holding_exit_sentinel`, `trade_review`, decision-support 쪽 `holding_exit_decision_matrix`, `statistical_action_weight`의 기존 source를 calibration 입력으로 재사용한다. `sentinel_followup`은 2026-05-07 단발 Markdown follow-up으로 현재 calibration 입력에서 제외한다. `preclose_sell_target`은 2026-05-10 제거된 operator review 축이므로 calibration 입력에서 제외한다.

스캘핑 simulator 청산 후 MFE/MAE는 실주문 `post_sell_feedback`과 분리한 `data/post_sell/sim_post_sell_candidates_YYYY-MM-DD.jsonl`, `sim_post_sell_evaluations_YYYY-MM-DD.jsonl`에 기록한다. 입력은 `scalp_sim_sell_order_assumed_filled + numeric profit_rate`만 인정하고, join key는 `sim_record_id`/`sim_parent_record_id`다. 이 source는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_equal_weight_observation_only`, `runtime_effect=false`를 유지하며, threshold/order/provider/bot/broker submit 변경의 단독 근거가 아니다. 소비자는 `daily_threshold_cycle_report.scalp_simulator.post_sell_join`과 `threshold_cycle_ev` 요약이다.

`calibration_source_bundle.report_only_cleanup_audit`는 report-only/legacy 산출물 중 현재 source bundle consumer가 없는 항목을 자동 감사한다. `sentinel_followup`, policy-disabled `server_comparison`, 정기 full snapshot에서 제외된 legacy `add_blocked_lock`, 제거된 `preclose_sell_target`이 관리 대상이다. 결과는 `metric_role=source_quality_gate`, `decision_authority=source_quality_only`, `primary_decision_metric=cleanup_candidate_count`로만 쓰며, 정리 후보 표면화 외에 runtime env, threshold, 주문, bot restart, provider route를 바꾸지 않는다.

`gemini_scalping_pattern_lab`와 `claude_scalping_pattern_lab`는 신규 관찰축을 runtime에 직접 추가하지 않는다. postclose wrapper가 두 lab을 `ANALYSIS_START_DATE=2026-04-21`, `ANALYSIS_END_DATE=YYYY-MM-DD`로 실행하고, `scalping_pattern_lab_automation`이 결과를 기존 family 입력, `auto_family_candidate(allowed_runtime_apply=false)`, `code_improvement_order(runtime_effect=false)`로 분류한다. daily EV report에는 freshness/consensus/order 요약만 포함하고 상세는 별도 artifact를 참조한다.

`position_sizing_cap_release`는 final user approval 전용 family다. 완벽한 개별 threshold 동시 충족이 아니라 overall EV 중심 efficient trade-off score로 판단한다. 표본, EV floor, severe downside, 주문 실패율만 hard floor로 두고, win rate/full-fill/soft-stop tail/cap opportunity는 가중 점수에 반영한다. 기준이 충족되어도 `allowed_runtime_apply=false`를 유지하며, `approval_contract_status=final_user_approval_required`, daily EV `approval_requests`, preopen apply `approval_requests`에만 노출한다. 사용자가 승인하기 전에는 신규 BUY, wait6579 probe, REVERSAL_ADD/PYRAMID 모두 1주 cap을 유지한다.

`position_sizing_dynamic_formula`는 cap 해제와 다른 동적수량 산식 튜닝 owner다. 입력은 `score`, `strategy`, `volatility`, `liquidity`, `spread`, `price_band`, `recent_loss`, `portfolio_exposure`로 고정하고, primary metric은 `notional_weighted_ev_pct` 또는 `source_quality_adjusted_ev_pct`를 사용한다. 산식 후보는 source bundle/approval request 근거가 될 수 있지만, sim/probe 단독으로 실주문 cap 해제나 수량 확대를 승인하지 않는다. 실주문 수량 확대는 별도 approval artifact, same-stage owner guard, rollback guard가 닫힌 경우에만 다음 장전 적용 후보로 본다. 상세 구현 단계와 approval schema는 [workorder-position-sizing-dynamic-formula](../../docs/workorder-position-sizing-dynamic-formula.md)를 따른다.

`panic_regime_mode`는 `panic_sell_defense`의 `panic_state`를 threshold-cycle이 해석하는 risk-regime 상태다. 현재 runtime authority는 `report_only`이며, `NORMAL -> PANIC_DETECTED -> STABILIZING -> RECOVERY_CONFIRMED` 모드는 source bundle, approval request, workorder evidence에만 들어간다. V2.0 후보는 `panic_entry_freeze_guard`이고 적용 범위는 scalping `entry_pre_submit` 신규 BUY 차단으로 제한한다. 미체결 진입 주문 cancel, holding/exit `panic_context`, 강제 축소/청산은 각각 별도 owner로 분리하며, approval artifact와 rollback guard 없이 preopen env나 broker order path에 반영하지 않는다. panic mode로 AI score threshold, stop-loss, TP/trailing, provider route, bot restart를 직접 바꾸는 것은 금지한다.

`panic_buy_regime_mode`는 `panic_buying`의 `panic_buy_state`를 threshold-cycle이 해석하는 risk-regime 상태다. 현재 runtime authority는 `report_only`이며, `NORMAL -> PANIC_BUY_DETECTED -> PANIC_BUY_CONTINUATION -> PANIC_BUY_EXHAUSTION -> COOLDOWN` 모드는 source bundle, approval request, workorder evidence에만 들어간다. V2.0 후보는 `panic_buy_runner_tp_canary`이고 적용 범위는 scalping 기존 보유분의 fixed TP 전량청산 대비 일부 익절 + runner trailing 후보로 제한한다. V2.1 `panic_buy_chase_entry_freeze`, V2.2 `panic_buy_continuation_trailing_width`, V2.3 `panic_buy_exhaustion_runner_cleanup`, V2.4 `panic_buy_cooldown_reentry_guard`는 각각 별도 owner로 분리하며 approval artifact와 rollback guard 없이 TP/trailing, 신규매수/추가매수, broker order path에 반영하지 않는다. panic buy mode로 추격매수, 시장가 전량청산, hard/protect/emergency override, provider route, bot restart를 직접 바꾸는 것은 금지한다.

`panic_lifecycle_actuator`는 live-selectable threshold family가 아니라 `sim_lifecycle_source`다. `threshold_family=panic_lifecycle_actuator`가 pipeline registry routing key로 남더라도 event는 `source_family=panic_lifecycle_actuator`, `family_type=sim_lifecycle_source`, `live_selectable=false`, `preopen_apply_allowed=false`, `env_apply_allowed=false`, `real_order_allowed=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`를 함께 남긴다. `panic_entry_freeze_guard`와 `panic_buy_runner_tp_canary`는 compatibility/read-only 이름이며 standalone preopen env, threshold mutation, provider route, bot restart trigger를 만들 수 없다. panic sell과 euphoria는 같은 source family를 쓰되 `risk_context_owner`, `risk_direction`, `action_namespace`로 방어성 축소와 수익확장/과열회수를 분리한다.

sim-first lifecycle 탐색은 별도 canonical report chain이 아니라 기존 threshold-cycle 자동화체인의 입력 범위와 판정 방식이다. 목적은 `scalp_ai_buy_all`처럼 BUY 확정 이후만 따라가거나 스캘핑 진입만 보는 것이 아니라, 스캘핑과 스윙의 BUY/selection 가능 후보 전체를 `selection -> entry -> holding -> scale_in -> exit` virtual lifecycle로 넓게 실행해 최적 threshold 후보와 기능개선 workorder를 찾는 것이다. 예수금 부족, 1주 cap, current selected family, 실주문 미제출은 sim exclusion 사유가 아니며 `real_blocker`/`actual_order_submitted=false` provenance로만 남긴다. 산출과 승격은 기존 `threshold_cycle_ev`, `threshold_cycle_cumulative`, `runtime_approval_summary`, `code_improvement_workorder`가 소유한다. 스캘핑 sim entry의 `entry_price` canary, passive submit revalidation, virtual pending, scale-in fill/unfill은 각각 기존 `pre_submit_price_guard`/`scale_in_price_guard` family의 sim-only 관찰 필드로 집계한다. sim 결과는 실주문 enable/cap 해제/provider 변경/bot restart의 단독 근거가 아니며, 손실이 난 arm은 전체 탐색축 폐기가 아니라 해당 bucket tighten 후보로 라우팅한다.

스윙 discovery sim은 이 sim-first 원칙의 스윙 탐색 구현체다. `swing_strategy_discovery_sim`이 safe pool 후보와 8개 arm을 만들고, bottom rebound source 후보는 breakout confirmation을 요구하지 않는 전용 anticipatory 3-arm으로 분리한다. `swing_strategy_discovery_label_builder`가 성숙 quote 기준으로 label을 채우며, `swing_strategy_discovery_ev_report`가 source-only EV를 집계한다. postclose wrapper는 `swing_daily_simulation` 직후 이 세 단계를 실행한다. `threshold_cycle_ev`와 `runtime_approval_summary`는 candidate/arm/labeled/pending/top surviving/avoid bucket 요약만 소비하고, `code_improvement_workorder`는 `runtime_effect=false` source-quality/report order만 만들 수 있다. 이 체인은 기존 스윙 runtime이나 `recommendation_history`를 대체하지 않는다.

`update_kospi` 이후 EOD DB refresh가 끝나면 바닥 반등 swing sim 후보 루프를 source-only로 실행한다. 순서는 `bottom_rebound_pattern_research -> swing_bottom_rebound_policy_auto_loop -> swing_bottom_rebound_candidate_source -> swing_strategy_discovery_sim --include-bottom-rebound-source`다. Tier-2 AI review가 백테스트/sim EV/승인된 real canary source를 검토해 1% 이상 개선이면 `sim_auto_approved`로 다음 후보 source policy만 승격한다. 이 승격은 `swing_sim_auto_approval` control-tower artifact에 먼저 통합되고, `swing_bottom_rebound_candidate_source`는 해당 artifact에 bottom rebound source 승인이 있을 때만 후보를 넘긴다. 승격은 virtual swing discovery candidate/arm 생성에만 연결되고, runtime env, broker order, real canary, threshold, provider, bot, `recommendation_history` 변경 권한은 없다.

스윙은 `swing_lifecycle_audit`와 `swing_improvement_automation`이 lifecycle 관찰축과 proposal/workorder를 만들고, `swing_runtime_approval`이 보수적 runtime 승인 요청만 만든다. hard floor는 family sample floor, critical instrumentation gap 없음, DB load gap 없음, fallback diagnostic contamination 없음, severe downside guard, same-stage owner 충돌 없음이다. 그 위에서 `overall_ev 45% + downside_tail 20% + participation/funnel 15% + regime_robustness 10% + attribution_quality 10%`의 `tradeoff_score >=0.68`이면 승인 요청을 생성한다. 완벽한 개별 threshold spot을 찾지 않고 전체 EV trade-off가 충분한 지점을 요청 기준으로 본다. 1차 env 적용 가능 family는 `swing_model_floor`, `swing_selection_top_k`, `swing_gatekeeper_reject_cooldown`, `swing_market_regime_sensitivity`이며, `AVG_DOWN`, `PYRAMID`, exit OFI/QI smoothing, AI contract 변경은 approval request까지만 허용한다.

스윙 entry drought와 후속 weak-contract audit는 approval request와 별개인 code-improvement/source-quality 경로다. `holding_exit_contract`, `scale_in_contract`, `real_canary_execution_contract`, `discovery_label_contract` gap은 workorder evidence로만 전달하며, phase0 auto-approval 또는 별도 approval artifact 없이 env apply, 1주 real canary, broker submit, provider route 변경으로 확장하지 않는다.

`swing_one_share_real_canary`는 위 dry-run approval과 별도의 broker execution 품질 수집축이다. 시작 조건은 `swing_runtime_approval` hard floor와 EV trade-off 통과, parsed AI Tier2 review, source report phase0 auto approval, 장전 preopen apply, DB load/instrumentation/fallback contamination/severe downside/same-stage conflict 없음이다. Optional real-canary artifact `data/threshold_cycle/approvals/swing_one_share_real_canary_YYYY-MM-DD.json`는 code allowlist/cap narrowing에만 사용한다. phase0 guard는 `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, 승인 code allowlist, `qty=1`, `max_new_entries_per_day=1`, `max_open_positions=3`, `max_total_notional_krw=300000`, same-symbol active real canary 1개, AVG_DOWN/PYRAMID/scale-in 실주문 금지다. `threshold_cycle_preopen_apply`는 parsed AI Tier2가 닫힌 source report auto approval이 없으면 env를 만들지 않고, auto approval이 있어도 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 유지한다. 이 canary의 realized PnL은 combined EV에 들어갈 수 있지만, broker receipt/order number binding/fill ratio/slippage/cancel/sell receipt는 real-only로만 판정한다. 통과해도 스윙 전체 실주문 전환은 별도 2차 계획/승인 없이는 금지한다.

## statistical_action_weight 적용 범위

`statistical_action_weight`는 dynamic threshold를 직접 바꾸는 family가 아니라 action weight source다. 장후 `daily_threshold_cycle_report`가 가격대/거래량/시간대별 `exit_only`, `avg_down_wait`, `pyramid_wait`의 confidence-adjusted score와 `policy_hint`를 만들고, 같은 실행에서 `holding_exit_decision_matrix`가 이를 report-only matrix entry와 `prompt_hint`로 변환한다.

적용 단계:

1. `stat_action_decision_snapshot`와 completed/action join 품질을 누적한다.
2. `statistical_action_weight_YYYY-MM-DD.json/md`에서 sample floor, policy hint, `eligible_but_not_chosen` proxy를 확인한다.
3. `holding_exit_decision_matrix_YYYY-MM-DD.json/md`가 bucket별 `recommended_bias`를 만든다.
4. runtime 반영은 `holding_exit_decision_matrix_advisory`의 deterministic/AI guard가 non-`no_clear_edge` bucket, safety guard, same-stage owner rule을 통과한 경우에만 자동 적용한다.

## 보호트레일링 평탄화 threshold family

`protect_trailing_smoothing` family는 `protect_trailing_smooth_hold`와 `protect_trailing_smooth_confirmed` stage를 수집한다.

관리 대상 값:

- `SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC`
- `SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC`
- `SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES`
- `SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO`
- `SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT`
- `SCALP_PROTECT_TRAILING_EMERGENCY_PCT`

런타임 override 키는 각각 `KORSTOCKSCAN_` prefix를 붙인 동일 이름이다. `protect_trailing_smoothing`은 GOOD_EXIT 훼손/safety risk가 커서 기본적으로 `hold_sample` 또는 `freeze`가 우선이며, 자동 적용은 같은 stage priority rule에서 선택된 경우에만 runtime env로 반영된다.

## OFI AI smoothing threshold family

`entry_ofi_ai_smoothing` family는 `entry_ai_price_ofi_skip_demoted` stage를 중심으로 P2 raw `SKIP` demotion 표본을 수집한다. `holding_flow_ofi_smoothing` family는 `holding_flow_ofi_smoothing_applied`와 `holding_flow_override_force_exit` stage를 수집해 flow 내부 OFI debounce/confirm 및 force-exit 우선권을 분리한다.

관리 대상 후보값:

- `SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE`
- `OFI_AI_SMOOTHING_STALE_THRESHOLD_MS`
- `OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED`
- `HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT`

holding/exit 쪽 `holding_flow_ofi_smoothing`은 `calibrated_apply_candidate` 후보가 될 수 있으며, same-stage priority와 AI correction guard를 통과하면 다음 장전 runtime env에 자동 반영된다. entry 쪽 `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 기존대로 기본 OFF이며, ON 전환은 별도 family metadata, manifest id/version, sample floor, fallback 급증 guard가 필요하다.

## Scale-in price guard threshold family

`scale_in_price_guard` family는 REVERSAL_ADD/PYRAMID 주문 직전 scale-in P1 resolver와 dynamic qty safety 표본을 수집한다.

수집 stage:

- `scale_in_price_resolved`
- `scale_in_price_guard_block`
- `scale_in_price_p2_observe`

관리 대상 후보값:

- `SCALPING_SCALE_IN_MAX_SPREAD_BPS`
- `SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS`
- `SCALPING_PYRAMID_MIN_AI_SCORE`
- `SCALPING_PYRAMID_MIN_BUY_PRESSURE`
- `SCALPING_PYRAMID_MIN_TICK_ACCEL`
- `SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP`

이 family는 resolved/block/P2 observe 건수, add_type, block_reason, qty_reason, P2 observe action, spread/micro-VWAP 분포, resolved-vs-curr, effective_qty를 장후 report 입력으로 남긴다. P2 `scale_in_price_v1`은 observe-only이며, threshold-cycle이 `SKIP`/`USE_DEFENSIVE`/`IMPROVE_LIMIT` 결과를 live 주문가나 주문 여부에 반영하지 않는다.

현재 `scale_in_price_guard`는 `report_only_calibration`이다. calibration candidate에 포함되지만, resolved/executed cohort가 없으면 `hold_sample`로만 출력한다. sample floor를 만족하기 전까지 threshold-cycle 산출물이 scale-in env 값을 자동 변경하지 않는다.

## 운영 판정 기준

1. `threshold_events`와 family partition은 canonical raw/compact data다. 사람이 읽는 판정은 `data/report/README.md`의 Markdown 생성 기준을 따른다.
2. `threshold_cycle_YYYY-MM-DD.json`은 top-level threshold 후보, calibration candidates, safety guard, calibration trigger를 담지만 현재 top-level Markdown은 없다. 운영자가 매일 직접 판정해야 하는 항목이면 `data/report/README.md`의 누락 후보로 승격하고 날짜별 checklist에 Markdown 생성 작업계획을 만든다.
3. `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative`는 report-only/decision-support artifact다. 자체 결과만으로 runtime 주문/청산 threshold를 변경하지 않는다.
4. POSTCLOSE collector는 기본적으로 live append 중인 `pipeline_events_YYYY-MM-DD.jsonl`을 직접 읽지 않고 immutable snapshot을 만든 뒤 backfill한다. `stopped_source_changed`가 발생하면 snapshot source로 재실행하고, report는 `checkpoint_completed=true`일 때만 완주 산출물로 본다.
5. IO guard 또는 availability guard로 backfill이 중단되면 같은 snapshot/checkpoint에서 chunk size를 낮춰 resume한다. 같은 날 무리한 raw full rebuild를 반복하지 않고 checkpoint, raw file size, paused reason을 report/checklist에 남긴다.
6. PREOPEN에는 전일 POSTCLOSE에서 생성된 report/apply plan과 AI correction guard를 읽어 `auto_bounded_live` runtime env를 생성한다. 같은 날 성과를 장전 통과조건으로 쓰지 않는다.
7. 자동 threshold 적용은 `report-based-automation-traceability.md`의 `R5` active 단계로 관리하고, `R6`는 daily EV report와 threshold version별 post-apply attribution으로 제출한다.
8. `pipeline_events_YYYY-MM-DD.jsonl`은 당일 forensic raw stream이고, `threshold_events_YYYY-MM-DD.jsonl`은 compact decision stream이다. 고빈도 diagnostic stage의 반복 raw count는 source-quality/ops volume 신호이며, summary/sampling artifact 없이 threshold 승격/rollback 근거로 쓰지 않는다.
9. raw/snapshot 압축은 `compress_db_backfilled_files`가 verified/backfilled 파일만 대상으로 수행한다. 당일 raw와 `skipped_unverified` 파일은 수동 삭제하지 않는다.

## 금지 사항

- 장중 live threshold auto-mutation 금지.
- `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`, `auto_bounded_live` 외 apply mode 임의 추가/사용 금지.
- family별 sample floor, safety guard, owner 없이 threshold를 runtime에 반영 금지.
- raw JSONL을 사람이 직접 해석해 승격/롤백 판정을 닫는 것 금지. 필요한 경우 Markdown/report artifact를 먼저 만든다.
