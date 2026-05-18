# Report-Based Automation Traceability

기준일: `2026-05-18 KST`

이 문서는 report 기반 자동화가 누락되지 않도록 `산출물 -> 소비자 -> 적용 단계 -> owner`를 추적하는 registry다. 최종 목표는 기대값/순이익 극대화지만, report 산출물이 곧바로 runtime threshold 변경으로 이어지지는 않는다.

## 1. 자동화 단계

| 단계 | 상태 | 의미 | live 영향 |
| --- | --- | --- | --- |
| `R0_collect` | active | runtime compact event, DB completed trade, monitor snapshot을 수집한다 | 없음 |
| `R1_daily_report` | active | 당일 threshold/report-only 산출물을 만든다 | 없음 |
| `R2_cumulative_report` | active | 누적/rolling cohort 산출물을 만든다 | 없음 |
| `R3_manifest_only` | active | 다음 장전 apply plan artifact를 만든다 | 없음 |
| `R4_preopen_apply_candidate` | active | owner/safety guard/sample floor가 닫힌 후보를 `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`로 분류한다 | 직접 변경 전 단계 |
| `R5_bounded_calibrated_apply` | active | deterministic guard + AI correction guard를 통과한 family를 다음 장전 1회 runtime env로 자동 반영한다. 조건 미달은 rollback이 아니라 calibration trigger다 | 있음 |
| `R6_post_apply_attribution` | active | threshold version별 applied/not-applied cohort와 daily EV performance report를 장후 제출한다 | 없음 |

현재 허용선은 완전 무인 `auto_bounded_live`다. calibration은 매일 `intraday`, `postclose` 2회 생성하고, preopen cron은 전일 report + AI correction guard를 읽어 다음 장전 runtime env를 만든다. env/code hot mutation은 하지 않고, 봇은 기동 시 당일 runtime env를 source한다. safety breach가 아닌 목표 미달은 `calibration_state=adjust_up|adjust_down|hold|hold_sample|hold_no_edge|freeze`로 처리하고, `rollback/safety_revert_required`는 hard/protect/emergency stop 지연, 주문 실패, provenance 손상, same-stage owner 충돌, severe loss guard 초과에만 쓴다. Sentinel 이상치는 자동 튜닝 명령이 아니라 기존 report source bundle 입력이다. 반복 이상치를 이유로 새 관찰축을 늘리지 않고, 운영장애는 incident playbook, 로그 누락은 instrumentation backlog, 정상 변동은 no-action으로 분리한다.

`2026-05-12`부터 postclose chain은 direct predecessor artifact 계약을 갖는다. 후행 단계는 직전 JSON/Markdown artifact가 없거나 JSON 검증이 끝나지 않으면 `THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC` 동안 대기하고, timeout 시 fail-closed한다. workorder source용 `threshold_cycle_ev` pre-pass와 workorder summary refresh용 post-pass를 분리하며, 최종 `threshold_cycle_postclose_verification`이 latest `START` 이후 wait/fail/timeout과 workorder `generation_id/source_hash/lineage`를 자동 점검한다. 같은 날짜 재생성 판정은 `mtime`이 아니라 `generation_id`, `source_hash`, `lineage.{new,removed,decision_changed}_order_ids`를 우선한다.

## 2. 산출물 추적성

| 산출물 | Producer | Consumer | 현재 단계 | 다음 owner | 누락 방지 확인 |
| --- | --- | --- | --- | --- | --- |
| `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl` | `backfill_threshold_cycle_events` | `daily_threshold_cycle_report` | `R0_collect` | `ThresholdCollectorIO0506` | immutable snapshot source, checkpoint, read bytes, availability guard |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | `daily_threshold_cycle_report` | `threshold_cycle_preopen_apply`, operator review | `R1_daily_report` | `ThresholdOpsTransition0506` | apply candidate, trade lifecycle attribution, calibration candidates, safety guard, calibration trigger, post-apply attribution, warnings |
| `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_{intraday,postclose}.json` | `daily_threshold_cycle_report` | operator review, next preopen manifest review | `R4_preopen_apply_candidate` artifact | `ThresholdCalibrationLoop0508`, `EfficientTradeoffCalibration0508` | calibration source bundle, candidate state, safety guard, no runtime mutation |
| `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.{json,md}` | `daily_threshold_cycle_report` via threshold cron wrappers | next preopen auto bounded apply guard | `R4_preopen_apply_candidate` support artifact | `ThresholdAICorrectionCron0508`, `ThresholdUnattendedApply0508` | OpenAI correction proposal, strict schema parse, family bounds/max-step guard, sample-window guard, AI 단독 runtime_change=false |
| `data/post_sell/sim_post_sell_candidates_YYYY-MM-DD.jsonl` | `sniper_state_handlers.record_sim_post_sell_candidate`, `sniper_post_sell_feedback --backfill-sim-candidates` | `sniper_post_sell_feedback --evaluate-sim`, `daily_threshold_cycle_report` | `R1_daily_report` sim post-exit source | `ScalpSimPostSellMFECheck0518` | scalp sim sell 완료 후 forward MFE/MAE 후보. `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_equal_weight_observation_only`, 실주문 post-sell candidate와 파일 분리 |
| `data/post_sell/sim_post_sell_evaluations_YYYY-MM-DD.jsonl` | `sniper_post_sell_feedback --evaluate-sim` | `daily_threshold_cycle_report`, `threshold_cycle_ev_report`, pattern lab/workorder source via EV summary | `R1_daily_report -> R6_post_apply_attribution` sim post-exit source | `ScalpSimPostSellMFECheck0518` | `sim_record_id`/`sim_parent_record_id`로 `scalp_sim_sell_order_assumed_filled`와 join한다. `primary_decision_metric=sim_post_decision_mfe_10m_pct`, `runtime_effect=false`; threshold/order/provider/bot/broker submit 직접 변경 금지 |
| `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}` | `scalping_pattern_lab_automation` | daily EV report, future implementation order queue | `R6_post_apply_attribution` support artifact | `PatternLabAutomation0508` | Gemini/Claude freshness, consensus findings, existing family inputs, auto family candidates(`allowed_runtime_apply=false`), code improvement orders(`runtime_effect=false`) |
| `data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_YYYY-MM-DD.{json,md}` | `swing_pattern_lab_automation` | daily EV report, code improvement workorder, swing approval/source-quality review | `R6_post_apply_attribution` support artifact | `SwingPatternLabAutomation0512` | DeepSeek payload schema, `analysis_window.start == target_date == end`, data-quality warnings, `source_quality_blocked_families`, sim/probe provenance, `runtime_effect=false` orders |
| `data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_YYYY-MM-DD.{json,md}` | `pattern_lab_currentness_audit` | code improvement workorder, threshold EV, propagation audit, runtime approval summary | `R6_post_apply_attribution` source-quality artifact | `PatternLabCurrentnessAudit0518` | lab code/README/output schema/metric contract/forbidden wording/source mode/stale-output risk, `code_improvement_orders.runtime_effect=false`, `allowed_runtime_apply=false`, no repo auto-patch |
| `data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_YYYY-MM-DD.{json,md}` | `pattern_lab_propagation_audit` | threshold EV refresh, runtime approval summary, postclose verification | `R6_post_apply_attribution` chain audit artifact | `PatternLabPropagationAudit0518` | lab automation -> currentness -> workorder -> threshold EV -> runtime summary source links, sim/probe provenance, runtime_effect=false contract |
| `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.{json,md}` | `swing_lifecycle_audit` | `threshold_cycle_preopen_apply`, `threshold_cycle_ev_report`, `runtime_approval_summary`, operator approval review | swing approval request artifact | `SwingRuntimeApproval0511` | approval requests, blocked reasons, real-canary policy, one-share real canary request, no runtime mutation by itself |
| `data/threshold_cycle/approvals/swing_runtime_approvals_YYYY-MM-DD.json` | user approval artifact | `threshold_cycle_preopen_apply` | manual approval gate | `SwingRuntimeApproval0511` | approved request ids only. env 반영 후에도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=true` 유지 |
| `data/threshold_cycle/approvals/swing_one_share_real_canary_YYYY-MM-DD.json` | user approval artifact | `threshold_cycle_preopen_apply`, runtime `sniper_state_handlers` via env | one-share real canary gate | `SwingOneShareRealCanaryPolicy0511` | approved request ids, code allowlist, 1주 cap, daily/open/notional cap. artifact 없으면 `one_share_real_canary_approval_artifact_missing` |
| `data/threshold_cycle/approvals/swing_scale_in_real_canary_YYYY-MM-DD.json` | user approval artifact | `threshold_cycle_preopen_apply`, runtime `execute_scale_in_order` via env | scale-in real canary gate | `SwingScaleInRealCanaryPhase0Policy0511` | approved arms only, 1주 cap, sim/probe/dry-run position forbidden, OFI/QI stale/bearish fail-closed |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | operator review, threshold candidate persistence check | `R2_cumulative_report` | `CumulativeThresholdCycleReport0504-Postclose`, `ThresholdOpsTransition0506` | daily/rolling/cumulative 방향성 일치 여부 |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | action weight review, ADM ladder, threshold-cycle source bundle | `R1_daily_report` | `StatActionWeight0506`, `StatActionMarkdown0506`, `StatActionEligibleOutcome0507`, `EfficientTradeoffCalibration0508` | bucket sample floor, policy_hint, data completeness, `eligible_but_not_chosen` report-only proxy, candidate_weight_source count |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | ADM advisory canary/live-readiness, threshold-cycle source bundle | `R1_daily_report` | `AIDecisionMatrix0506`, `EfficientTradeoffCalibration0508` | matrix_version, hard_veto, prompt_hint, non-no_clear_edge bucket count |
| `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}` + `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl` | `buy_funnel_sentinel` with slim append cache `data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_YYYY-MM-DD.*` and high-volume diagnostic summary manifest `data/pipeline_event_summaries/pipeline_event_summary_manifest_YYYY-MM-DD.json` | operator intraday review, threshold/anomaly routing | `R1_daily_report` | `BuyFunnelSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday`, `SentinelTelegramRemoval0508`, `PipelineEventVerbosityCompaction0514` | classification, baseline comparison, forbidden auto mutation, no Telegram alert, cache/summary are performance optimizations only; high-volume summary has `decision_authority=diagnostic_aggregation` |
| `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}` | `holding_exit_sentinel` with slim append cache `data/runtime/sentinel_event_cache/holding_exit_sentinel_events_YYYY-MM-DD.*` | operator intraday review, holding/exit anomaly routing | `R1_daily_report` | `HoldingExitSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday`, `SentinelTelegramRemoval0508` | classification, holding/exit conversion, forbidden auto mutation, no Telegram alert, cache is performance optimization only |
| `data/report/market_panic_breadth/market_panic_breadth_YYYY-MM-DD.json` | `market_panic_breadth_collector` via `run_panic_sell_defense_intraday.sh`, `run_panic_buying_intraday.sh`, and `run_threshold_cycle_postclose.sh` best-effort/pre-report step | `panic_sell_defense_report`, `panic_buying_report`, operator intraday review | `R0_collect -> R1_daily_report` source-quality artifact | `MarketPanicBreadthCollector0515` | Kiwoom REST `ka20003` `/api/dostk/sect` `inds_cd=001/101` live industry/index snapshot, KOSPI/KOSDAQ weighted composite decline/rise breadth, `risk_off_advisory`, `risk_on_advisory`, `single_market_risk_off_advisory`, `single_market_risk_on_advisory`, `decision_authority=source_quality_only`, forbidden runtime/order/provider/bot mutation; Kiwoom WS `0J`/`0U` is documented as future lower-latency source, not enabled by this artifact |
| `data/report/panic_sell_defense/panic_sell_defense_YYYY-MM-DD.{json,md}` | `panic_sell_defense_report` | operator intraday/postclose review, threshold-cycle source bundle candidate | `R1_daily_report` | `PanicSellDefenseReportOnly0512` | `panic_state`, stop-loss cluster, real/non-real split, active sim/probe provenance, post-sell rebound, `microstructure_market_context`, forbidden runtime mutation |
| `data/report/panic_buying/panic_buying_YYYY-MM-DD.{json,md}` | `panic_buying_report` | operator intraday/postclose review, threshold-cycle source bundle context | `R1_daily_report` | `PanicBuyingReportOnly0513` | `panic_buy_state`, `panic_buy_regime_mode`, active/exhausted symbol split, market-wide `risk_on_advisory` context, TP counterfactual, `panic_buy_runner_tp_canary`, forbidden runtime mutation |
| `tmp/monitor_snapshot_completion_YYYY-MM-DD_PROFILE.json` | `run_monitor_snapshot_safe.sh` | cron/admin completion check, web async refresh status | `R0_collect` | `MonitorSnapshotAsyncCompletion0507` | async worker pid, result file, status, skip/failure reason, log path |
| `data/report/tuning_monitoring/status/tuning_monitoring_postclose_YYYY-MM-DD.json` | `run_tuning_monitoring_postclose.sh` | postclose monitoring chain health check | `R0_collect` | `TuningMonitoringPostcloseFallback0507` | lock/retry status, per-step exit code, failed step, command provenance |
| `data/ipo_listing_day/status/ipo_listing_day_YYYY-MM-DD.status.json` | `run_ipo_listing_day_autorun.sh` | operator IPO run audit. YAML 존재 시만 별도 real-order runner 실행 | IPO_YAML_GATED_REAL_ORDER | `IpoListingDayYamlGatedAutorun0510` | missing YAML skip, STOP skip, dry-select result, lock/status/log path. threshold-cycle/daily EV consumer 금지 |
| `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json` | `threshold_cycle_preopen_apply` | preopen bot start workflow | `R5_bounded_calibrated_apply` | `ThresholdUnattendedApply0508` | apply_mode, auto_apply_decisions, selected family, runtime env, safety guard, calibration trigger, same-stage owner rule |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}` | `threshold_cycle_preopen_apply` | `src/run_bot.sh` | `R5_bounded_calibrated_apply` | `ThresholdUnattendedApply0508` | env override provenance, selected family, source report, generated_at |
| runtime env path contract events | `sniper_state_handlers` | operator intraday review, `daily_threshold_cycle_report`, `threshold_cycle_ev_report` | `R5_bounded_calibrated_apply -> R6_post_apply_attribution` | `RuntimeApplyEnvBlockAudit0518` | selected env family별 `env loaded -> family applied -> intended downstream consumer reached|intended safety block` 확인. probe/canary가 armed/source를 세운 뒤 공통 gate에서 의도와 다르게 재차단되면 `runtime_apply_contract_bug`; safety/source-quality/cap block은 reason과 provenance를 남김 |
| `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}` | `threshold_cycle_ev_report` | postclose daily EV submission | `R6_post_apply_attribution` | `ThresholdDailyEVReport0508` | selected families, completed valid PnL, entry funnel, holding/exit latency, calibration decisions, pattern lab automation summary, pattern lab currentness/propagation audit summary |
| `data/report/pipeline_event_verbosity/pipeline_event_verbosity_YYYY-MM-DD.{json,md}` + `data/pipeline_event_summaries/pipeline_event_producer_summary_YYYY-MM-DD.jsonl` | `pipeline_event_verbosity_report`, optional producer-side `pipeline_event_logger` compactor | postclose ops/source-quality summary, code improvement workorder source | `R6_post_apply_attribution` support artifact | `PipelineEventCompactionV2Shadow0514` | raw size/line count, high-volume diagnostic share, V1 raw-derived summary vs producer summary parity, suppress eligibility; `decision_authority=diagnostic_aggregation`, `runtime_effect=false`, default compaction mode `off` |
| `data/report/observation_source_quality_audit/observation_source_quality_audit_YYYY-MM-DD.{json,md}` | `observation_source_quality_audit` | operator source-quality review, code improvement workorder, threshold source-quality blocker review | `R0_collect -> R6_post_apply_attribution` diagnostic artifact | `ObservationSourceQualityAudit0515` | stage별 source-quality field contract, AI tick/quote freshness coverage, AI overlap/range zero-rate, sim/probe authority provenance, OFI/QI micro-context field coverage, swing `observer_gap_with_fresh_ws_quote` provenance, high-volume diagnostic stage contract gaps; `metric_role=source_quality_gate`, `decision_authority=source_quality_only`, `runtime_effect=false`, forbidden runtime/order/provider/bot mutation |
| `data/report/codebase_performance_workorder/codebase_performance_workorder_YYYY-MM-DD.{json,md}` | `codebase_performance_workorder_report` | postclose ops performance workorder source | `R6_post_apply_attribution` support artifact | `CodebasePerformanceWorkorder0514` | accepted/deferred/rejected performance candidates from `docs/codebase-performance-bottleneck-analysis.md`; `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`; user-instructed implementation only |
| `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.{json,md}` | `runtime_approval_summary` | operator postclose review, next checklist, approval/workorder triage | `R6_post_apply_attribution` read-only summary | `RuntimeApprovalSummary0512` | `warnings`, scalping selected count, swing requested/approved/blocked, pattern lab currentness/propagation audit status, `gate_review_class`, `legacy_hard_gate_risk`, `tuning_route`, `runtime_mutation_allowed=false`; flow 조정/차단 권한 없음 |
| `data/report/plan_rebase_daily_renewal/plan_rebase_daily_renewal_YYYY-MM-DD.{json,md}` | `plan_rebase_daily_renewal` | Plan Rebase/prompt/AGENTS daily renewal proposal review | `R6_post_apply_attribution` proposal-only artifact | `PlanRebaseDailyRenewal0513` | postclose source bundle 기반 bounded renewal proposal, `document_mutation_allowed=false`, `runtime_mutation_allowed=false`, no file mutation |
| `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json` + `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md` | `build_code_improvement_workorder` | Codex implementation session, operator triage | implementation-intake artifact | `CodeImprovementWorkorderReview0512` | `generation_id`, `source_hash`, `lineage`, `decision_counts`, currentness audit source/orders, `runtime_effect=false`, `allowed_runtime_apply=false`; 생성만으로 repo/runtime 수정 금지 |
| `data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_YYYY-MM-DD.{json,md}` | `verify_threshold_cycle_postclose_chain` | postclose chain health review, workorder regeneration safety | chain verification artifact | `PostcloseChainVerification0512` | latest `START` 이후 predecessor wait/fail/timeout count, direct artifact presence, audit artifact presence, DONE marker flags, downstream source links, workorder `generation_id/source_hash/lineage` diff |
| `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json` | `update_kospi.py` | error detector artifact freshness, operator 21:00 data chain review | EOD data-chain status artifact | `RunbookOps` | `status`, `failed_steps`, `warning_steps`, `db_state.latest_quote_date`, recovered/manual recovery steps; `completed_with_warnings`는 DB 적재와 후속 추천/리포트 실패를 분리 |
| threshold version attribution section | `daily_threshold_cycle_report`, `threshold_cycle_ev_report` | post-apply attribution | `R6_post_apply_attribution` active | `ThresholdDailyEVReport0508` | threshold_version, applied/not-applied cohort key, calibration_state, safety_revert_required, daily EV |
| entry passive probe lifecycle events | `sniper_state_handlers` | `backfill_threshold_cycle_events`, `daily_threshold_cycle_report`, daily EV report | `R0_collect -> R6_post_apply_attribution` | `PassiveEntryProbeLifecycle0508` | `entry_order_lifecycle=passive_probe`, bid-1tick adjusted price, submit revalidation age, timeout cancel request/confirm provenance |
| `trade_lifecycle_attribution` section | `daily_threshold_cycle_report` | threshold calibration, AI correction input, daily EV report | `R2_candidate_context -> R6_post_apply_attribution` | `TradeLifecycleAttribution0508` | entry submit/cancel, holding 후보 신호, exit rule/source, post-sell outcome을 `record_id`로 join한 family 공통 전중후 유형 |

## 2.1 Postclose Chain Contract

`deploy/run_threshold_cycle_postclose.sh`의 최신 순서는 아래 계약을 따른다.

1. `15:45` `run_swing_live_dry_run_report.sh`는 기본적으로 lightweight `swing_selection_funnel_report`와 status만 생성하고, `lifecycle_audit_mode=postclose_deferred`로 닫는다. heavy `swing_lifecycle_audit`/AI review/runtime approval은 `16:10` postclose chain에서 실행한다.
2. `swing_daily_simulation_report`를 먼저 생성하고, `swing_lifecycle_audit`/`swing_runtime_approval`은 해당 JSON/Markdown이 존재하고 JSON 검증이 끝난 뒤에만 실행한다.
3. `daily_threshold_cycle_report`는 immutable snapshot/checkpoint를 우선 사용한다. 같은 날짜 retry는 기존 snapshot/checkpoint를 재사용하고 중복 snapshot retention을 정리한다.
4. compact threshold event 수집 직후 `sniper_post_sell_feedback --backfill-sim-candidates --evaluate-sim`을 실행해 `scalp_sim_sell_order_assumed_filled` 표본을 `sim_post_sell_candidates/evaluations`에 분리 기록한다. 이 단계는 report-only이며 기존 실주문 `post_sell_candidates/evaluations`를 오염시키지 않는다.
5. scalping/swing pattern lab automation 이후 `pattern_lab_currentness_audit`가 lab code/README/schema/source-mode/stale-output 위험을 `runtime_effect=false` currentness workorder 후보로 고정한다.
6. `pipeline_event_verbosity_report`가 raw volume과 V1/V2 producer summary parity를 생성한다. 이 artifact는 workorder source-quality/ops 입력이며 threshold/order/provider/bot restart 권한이 없다.
7. `codebase_performance_workorder_report`가 코드베이스 성능점검 문서를 workorder source artifact로 변환한다. 이 artifact는 user-instructed performance backlog이며 전략 로직/데이터품질/튜닝축 변경 권한이 없다.
8. `threshold_cycle_ev` pre-pass를 생성해 workorder source로 사용한다.
8. `build_code_improvement_workorder`가 pattern lab currentness audit를 포함한 source bundle에서 code improvement JSON/Markdown을 생성한다.
9. `threshold_cycle_ev` post-pass를 다시 생성해 workorder summary와 source-quality blocker를 refresh한다.
10. `pattern_lab_propagation_audit`가 lab automation -> currentness -> workorder -> threshold EV -> runtime summary source link를 점검한다. 같은 wrapper에서는 runtime summary가 아직 생성 전일 수 있으므로 propagation audit 결과를 `threshold_cycle_ev`에 한 번 더 refresh한 뒤 runtime summary가 소비한다.
11. `runtime_approval_summary`는 refreshed EV/workorder/audit가 닫힌 뒤에만 실행한다.
12. `plan_rebase_daily_renewal`은 `runtime_approval_summary` 이후 Plan Rebase/prompt/AGENTS 갱신 제안 artifact만 만든다. 기본은 `proposal_only`이며 `document_mutation_allowed=false`, `runtime_mutation_allowed=false`다.
13. 다음 영업일 checklist를 생성한다.
14. `threshold_cycle_postclose_verification`이 최신 run의 predecessor wait/fail/timeout, 필수 audit artifact, DONE marker flag, downstream source link, workorder lineage를 기록한다.

2026-05-12 기준 검증 결과는 `threshold_cycle_postclose_verification_2026-05-12` `status=pass`, `predecessor_wait_count=0`, `timeout_count=0`, workorder `generation_id=2026-05-12-5abbfc31939d`, `source_hash=5abbfc31939dffedcaab60313d1641234dbc026363b0f2842778d63b45f9440a`, `lineage.new_order_ids=[]`, `lineage.removed_order_ids=[]`, `lineage.decision_changed_order_ids=[]`다.

## 2.2 Source-Quality as Automation Input

report-only 산출물은 runtime mutation 권한이 없지만, source-quality 값은 자동화 체인의 입력으로 사용될 수 있다. 2026-05-12부터 `swing_pattern_lab_automation`/`threshold_cycle_ev`/workorder는 OFI/QI `stale_missing_flag`를 단일 boolean이 아니라 reason과 unique record 기준으로 노출한다.

| 항목 | 최신 처리 |
| --- | --- |
| `micro_missing` / `micro_stale` / `observer_unhealthy` / `micro_not_ready` / `state_insufficient` | DeepSeek fact/payload, swing lifecycle audit, threshold EV, workorder evidence에 reason count로 표면화 |
| unique record count | stage 반복 이벤트와 독립 record를 분리해 `stale_missing_unique_record_count`로 사용 |
| `source_quality_blocked_families` | `swing_scale_in_ofi_qi_confirmation`, `swing_scale_in_real_canary_phase0` 같은 family의 approval/workorder blocker 입력으로 사용 |
| 금지선 | source-quality blocker만으로 runtime threshold/order mutation 금지. approval artifact 또는 family guard 없이 live env apply 금지 |

2026-05-12 기준 `threshold_cycle_ev`의 남은 source-quality warning은 `OFI/QI stale/missing ratio: 0.0776 (9/116); reasons: micro_missing=9, observer_unhealthy=3, micro_not_ready=9, state_insufficient=9`다. 이는 DB/추천 실패가 아니라 scale-in micro-context source-quality blocker다.

## 2.3 Pipeline Event Source Contract

`pipeline_events_YYYY-MM-DD.jsonl`은 lossless forensic raw stream이고 `threshold_events_YYYY-MM-DD.jsonl`은 threshold-cycle compact decision stream이다. raw event count나 파일 크기는 source-quality/ops 입력으로만 사용하며, runtime family 승격/rollback은 report artifact, owner, sample floor, rollback guard를 통과해야 한다.

고빈도 diagnostic stage는 `metric_role=ops_volume_diagnostic`, `decision_authority=none`, `forbidden_uses=runtime_threshold_or_order_guard_mutation`으로 취급한다. `blocked_*` 반복 이벤트를 튜닝 입력으로 쓰려면 먼저 stage/date/stock/source-quality 단위 summary를 만들고, suppressed count 또는 sample rate를 명시해야 한다. 주문 제출/체결/exit/safety/provenance/source-quality transition은 throttle/compaction에서도 lossless 보존 대상이다.

BUY Sentinel v1 summary는 raw suppression 없이 `strength_momentum_observed`, `blocked_strength_momentum`, `blocked_swing_score_vpw`, `blocked_overbought`, `blocked_swing_gap`만 1분 bucket으로 집계한다. summary row는 `event_count`, `second_counts`, `field_presence_counts`, numeric stats, raw offset, deterministic sample을 포함하며 `decision_authority=diagnostic_aggregation`이다. `actual_order_submitted`, 주문/체결/청산, AI score, budget/latency/order lifecycle, provenance/source-quality transition은 기존 row cache에서 lossless로 유지한다. summary manifest가 없거나 stale이면 BUY Sentinel은 raw/cache 경로로 fallback한다.

Pipeline Event Compaction V2는 producer-side compactor를 `PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE=off|shadow|suppress`로 노출하며 기본값은 `shadow`다. `shadow`는 raw JSONL/DB upsert를 그대로 유지하면서 `pipeline_event_producer_summary_YYYY-MM-DD.jsonl`과 manifest만 추가 생성하는 report-only 계측이다. `off`는 장애 대응용으로 producer summary 생성을 끄는 옵션이다. `suppress`는 구현되어도 기본 비활성이고, V1 raw-derived summary와 2영업일 이상 parity를 통과한 뒤 별도 workorder/approval owner가 열리기 전에는 사용하지 않는다. `pipeline_event_verbosity_report`의 state와 suppress eligibility는 ops/code-improvement 입력일 뿐 실주문 승인, threshold apply, EV primary metric 단독 근거가 아니다.

보관 정책은 runbook의 `Pipeline Event Verbosity/Retention Policy`를 따른다. `compress_db_backfilled_files --days 7`은 verified/backfilled raw와 snapshot만 압축하며, 미검증 파일 삭제나 당일 raw 수동 삭제는 허용하지 않는다.

### Scalping Pre-AI Gate Risk Context Contract

2026-05-18 operator override 이후 스캘핑 `strength_momentum`, `overbought`, `liquidity`는 AI 호출 전 후보를 폐기하는 terminal gate가 아니라 AI/counterfactual로 전달하는 risk context로 기록한다. 단, source-quality blocker와 broker submit safety는 그대로 fail-closed한다.

| family | stage/source | runtime 권한 | consumer |
| --- | --- | --- | --- |
| `strength_momentum_soft_gate_p1` | `blocked_strength_momentum`, `blocked_vpw` with `gate_action=risk_context_only|source_quality_block` | `runtime_effect=false`; source-quality blocker만 pre-AI 차단 | AI input, BUY funnel, missed-entry counterfactual, threshold EV |
| `overbought_pullback_guard_p1` | `blocked_overbought` risk context, `pre_submit_overbought_pullback_guard_block` safety block | risk context는 `runtime_effect=false`; pre-submit guard는 `runtime_effect=pre_submit_block` | AI input, counterfactual, broker submit safety |
| `liquidity_pre_submit_guard_p1` | `blocked_liquidity` risk context, `pre_submit_liquidity_guard_block` safety block | risk context는 `runtime_effect=false`; pre-submit guard는 `runtime_effect=pre_submit_block` | AI input, counterfactual, broker submit safety |

`liquidity_gate_refined_candidate`와 `overbought_gate_refined_candidate`는 historical/reference family로 격하한다. 같은 `blocked_liquidity`/`blocked_overbought` 표본을 active calibration candidate로 두 번 만들지 않으며, 기존 source bundle metric은 각각 `liquidity_pre_submit_guard_p1`, `overbought_pullback_guard_p1`의 `source_metrics`로 승계한다. report consumer는 `supersedes` 필드를 보고 legacy family를 runtime/apply 후보가 아니라 migration lineage로만 해석한다.

공통 필드는 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`, `runtime_effect`를 선언한다. pre-AI risk context는 `metric_role=risk_context`, `decision_authority=source_quality_only`, `window_policy=same_day_intraday_light + rolling_5d attribution`, `sample_floor=20`, `primary_decision_metric=source_quality_adjusted_ev_pct after counterfactual`, `source_quality_gate=insufficient_history/stale_quote/extreme_sell_dominance`, `runtime_effect=false`다. `actual_order_submitted=false` 관찰 표본은 missed-upside/avoided-loss 분석 대상이지만 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.

금지 사용처는 score threshold 전면 완화, fallback 재개, provider route 변경, 주문가 guard 완화, 스윙 dry-run 해제, approval 없는 broker order submit이다. `liquidity_pre_submit_guard_p1`과 `overbought_pullback_guard_p1`의 pre-submit block은 주문 제출 직전 safety guard이며 threshold/provider/bot 상태를 바꾸지 않는다.

### Runtime Approval Hard Gate Review Contract

`runtime_approval_summary`는 각 scalping/swing family에 `gate_review_class`, `legacy_hard_gate_risk`, `hard_gate_review`, `tuning_route`, `analysis_coverage`를 노출한다. 목적은 historical hard gate, 의도된 safety guard, runtime contract gap, same-stage owner conflict, sample/source-quality gap을 한 화면에서 분리해 보는 것이다.

분류 기준:

| 분류 | 의미 | 조치 |
| --- | --- | --- |
| `legacy_summary_superseded` | 과거 hard pre-AI gate family가 summary에 남은 경우 | active family의 `supersedes`/`source_metrics` lineage로만 해석하고 runtime/apply 후보에서 제외 |
| `intentional_safety_guard` | submit 직전 가격/유동성/과열/scale-in safety guard | AI/counterfactual 분석은 허용하되 broker submit guard는 fail-closed 유지 |
| `contract_gap` | 분석 표본은 있으나 runtime env key/guard/approval consumer가 없는 경우 | code-improvement workorder 또는 approval contract 설계가 먼저다 |
| `same_stage_deferred` | 같은 stage owner와 충돌해 보류된 경우 | active owner attribution이 닫힌 뒤 별도 approval route로 재검토 |
| `sample_or_contract_gap` / `source_quality_or_contract_gap` | 표본, source-quality, runtime guard가 부족한 경우 | source-quality blocker와 sample floor를 먼저 닫고 tuning 후보로 승격 |
| `no_unreviewed_hard_gate` | hard gate 잔존 문제가 아니라 selected/applied/advisory/approval-ready 축 | 기존 threshold-cycle 또는 approval route로 판정 |

이 분류는 read-only review metadata이며 `runtime_mutation_allowed=false`를 바꾸지 않는다. 특히 스윙 `swing_gatekeeper_accept_reject`는 `blocked_gatekeeper_reject`/`swing_probe_entry_candidate` 분석 표본이 있어도 accept/reject 자체 env guard가 없으면 `contract_gap`으로 남긴다. 반대로 `swing_gatekeeper_reject_cooldown`, `swing_model_floor`, `swing_one_share_real_canary_phase0`처럼 approval route가 있는 축은 hard gate 잔존이 아니라 승인/적용 절차 문제로 본다.

## 2.4 Codebase Performance Workorder Contract

`codebase_performance_workorder_report`는 `docs/codebase-performance-bottleneck-analysis.md`의 성능개선 후보를 자동화체인 source artifact로 승격한다. accepted 후보도 즉시 코드 변경이 아니라 사용자가 별도 구현 지시할 수 있는 workorder 입력이며, 모든 후보는 `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`와 parity contract를 가져야 한다.

이 artifact의 금지선은 `runtime_threshold_mutation`, `provider_route_change`, `broker_order_guard_change`, `bot_restart`, `tuning_axis_change`, `source_quality_policy_change`, `raw_forensic_stream_suppression`이다. `kiwoom_orders` transport 재사용, config cache, legacy dashboard DB pool, WS tick parsing, raw suppression처럼 runtime/data-quality semantics가 바뀔 수 있는 후보는 accepted로 승격하지 않고 deferred/rejected로 남긴다.

## 2.3 Metric Decision Contract

자동화 체인이 소비하는 새 관찰지표와 새 report section은 생성 시점에 판정 계약을 함께 선언해야 한다. 계약이 없으면 해당 지표는 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅하고, threshold candidate, approval request, runtime env apply 입력으로 쓰지 않는다.

필수 필드는 아래와 같다.

| 필드 | 의미 |
| --- | --- |
| `metric_role` | 지표의 판정 역할. 아래 role taxonomy 중 하나 이상을 명시한다 |
| `metric_definition` | 분자/분모, 집계 단위, 포함/제외 조건, provenance field |
| `decision_authority` | `real_only`, `main_only_completed`, `sim_equal_weight`, `probe_observe_only`, `combined_diagnostic`, `source_quality_only`, `counterfactual_only` 중 하나 |
| `window_policy` | `daily_only`, `rolling_3d`, `rolling_5d`, `rolling_10d`, `cumulative_since_owner_start`, `post_apply_version_window`, `same_day_intraday_light` 중 primary/secondary window |
| `sample_floor` | hard 판정 최소 표본과 denominator. 표본 미달 시 `hold_sample` 또는 `report_only_calibration`으로 fail-closed |
| `primary_decision_metric` | 자동화 판정에 쓰는 단일 primary metric. EV 계열이면 필드명을 EV로 명확히 쓴다 |
| `secondary_diagnostics` | win rate, blocker share, active recovery, funnel count처럼 primary를 보조하는 지표 |
| `source_quality_gate` | freshness, missing, duplicate, stage provenance, real/sim/probe split 조건 |
| `runtime_effect` | 기본값은 `runtime_effect=false`. runtime 변경 가능 시 approval artifact, env key, rollback guard, same-stage owner rule을 함께 명시 |
| `forbidden_uses` | 단독 live 승인, real-like EV 합산, daily-only apply 등 금지 사용처 |

`metric_role` taxonomy는 아래 기준으로 고정한다.

| metric_role | 판정 용도 | 금지선 |
| --- | --- | --- |
| `primary_ev` | 기대값/순이익 개선 여부의 primary 판정. `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나로 명명한다 | `win_rate` 또는 단순 합산값으로 대체 금지 |
| `diagnostic_win_rate` | 방향성/일관성/꼬리 리스크 보조 진단 | 단독 approval/live/canary 승격 금지 |
| `funnel_count` | 참여율, blocker, coverage, submitted drought 판단 | 손익 edge 또는 live 승인 근거로 단독 사용 금지 |
| `safety_veto` | severe loss, 주문 실패, provenance 손상, hard/protect/emergency stop 지연 차단 | 기대값 개선 지표로 사용 금지 |
| `source_quality_gate` | stale/missing/duplicate/provenance 품질 gate | edge 또는 threshold 추천값으로 사용 금지 |
| `active_unrealized` | open sim/probe 회복률, active position context | closed EV로 해석하거나 realized PnL과 합산 금지 |
| `execution_quality_real_only` | 브로커 체결/취소/receipt 품질 | sim/probe/combined 진단으로 대체 금지 |
| `sim_probe_ev` | sim/probe equal-weight 기대값 관찰 | real execution 품질 또는 실주문 전환 근거로 단독 사용 금지 |
| `risk_regime_state` | 패닉/시장상태처럼 매매 가능 행동의 범위를 해석하는 상태값 | approval artifact와 rollback guard 없이 주문, 청산, threshold, provider, bot 상태를 직접 변경 금지 |

window 해석은 아래처럼 분리한다.

| window_policy | 허용 용도 |
| --- | --- |
| `daily_only` | incident, safety veto, freshness/source-quality, same-day operational trigger. edge apply 승인에는 단독 사용 금지 |
| `rolling_3d` / `rolling_5d` / `rolling_10d` | 방향성 지속성, step size, candidate persistence |
| `cumulative_since_owner_start` | owner/canary baseline 누적 성과와 rollback guard 판정 |
| `post_apply_version_window` | threshold version별 applied/not-applied attribution |
| `same_day_intraday_light` | Sentinel/ops 상태 확인. threshold/live candidate 승격 금지 |

판정 규칙은 다음을 따른다.

1. `win_rate`는 `diagnostic_win_rate`다. 기대값/순이익 목표의 primary 판정은 `primary_ev`가 맡는다.
2. 단순 손익 합산은 EV가 아니다. 필드명은 `simple_sum_profit_pct`로 쓰고, EV 판정 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나를 사용한다.
3. `sim_equal_weight`, `probe_observe_only`, `counterfactual_only`, `combined_diagnostic` 권한 지표는 source bundle, approval request, workorder evidence에는 들어갈 수 있지만 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
4. `sim/probe/counterfactual` 예산은 실주문 주문가능금액과 분리한다. 실주문 경로는 `blocked_zero_qty`/broker budget guard를 유지하지만, `actual_order_submitted=false` 관찰축은 기본 `SIM_VIRTUAL_BUDGET_KRW=10,000,000`을 가상 주문가능금액으로 두고 실주문 동적수량 산식(`describe_buy_capacity`, strategy ratio, safety ratio, 해당 전략 cap)을 그대로 탄다. provenance는 `virtual_budget_override=true`, `budget_authority=sim_virtual_not_real_orderable_amount`, `qty_source=sim_virtual_budget_dynamic_formula`, `virtual_budget_krw`, `target_budget`, `safe_budget`, `counterfactual_notional_krw`를 남긴다. 이 값은 real buying power, broker execution 품질, 실주문 가능 여부로 해석하지 않는다.
5. `position_sizing_dynamic_formula`는 동적수량 산식 튜닝 owner다. 입력은 `score`, `strategy`, `volatility`, `liquidity`, `spread`, `price_band`, `recent_loss`, `portfolio_exposure`로 선언하고, primary metric은 `notional_weighted_ev_pct` 또는 `source_quality_adjusted_ev_pct`만 허용한다. 상세 source bundle, sample floor, provenance fields, approval artifact schema는 [workorder-position-sizing-dynamic-formula](./workorder-position-sizing-dynamic-formula.md)가 소유한다. `position_sizing_cap_release`와 분리해 관리하며, sim/probe 단독으로 실주문 cap 해제나 수량 확대를 승인할 수 없다. 실주문 수량 확대는 별도 approval artifact와 rollback guard가 필요하다.
6. `daily`, `rolling`, `cumulative`가 필요한 family에서 daily-only 악화/개선은 safety veto 또는 calibration trigger로만 쓰고, edge apply 승인은 rolling/cumulative와 source-quality gate가 닫힌 뒤에만 허용한다.
7. 새 관찰지표가 위 필드를 갖지 않으면 자동화 체인은 `hold_sample`, `hold_no_edge`, `source_quality_blocker`, `instrumentation_gap` 중 하나로 닫고 threshold mutation을 만들지 않는다.

새 관찰지표 onboarding은 아래 10개 항목이 모두 닫힌 뒤에만 자동화 source bundle에 편입한다.

| 항목 | 필수 결정 |
| --- | --- |
| 1 | `metric_role` |
| 2 | `decision_authority` |
| 3 | `window_policy` |
| 4 | `primary_decision_metric`과 `secondary_diagnostics` 분리 |
| 5 | `sample_floor`와 denominator |
| 6 | source-quality/provenance gate |
| 7 | forbidden automation / forbidden live uses |
| 8 | consumer와 owner |
| 9 | JSON/Markdown field names |
| 10 | fail-closed behavior |

## 2.6 Sim-to-Live Approval Contract

sim/probe 결과는 source bundle, approval request, workorder evidence에는 들어갈 수 있지만 live 반영에는 반드시 별도 계약이 필요하다. 최소 계약은 `approval request`, `approval artifact`, `preopen env key mapping`, `runtime guard`, `rollback/provenance`, `real/sim metric split`이다.

2026-05-15 전수 감사 결과는 [sim-to-live-automation-contract-audit-2026-05-15](./sim-to-live-automation-contract-audit-2026-05-15.md)를 기준으로 한다. 현재 보정 완료된 연결부는 `swing_one_share_real_canary_phase0`이며, 기본 OFF, 별도 artifact 필수, 승인 code allowlist, qty 1, global swing dry-run 유지 조건을 갖는다. approval 요청 후보는 `approval_contract_status`, `approval_live_ready`, `approval_artifact_path`, `approval_contract_missing_components`를 함께 노출해야 한다. `position_sizing_cap_release`, `position_sizing_dynamic_formula`, `panic_entry_freeze_guard`, `panic_buy_runner_tp_canary`는 현재 `contract_missing`이며, artifact loader/env mapping/runtime guard가 구현되기 전까지 approval artifact를 만들어도 live 반영할 수 없다.

## 3. Sentinel Routing Standard

| Sentinel classification | 기본 라우팅 | threshold-cycle 연결 조건 | 금지된 자동변경 |
| --- | --- | --- | --- |
| `UPSTREAM_AI_THRESHOLD` | score50/wait65_74 cohort review, single-axis canary 후보 검토 | `COMPLETED + valid profit_rate`, missed/avoided counterfactual, sample floor, rollback owner가 모두 닫힌 별도 workorder | score threshold 완화, fallback 재개 |
| `LATENCY_DROUGHT` | latency 원인분해, quote freshness/SAFE normal submit 직전 수급 fade review | 두산 rollback 이후에는 spread cap 자동완화 금지. 반복성과 price/latency blocker attribution이 분리될 때만 `R3_manifest_only` 후보 | spread cap 완화, bot restart |
| `PRICE_GUARD_DROUGHT` | price resolver/guard attribution review | guard family sample floor와 fill quality rollback owner가 닫힌 경우만 `R3_manifest_only` 후보 | entry/scale-in guard runtime mutation |
| `HOLD_DEFER_DANGER` | holding_flow_override defer cost/worsen floor review | sell receipt/completed, GOOD_EXIT/MISSED_UPSIDE, defer worsen floor가 daily/rolling/cumulative에서 같은 방향일 때만 후보 | 자동 매도, holding_flow_override mutation |
| `SOFT_STOP_WHIPSAW` | soft stop rebound/tail report-only review | same-stage owner 충돌 해소, sample floor, rollback command가 닫힌 다음 장전 단일 owner 후보 | hard/protect stop 완화, 자동 청산 변경 |
| `TRAILING_EARLY_EXIT` | trailing missed-upside/winner wide-window review | protect/trailing family owner와 rollback guard가 닫힌 `R3_manifest_only` 후보 | trailing threshold runtime mutation |
| `AI_HOLDING_OPS` | AI cache/Tier provenance instrumentation backlog | threshold-cycle 직결 금지. cache 변경은 별도 AI ops workorder 필요 | AI cache TTL mutation, provider routing 변경 |
| `RUNTIME_OPS` | incident/playbook, stale pipeline/cron/runtime health check | threshold-cycle 직결 금지 | bot restart 자동 실행 |
| `NORMAL` | no-action | 없음 | 없음 |

Sentinel routing은 [2026-05-07 checklist](./2026-05-07-stage2-todo-checklist.md) `SentinelThresholdFeedback0507-Intraday`에서 표준화했다. `2026-05-08`부터 Sentinel Telegram 알림과 날짜별 notify state는 삭제됐고, report JSON/Markdown 생성과 classification 갱신만 매 실행 유지한다.

### 3.1 Panic Sell Defense Routing Standard

| panic_state | 기본 라우팅 | threshold-cycle 연결 조건 | 금지된 자동변경 |
| --- | --- | --- | --- |
| `NORMAL` | no-action | 없음 | 없음 |
| `PANIC_SELL` | 신규 live 진입 완화 금지 후보, stop-loss cluster attribution | V2 1차 후보는 `panic_entry_freeze_guard`다. approval artifact, rollback guard, runtime env key가 닫힌 뒤 다음 장전 pre-submit freeze canary로만 검토한다. `panic_stop_confirmation`은 후순위 | score threshold 완화, stop-loss 완화, 자동매도, bot restart |
| `RECOVERY_WATCH` | 회복 evidence 관찰, missed upside/방어효과 분리 | active sim/probe 평균 미실현 수익률 또는 post-sell rebound가 유지되고 provenance pass일 때 report-only 후보 유지 | live threshold mutation, 스윙 실주문 전환 |
| `RECOVERY_CONFIRMED` | `panic_rebound_probe` 후보 검토 | sim/probe only, `actual_order_submitted=false`, `broker_order_forbidden=true`, 장후 attribution과 다음 장전 bounded guard 필요 | broker order 제출, approval artifact 없는 swing real canary |

`panic_regime_mode`는 `panic_state`를 매매 로직에 직접 덮어쓰는 실행 신호가 아니라 risk-regime 해석 계층이다. metric contract는 `metric_role=risk_regime_state`, `decision_authority=source_quality_only` until approval artifact, `window_policy=same_day_intraday_light + postclose_attribution + next_preopen_apply`, `sample_floor=panic report freshness <= 5m and microstructure breadth floor when used`, `primary_decision_metric=source_quality_adjusted_avoided_loss_vs_missed_upside_ev_pct` for implemented guard attribution, `source_quality_gate=panic report provenance + real/sim/probe split + market/breadth confirmation`, `runtime_effect=false by default`, `forbidden_uses=auto_sell, stop_loss_relaxation, threshold_relaxation, provider_route_change, bot_restart, swing_real_order_enable`이다.

| panic_regime_mode | 입력 상태 | 허용되는 해석 | runtime 전환 조건 |
| --- | --- | --- | --- |
| `NORMAL` | `panic_state=NORMAL`, confirmed risk-off 없음 | 기존 selected family 유지 | 없음 |
| `PANIC_DETECTED` | `PANIC_SELL` 또는 confirmed risk-off/stop-loss cluster | 신규 위험 증가 금지 후보. AI BUY 판단은 기록하되 `blocked_by_panic` attribution 후보로 분리 | V2.0 `panic_entry_freeze_guard`만 approval artifact, env key, rollback guard, same-stage owner rule 완료 후 다음 장전 entry pre-submit canary 가능 |
| `STABILIZING` | `RECOVERY_WATCH`, 최소 관찰 시간/OFI 개선/스프레드 정상화/저점 재이탈 실패 후보 | 정상 모드 즉시 복귀 금지. sim/probe와 missed upside/avoided loss 비교만 유지 | 실주문 복구 금지. 필요 시 소량 탐색은 별도 approval-required canary로 분리 |
| `RECOVERY_CONFIRMED` | `RECOVERY_CONFIRMED`와 2~3회 회복 evidence | 일부 복구 후보를 장후 attribution에 남김 | 다음 장전 bounded guard 전까지 broker order 제출 금지 |

패닉 lifecycle 확장은 단계별 owner를 분리한다. V2.0은 `panic_entry_freeze_guard`로 scalping 신규 BUY pre-submit 차단만 다룬다. V2.1의 미체결 진입 주문 cancel guard, V2.2의 holding/exit `panic_context` 반영, V2.3의 강제 축소/청산 guard는 각각 별도 workorder, approval artifact, rollback guard가 필요하며 V2.0 승인과 자동으로 묶지 않는다.

`panic_sell_defense_report`는 장중 cron으로 5분 주기 생성하고, `2026-05-13`부터 `run_threshold_cycle_postclose.sh`가 threshold-cycle canonical report 생성 직전에 한 번 더 재생성한다. 이 postclose 재생성은 `panic_sell_state_detector`의 microstructure risk-off/recovery signal, stop-loss cluster, active sim/probe recovery, post-sell rebound를 같은 source bundle에 고정하기 위한 것이며 runtime mutation 권한은 없다.

`micro_cusum_observer`는 OFI z-score CUSUM과 2-of-N micro consensus를 `source_quality_gate` / `source_quality_only` / `intraday_observe_only` 계약으로만 노출한다. `primary_decision_metric`이 아니며 `runtime_threshold_apply`, 주문 제출, 자동매도/자동매수, bot restart, provider route 변경 근거로 사용할 수 없다.

`microstructure_market_context`는 개별 보유/관찰 종목군에서 나온 micro risk-off가 전체 지수/breadth로 확인되는지 검증하는 source-quality gate다. `confirmed_micro_risk_off_advisory=true`는 시장 snapshot `RISK_OFF` 또는 평가 종목수 `20`개 이상과 risk-off 비율 `20%` 이상일 때만 가능하다. `market_panic_breadth.risk_off_advisory=true`는 KOSPI/KOSDAQ weighted composite index/stock breadth 기준이며, 한 시장만 급락/급등한 경우는 `single_market_risk_off_advisory` 또는 `single_market_risk_on_advisory`로 분리한다. 확인되지 않은 국소 risk-off는 `portfolio_local_risk_off_only=true`와 `source_quality_blockers`로 downstream attribution에 전달하고, panic runtime approval은 `freeze` 또는 follow-up 후보로만 해석한다.

`panic_entry_freeze_guard`의 approval artifact 후보는 `data/threshold_cycle/approvals/panic_entry_freeze_guard_YYYY-MM-DD.json`이다. artifact가 없으면 env key를 쓰지 않고, artifact가 있어도 적용 범위는 scalping `entry_pre_submit` 신규 BUY 차단 후보로 제한한다. 기존 보유 청산, stop-loss, trailing, 스윙 실주문에는 영향을 주지 않는다. 상세 workorder는 [panic_entry_freeze_guard_v2_2026-05-13](./code-improvement-workorders/panic_entry_freeze_guard_v2_2026-05-13.md)를 기준으로 한다.

### 3.2 Panic Buying Routing Standard

`panic_buying_report`는 장중 cron으로 2분 offset 주기 생성하고, `2026-05-13`부터 `run_threshold_cycle_postclose.sh`가 threshold-cycle canonical report 생성 직전에 한 번 더 재생성한다. 이 postclose 재생성은 `panic_buying_state_detector`의 panic-buy/exhaustion signal과 fixed TP 대비 runner opportunity를 같은 source bundle에 고정하기 위한 것이며 TP/trailing/주문/threshold/provider mutation 권한은 없다.

`panic_buy_regime_mode`는 패닉바잉을 신규 추격매수 신호로 쓰기 위한 값이 아니라 보유 포지션의 TP/runner, 추격 진입 차단 후보, 급등 소진 후 cooldown 후보를 분리하는 risk-regime 해석 계층이다. metric contract는 `metric_role=risk_regime_state`, `decision_authority=source_quality_only` until approval artifact, `window_policy=same_day_intraday_light + postclose_attribution + next_preopen_apply`, `sample_floor=panic buying report freshness <= 2m intraday or postclose regenerated source bundle`, `primary_decision_metric=source_quality_adjusted_runner_vs_fixed_tp_ev_pct`, `source_quality_gate=panic buying detector confidence + market/breadth risk-on context + real/sim/probe split + TP counterfactual provenance`, `runtime_effect=false by default`, `forbidden_uses=auto_buy, chase_entry_without_pullback_rebreak_guard, full_market_sell, TP/trailing mutation without approval, hard/protect/emergency override, provider_route_change, bot_restart, broker_order_submit_without_approval`이다.

`market_wide_panic_buy_confirmed=false`이거나 `missing_orderbook_count`/`missing_trade_aggressor_count`가 남은 경우 downstream consumer는 이를 `source_quality_blocker` 또는 collector coverage workorder로만 라우팅한다. 해당 blocker가 존재하면 `panic_buy_runner_tp_canary` 표본이 있어도 threshold 후보, approval request, 실주문 전환 근거로 승격하지 않고 source-quality 보강 완료 후 재평가한다.

| panic_buy_regime_mode | 입력 상태 | 허용되는 해석 | runtime 전환 조건 |
| --- | --- | --- | --- |
| `NORMAL` | `panic_buy_state=NORMAL` | 기존 selected family와 고정 TP 정책 유지 | 없음 |
| `PANIC_BUY_DETECTED` | `PANIC_BUY_WATCH` 또는 초기 panic-buy signal | 신규 추격매수 금지 후보, 일부 익절 + runner 전환 후보를 report-only로 기록 | V2.0/V2.1 각각 approval artifact, env key, rollback guard, same-stage owner rule 완료 후 다음 장전 canary 가능 |
| `PANIC_BUY_CONTINUATION` | `PANIC_BUY`와 runner 허용 signal | 잔량 보유, 변동성 기반 trailing 폭 확대, 눌림/재돌파 진입 조건 후보를 attribution에 남김 | 기존 보유 TP/runner canary인 V2.0 범위부터 검토. 신규 진입 조건은 V2.1 이후 별도 owner |
| `PANIC_BUY_EXHAUSTION` | `EXHAUSTION_WATCH`, `BUYING_EXHAUSTED`, force runner exit signal | 잔량 cleanup/tight trailing 후보, 신규 진입 금지 후보 | V2.3 별도 approval-required canary 전까지 live exit 변경 금지 |
| `COOLDOWN` | detector internal `COOLDOWN` | 급등 종료 후 재진입 금지 후보, 과대 되돌림 counterfactual 관찰 | V2.4 별도 owner 전까지 entry gate 변경 금지 |

패닉바잉 lifecycle 확장은 단계별 owner를 분리한다. V2.0은 `panic_buy_runner_tp_canary`로 기존 보유 포지션의 fixed TP 전량청산 대비 일부 익절 + runner trailing 후보만 다룬다. V2.1은 `panic_buy_chase_entry_freeze`, V2.2는 `panic_buy_continuation_trailing_width`, V2.3은 `panic_buy_exhaustion_runner_cleanup`, V2.4는 `panic_buy_cooldown_reentry_guard`이며 각각 별도 workorder, approval artifact, rollback guard가 필요하다. V2.0 승인은 신규 매수 차단, 추가매수 금지, exhaustion cleanup, cooldown 진입차단으로 자동 확장되지 않는다.

`panic_buy_runner_tp_canary`의 approval artifact 후보는 `data/threshold_cycle/approvals/panic_buy_runner_tp_canary_YYYY-MM-DD.json`이다. artifact가 없으면 env key를 쓰지 않고, artifact가 있어도 적용 범위는 scalping 기존 보유분의 TP/runner canary로 제한한다. 신규 추격매수, 추가매수, hard/protect/emergency stop, provider route에는 영향을 주지 않는다. 상세 workorder는 [panic_buying_regime_mode_v2_2026-05-14](./code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md)를 기준으로 한다.

Panic Telegram 안내는 report 결과의 상태 전환만 소비한다. `notify_panic_state_transition`은 `tmp/panic_state_telegram_notify_state.json`으로 직전 상태를 저장하고, 패닉셀/패닉바잉의 시작과 해제에만 사용자 친화 문구를 보낸다. 패닉셀 `RECOVERY_CONFIRMED`는 1회 관측만으로 즉시 해제 알림을 보내지 않고 `release_pending`으로 한 번 보류한다. 다음 관측이 계속 `RECOVERY_CONFIRMED` 또는 `NORMAL`이면 해제를 보내고, `RECOVERY_WATCH`/`PANIC_SELL`로 재활성화되면 해제 알림 없이 active 상태를 유지해 해제 후 주의가 뒤따르는 역순 알림을 막는다. 또한 report 판정에서는 `confirmed_risk_off_advisory=true` 또는 live market breadth `risk_off_advisory=true`가 남아 있으면 개별 microstructure `recovery_confirmed_count>0`만으로 `RECOVERY_CONFIRMED`를 열지 않고 `RECOVERY_WATCH`로 제한한다. runtime wrapper 기본 수신자는 전체 등록 사용자이며, `PANIC_*_DRY_RUN=1` 또는 수동 `--audience admin --force` 테스트는 admin only다. 이 알림은 `R1_daily_report` 안내이며 주문/threshold/runtime guard 변경 권한이 없다.

## 4. auto bounded calibration gate

`R5_bounded_calibrated_apply`는 완전 무인으로 실행하되 아래 조건을 deterministic guard와 AI correction guard가 매일 자동 확인한다.

1. 후보 family별 sample floor와 current/recommended diff가 report에 존재한다.
2. `daily`, `rolling`, `cumulative`가 같은 방향을 가리키고, 그 방향은 `diagnostic_win_rate`나 `simple_sum_profit_pct`가 아니라 family 계약의 `primary_ev` metric으로 확인된다.
3. `main-only`, `normal_only`, `post_fallback_deprecation` cohort를 분리할 수 있다.
4. full fill과 partial fill이 섞여 있으면 손익 결론을 hard 승인 근거로 쓰지 않는다.
5. 같은 stage의 live owner가 하나만 존재한다.
6. safety guard owner, env key, 봇 기동 시 runtime env source 절차가 문서화되어 있다.
7. apply plan은 장중 mutation이 아니라 다음 장전 runtime env manifest로만 반영된다.
8. 적용 후 threshold version별 post-apply attribution과 daily EV report가 생성된다.
9. 조건 미달은 다음 manifest의 `calibration_state`로 조정한다. safety guard 위반 시에만 `safety_revert_required=true`로 원복 후보 처리한다.

현재 auto-bounded calibration 후보군은 `score65_74_recovery_probe`, `soft_stop_whipsaw_confirmation`, `holding_flow_ofi_smoothing`, `protect_trailing_smoothing`, `holding_exit_decision_matrix_advisory`, `bad_entry_refined_canary` 등이다. 단, 후보군에 있다는 사실은 apply 승인과 다르다. `bad_entry_refined_canary`는 2026-05-12 기준 joined lifecycle 표본 부족으로 observe-only hold이며, `trailing_continuation`은 GOOD_EXIT 훼손 리스크가 커서 report/calibration만 수행하고 live apply는 후순위로 둔다. calibration source는 `threshold_cycle` compact event와 함께 `data/report`의 BUY source(`buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`), 보유/청산 source(`holding_exit_observation`, `post_sell_feedback`, `trade_review`, `holding_exit_sentinel`), decision-support source(`holding_exit_decision_matrix`, `statistical_action_weight`) 요약을 사용한다. rolling/cumulative primary family는 `threshold_snapshot_by_window`뿐 아니라 창별 `calibration_source_bundle_by_window`를 같이 소비하고, source denominator가 snapshot denominator를 보완한 경우 `window_policy_audit`에 rendering/source alignment gap을 남긴다. `sentinel_followup`은 2026-05-07 단발 Markdown follow-up으로 현재 source bundle에서 제외한다. `preclose_sell_target`은 2026-05-10 제거되어 source bundle과 traceability inventory에서 제외한다.

`calibration_source_bundle.report_only_cleanup_audit`는 source bundle consumer가 없는 report-only/legacy 산출물을 매 실행마다 `source_quality_gate`로 감사한다. 현재 관리 대상은 `sentinel_followup`, policy-disabled `server_comparison`, 정기 full snapshot에서 제외된 legacy `add_blocked_lock`, 제거된 `preclose_sell_target`이다. `cleanup_candidate_count > 0`이면 source-quality warning과 정리 후보로 표면화하지만, 이 audit는 `source_quality_only`이며 runtime threshold, 주문, 자동매수/자동매도, bot restart, provider route 변경 권한이 없다.

2026-05-12 postclose 기준 `runtime_approval_summary`는 `warnings=[]`, `runtime_mutation_allowed=false`, `scalping_items=12`, `scalping_selected_auto_bounded_live=2`, `swing_requested=2`, `swing_approved=0`이다. 다음 장전 apply 후보는 deterministic/AI/same-stage guard가 닫힌 family만 인정하고, 스윙 approval request는 별도 approval artifact 없이는 env apply 대상이 아니다.

`pre_submit_price_guard` family에는 `entry_ai_price_canary_applied`, `latency_pass`, `order_bundle_submitted` 외에 `entry_submit_revalidation_warning`, `entry_submit_revalidation_block`, `entry_order_cancel_requested`, `entry_order_cancel_confirmed`, `entry_order_cancel_failed`를 포함한다. `scalp_ai_buy_all` simulator가 같은 entry price owner를 관찰할 때는 `scalp_sim_entry_ai_price_applied`, `scalp_sim_entry_ai_price_skip_order`, `scalp_sim_entry_submit_revalidation_warning`, `scalp_sim_entry_submit_revalidation_block`, `scalp_sim_buy_order_virtual_pending`을 같은 family의 sim-only 관찰 표본으로 포함하되, 실주문 제출/체결 품질과 섞지 않는다. `WAIT+score>=75+DANGER+1주 cap+USE_DEFENSIVE` 주문은 새 runtime family가 아니라 같은 entry price owner 내부 `passive_probe` lifecycle로 보며, bid-1tick 조정과 30초 timeout/cancel provenance를 daily EV attribution 입력으로만 사용한다. `passive_probe` 제출 직전 revalidation에서 `stale_context_or_quote`가 확인되면 브로커 제출 전 `entry_submit_revalidation_block`으로 차단하고, simulator에서는 `scalp_sim_entry_submit_revalidation_block`으로 차단해 모두 `actual_order_submitted=false`를 남긴다.

## 5. 금지선

- 누적 평균 단독으로 live threshold를 적용하지 않는다.
- report-only 산출물 이름에 `apply_ready=True`가 있어도 `auto_bounded_live`의 deterministic/AI/same-stage owner guard를 통과하기 전에는 runtime 변경으로 해석하지 않는다.
- 장중 threshold runtime mutation은 열지 않는다. 적용 단위는 장후 산출 -> 다음 장전 apply plan -> 장후 attribution이다.
- Project/Calendar owner가 없는 미래 자동화 작업은 유효한 next action으로 보지 않는다.
- Sentinel abnormal alert를 즉시 threshold 완화/강화, fallback 재개, 자동 매도, cache TTL mutation, bot restart로 연결하지 않는다.
- postclose collector가 live `pipeline_events_YYYY-MM-DD.jsonl` 대신 immutable snapshot을 읽어 `checkpoint_completed=true`를 만들더라도, 이는 R0/R1 수집 안정화일 뿐 auto bounded apply 통과로 보지 않는다.
- IPO listing-day autorun status는 YAML-gated 실주문 실행 감사용이다. 결과를 threshold-cycle calibration, daily EV, scalping/swing runtime threshold 입력으로 자동 소비하지 않는다.
- `runtime_approval_summary`는 read-only 요약 artifact다. `runtime_mutation_allowed=false`일 때는 flow 조정, 주문 차단, threshold mutation 권한이 없다.
- `plan_rebase_daily_renewal`은 proposal-only 문서 갱신 제안이다. 생성만으로 Plan Rebase, prompt, AGENTS.md, checklist, runtime env를 수정하지 않는다.
- 같은 날짜 workorder 재생성 여부를 `mtime`만으로 판정하지 않는다. `generation_id/source_hash/lineage` diff가 source of truth다.
- `update_kospi_status.completed_with_warnings`는 DB 적재 실패와 동일하지 않다. `failed_steps`를 확인해 `recommend_daily_v2`, dashboard upload, swing daily reports 같은 후행 step 실패를 분리한다.
- `_error.log` 파일명만 보고 모든 `DB` 문자열을 DB 장애로 분류하지 않는다. `log_scanner`는 ERROR/CRITICAL/traceback/exception/에러/오류/실패 후보 라인만 incident 후보로 본다. `MEMORY_ERROR`는 실제 memory/OOM signature만 인정하고 `kiwoom_*` logger 이름 내부의 `oom` 같은 부분 문자열은 메모리 장애로 분류하지 않는다.
- `win_rate`, `simple_sum_profit_pct`, `active_unrealized`, `combined_diagnostic`, `counterfactual_only` 지표는 단독으로 runtime apply, 실주문 전환, threshold 완화/강화 승인 근거가 될 수 없다.
- `metric_role`, `decision_authority`, `window_policy`가 없는 새 관찰지표는 threshold candidate가 아니라 instrumentation/source-quality backlog로만 본다.

## 6. 다음 추적 항목

미래 작업의 실행 owner는 날짜별 checklist가 소유한다. 현재 연결 owner는 [2026-05-13-stage2-todo-checklist.md](./2026-05-13-stage2-todo-checklist.md)의 장전/장중/장후 자동 생성 항목이며, 이전 완료 기록은 [2026-05-12-stage2-todo-checklist.md](./2026-05-12-stage2-todo-checklist.md)의 `PostcloseAutomationHealthCheck20260512`, `CodeImprovementWorkorderReview0512`, `LogScannerDbErrorBurstFalsePositive0512`를 증적으로 본다.
