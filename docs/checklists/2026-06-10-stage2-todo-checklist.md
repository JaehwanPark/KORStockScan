# 2026-06-10 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- 2026-06-10 사용자 승인으로 실제 스캘핑 신규 BUY의 1주 hard cap은 해제하고, 주문가능금액 기준 10~30% 비중 산식과 주문가능금액 내 최소 1주 floor만 허용한다. sim/probe, 스윙 dry-run, threshold/provider/bot 권한과 분리한다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-06-09` postclose -> `2026-06-10`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0610] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-10`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-09.json), [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과: `pre_final_auto_selected`.
  - 판정: 스윙 final full-live 승인 artifact는 없고, `swing_gatekeeper_reject_cooldown`만 AI Tier2 pre-final auto 상태로 2026-06-10 PREOPEN dry-run env 후보에 선택됐다. 실주문, full-live 전환, cap release, provider/bot 변경 권한은 열지 않는다.
  - 근거: `swing_runtime_approval_2026-06-09.json` summary는 `requested=1`, `blocked=12`, `runtime_change=false`이고 `swing_entry_ofi_qi_execution_quality`, `swing_scale_in_ofi_qi_confirmation` source-quality blocked family를 남겼다. `threshold_apply_2026-06-10.json`의 PREOPEN 소비 결과는 `swing_gatekeeper_reject_cooldown` 1건을 `approval_mode=ai_tier2_pre_final_auto`, `approval_runtime_scope=swing_dry_run_env_only`, `dry_run_forced=true`로 선택했고, `KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN=6600`만 env 후보에 반영했다.
  - 다음 액션: 오늘 장중에는 dry-run env provenance만 관찰한다. 스윙 OFI/QI source-quality blocked family와 final full-live conversion은 장후 source-quality/workorder 및 별도 final approval artifact 기준으로 재확인한다.

- [x] `[ThresholdEnvAutoApplyPreopen0610] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-10`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과: `applied_guard_passed_env`.
  - 판정: 2026-06-10 PREOPEN wrapper, apply plan, runtime env 생성은 성공했다. 단, lifecycle/runtime apply bridge live-auto 후보는 계속 blocked/selected 없음으로 남아 있고 수동 override는 감지되지 않았다.
  - 근거: `threshold_cycle_preopen_2026-06-10.status.json`은 `status=succeeded`, `exit_code=0`, `apply_mode=auto_bounded_live`, `runtime_effect=preopen_runtime_env_apply_only`, `finished_at=2026-06-10T07:35:01+09:00`이다. `threshold_apply_2026-06-10.json`은 `status=auto_bounded_live_ready`, `runtime_change=true`, `warnings=[]`, runtime env path를 기록했다. `threshold_runtime_env_2026-06-10.json`의 selected families는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `swing_gatekeeper_reject_cooldown`, `scalp_sim_scale_in_window_expansion`, `lifecycle_bucket_discovery_sim_auto_approval`, `swing_sim_auto_approval`이고 `operator_runtime_override=null`이다. runtime apply bridge는 `approved=0`, `selected=[]`이며 bridge/source-quality/AI parse blocker를 유지한다.
  - 주의: 현재 bot process env에서는 2026-06-09 operator percent-bps 진입가 override 계열 env가 확인되지 않았다. 오늘도 해당 override를 유지하려면 별도 operator 지시와 우아한 재기동 판단이 필요하며, 이 체크리스트 처리에서는 runtime 값을 변경하지 않았다.
  - 다음 액션: 오늘 장중에는 생성된 2026-06-10 runtime env만 source로 보고 provenance/rollback guard를 관찰한다. blocked bridge family는 수동 env override로 우회하지 않는다.

운영 확인 메모: `[PreopenAutomationHealthCheck20260610]` 판정은 `warning`.

- 판정: 장전 자동화 core chain은 정상 완료됐고 bot도 07:40 정상 기동했지만, 07:20 scanner의 macro Gemini 호출이 `RESOURCE_EXHAUSTED`로 실패해 cache fallback을 사용했으므로 운영 상태는 `warning`으로 닫는다.
- 근거: `logs/threshold_cycle_preopen_cron.log`는 `[DONE] threshold-cycle preopen target_date=2026-06-10 finished_at=2026-06-10T07:35:01+0900`를 남겼고, `logs/bot_history.log`는 tmux bot 기동, Kiwoom login/WS 연결, 계좌 sync, 조건식 등록, OpenAI engine 초기화, 07:45~07:55 monitor heartbeat를 기록했다. `data/report/error_detection/error_detection_2026-06-10.json`은 `summary_severity=pass`이며 process/cron/log/auth/artifact/resource/stale-lock detector가 모두 pass다. `logs/ensemble_scanner.log`는 final scanner DONE과 V2 CSV 3개 우선 적재를 기록했지만 macro Gemini 429 cache fallback도 함께 기록했다.
- 다음 액션: Gemini quota/provider fallback은 threshold/order/provider route 변경 근거로 쓰지 않고, 장중 RunbookOps에서는 bot heartbeat, Kiwoom WS, scanner fallback 지속 여부만 추가 관찰한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0610] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-10`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0610] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-10`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0610] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-10`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-10.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-10.jsonl), [threshold_events_2026-06-10.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-10.jsonl), [observation_source_quality_audit_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-10.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-10 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[PostcloseSourceQualityGateReview0610] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-10`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-10.json), [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json), [code_improvement_workorder_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-10.json), [threshold_cycle_postclose_verification_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-10.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0610] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-10`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0610] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-10`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-09.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-09.md), [code_improvement_workorder_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-09.json)
  - 판정 기준: selected_order_count=122와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0610] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-10`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[LifecycleQuietGapReview0610] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-06-10`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-09.json), [runtime_apply_gap_audit_2026-06-09.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-09.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`281`, rollup_required_count=`281`, sim_live_connected_quiet_gap_count=`18`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'absorbed_into_parent_policy': 5, 'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 21, 'parent_conflict_child': 69, 'positive_source_only_keep_collecting': 262}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0610] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-10`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-09.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`13`, skip_count=`2`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review, codebase_performance_workorder`, top_reasons=`upstream_drift_signal:13, fresh_outputs_no_trigger:2, output_missing_or_unreadable:2, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
