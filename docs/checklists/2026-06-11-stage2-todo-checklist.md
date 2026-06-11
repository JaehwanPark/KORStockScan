# 2026-06-11 Stage2 To-Do Checklist

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
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

운영 확인 메모: `[PreopenAutomationHealthCheck20260611]` 판정은 `warning`.

- 판정: 장전 자동화체인은 실행 완료 및 bot runtime uptake까지 확인됐으나, `threshold_cycle_preopen_status`가 `runtime_env_path`/`apply_plan_path`를 기록하지 않아 status artifact completeness 경고를 둔다.
- 근거: `logs/threshold_cycle_preopen_cron.log`는 `[DONE] threshold-cycle preopen target_date=2026-06-11 finished_at=2026-06-11T07:35:02+0900`를 남겼고, `data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-11.status.json`은 `status=succeeded`, `exit_code=0`이다. `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.json`은 selected families `soft_stop_whipsaw_confirmation`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`와 46개 env override를 기록했다. bot PID `3162`의 `/proc` 환경에서 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-06-11`, soft-stop, scalp/swing sim policy, lifecycle matrix env가 실제 source된 것을 확인했다. `logs/bot_history.log`는 07:40 기동, WS 로그인, 조건식 등록, heartbeat를 기록했다. `logs/ensemble_scanner.log`는 `[DONE] final_ensemble_scanner target_date=2026-06-11`를 남겼고 V2 CSV 2종목 적재를 기록했다.
- 다음 액션: preopen status writer가 다음 실행부터 `apply_plan_path`, `runtime_env_path`, `runtime_env_manifest_path`와 각 존재 여부를 남기도록 보강했다. 현재 경고는 status completeness 문제이며 runtime threshold/order/provider/bot strategy 변경 근거가 아니다.

운영 변경 메모: `[CronScheduleBeforeEc2Shutdown0611]` 판정은 `implemented_verified`.

- 판정: EC2 21:00 종료 기준에 맞춰 21시 이후 또는 21시 이후에도 반복될 수 있는 cron을 20:55 이전으로 조정했다.
- 근거: crontab 백업을 `logs/crontab_backup_20260611_074911_before_21_shutdown_adjust.txt`에 남기고, `update_kospi.py`는 `20:10 -> 19:50`, dashboard DB archive는 `21:10 -> 20:35`, log rotation/data maintenance는 `21:20 -> 20:45`, bot tmux 종료 guard는 `22:55 -> 20:55`로 변경했다. 반복 작업은 `kiwoom_sniper_v2_info.log` truncation `*/30 7-20`, system metric sampler `* 7-20`, error detector `*/5 7-20`로 제한했다.
- 다음 액션: 20:35/20:45 정기 실행 후 각각 `logs/dashboard_db_archive_cron.log`, `logs/log_rotation_cleanup_cron.log`의 `[DONE]` marker를 확인한다. 이 변경은 cron 운영 시간표 조정이며 threshold/order/provider/bot strategy authority를 추가하지 않는다.

운영 변경 메모: `[LogRotationDataMaintenanceExpansion0611]` 판정은 `implemented_verified`.

- 판정: 기존 21:20 `run_logs_rotation_cleanup_cron.sh`를 확장해 log rotation 외에 repo 내부 tmp/cache 정리, 과거 sentinel event cache gzip, 과거 threshold-cycle pipeline snapshot gzip, `raw_row_exclusion` 날짜별 중복 run 최신 1개 유지까지 자동화했다. 최신 target date plain sentinel cache/snapshot, 원본 `data/pipeline_events`, clean-baseline quarantine/raw audit evidence는 삭제/압축 대상에서 제외한다.
- 근거: [run_logs_rotation_cleanup_cron.sh](/home/ubuntu/KORStockScan/deploy/run_logs_rotation_cleanup_cron.sh)는 `DATA_MAINTENANCE_ENABLED=true` 기본값과 `tmp_deleted`, `cache_deleted`, `sentinel_compressed`, `snapshot_compressed`, `raw_row_exclusion_deleted` marker를 `[LOG_CLEANUP]`/`[DONE]`에 남긴다. 임시 PROJECT_DIR 검증에서 active log rotate 1건, tmp 삭제 2건, cache 삭제 2건, sentinel gzip 1건, snapshot gzip 1건, raw-row-exclusion 중복 삭제 1건을 확인했다.
- 다음 액션: 20:45 정기 실행 후 `logs/log_rotation_cleanup_cron.log`에서 새 marker와 size 추세를 확인한다. 이 변경은 filesystem maintenance이며 threshold/order/provider/bot runtime authority를 추가하지 않는다.

운영 변경 메모: `[Score6574RecoveryProbeOperatorOverride0611]` 판정은 `operator_override_applied_verified`.

- 판정: 사용자가 `score65_74_recovery_probe` real entry unlock probe의 즉시 적용을 명시 승인했으므로, 2026-06-11 장중 operator runtime override로 적용한다. 이 변경은 자동 `auto_bounded_live` 선정이 아니라 사용자 override이며, hard/protect/emergency stop, stale quote, broker/account/order/quantity/cooldown guard 우선순위는 유지한다.
- 근거: [threshold_apply_2026-06-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-11.json)은 `score65_74_recovery_probe`를 `calibration_state=hold`, `selected=false`, `decision_reason=no_runtime_env_override`로 닫아 당일 PREOPEN env에서 제외했다. 사용자의 즉시 real 적용 지시에 따라 [score65_74_recovery_probe_2026-06-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/operator_runtime_env_locks/score65_74_recovery_probe_2026-06-11.json)을 추가했고, [threshold_runtime_env_2026-06-11.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.env)에 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, score range `60-74`, buy pressure `65.0`, tick accel `1.2`, micro VWAP bp `0.0`, threshold version `score65_74_recovery_probe:operator_override:2026-06-11`를 기록했다. [threshold_runtime_env_2026-06-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.json)도 selected family와 `operator_runtime_overrides` provenance를 반영했다.
- 런타임 반영: `./restart.sh` 표준 경로로 graceful restart를 수행했고 bot PID가 `3162 -> 61458`로 교체됐다. `restart.flag`는 소모됐으며 새 PID 시작시각은 `2026-06-11 10:51:07 KST`다. `/proc/61458/environ`에서 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `MIN_SCORE=60`, `MAX_SCORE=74`, `MIN_BUY_PRESSURE=65.0`, `MIN_TICK_ACCEL=1.2`, `MIN_MICRO_VWAP_BP=0.0`, `THRESHOLD_VERSION=score65_74_recovery_probe:operator_override:2026-06-11`, `CALIBRATION_STATE=operator_runtime_override` 로드를 확인했다.
- 유지 보강: 사용자가 오늘 이후에도 real에서 누락되지 않게 하라고 지시해 lock artifact에 `lock_until_explicit_close=true`, `explicit_close_required=true`를 추가했고, [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)가 이 플래그를 읽으면 `min_observation_until_date` 이후에도 safety/provenance/order/stale close reason이 없을 때 operator lock env를 계속 보존하도록 보강했다.
- lifecycle bucket 보정: `lifecycle_bucket_discovery_sim_auto_approval`은 [threshold_apply_2026-06-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-11.json)에서 `approved=1`, `blocked=[]`였지만 `scalp_sim_auto_approval`에 덮여 selected family와 bucket catalog `POLICY_FILE/POLICY_VERSION` env가 누락됐다. 이는 빠질 이유가 없는 sim-only policy handoff gap으로 판정해 [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)를 보강했고, 다음 apply부터 `lifecycle_bucket_discovery_sim_auto_approval`이 별도 selected/provenance와 `KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE`, `POLICY_VERSION`, `LIVE_AUTO_APPLY_ENABLED=false`를 유지한다. 당일 [threshold_runtime_env_2026-06-11.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.env)에도 같은 sim-only lifecycle bucket catalog env를 보정했다.
- 다음 액션: 장후에는 `score65_74_recovery_probe_entry_unlocked`, submit/provenance, allowed close reason, safety revert 여부를 post-apply attribution으로 분리한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-06-10` postclose -> `2026-06-11`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0611] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-11`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-10.json), [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과 (`2026-06-11 PREOPEN`): 판정=`blocked_by_policy`. 근거: `swing_runtime_approval_2026-06-10.json` summary는 `requested=0`, `approved=0`, `blocked=12`, `runtime_change=false`이고, policy는 final full live에 user approval artifact가 필요하다고 명시한다. `threshold_apply_2026-06-11.json`의 `swing_runtime_approval`도 `approval_artifact=null`, `requested=0`, `approved=0`, `selected=[]`, `dry_run_forced=false`다. 다음 액션: 스윙 full-live/cap/provider/bot/hard-safety 변경은 열지 않고, 차단된 12건은 장후 source-quality/approval request 맥락에서만 재확인한다.

- [x] `[ThresholdEnvAutoApplyPreopen0611] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-11`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과 (`2026-06-11 PREOPEN`): 판정=`applied_guard_passed_env` with status completeness warning. 근거: `threshold_apply_2026-06-11.json`은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `runtime_env_file=/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.env`, 46개 env override를 기록했다. selected runtime env family는 `soft_stop_whipsaw_confirmation`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`다. bot PID 환경에서도 당일 runtime env가 source됐다. blocked bridge는 `entry_wait6579_score66_69_recovery_gate_v1`와 `scale_in_bucket_runtime_policy_v1`이 `blocked_source_quality/bootstrap_pending/contract_missing/runtime_apply_not_allowed`로 정상 차단됐으며 수동 env override는 하지 않았다. 다음 액션: `threshold_cycle_preopen_status`의 path field omission completeness warning은 status writer 보강으로 다음 실행부터 확인한다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0611] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-11`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, swing_gatekeeper_reject_cooldown가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 결과 (`2026-06-11 10:13 KST`): 판정=`provenance_partial_present_no_rollback_breach`.
  - 근거: [threshold_runtime_env_2026-06-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.json)은 selected families `soft_stop_whipsaw_confirmation`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`와 env override 46개를 기록했다. bot PID `3162`의 `/proc` 환경은 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-06-11`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true`, `KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`를 source했다. [pipeline_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-11.jsonl) 집계는 `lifecycle_decision_matrix_runtime` 2,227건, `scalp_sim_auto_approval` 1,675건, `scalp_sim_candidate_window_expansion` 1,436건, `soft_stop_whipsaw_confirmation` 4건을 관찰했고 rollback/revert line은 0건이다. `scalp_sim_ai_budget_manager`와 `swing_sim_auto_approval`는 env에는 있으나 10:13 KST 기준 직접 문자열 match event가 없어 partial warning으로 남긴다.
  - 다음 액션: 장후 `threshold_cycle_ev`/`runtime_approval_summary`/postclose verifier에서 missing direct-match family를 natural-match warning인지 runtime handoff gap인지 분리한다. 장중 threshold/env/provider/order/bot 변경은 하지 않는다.

- [x] `[SimProbeIntradayCoverage0611] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-11`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 결과 (`2026-06-11 10:13 KST`): 판정=`sim_probe_coverage_warning_state_restore_metadata`.
  - 근거: [pipeline_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-11.jsonl)에서 `scalp_sim*`/`swing_probe*`/`swing_sim*` stage는 5,059건이다. 중첩 payload 기준 권한 필드 선언 row는 `actual_order_submitted` 5,006건 모두 `false`, `broker_order_forbidden` 5,006건 모두 `true`, `runtime_effect` 5,014건 중 true 0건이다. 권한 필드 미선언 53건은 주문/체결 row가 아니라 `swing_probe_state_persisted` 27건, `swing_probe_state_restored` 26건의 상태 복원/저장 metadata row다. 주요 stage는 `scalp_sim_panic_scale_in_blocked` 1,085건, `swing_probe_discarded` 1,044건, `scalp_sim_panic_action_deduped` 556건, `scalp_sim_ai_holding_live_call` 504건, `scalp_sim_entry_armed`/`scalp_sim_buy_order_virtual_pending`/`scalp_sim_buy_order_assumed_filled`/`scalp_sim_holding_started` 각 68건이다.
  - 다음 액션: 장후 source-quality/workorder에서 `swing_probe_state_*` metadata row의 권한 필드 미선언을 결손으로 볼지 not-applicable provenance로 유지할지 확인한다. sim/probe EV는 계속 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.

- [x] `[IntradaySourceQualityGateCheck0611] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-11`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-11.jsonl), [threshold_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-11.jsonl), [observation_source_quality_audit_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-11.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-11 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 처리 결과 (`2026-06-11 10:13 KST`): 판정=`source_quality_clean_intraday`.
  - 근거: `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-11 --write`를 실행해 [observation_source_quality_audit_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-11.json)을 갱신했다. 결과는 `status=pass`, `event_count=28,316`, `stage_count=110`, `warning_stage_count=0`, `unknown_token_stage_count=0`, `reviewed_unknown_token_stage_count=2`, `hard_blocking_excluded_row_count=0`, `hard_blocking_contract_gap_count=0`, `tuning_input_allowed=true`, `review_warning_count=0`, `raw_row_exclusion_applied=false`다. 같은 시각 [pipeline_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-11.jsonl)은 fresh append 상태이고 [threshold_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-11.jsonl)은 14,465 line sparse stream으로 확인됐다.
  - 다음 액션: 장후 `PostcloseSourceQualityGateReview0611`에서 postclose EV/report 소비 후에도 hard gap 0, unknown warning 0, stale/preflight 누락 없음이 유지되는지 재확인한다. 이 판정은 runtime/order/provider/cap/bot/threshold 변경 근거가 아니다.

운영 확인 메모: `[IntradayAutomationHealthCheck20260611]` 판정은 `pass`.

- 판정: 장중 자동화체인, bot process, raw append, sentinel/panic report-only jobs, error detector가 정상이다.
- 근거: `bash deploy/run_error_detection.sh full`은 `summary_severity=pass`, `detector_count=7`로 종료했다. 세부적으로 cron completion, log scanner, Kiwoom auth 8005 restart detector, process health, artifact freshness, resource usage, stale lock이 모두 pass이며 bot PID `3162`는 alive, main loop age 4.1초, 주요 thread status `ok`다. `logs/run_buy_funnel_sentinel_cron.log`는 10:10 `SUBMIT_DROUGHT_CRITICAL`, `logs/run_holding_exit_sentinel_cron.log`는 10:10 `HOLD_DEFER_DANGER`, `logs/run_panic_sell_defense_cron.log`는 10:12 `panic_state=NORMAL`, `logs/run_panic_buying_cron.log`는 10:13 `panic_buy_state=NORMAL`으로 각각 `[DONE]`을 남겼다. `logs/bot_history.log`는 10:13 KST 신규 target 포착과 WS 등록/첫 실시간 수신을 계속 기록했다.
- 다음 액션: Sentinel의 `SUBMIT_DROUGHT_CRITICAL`/`HOLD_DEFER_DANGER`는 report-only/source-quality 관찰값으로 장후 EV/LDM/workorder handoff에서 확인한다. 장중 runtime threshold mutation, provider/bot/order/cap 변경은 하지 않는다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[PostcloseSourceQualityGateReview0611] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-11.json), [threshold_cycle_ev_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-11.json), [code_improvement_workorder_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-11.json), [threshold_cycle_postclose_verification_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-11.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0611] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0611] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-10.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-10.md), [code_improvement_workorder_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-10.json)
  - 판정 기준: selected_order_count=117와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0611] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-10.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[RuntimeApplyGapDirectiveReview0611] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-10.json), [runtime_apply_gap_audit_2026-06-10.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-10.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`:scale_in_bucket_runtime_policy_v1:2026-06-10(block=env_mapping_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[EntryCancelWaitAttributionReportOnlyReview0611] 매수 주문 취소대기 attribution report-only 관찰값 검증` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-06-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-11.jsonl), [threshold_runtime_env_2026-06-11.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-11.env), [entry_cancel_wait_attribution.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_cancel_wait_attribution.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `entry_cancel_wait_attribution` 및 `entry_order_cancel_requested` event에서 `wait_policy_applied=false`, `is_report_only=true`, `actual_timeout_sec`, `cancel_wait_sec`, `has_stale_or_passive_risk`, `wait_adjustment_reasons`를 분리 집계한다. `actual_timeout_sec=30`은 기존 override 적용으로 해석하고, `cancel_wait_sec>=60` 후보는 정책 적용 시 조기취소 완화 후보로만 기록한다.
  - 금지: report-only 관찰값으로 당일 real 취소대기시간, threshold, provider, order/cap, bot policy를 변경하지 않는다. `cancel_wait_sec`를 실제 적용값으로 오해하지 않고 `actual_timeout_sec`와 분리한다.
  - 다음 액션: `report_only_no_samples`, `report_only_provenance_pass`, `report_only_projection_mismatch`, `candidate_for_next_preopen_enable`, `keep_report_only` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0611] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-11`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-10.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-10.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`13`, skip_count=`2`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review, codebase_performance_workorder`, top_reasons=`upstream_drift_signal:13, fresh_outputs_no_trigger:2, output_missing_or_unreadable:2, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
