# Time-Based Operations Runbook

작성 기준: `2026-07-03 KST`
목적: 장전, 장중, 장후 자동화 체인의 실행 주체, 산출물, 확인 기준을 간결하게 고정한다.

이 문서는 실행 절차 runbook이다. 튜닝 원칙과 active owner는 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 작업 소유권은 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 산출물 추적성은 [report-based-automation-traceability.md](./report-based-automation-traceability.md), threshold-cycle 공통 산출물 정의는 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)를 기준으로 한다.

튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 이 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 본다. EV, rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다. `threshold_cycle_preopen_status`와 `threshold_cycle_postclose_status`는 운영 freshness status artifact라 이 제한에서 제외한다.

## 운영 원칙

- 기본 흐름은 무인 자동화다. 장전에는 전일 postclose artifact와 deterministic guard가 만든 `auto_bounded_live` 후보만 runtime env로 반영한다.
- 장중 threshold runtime mutation은 금지한다. 장중 산출물은 source-quality, incident, 다음 장전 후보 입력으로만 쓴다.
- AI reviewer는 제안과 감리 계층이다. 최종 state/value는 deterministic guard, source-quality gate, approval contract가 결정한다.
- broker submit guard, stale quote, price freshness, hard/protect/emergency stop, account/order/cooldown/quantity guard는 항상 최상위 safety다. ADM, LDM, bridge, approval artifact는 이 guard를 우회할 수 없다.
- `lifecycle_decision_matrix_runtime`은 ADM 확장 owner다. selected PREOPEN env가 있을 때만 기존 ADM adapter를 감싸며, 기본 산출물은 `runtime_effect=false`인 report/provenance다.
- `lifecycle_bucket_discovery`와 `runtime_apply_bridge`는 complete lifecycle bucket이 실제 runtime 후보가 될 수 있는지 확인하는 계약 계층이다. entry-only bridge metadata, source-only 후보, blocked contract gap은 live env로 해석하지 않는다.
- `producer_gap_discovery`, `time_window_regime_counterfactual`, pattern lab, sentinel류 report는 source-only 또는 report-only다. workorder와 후속 분석을 만들 수 있지만 실주문, threshold, provider, bot, cap을 직접 바꾸지 않는다.
- sim-first lifecycle은 기존 threshold-cycle 자동화체인의 관찰 범위다. sim/probe/dry-run row는 `actual_order_submitted=false`, `broker_order_forbidden=true` 계약을 유지한다.
- 스윙은 기본 dry-run이다. pre-final dry-run auto approval은 다음 PREOPEN env 후보가 될 수 있지만, final full-live conversion은 별도 사용자 승인 artifact와 runtime guard가 닫힌 경우에만 열린다.
- `entry_cancel_wait_runtime`, `entry_reprice_after_submit_runtime`, panic gap weight, submit drought quote freshness 보강처럼 real-only 운영축은 각 축의 runtime family와 operator lock 기준을 따른다. 일반 LDM/ADM EV와 섞어 자동 승격하지 않는다.
- BUY Telegram은 브로커 BUY 주문 제출 성공 이후에만 발송한다. AI confirmed, sim/probe, pre-submit 분석은 Telegram 알림 대상이 아니다.
- 사람이 개입하는 지점은 운영 장애, final full-live/cap/provider/bot/hard-safety 승인, Codex runner 차단 해소, 문서 backlog Project/Calendar 동기화다. safe-scope `runtime_effect=false` workorder는 사용자 지시 또는 수동 opt-in runner에서만 구현한다.
- 이 문서에서 “확인”은 artifact, log, source-of-truth 문서를 읽고 `pass|warning|fail|not_yet_due`로 분류하는 행위다. 확인만으로 live env, runtime threshold, broker 주문 상태를 변경하지 않는다.

## 역할/권한 경계

| 주체 | 할 일 | 하지 말 일 | 증적 |
| --- | --- | --- | --- |
| cron/runtime wrapper | 정해진 시각에 preopen/intraday/postclose job 실행, artifact와 log 생성 | 임의 threshold 변경, broker 주문 가드 우회, 실패 은폐 | `data/report/**`, `data/threshold_cycle/**`, `data/pattern_lab/**`, cron log |
| deterministic guard | threshold family별 bounds, max step, sample floor, rollback guard를 적용해 최종 state/value 산출 | AI 제안을 그대로 live 적용, 장중 runtime mutation 수행 | apply plan JSON, runtime env JSON, daily EV report |
| runtime apply bridge | Parsed AI 2-pass가 명시적 gap을 찾지 못한 LDM entry/scale bucket 후보를 named runtime family 후보로 정규화하고 env mapping/runtime hook/post-apply attribution 준비 여부를 판정 | AI failure/unparsed 상태의 pre-final apply, `runtime_effect=false` bucket 직접 적용, not-ready 후보 수동 승인 | `lifecycle_bucket_discovery_YYYY-MM-DD.{json,md}`, `runtime_apply_bridge_YYYY-MM-DD.{json,md}`, target env keys, blocked reasons |
| 자동 AI reviewer | threshold/logic/prompt 개선 후보를 proposal-only로 작성 | live env 변경, 주문 판단 직접 변경, deterministic guard 대체 | `swing_threshold_ai_review`, AI correction artifact, strict JSON schema 결과 |
| producer gap discovery | sim/probe/real-flow 결과에서 누락 producer 후보를 source-only로 발굴하고 AI review로 구현요건을 보강해 workorder에 넘김. rolling sim scan을 기본으로 entry/submit/holding/exit/scale-in/time-window/source-quality 누락을 먼저 확인하고, real 사례는 incident anchor로만 보조 사용. time-window seed cutoff는 hard gate가 아니라 `time_window_regime_counterfactual` source와 비교해 확인 | 누락 producer 후보를 live 적용, 실주문 전환, threshold/provider/bot/cap 변경 또는 시간대 hard gate 근거로 사용 | `producer_gap_discovery_YYYY-MM-DD.{json,md}`, `time_window_regime_counterfactual_YYYY-MM-DD.{json,md}`, `code_improvement_workorder`, postclose verifier |
| swing runtime approval | 스윙 dry-run pre-final auto approval 생성, final-stage approval request 생성, dry-run runtime env 후보 연결 | Tier2 실패 상태의 env 반영, dry-run 해제, 사용자 승인 없는 full-live 전환, 승인 없는 real authority 생성, 브로커 주문 허용 | `swing_runtime_approval`, `threshold_apply_YYYY-MM-DD.json`, runtime env JSON |
| Codex | 사용자 요청 또는 postclose workorder runner safe scope에서 코드/문서 수정, artifact 검증, parser/test 실행, workorder 작성 또는 구현, dedicated worktree branch commit | GitHub Project/Calendar 동기화 실행, 사용자 승인 없는 live guard 완화, broker 주문 제출, provider/bot/cap/hard-safety 변경, 임의 패키지 설치 | 변경 파일, 테스트 결과, runner artifact, dedicated branch commit |
| 사람/operator | 장전/장중/장후 판정 검토, approval request 승인 여부와 approval artifact 생성 여부 결정, 외부 동기화 명령 실행, 운영 장애 복구 판단, Codex SDK 인증/package gap 해소 여부 결정 | 자동화 artifact만 보고 이미 live 변경됐다고 간주, approval artifact 없이 env를 수동 작성, 출처 없는 수동 threshold 변경 | approval artifact, 수동 실행 명령, Project/Calendar 상태, 운영 메모 |

## 판정 상태 정의

- `pass`: 필수 artifact가 존재하고, 필수 필드가 유효하며, 금지된 runtime 변경이나 provenance 누락이 없다.
- `warning`: artifact는 존재하지만 sample 부족, stale/missing 관찰축, retry, 일부 보조 산출물 지연처럼 다음 관찰이 필요한 상태다. 이 상태만으로 live threshold를 변경하지 않는다.
- `fail`: 필수 artifact 누락, schema/parse 실패, 미정의 canonical label, cron/wrapper 실패, runtime provenance 누락, 금지된 runtime 변경 징후가 있는 상태다. 조치는 운영 장애 복구, instrumentation 보강, 또는 workorder 생성이지 즉시 threshold 수동 변경이 아니다.
- `not_yet_due`: 정해진 실행 시각이 아직 지나지 않았거나, 장후 장시간 job이 허용 대기시간 안에서 실행 중인 상태다.

## 체크리스트 반영 기준

- 날짜별 `stage2 todo checklist`는 구현/판정/미래 재확인처럼 소유자가 필요한 작업항목만 체크박스로 소유한다.
- 장전/장중/장후 반복 운영 확인은 날짜별 체크박스가 아니라 `build_codex_daily_workorder --slot PREOPEN|INTRADAY|POSTCLOSE`가 생성하는 `Runbook 운영 확인` 블록과 `sync_docs_backlog_to_project`가 생성하는 `RunbookOps` Project/Calendar 항목이 소유한다. 같은 날짜 checklist에서 해당 슬롯의 health-check 항목이 완료 체크되면 같은 날짜 workorder/Project backlog에서 다시 열지 않는다.
- 날짜별 checklist의 장전/장중 섹션이 신규 수동 작업 없음으로 비어 있어도 runbook 운영 확인은 생략된 것이 아니다. 해당 섹션에는 runbook 확인절차 참조 문구를 남긴다.
- runbook의 반복 확인 artifact, 시간표, 금지사항을 바꾸면 [build_codex_daily_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_codex_daily_workorder.py)의 `build_runbook_operational_checks`와 관련 테스트를 같은 변경 세트로 맞춘다.
- 새 recurring operational check는 `RunbookOps` track으로 Project/Calendar에 동기화한다. 특정 날짜에만 확인해야 하거나 사람이 구현해야 하는 후속은 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 별도 등록한다.

## Runtime Apply Bridge 사용 절차

`runtime_apply_bridge`는 lifecycle bucket discovery 결과가 실제 runtime env 후보가 될 수 있는지 확인하는 계약 산출물이다. 사용자가 매일 별도 승인할 단계가 아니라, 자동화체인이 env mapping, runtime hook, rollback/post-apply attribution을 닫았는지 확인하는 절차다.

별도 축:

- `entry_cancel_wait_runtime`은 독립 operational family다. ADM/LDM, lifecycle bucket, 일반 threshold EV, runtime apply bridge 입력에서 제외한다.
- `entry_wait6579_score66_69_recovery_gate_v1`는 entry-only bridge metadata다. complete lifecycle bucket이나 PREOPEN live env 후보로 보지 않는다.
- counterfactual-only, missed-entry, source-only 후보는 provenance로 보존하고 live 적용 근거로 쓰지 않는다.

확인 순서:

1. 장후 `data/report/runtime_apply_bridge/runtime_apply_bridge_YYYY-MM-DD.{json,md}`를 확인한다.
2. 후보가 surfaced 되었는지 확인한다. 성과 후보가 있었는데 `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, `runtime_apply_bridge`, `threshold_cycle_postclose_verification` 중 어디에도 없으면 `automation_handoff_gap`으로 본다.
3. 각 후보의 `bridge_candidate_state`를 확인한다.

| 상태 | 의미 | 처리 |
| --- | --- | --- |
| `live_auto_apply_ready` | contract, env key, runtime hook, post-apply attribution, parsed AI review가 닫힘 | 다음 PREOPEN live auto apply 후보로 소비 가능 |
| `sim_auto_approved` | sim policy 적용 조건이 닫힘 | 다음 PREOPEN sim policy 후보로 소비 |
| `entry_only_bridge_metadata` | entry dimension/provenance 전용 | live 후보나 blocked live 후보로 보지 않음 |
| `bootstrap_pending` | 표본/rolling 확인 부족 | 승인하지 않고 관찰 지속 |
| `blocked_source_quality` | join/provenance/source-quality 결함 | 데이터 또는 instrumentation workorder로 닫음 |
| `blocked_rolling_conflict` | rolling/cumulative 결론 충돌 | 후보 축소 또는 추가 확인 |
| `code_patch_required` | runtime hook이나 contract 구현 필요 | Codex safe-scope workorder 후보 |
| `blocked_contract_gap` | approval contract, env mapping, hook, rollback/post-apply attribution 중 누락 | 구현 전 env 소비 금지 |

사용자 개입은 구현 누락을 Codex에 지시하거나, discovery 범위 밖 final-stage 후보의 approval artifact 생성 여부를 결정하는 경우뿐이다. Bridge가 env를 만들더라도 hard safety, broker/account/order/cooldown/qty guard, stale quote, price freshness, stop guard, provider route, bot restart, cap release를 우회하지 않는다.

## 시간대별 Runbook

`panic_entry_freeze_guard`는 패닉셀 V2 1차 후보지만, runbook상 즉시 적용 대상이 아니다. `data/threshold_cycle/approvals/panic_entry_freeze_guard_YYYY-MM-DD.json` approval artifact, `KORSTOCKSCAN_PANIC_ENTRY_FREEZE_GUARD_*` env key mapping, stale source/owner conflict/provenance rollback guard가 모두 구현되기 전에는 `panic_sell_defense`가 `PANIC_SELL`이어도 신규 BUY를 자동 차단하지 않는다. `panic_regime_mode=NORMAL|PANIC_DETECTED|STABILIZING|RECOVERY_CONFIRMED`는 report/approval source이며, V2.0 신규 BUY pre-submit freeze, V2.1 미체결 진입 주문 cancel, V2.2 holding/exit context, V2.3 강제 축소/청산은 서로 다른 owner다. approval/rollback guard 없이 mode 전환만으로 주문 취소, 자동매도, stop/TP/trailing/threshold/provider/bot restart를 수행하지 않는다.

| 시간대 KST | 실행 주체 | 실행/트리거 | 산출물 | 운영 확인 기준 | 금지/주의 |
| --- | --- | --- | --- | --- | --- |
| `07:20` | cron | `final_ensemble_scanner.py` | `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json` | 스캐너 실패/빈 결과, fallback diagnostic 혼입, 추천 CSV/DB 적재 gap 여부만 확인 | 스캐너 결과만으로 floor/threshold 수동 변경 금지 |
| `07:30` | cron | 기존 `tmux bot` 세션 종료 | tmux session 상태 | 기존 세션이 남아 있으면 `tmux ls` 확인 | 장중 실행 중 강제 종료 금지 |
| `07:35` | cron | `deploy/run_threshold_cycle_preopen.sh` with `THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live`, `THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true` | `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}`, `logs/threshold_cycle_preopen_cron.log` | 실패 시 apply plan의 `blocked_reason`, AI guard, same-stage owner 충돌, `swing_runtime_approval.requested/approved/blocked`를 확인한다. `lifecycle_decision_matrix_runtime`이 selected이면 policy file/version/promote cap/env key와 fixed threshold contract가 함께 기록됐는지 확인한다 | 실패했다고 수동으로 env 값을 직접 덮어쓰지 않는다. parsed AI Tier2 auto state 또는 final user approval artifact 없이는 승인 요청만 보고 적용하지 않는다. lifecycle matrix selected 전에는 직접 ADM/fixed threshold 역할을 장중 변경하지 않는다 |
| `07:55` | cron | `src/run_bot.sh`를 tmux `bot` 세션에서 실행 | bot runtime log, source된 runtime env echo | Kiwoom API service start에 맞춰 `runtime_env` 적용 여부와 봇 기동 여부를 확인한다. env가 없으면 `run_bot.sh`가 먼저 `deploy/promote_gcp_preopen_artifacts.sh`로 `data/threshold_cycle_remote` staging artifact를 live `data/threshold_cycle`로 승격 시도하고, 그래도 없으면 `deploy/run_threshold_cycle_preopen.sh`로 local env 생성을 시도한다. 이후에도 없으면 최대 `KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_WAIT_SEC` 동안 대기한다 | runtime env 파일이 없으면 봇을 먼저 띄우지 않는다. follower staging과 live 경로를 혼동해 `threshold_cycle_remote`만 보고 기동 성공으로 처리하지 않는다. bootstrap/대기 timeout 시 preopen apply 또는 bridge 실패로 보고 원인 확인 |
| `08:00~09:00` | operator/guard | PREOPEN 안정 구간 | 없음 | checklist 상단 `오늘 목적/강제 규칙`과 전일 EV report를 읽고 불일치가 있으면 `warning`으로 기록 | full monitor snapshot build는 wrapper가 차단한다. 새 workorder 없는 live toggle 금지 |
| `09:00~09:05` | runtime | 장 시작 후 runtime/sim/probe 이벤트 수집 시작 | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | 봇 연결, 계좌/잔고/주문 가능 상태, `actual_order_submitted` provenance split 확인 | threshold 변경, provider 라우팅 변경 금지. 실계좌 예수금 부족을 sim/probe 후보 제외 사유로 쓰지 않는다 |
| `09:00~15:30` | cron | `deploy/run_system_metric_sampler_cron.sh` 1분 주기 | `logs/system_metric_samples.jsonl`, `logs/system_metric_sampler_cron.log`, `tmp/system_metric_sampler_state.json` | CPU busy, load, memory, swap, disk 사용률과 sampler stale 여부를 확인한다. error detector resource_usage의 입력 source다 | resource pressure를 전략 threshold/order guard 변경으로 해석하지 않는다 |
| `09:05~15:20` | cron | `deploy/run_buy_funnel_sentinel_intraday.sh` 5분 주기, 기본 `BUY_FUNNEL_SENTINEL_USE_CACHE=1`, `BUY_FUNNEL_SENTINEL_USE_SUMMARY=1` | `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}`, `data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_YYYY-MM-DD.*`, `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`, `data/pipeline_event_summaries/pipeline_event_summary_manifest_YYYY-MM-DD.json`, `logs/run_buy_funnel_sentinel_cron.log` | `UPSTREAM_AI_THRESHOLD`, `SUBMIT_DROUGHT_CRITICAL`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `RUNTIME_OPS` 추세와 `followup.route`, `operator_action_required=false` for submit drought, `runtime_effect=auto_workorder_no_intraday_mutation`, cache `rebuilt=false`/append rows, summary `status=ok` 또는 fallback 확인 | Submit drought는 postclose workorder/LDM handoff로 자동 승격한다. Sentinel 결과만으로 score/spread/fallback/restart 자동 변경 금지. summary는 diagnostic aggregation이며 raw suppression이 아니다 |
| `08:00~19:55` | cron | `deploy/run_scalping_pyramid_intraday_feedback.sh` 5분 주기 | `data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_YYYY-MM-DD.{json,md}`, `logs/run_scalping_pyramid_intraday_feedback_cron.log` | `pyramid_feedback_row_count`, blocker별 `recovered_or_extended_rate`, `reversal_or_flat_rate`, `blocked_then_recovered_rate`, 전체 one-share event 기반 `one_share_pyramid_opportunity_rows`/missed-upside/opportunity-cost, required provenance(`actual_order_submitted`, `broker_order_forbidden`, `runtime_effect`, `decision_authority`, `forbidden_uses`) 확인 | 장중 runtime prior 보조 입력일 뿐이다. threshold/env mutation, broker/order/stale quote/cooldown/quantity/cap/price guard 완화, provider/bot 변경 금지 |
| `09:05~15:20` | cron | `deploy/run_bd_fbuy_accum_pre_intraday.sh` 10분 주기 | `data/runtime/bd_fbuy_accum_pre/BD_FBUY_ACCUM_PRE_V1_YYYY-MM-DD.json`, `logs/bd_fbuy_accum_pre_intraday_cron.log`, `data/runtime/kiwoom_ws_snapshot/latest.json` | DB-first `BD_FBUY_ACCUM_PRE_V1` 후보 수, star score, source_quality, WS snapshot freshness, `runtime_effect=false`, `broker_order_forbidden=true` 확인 | 조회/source-quality 화면 전용이다. 결과로 broker 주문, threshold/env/provider 변경, bot restart, runtime approval/workorder 자동 연결 금지 |
| `09:05~15:20`, `16:00~19:20` | cron | `deploy/run_intraday_ws_freshness_monitor.sh` 5분 주기, 기본 `INTRADAY_WS_FRESHNESS_MONITOR_ONLY=true`; 16시 이후는 NXT source-quality 관측 전용이며 완료시각 기반 cooldown으로 다음 슬롯이 빠지지 않도록 `INTRADAY_WS_FRESHNESS_MONITOR_COOLDOWN_SEC=240`을 사용한다 | `data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_YYYY-MM-DD.{json,md}`, `logs/run_intraday_ws_freshness_monitor_cron.log` | `subscription_stale`, `trade_tick_quiet`, both-WS-stale, scout/submit 영향, `provider=none` incident를 분리 확인한다. NXT 구간에서는 통합 0B/0D route, 직접 체결가 결측, 0D quote proxy 복구, unresolved source gap을 별도 확인한다. 기본 모드는 monitor-only라 docs workorder를 갱신하지 않는다 | source-quality/report-only이다. NXT 결과를 KRX threshold에 혼입하거나 stale submit/broker guard를 우회하지 않는다. NXT threshold 변경은 별도 NXT runtime family와 근거가 있을 때만 허용한다. 장후 postclose wrapper가 `intraday_ws_freshness_workorder`를 생성한다 |
| `09:05~15:30` | cron | `deploy/run_holding_exit_sentinel_intraday.sh` 5분 주기, 기본 `HOLDING_EXIT_SENTINEL_USE_CACHE=1` | `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}`, `data/runtime/sentinel_event_cache/holding_exit_sentinel_events_YYYY-MM-DD.*`, `logs/run_holding_exit_sentinel_cron.log` | `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `AI_HOLDING_OPS`, `SELL_EXECUTION_DROUGHT` 추세와 real/non-real exit split, `followup.route`, `operator_action_required`, `runtime_effect=report_only_no_mutation`, cache `rebuilt=false`/append rows 확인 | Sentinel 결과로 자동 매도, threshold mutation, bot restart 금지 |
| `09:05~15:30` | cron | `deploy/run_panic_sell_defense_intraday.sh` 2분 주기 | `panic_sell_defense`, `market_panic_breadth`, cron log | `panic_state`, stop-loss cluster, active sim/probe 회복률, post-sell rebound, Telegram transition, resource spike 여부를 확인한다 | panic 결과만으로 score/stop threshold, 자동매도, bot restart, 스윙 실주문 전환 금지 |
| `09:05~15:30` | cron | `deploy/run_panic_buying_intraday.sh` 2분 주기 | `panic_buying`, `market_panic_breadth`, cron log | `panic_buy_state`, `panic_buy_regime_mode`, active/소진 count, TP counterfactual, Telegram transition, resource spike 여부를 확인한다 | panic buying 결과만으로 TP, trailing, score/threshold, provider, 자동매수/자동매도, bot restart 변경 금지 |
| `09:30~11:00` | cron | `src.engine.buy_pause_guard evaluate` 5분 주기 | `logs/buy_pause_guard.log` | pause guard 반복 발동 여부와 `[DONE] buy_pause_guard target_date=YYYY-MM-DD` marker 확인 | pause guard를 진입 threshold 튜닝 근거로 단독 사용 금지 |
| `09:35~12:00` | cron | monitor snapshot incremental/full | `data/report/monitor_snapshots/*_YYYY-MM-DD.json`, `logs/run_monitor_snapshot_cron.log`, `data/runtime/monitor_snapshot_completion_*.json` | snapshot failure, async timeout, manifest status, completion artifact 확인. 완료 Telegram 발송은 기본 제거하고 로그/산출물 기준으로 판정한다 | 장전 full build 차단을 우회하지 않는다 |
| `15:10` | cron | `deploy/run_scalp_sim_overnight_preclose.sh` with OpenAI `overnight_v1` | `data/report/scalp_sim_overnight/scalp_sim_overnight_YYYY-MM-DD.{json,md}`, `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `logs/scalp_sim_overnight_preclose_cron.log` | active 스캘핑 sim position이 `scalp_sim_overnight_decision`으로 판정되고 `SELL_TODAY`는 sim 가상청산, `HOLD_OVERNIGHT`는 active carry로 남는지 확인한다. `active_undecided_count`, `decision_coverage_rate`, `source_quality_status`, OpenAI provenance를 확인한다 | sim-only source다. 실주문, 자동매도, threshold apply, provider route 변경, bot restart 근거로 쓰지 않는다. state lock 경합 시 `scalp_sim_overnight_lock_skipped` source-quality blocker로 보고 postclose verifier에서 닫는다 |
| `15:10~15:30` | runtime/cron | 오버나이트 flow, 미체결 청산 복구, HOLD/EXIT sentinel final window | pipeline events, holding sentinel, order receipts | `SELL_TODAY`, `HOLD_OVERNIGHT`, force-exit/safety 이벤트와 SELL_TODAY 주문의 접수/체결/취소/롤백 상태를 확인한다 | flow `TRIM`을 부분청산 구현 없이 HOLD로 해석 금지. 15:20 이후 신규 판정보다 미체결 복구와 잔량 확인을 우선한다 |
| `20:05` | cron | `update_kospi.py` | `logs/update_kospi.log`, `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json`, `data/daily_recommendations_v2.csv` | NXT 종료 직후 EOD DB 갱신을 시작한다. `[START]/[DONE]/[FAIL]` marker와 status JSON의 `status`, `failed_steps`, `warning_steps`, `recovered_steps`, 최신 DB quote 상태 확인. detector window end 전 `START-only`는 in-progress로 본다 | 매매 runtime과 무관한 데이터 갱신으로 취급. `completed_with_warnings`는 DB 적재 실패와 동일하지 않으며 추천/대시보드/스윙 일일 리포트 후속 step 실패를 분리 확인 |
| `20:10` | cron | `deploy/run_threshold_cycle_postclose.sh` with OpenAI correction, 기본 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop` | postclose threshold-cycle reports, ADM/LDM, source-quality audit, rising missed feedback/calibration, PYRAMID feedback/calibration, code improvement workorder, runtime approval summary, postclose verification, 다음 영업일 checklist | `[START]/[DONE]/[FAIL]` marker, bot stop/isolation marker, required report freshness, AI review parsed 여부, source-quality gate, rising missed feedback/calibration handoff, PYRAMID feedback/calibration handoff, workorder handoff, verifier status를 확인한다. postclose wrapper가 시작되면 기존 bot 세션은 wrapper owner로 종료되어야 한다 | 장후 resource isolation 정지는 threshold/order/provider 변경 권한이 아니다. report/proposal/verification 산출물만으로 실주문, provider, bot restart, cap, hard-safety를 변경하지 않는다 |
| `20:10` | cron | `deploy/run_postclose_done_controller.sh` | controller artifact, verifier final pass, optional source refresh/rerun | `postclose_done_controller_YYYY-MM-DD.{json,md}`, controller log, verifier pass/fail, recoverable warning closure를 확인한다. controller는 postclose wrapper와 병렬로 시작하고, predecessor가 running/missing이면 내부 wait로 대기하므로 복구 attempt를 소모하지 않는다 | 기본값에서는 Codex runner를 실행하지 않고 runner 완료를 `[DONE]` 조건으로 요구하지 않는다. opt-in runner도 `runtime_effect=false` safe scope만 처리한다 |
| `20:10` | cron | `deploy/run_tuning_monitoring_postclose.sh` with `TUNING_MONITORING_PREDECESSOR_WAIT_SEC=6300` | Parquet/DuckDB late-pass refresh status, `data/report/tuning_monitoring/status/*` | postclose wrapper와 병렬로 시작하고 같은 날짜 postclose DONE/pass를 기다린다. 아직 postclose가 running이면 내부 wait로 대기하거나 fail-closed한다. `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`인지 확인한다 | 선행 postclose/controller 완료 전 Parquet/DuckDB refresh 금지. pattern lab 중복 실행 금지. Codex worktree branch를 production branch로 자동 merge 금지 |
| `20:15` | cron | `deploy/run_swing_live_dry_run_report.sh` 기본 `SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT=false`, `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none` | `data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.{json,md}`, status JSON, `logs/swing_live_dry_run_cron.log` | `swing_sim_*` stage, `actual_order_submitted=false`, `recommendation_db_load.db_load_skip_reason`, 20:15 lightweight selection/funnel completion, status `lifecycle_audit_mode=postclose_deferred` 확인 | lightweight wrapper는 lifecycle/AI review/runtime approval을 기본 실행하지 않는다. 같은 날 heavy swing audit/approval은 threshold postclose chain이 소유한다. 스윙 dry-run 결과로 당일 runtime guard 완화 금지 |
| `20:50` | cron | dashboard DB archive, `deploy/run_dashboard_db_archive_cron.sh 0` | `logs/dashboard_db_archive_cron.log`, `logs/dashboard_db_archive.log` | `DASHBOARD_ARCHIVE_*` 통계와 `skipped_unverified` 확인. 같은 날짜 verified/backfilled raw/snapshot 압축을 시도한다 | 미검증 파일 강제 삭제 금지. 이 archive는 저장소 운영 보강이며 threshold/order/provider/bot 변경 권한이 없다 |
| `21:00` | cron | `deploy/run_logs_rotation_cleanup_cron.sh 30` | `logs/log_rotation_cleanup_cron.log` | `active_rotated`, `active_deleted`, `archive_deleted`, `archive_compressed`, `size_before/size_after`, `tmp_deleted`, `cache_deleted`, `sentinel_compressed`, `snapshot_compressed`, `raw_row_exclusion_deleted`, `raw_row_exclusion_backup_deleted` 추세 확인 | 당일 장애 분석 전 로그 수동 삭제 금지. 최신 target date plain sentinel cache/snapshot, 원본 `data/pipeline_events`, clean-baseline quarantine/raw audit evidence는 cleanup 대상이 아니다 |
| `21:10` | cron | `KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE=true auto_retrain_pipeline.sh` | `data/report/swing_model_retrain/swing_model_retrain_YYYY-MM-DD.json`, `data/report/swing_model_retrain/diagnosis_YYYY-MM-DD.json`, `data/report/swing_model_retrain/bull_period_ai_review_YYYY-MM-DD.json`, `data/report/swing_model_retrain/status/swing_model_retrain_YYYY-MM-DD.status.json`, `logs/swing_model_retrain_cron.log` | `[START]/[DONE]/[FAIL] swing_model_retrain target_date=YYYY-MM-DD` marker, status, diagnosis, promotion guard, current registry 갱신 여부를 확인한다 | auto-promote는 model artifact promotion guard만 통과할 수 있다. 스윙 dry-run 해제, threshold/floor env 작성, 브로커 주문 허용 근거로 쓰지 않는다 |
| `07:00~21:55/5` | cron | `bash deploy/run_error_detection.sh full` | `data/report/error_detection/error_detection_YYYY-MM-DD.json`, `logs/run_error_detection.log` | wrapper가 `logs/run_error_detection.log`를 보장하고 `[START]/[DONE]/[FAIL]` marker를 남기는지 확인. 6개 detector (process health, cron, log, artifact, resource, stale lock). 4개 report-only, 2개 filesystem maintenance mutation (flag gated). `summary_severity=fail`이면 bot daemon이 떠 있지 않아도 wrapper가 관리자 Telegram 직접 알림을 시도한다 | 탐지 결과로 runtime threshold/spread/주문 자동 변경 금지. Telegram 알림은 report-only 운영 알림이며 자동 복구/재시작 권한이 아니다 |

Postclose backfill 명령의 stdout에는 API 초기화 안내가 JSON보다 먼저 기록될 수 있다. `run_threshold_cycle_postclose.sh`는 마지막 유효 JSON object를 backfill summary로 해석하며, 유효 JSON summary가 없거나 `status`가 실패이면 hard fail로 종료한다. 이 경우 controller를 먼저 DONE으로 강제하지 말고 wrapper 실패 로그와 backfill stdout을 확인한 뒤 wrapper/controller 순서로 복구한다.

### Pipeline Event Verbosity/Retention Policy

`data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`은 당일 forensic raw stream이고, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl`은 threshold-cycle이 읽는 compact decision stream이다. raw stream 증가는 `logs/` rotation으로 해결되지 않으며, disk pressure 원인 판정 시 두 경로를 분리한다.

1. 당일 raw stream은 postclose snapshot/DB/parquet 검증 전까지 수동 삭제하지 않는다. 주문 제출, 체결, exit, safety, threshold family, provenance, source-quality 이벤트는 손실 없이 보존한다.
2. `strength_momentum_observed`, `blocked_strength_momentum`, `blocked_swing_score_vpw`, `blocked_overbought`, `blocked_swing_gap`처럼 고빈도 diagnostic stage는 기본 decision authority가 없다. 반복 tick 단위 raw 기록을 live threshold/order guard 근거로 직접 쓰지 않고, stage/date/stock/source-quality 단위 summary 또는 sampling artifact를 먼저 만든다. BUY Sentinel v1은 이 5개 stage만 `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`로 1분 bucket 집계하고, 원문 raw 기록은 줄이지 않는다.
3. verbosity/throttle code change는 lossless decision-stage allowlist 또는 raw 보존 shadow 계측으로 시작한다. pass/order/safety/source-quality transition은 throttle 대상에서 제외하고, suppressed count/first_seen/last_seen을 별도 metric으로 남겨야 한다. producer-side compaction V2의 기본값은 `PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE=shadow`이고, `shadow`는 raw JSONL/DB upsert를 보존한 채 `data/pipeline_event_summaries/pipeline_event_producer_summary_YYYY-MM-DD.jsonl`과 manifest만 생성한다. `off`는 장애 대응용 비활성 옵션이다. `suppress`는 코드가 있어도 기본 비활성이며 V1 raw-derived summary와 2영업일 이상 parity 통과, 별도 workorder/approval owner 전에는 사용하지 않는다.
4. 보관/압축은 `compress_db_backfilled_files`가 소유한다. EC2는 21시대 초반 종료될 수 있으므로 정규 cron은 평일 20:50에 `run_dashboard_db_archive_cron.sh 0`로 같은 날짜 verified/backfilled raw/snapshot 압축을 시도하고, 21:00에 log rotation/data maintenance를 실행한다. 검증되지 않은 raw는 skip되며, 운영자가 수동 정리할 때는 dry-run으로 verified/backfilled 대상과 `skipped_unverified`를 먼저 확인한다. 미검증 파일 강제 삭제는 금지한다.
5. 이 정책은 운영 저장소/verbosity 정책이며 runtime threshold, provider route, 주문가/수량 guard, bot restart 권한이 없다. 구현 필요 시 `pipeline_event_verbosity_compaction_workorder`로 code improvement owner를 열어 장후 처리한다.

## System Error Detector 사용 절차

System Error Detector는 전략 튜닝 도구가 아니라 운영 감시 도구다. 사용 목적은 봇/cron/log/artifact/resource/lock 상태를 조기에 발견하고 `pass`, `warning`, `fail`로 분류하는 것이다. 탐지 결과는 incident, instrumentation gap, runtime ops 확인으로 라우팅하며, score threshold, spread cap, 주문 guard, provider routing, bot restart를 자동 변경하지 않는다.

### 신규 기능 detector coverage 의무

새 recurring runtime, cron wrapper, 장중/장후 report, 장기 실행 thread/daemon을 추가하거나 runbook 시간표에 새 행을 추가하면 같은 변경 세트에서 detector coverage를 반드시 선언한다. coverage 선언 없이 운영 기능만 추가하는 변경은 미완료로 본다.

필수 등록 기준:

| 신규 기능 유형 | 필수 조치 | 검증 기준 |
| --- | --- | --- |
| cron/wrapper/정기 실행 job | [cron_completion.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/cron_completion.py)의 `CRON_JOB_REGISTRY`와 [error_detector_coverage.py](/home/ubuntu/KORStockScan/src/engine/error_detector_coverage.py)의 `REQUIRED_CRON_JOB_IDS`에 같은 `id` 등록 | `src/tests/test_error_detector_coverage.py` 통과 |
| report/artifact 생성 기능 | [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py)의 `ARTIFACT_REGISTRY`와 `REQUIRED_ARTIFACT_IDS`에 같은 `id` 등록 | artifact path, window, critical 여부가 runbook 실행시각과 일치 |
| 장기 실행 thread/daemon | [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py)의 `write_heartbeat(component=...)` 호출 추가, `REQUIRED_HEARTBEAT_COMPONENTS` 반영 | heartbeat file에 component가 남고 process health dry-run이 fail하지 않음 |
| 새 health domain | `src/engine/error_detectors/*.py`에 `@register_detector` detector 추가, [error_detector.py](/home/ubuntu/KORStockScan/src/engine/error_detector.py)에서 import | `--mode full --dry-run` 결과에 detector 포함 |
| 감시 제외 대상 | `DETECTOR_COVERAGE_EXEMPTIONS`에 제외 사유 등록 | installer/one-off/manual replay처럼 반복 운영 대상이 아님이 명확해야 함 |

`cron_completion` 감시 대상은 wrapper 또는 직접 실행 스크립트가 같은 날짜의 완료 marker를 반드시 남겨야 한다. 표준 marker는 `[START] <job_id> target_date=YYYY-MM-DD started_at=...`, `[DONE] <job_id> target_date=YYYY-MM-DD finished_at=...`, `[FAIL] <job_id> target_date=YYYY-MM-DD ...`이며, log redirect 후 stdout/stderr에 기록되어야 한다. 실행 본문이 정상 종료돼도 detector log에 `[DONE]`과 `target_date`가 없으면 `no completion marker` 운영 결함으로 본다.

표준 marker 계약은 `monitor_snapshot`, `system_metric_sampler`, `swing_live_dry_run`, `swing_model_retrain_postclose`, `tuning_monitoring_postclose`, `dashboard_db_archive`, `log_rotation_cleanup`를 포함한 반복 wrapper 전체에 적용한다. 새 cron/wrapper를 추가할 때는 registry id와 wrapper 출력 id가 일치하는지도 같은 변경 세트에서 확인한다.

필수 검증 명령:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_coverage.py
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
```

이 검증은 운영 감시 coverage만 확인한다. 통과하더라도 새 기능의 live 적용, threshold 변경, 주문 guard 완화가 승인된 것은 아니다.

### 실행 경로

| 경로 | 용도 | 명령/트리거 | 결과 |
| --- | --- | --- | --- |
| cron | 5분 단위 운영 report 생성 및 fail 관리자 알림 | `bash deploy/run_error_detection.sh full` | `data/report/error_detection/error_detection_YYYY-MM-DD.json`, `logs/run_error_detection.log` (`touch` 보장), fail 시 `notify_error_detection_admin` Telegram direct notify |
| bot daemon | 장중 빠른 health alert | `bot_main.py` 내부 `error_detection_loop` (`TRADING_RULES.ERROR_DETECTOR_ENABLED`) | 동일 report 갱신, fail 전환/summary 변경 시 `SYSTEM_HEALTH_ALERT` |
| 수동 dry-run | 배포 전/수정 후 안전 점검 | `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` | report 파일 미작성, filesystem mutation 차단 |
| 수동 단일 범위 | 특정 detector 재현 | `--mode health_only|cron_only|log_only|auth_only|artifact_only|resource_only` | 해당 detector만 실행 |

### 글로벌 위기/매매 리스크 경보 알림 제한

`crisis_monitor`는 bot daemon 안에서 60분 주기로 RSS 위기 뉴스를 수집하고 DB에 저장한다. 단, 관리자 Telegram `시스템 경보: 매매 리스크 감지`는 수집 주기마다 보내지 않고 아래 KST 슬롯에서 risk 조건이 살아 있을 때만 슬롯별 1회 발송한다.

| 슬롯 | 발송 허용 window | 조건 | 상태 파일 |
| --- | --- | --- | --- |
| 장전 | `08:00~09:30` | 최근 12시간 severe risk count `>=4` 및 신규 severe alert 존재 | `data/runtime/crisis_monitor_alert_state.json` |
| 정오 | `11:30~12:30` | 동일 | 동일 |
| 장후 | `15:30~16:30` | 동일 | 동일 |

이 제한은 알림 피로도를 줄이기 위한 notification throttle이다. RSS 수집, macro alert DB 저장, risk count 계산은 계속 수행하며 threshold, 주문 guard, provider, bot restart, 자동매도 권한을 갖지 않는다. 긴급 운영자가 일시적으로 기존 주간 시간대 발송 방식으로 되돌릴 때만 `KORSTOCKSCAN_CRISIS_ALERT_SLOT_THROTTLE_ENABLED=false`를 사용하고, 사유와 복구 시각을 checklist에 남긴다.

nproc 기반 CPU profile로 bot hot path와 report-only job 경합을 줄인다. 공통 profile은 [cpu_affinity_profile.sh](/home/ubuntu/KORStockScan/deploy/cpu_affinity_profile.sh)가 소유한다. 4 vCPU 이상에서는 [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)의 기본 `KORSTOCKSCAN_BOT_CPU_AFFINITY`가 `0-1`, report-only wrapper 기본값이 `2-3`, health/sampler 기본값이 `3`이다. 2~3 vCPU 환경에서는 bot `0`, wrapper `1` 또는 `1-2` 계열로 축소되고, 1 vCPU 또는 `taskset` 부재 환경에서는 affinity 없이 실행한다. 적용 대상은 `run_error_detection.sh`, `run_buy_funnel_sentinel_intraday.sh`, `run_holding_exit_sentinel_intraday.sh`, `run_panic_sell_defense_intraday.sh`, `run_panic_buying_intraday.sh`, `run_system_metric_sampler_cron.sh`, `run_monitor_snapshot_cron.sh`, `run_monitor_snapshot_incremental_cron.sh`, `run_monitor_snapshot_midcheck_safe.sh`, `run_monitor_snapshot_safe.sh`, `run_threshold_cycle_calibration.sh`, `run_threshold_cycle_postclose.sh`이며, 각각 `ERROR_DETECTION_CPU_AFFINITY`, `BUY_FUNNEL_SENTINEL_CPU_AFFINITY`, `HOLDING_EXIT_SENTINEL_CPU_AFFINITY`, `PANIC_SELL_DEFENSE_CPU_AFFINITY`, `PANIC_BUYING_CPU_AFFINITY`, `SYSTEM_METRIC_SAMPLER_CPU_AFFINITY`, `MONITOR_SNAPSHOT_CPU_AFFINITY`, `THRESHOLD_CYCLE_CALIBRATION_CPU_AFFINITY`, `THRESHOLD_CYCLE_POSTCLOSE_CPU_AFFINITY`로 override할 수 있다. panic sell/buy wrapper 내부의 `market_panic_breadth_collector`도 같은 panic wrapper affinity/nice/ionice와 shared lock/fresh artifact 재사용 계약을 따른다. 이 설정은 CPU 배치만 바꾸며 threshold, 주문 guard, provider 변경 권한은 없다. 단 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart`는 15:45 장후 postclose resource isolation 전용 운영 재기동이며, strategy/runtime threshold 변경으로 해석하지 않는다.

`run_error_detection.sh`의 직접 Telegram 알림은 `KORSTOCKSCAN_ERROR_DETECTION_TELEGRAM_NOTIFY_ENABLED=false`로 비활성화할 수 있다. 동일 fail signature는 `tmp/error_detection_telegram_notify_state.json` 기준 10분 cooldown으로 중복 전송을 막는다.

설치/갱신 명령:

```bash
bash deploy/install_error_detection_cron.sh
```

수동 확인 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
tail -n 120 logs/run_error_detection.log
ls -l data/report/error_detection/error_detection_$(TZ=Asia/Seoul date +%F).json
```

### Detector별 판정과 조치

| detector | fail/warning 의미 | operator 조치 | 자동 변경 금지 |
| --- | --- | --- | --- |
| `process_health` | KRX 거래일 `07:55~20:10 KST` bot expected runtime window 안에서 main loop, daemon thread heartbeat stale 또는 PID 불일치. 비거래일 또는 이 시간창 밖의 dead/stale heartbeat는 `expected_stopped`로 닫고 fail 알림 대상이 아니다. expected start 직후 `ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC` 동안은 tmux/run_bot/heartbeat 갱신 race를 fail이 아니라 startup grace warning으로 본다. `restart.flag` 기반 graceful restart 직후 `ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC` 이내의 dead PID + fresh heartbeat는 handoff warning으로 보고 즉시 재시작하지 않는다. 20:10 postclose wrapper가 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop`으로 bot을 의도적으로 내리면 `tmp/postclose_bot_isolation.json` marker를 쓰며, marker가 신선한 동안 dead/missing/stale heartbeat는 장애 FAIL이 아니라 postclose isolation warning이다 | expected window 안이면 heartbeat owner와 실제 tmux/process 상태 확인. 장애면 운영 복구 playbook으로 분리. expected window 밖이면 정상 스케줄 종료로 본다. startup/restart grace warning은 grace 이후 재확인에서 pass/fail로 닫는다. postclose isolation warning은 장후 의도적 정지로 보고 다음 PREOPEN `07:55` 기동까지 재기동하지 않는다 | 자동 restart, threshold 변경 |
| `cron_completion` | 필수 cron log의 당일 DONE 누락 또는 FAIL 최신 marker. 거래일 전용 cron은 KRX 비거래일에 `skip_non_trading_day`로 닫는다 | 해당 cron log와 산출물 재확인 후 같은 date 재실행 여부 판단 | 실패를 threshold 성과로 해석 |
| `log_scanner` | error log burst 또는 신규 error pattern. `ERROR`/`CRITICAL`/traceback/exception/에러/오류/실패 같은 에러 후보 라인만 분류하며, `_error.log`에 섞인 INFO/WARNING성 DB 성공·업로드 로그는 운영 incident에서 제외한다. `TEST`, `123456`, `_DummySession`, `bus fail`처럼 pytest fixture signature가 붙은 라인도 제외한다. memory/OOM 분류는 `MemoryError`, 독립 단어 `memory`/`oom`, `out of memory`, `cannot allocate memory`만 인정하고 `kiwoom_*` 같은 logger/module 이름 내부 문자열은 OOM으로 보지 않는다 | stack trace/source artifact 확인 후 incident 또는 code workorder로 분리. fixture noise나 INFO성 운영 로그가 runtime error log에 섞이면 test/log sink 분리 또는 scanner ignore rule 보강으로 닫는다 | 에러만 보고 live guard 완화 |
| `kiwoom_auth_8005_restart` | fresh runtime log에서 `8005 Token이 유효하지 않습니다` 계열 인증 실패 감지. 기존 offset 이전 로그, pytest fixture signature, `run_error_detection*` meta log는 제외한다 | `restart.flag` 기반 graceful restart 후 새 PID, WS 수신, REST 시세/잔고 응답 회복을 확인한다. 이 detector는 warning도 Telegram alert 대상이다. 하루 3회까지 restart 복구를 허용하고, 이후 fresh 8005는 추가 `restart.flag` 없이 fail artifact/Telegram으로 operator 확인을 요구한다. Kiwoom REST/account/order 호출 지점은 8005 응답에 한해 token cache invalidation, force-refresh, same-request 1회 retry를 수행할 수 있다 | threshold/spread/order guard 변경, provider route 변경, retry loop 확장 |
| `artifact_freshness` | 시간창 기준 필수 report/artifact stale/누락 또는 JSON status 값 비정상. 장중 `pipeline_events`는 09:00~09:05 startup grace를 두고, `threshold_events` compact stream은 sparse stream이라 stale을 warning으로 본다. `threshold_cycle_ev`와 `swing_daily_simulation` 같은 one-shot postclose artifact는 완료 후 age만으로 재실행하지 않는다. `daily_recommendations_v2.csv`와 diagnostics는 장전 입력 특성상 mtime만 보지 않고 내부 `date`/`latest_date`, row/count 계약이 통과하면 `pass_content_date`로 닫는다 | window, startup grace, trading_day skip, upstream cron 실패, status JSON의 `failed_steps`/`recovered_steps`, content date/count 확인 | 누락 artifact를 수동 값으로 대체 |
| `resource_usage` | CPU/memory/swap/load/disk threshold 위반, sampler stale. CPU busy fail 기준은 `ERROR_DETECTOR_CPU_BUSY_MAX_PCT=95.0`이며 90% 구간부터 warning으로 본다. KRX 비거래일에는 system metric sampler stale만 `skip_non_trading_day`로 제외하고 disk/memory/load 같은 host resource check는 유지한다 | resource pressure 원인 확인. disk-low면 log rotate 결과와 cooldown state 확인. swap만 높고 `mem_available`이 충분한 경우는 즉시 장애보다 reclaim/캐시 잔존 가능성을 먼저 본다 | 전략 runtime parameter 변경 |
| `stale_lock` | 오래된 lock 발견 또는 cleanup 실패 | active lock인지 확인. 반복되면 wrapper lock lifecycle 보강 | 실행 중인 process lock 강제 삭제 |

### 코드수정 필요 에러 처리 절차

`summary_severity=fail` 또는 반복 `warning`이 코드 결함, instrumentation gap, wrapper 계약 불일치로 보이면 사람이 Codex에 수정 작업을 지시한다. detector 결과만으로 live threshold, spread cap, 주문 guard, provider routing, bot restart를 임의 변경하지 않는다. 단, Kiwoom auth 8005 복구는 인증/runtime data path 예외로 처리한다. 호출 지점은 8005 응답에 한해 token cache invalidation, force-refresh, same-request 1회 retry를 수행할 수 있고, `kiwoom_auth_8005_restart` detector는 fresh 8005 감지 시 daily cap/cooldown 계약 안에서 `restart.flag` 생성 또는 fail artifact/Telegram 표면화만 수행한다.

1. 최신 detector report를 연다.

   ```bash
   ls -l data/report/error_detection/error_detection_$(TZ=Asia/Seoul date +%F).json
   ```

2. 실패 항목의 `detector_id`, `summary`, `details`, `recommended_action`과 관련 log tail을 확인한다.

   ```bash
   PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
   tail -n 160 logs/run_error_detection.log
   ```

3. 원인을 `운영 장애`, `instrumentation gap`, `code bug`, `normal drift` 중 하나로 분류한다. 분류가 불명확하면 artifact/log 정합성부터 확인한다.

4. 코드 수정이 필요하면 Codex에 아래 형식으로 지시한다.

   ```text
   data/report/error_detection/error_detection_YYYY-MM-DD.json 기준으로
   detector_id=...
   summary=...
   details=...
   관련 로그=...
   원인 진단 후 코드 수정, 테스트, runbook/checklist 필요시 업데이트, 결과 보고 바람.
   단, runtime threshold/spread/order guard/provider routing 변경 금지.
   ```

5. 수정 후 최소 검증은 관련 단위 테스트, detector coverage 테스트, full dry-run, `git diff --check`다.

   ```bash
   PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_coverage.py
   PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
   git diff --check
   ```

6. detector 자체 장애로 bot 기동을 방해하거나 명시적 운영자 일시 중지 요청이 있을 때만 `KORSTOCKSCAN_ERROR_DETECTOR_ENABLED=false`를 임시 사용한다. 적용 시 날짜별 checklist 또는 운영 메모에 사유, 복구 기준, 재활성화 확인 명령을 남긴다.

### 허용된 filesystem maintenance

7개 detector 중 4개는 순수 report-only다. 아래 3개만 운영 filesystem/runtime maintenance mutation을 허용한다.

- `stale_lock`: `ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=True`이고 dry-run이 아닐 때, `tmp/*.lock` 중 `ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC`를 넘고 `fcntl` non-blocking lock 획득에 성공한 파일만 삭제한다.
- `resource_usage`: disk free가 `ERROR_DETECTOR_DISK_FREE_MIN_MB` 미만이고 `ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=True`이며 dry-run이 아닐 때 `deploy/run_logs_rotation_cleanup_cron.sh 30`을 호출한다. 이 cleanup은 오래된 회전/압축/날짜형 archive 로그 삭제뿐 아니라 active cron/wrapper 로그가 `LOG_ROTATION_ACTIVE_MAX_BYTES` 기본 20MB를 넘으면 `.log.1`로 회전한다. `.log.1`은 plain으로 유지하고 `LOG_ROTATION_COMPRESS_MIN_INDEX` 기본 `2` 이상 숫자 백업은 gzip으로 압축한다. stale active 로그는 `LOG_ROTATION_ACTIVE_RETENTION_DAYS` 기본 14일, archive 로그는 30일, `system_metric_samples.jsonl`은 `SYSTEM_METRIC_RETENTION_DAYS` 기본 3일만 raw로 유지한다. `DATA_MAINTENANCE_ENABLED=true` 기본값에서는 repo 내부 tmp/cache 정리, 최신 target date 제외 sentinel cache/snapshot gzip, `raw_row_exclusion` 날짜별 최신 run 유지, 그리고 `RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS` 기본 7일 경과 gzip backup 삭제도 같이 수행한다. 성공한 호출만 `tmp/error_detector_last_log_rotate_ts.txt`에 기록하며, 30분 cooldown 중에는 `log_rotate_trigger=cooldown_active`로 보고한다.
- `kiwoom_auth_8005_restart`: fresh runtime `8005` 인증 실패를 감지하고 dry-run이 아닐 때 `restart.flag`만 생성한다. 이 detector는 warning도 Telegram alert 대상이므로 첫 auth failure와 cooldown 중 auth failure가 조용히 묻히지 않아야 한다. 동일 auth incident 120초 cooldown 중에는 중복 flag 생성을 억제하고, 하루 누적 3회까지 restart 복구를 허용한다. 3회 이후 fresh 8005는 token cache invalidation과 fail artifact/Telegram만 남기고 추가 `restart.flag`를 만들지 않는다. 호출 지점별 REST/account/order helper는 8005 응답을 받으면 cache invalidate 후 force-refresh token으로 같은 요청을 1회만 재시도하며, 반복 실패는 source-quality/auth incident로 남긴다.

maintenance mutation도 전략 runtime 변경이 아니다. 실패하거나 반복되면 `warning/fail`로 보고 원인 복구를 진행하며, 매매 threshold를 수동 조정하지 않는다.

### Graceful bot restart

수동 또는 detector 복구로 봇 재기동이 필요한 경우 표준 경로는 `restart.flag` handoff다.

```bash
./restart.sh
```

이 스크립트는 `restart.flag`를 원자적으로 생성하고 `bot_main.py`의 기존 감지 루프가 자체 종료하도록 둔다. 이후 기존 PID 종료와 `src/run_bot.sh` supervisor가 올린 신규 PID를 제한시간 안에서 기다리고, 신규 PID에 대해 당일 `threshold_runtime_env_YYYY-MM-DD.env` handoff 검증 artifact까지 갱신한다. 소스 변경을 반영하는 재기동은 review gate와 targeted validation을 닫고 로컬 커밋을 만든 뒤 수행해 신규 프로세스의 `KORSTOCKSCAN_RUNTIME_GIT_COMMIT`이 실제 로드 소스와 일치하고 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`가 되게 한다. `pkill -9`, 직접 `nohup python src/engine/kiwoom_sniper_v2.py`, 텔레그램 매니저 별도 중복 기동, provider/threshold/order env hot mutation은 금지한다. 재시작 후에는 새 `bot_main.py` PID, `logs/bot_history.log`, heartbeat, Kiwoom WS/REST 회복, `/proc/<pid>/environ`의 commit/source-dirty와 당일 runtime env 반영 여부, verify artifact의 `status=pass`를 확인한다.

### Env override

| env var | 효과 | 사용 기준 |
| --- | --- | --- |
| `KORSTOCKSCAN_ERROR_DETECTOR_ENABLED=false` | bot daemon health detector 비활성화 | detector 자체 장애로 bot 기동을 방해하거나 명시적 운영자 일시 중지 요청이 있을 때 임시 차단. 재개 시 env override를 제거하거나 `true` |
| `KORSTOCKSCAN_ERROR_DETECTOR_DAEMON_INTERVAL_SEC=<sec>` | bot daemon 실행 주기 변경 | alert 과다/부하 조정이 필요할 때 |
| `KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED=false` | `process_health`의 bot expected runtime window gate 비활성화 | 24시간 bot 운영으로 바뀐 경우에만 사용 |
| `KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_START_HHMM=07:55`, `KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_END_HHMM=20:10` | bot 정상 기동/종료 스케줄 기준. window 밖 dead/stale heartbeat는 `expected_stopped` pass | runbook의 `07:55` 기동, `20:10` postclose 시작 종료 스케줄과 함께 변경 |
| `KORSTOCKSCAN_ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC=180` | bot expected start 직후 tmux/run_bot/heartbeat 갱신 race를 fail이 아닌 warning/recheck로 낮추는 유예 시간 | 실제 장중 process death를 숨기지 않도록 짧게 유지. grace 이후에도 heartbeat/PID가 죽어 있으면 fail |
| `KORSTOCKSCAN_ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC=<sec>` | resource sampler stale 기준 변경 | sampler 주기 변경과 함께만 조정 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=false` | stale lock 자동 삭제 차단 | lock lifecycle 조사 중 cleanup을 멈출 때 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC=<sec>` | stale lock age 기준 변경 | wrapper별 lock 보존시간이 다른 경우 |
| `KORSTOCKSCAN_ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=false` | disk-low 자동 log rotate 차단 | 장애 분석을 위해 로그 보존이 우선일 때 |
| `KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES=005930,001820` | 지정 종목의 봇 컨트롤을 중지 | 수동관리할 종목에 사용한다. 신규 WATCHING attach, WATCHING BUY 판단, HOLDING 매도/물타기, BUY/SELL timeout 취소를 모두 봇이 수행하지 않는다 |
| `KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE=/path/to/manual_control_excluded_codes.txt` | 수동관리 제외 종목 파일 경로 지정. 기본값은 `data/config/manual_control_excluded_codes.txt` | 장중 편집 반영이 필요하면 파일 방식을 사용한다. 한 줄 또는 쉼표 구분 종목코드를 허용하고 `#`/`//` 주석을 무시한다 |
| `KORSTOCKSCAN_MANUAL_CONTROL_OPEN_LOSS_EXCLUSION_WINDOW_SEC=300` | 08:00 NXT, 09:00 KRX 시작 후 손절선 아래 보유 종목을 수동관리 제외 파일에 자동 편입하는 윈도우 | 보유 종목이 시작 직후 기존 전략 손절선을 이미 하회하면 강제 청산보다 먼저 `data/config/manual_control_excluded_codes.txt`에 append하고 HOLDING 매도/물타기/취소 경로를 중단한다. 손절선 값 자체는 변경하지 않는다 |
| `manual_control auto_* average-price release` | 파일 주석이 `auto_open_loss`, `auto_scale_in_qty_guard_block`, `auto_hard_stop_handoff`인 HOLDING 종목을 신선한 WS 현재가가 평단가 이상일 때 파일과 인메모리 차단에서 자동 해제 | 수동 주석과 env 제외는 자동 해제하지 않는다. 현재가가 평단가 미만이거나 stale/missing이면 차단을 유지하며, 해제 후부터 기존 HOLDING 자동 관리가 다시 적용된다 |
| `KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED=true` | probe-first 1주 체결 뒤 잔량 가격을 기존 P1 resolver가 재검증·leg별 reprice | `ENTRY_SPLIT_PROBE_FIRST_ENABLED=true`이고 P1 기본 경로가 활성인 real SCALPING 최초진입에만 사용한다. 기본값은 `false` |

Env override는 운영 안전장치 조정이다. 적용/해제 시 runbook 또는 날짜별 checklist에 이유와 복구 기준을 남긴다.

Post-probe P1 capability가 활성화되면 rising-missed를 포함한 모든 probe-first 대상은 동일 경로를 사용한다. `STRONG`은 fill-clamped fresh BBO anchor의 `0/1/2 tick`, `NEUTRAL`은 기존 `0%/-0.3%/-0.8%`, 한 번이라도 `WEAK/UNKNOWN`으로 defer된 뒤 회복한 경우는 기존 `-0.3%/-0.8%` profile만 사용한다. 250ms 간격 재확인은 기존 3초 TTL을 넘지 않으며 끝까지 회복하지 않으면 잔량을 제출하지 않고 1주만 유지한다. 잔량 claim 전 stop/exit, account/order/cooldown/quantity guard를 모두 재확인하고, 각 residual leg 직전에는 fresh BBO·stale/conflict·방향·P1 가격·pre-submit price guard를 다시 확인한다. P1 계약 손상 시 legacy offset으로 fallback하지 않는다. 롤백은 `KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED=false`이며 probe-first 자체를 함께 닫아야 할 때만 `KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=false`를 추가한다.

### Greenfield Real-Env Containment

`greenfield_real_environment_authority`는 full lifecycle bundle이 완성된 경우에만 켠다. `scope=full_lifecycle`인데 policy allowlist가 entry-only이거나 `entry/submit/holding/exit` 중 명시적 policy 또는 `baseline_passthrough`가 없는 stage가 있으면 장중 왜곡 방지를 위해 Greenfield authority와 stage Telegram만 OFF로 내리고 raw event는 보존한다.

운영 override 필수 기록:

- `KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED=false`
- `KORSTOCKSCAN_GREENFIELD_REAL_ENV_TELEGRAM_ENABLED=false`
- `data/threshold_cycle/contamination_windows/lifecycle_bucket_quarantine_YYYY-MM-DD.json`
- postclose 재생성 시 contaminated window는 live promotion EV에서 제외하고 source-quality/incident evidence로만 유지

이 containment는 threshold 값, provider route, order/quantity/cap guard, hard/protect/emergency safety를 변경하는 권한이 아니다. 봇이 runtime env를 시작 시점에만 source한 경우에만 `restart.flag` 기반 graceful restart로 OFF env 로드를 확인한다.

## 장전 확인 절차

`build_codex_daily_workorder --slot PREOPEN`은 이 절차를 `PreopenAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. `logs/threshold_cycle_preopen_cron.log`에서 preopen apply `[DONE]` marker와 runtime env 생성 여부를 확인한다. 동시에 `data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_YYYY-MM-DD.status.json`의 `status=succeeded`, `apply_plan_path`, `runtime_env_path`, `runtime_env_manifest_path`, `apply_plan_exists`, `runtime_env_exists`, `runtime_env_manifest_exists`를 확인한다. `reason=operator_runtime_env_lock_preserved_missing_source_report`는 canonical source report는 없지만 explicit operator runtime env lock으로 live runtime env handoff가 성립한 예외 성공이다. lock busy나 command fail이 exit 0 로그처럼 지나가도 status artifact가 `skipped|failed|running`이면 apply 완료로 보지 않는다.
2. `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json`에서 스윙 추천 생성/empty/fallback diagnostic 분리를 확인한다. detector 기준 완료 marker는 `final_ensemble_scanner target_date=YYYY-MM-DD`가 포함된 `[DONE]` 로그다.
3. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`에서 selected family와 blocked family를 본다.
4. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`이 있으면 `runtime_change=true` family와 env key를 확인한다. 파일이 없으면 apply plan의 `blocked_reason`을 읽고 `warning` 또는 `fail`로 분류한다.
5. `src/run_bot.sh` 기동 로그에서 당일 runtime env 파일 source 여부를 확인한다. 봇 기동 시각이 env 생성 시각보다 빠르면 `pre_env_boot_gap=true`로 보고, env 생성 후 재기동 또는 `run_bot.sh` 대기 동작이 있었는지 확인한다. GCP follower/one-shot 서버에서는 AWS push가 `data/threshold_cycle_remote/**` staging만 채우므로, live 경로 기동 전 `deploy/promote_gcp_preopen_artifacts.sh YYYY-MM-DD`가 staging env/apply/runtime manifest를 `data/threshold_cycle/**`로 승격했는지도 함께 확인한다.
6. apply plan의 `swing_runtime_approval` 섹션에서 `requested`, `approved`, `blocked`, `selected`, `dry_run_forced`를 확인한다. `dry_run_auto_apply_ready`는 parsed AI Tier2 contract가 있어야 통과하며, `approval_required`는 final-stage 사용자 승인 artifact 없으면 정상 차단이다. Final full-live approval 밖의 과거 실주문 요청/산출물은 env override를 생성하지 않아야 한다.
7. 스윙 approved env가 있더라도 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 runtime env에 포함되어야 한다. 장전에는 주문 guard를 완화하거나 `SWING_LIVE_ORDER_DRY_RUN_ENABLED`를 임의로 끄지 않는다.
8. apply plan의 `runtime_apply_bridge` 또는 blocked reason에서 bridge 후보 상태를 확인한다. entry/scale bridge는 `bridge_candidate_state=live_auto_apply_ready`, `allowed_runtime_apply=true`, target env mapping, runtime hook/provenance mapping, parsed AI Tier2 review가 모두 맞는 후보만 selected될 수 있다. `ai_two_pass_review_status`가 `parsed`가 아니면 pre-final live-auto는 fail-closed 차단하고 다음 postclose review로 넘긴다. `bootstrap_pending`, `blocked_source_quality`, `blocked_rolling_conflict`, `runtime_blocked_contract_gap`, `code_patch_required`, 명시적 AI contract/safety block은 env 미생성이 정상이다.
9. bridge selected env가 있으면 `runtime_apply_bridge_family`, `bridge_candidate_id`, `source_bucket_key`, `discovery_ai_review_id` 또는 `ai_two_pass_review_status`, `actual_runtime_effect` provenance가 runtime env JSON 또는 post-apply attribution 입력에 남는지 확인한다. discovery 범위 밖 approval-required 후보는 기존 `approval_id`도 함께 확인한다. provenance가 없으면 적용 성공이 아니라 `warning`으로 닫는다.
10. 실패 시 수동 approve가 아니라 `safety_revert_required`, `hold_sample`, `hold_no_edge`, `AI instrumentation_gap/incident`, same-stage owner 충돌 중 어느 차단인지 판정한다.

### 장중 운영 override 기준

장중 운영 override는 사용자가 명시적으로 지시한 경우에만 적용한다. 기본 원칙은 장중 threshold/runtime mutation 금지다.

1. override는 `operator_runtime_env_lock` 또는 명시 runtime env로 증적을 남긴다.
2. 적용 전후 `/proc/<pid>/environ`, runtime env JSON, pipeline provenance를 확인한다.
3. override가 있어도 broker/account/order/cooldown/qty, stale quote, price freshness, hard/protect/emergency stop을 우회하지 않는다.
4. rollback은 단순 성과 부진이 아니라 safety breach, severe loss, order failure, receipt/provenance 손상, stale submit 같은 운영 손상 기준으로 판단한다.
5. 장중 artifact는 다음 postclose와 다음 PREOPEN apply의 입력으로만 쓴다.
6. 관측복구 전용 scanner override 중 REST quote fallback 예산, fallback defer, WS repair/recheck freshness 키는 `operator_runtime_overrides.env` 변경을 runtime에서 5초 주기로 hot reload한다. 이 hot reload는 source freshness 복구 전용이며 score/threshold, provider, order price, broker guard, quantity, stale-submit guard 변경 권한이 아니다.

### Operator Runtime Env Lock 절차

사용자가 특정 runtime env를 명시적으로 보존하라고 지시한 경우에만 `data/threshold_cycle/operator_runtime_env_locks/*.json` lock artifact를 만든다. 이 lock은 자동화체인의 정상 재평가를 끄는 장치가 아니라, 지정된 관찰 기간 동안 sample shortfall/no-applied gap/instrumentation gap만으로 env가 닫히는 것을 막는 보존 가드다.

필수 필드는 `lock_id`, `family`, `stage`, `env_key`, `env_value`, `active_from_date`, `min_observation_until_date`, `allowed_close_reason_keywords`, `decision_authority`, `source_evidence`다. `threshold_cycle_preopen_apply`는 active lock을 읽어 같은 family가 `hold_sample`, `no_runtime_env_override`, AI instrumentation gap 등으로 차단될 때도 lock의 env override를 유지한다.

lock이 있어도 아래 close reason은 계속 허용한다.

- `safety_revert_required`
- `severe_loss`
- `order_provenance`/`provenance_breach`
- `stale_quote`/`stale_context_or_quote`
- `hard_stop`/`protect_stop`/`emergency_stop`
- `order_failure`/`receipt_missing`

`score65_74_recovery_probe` entry unlock처럼 post-restart cohort 수집을 위해 연 operator lock은 장후 또는 다음 장전 source evaluation에서 `operator_runtime_env_lock.applied`, `close_reasons`, `allowed_close`를 확인해 연장/해제/차단 중 하나로 닫는다. lock은 score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제 권한이 아니다.

표준 확인 명령:

```bash
tail -n 80 logs/threshold_cycle_preopen_cron.log
tail -n 80 logs/ensemble_scanner.log
ls -l data/daily_recommendations_v2.csv data/daily_recommendations_v2_diagnostics.json
ls -l data/threshold_cycle/apply_plans/threshold_apply_$(TZ=Asia/Seoul date +%F).json
ls -l data/threshold_cycle/runtime_env/threshold_runtime_env_$(TZ=Asia/Seoul date +%F).json
grep -n "SWING_LIVE_ORDER_DRY_RUN_ENABLED" data/threshold_cycle/runtime_env/threshold_runtime_env_$(TZ=Asia/Seoul date +%F).env || true
tmux ls
```

## 장중 확인 절차

`build_codex_daily_workorder --slot INTRADAY`는 이 절차를 `IntradayAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. Sentinel은 상태 확인용이다. BUY/HOLD-EXIT 이상치가 보여도 runtime threshold를 바꾸지 않는다.
2. `pipeline_events_YYYY-MM-DD.jsonl` append가 멈추지 않았는지 확인한다. `threshold_events_YYYY-MM-DD.jsonl`는 threshold-family 대상 stage만 남는 sparse compact stream이므로, stale은 fatal runtime 중단이 아니라 source coverage warning으로 분류한다.
3. 스윙 dry-run은 실전 판단 흐름 관찰용이다. `swing_sim_*`, `swing_probe_*`, `blocked_swing_score_vpw`, `swing_entry_micro_context_observed`, `swing_scale_in_micro_context_observed`, `swing_sim_scale_in_order_assumed_filled`, `swing_probe_scale_in_order_assumed_filled`, `holding_flow_ofi_smoothing_applied`가 보이면 주문 제출 여부와 별도로 provenance만 본다. `swing_probe_*`는 `data/runtime/swing_intraday_probe_state.json`에서 재시작 복원되며, open cap/일일 cap 초과 시 `swing_probe_discarded`로 닫힌다.
4. 스캘핑 live simulator는 실전 주문이 아니라 BUY 신호 전체 관측용 `signal_inclusive_best_ask_v1` 가상 체결이다. quote touch/timeout은 진입 허들이 아니라 `would_limit_fill`, `fill_source`, `limit_fill_price` 진단 필드로만 본다. 장중에는 `scalp_sim_*` stage와 Kiwoom WS 유지 여부만 확인하고, sim 손익만으로 당일 threshold를 바꾸지 않는다.
5. sim/probe 수량과 lifecycle 생성은 실계좌 주문가능금액이 아니라 `SIM_VIRTUAL_BUDGET_KRW`와 동적수량 산식 provenance를 기준으로 본다. `active_count=0`, `post_sell_joined_candidates=0`, AVG_DOWN/PYRAMID completed `0`은 실주문/시뮬레이션 source split과 lifecycle arm별 blocker를 먼저 확인한 뒤 병목으로 분류한다.
6. 패닉셀 급변 구간은 `panic_sell_defense_report`로 `panic_state`, stop-loss cluster, active sim/probe 회복률, post-sell rebound를 분리 확인한다. 이 리포트는 `report_only_no_mutation`이며 score/stop threshold 변경, 자동매도, 봇 재기동, 스윙 실주문 전환 권한이 없다.
7. `RUNTIME_OPS`, snapshot failure, model call timeout, 주문 receipt/provenance 손상이 있으면 전략 threshold 문제가 아니라 운영 장애로 분류한다.
8. safety breach가 아니라 목표 미달이면 rollback이 아니라 postclose calibration 입력으로 넘긴다.

`12:05` threshold-cycle intraday calibration cron은 운영 대상이 아니다. next-preopen apply의 authoritative source는 전일 postclose artifact이며, intraday phase artifact는 명시 수동 forensic run이 있을 때만 생성할 수 있고 cron completion/장중 runbook 필수 확인 대상이 아니다.

표준 확인 명령:

```bash
tail -n 80 logs/run_buy_funnel_sentinel_cron.log
tail -n 80 logs/run_holding_exit_sentinel_cron.log
tail -n 80 logs/run_panic_sell_defense_cron.log
tail -n 80 logs/run_panic_buying_cron.log
ls -l data/pipeline_events/pipeline_events_$(TZ=Asia/Seoul date +%F).jsonl
ls -l data/threshold_cycle/threshold_events_$(TZ=Asia/Seoul date +%F).jsonl
PYTHONPATH=. .venv/bin/python -m src.engine.panic_sell_defense_report --date $(TZ=Asia/Seoul date +%F) --print-json
PYTHONPATH=. .venv/bin/python -m src.engine.panic_buying_report --date $(TZ=Asia/Seoul date +%F) --print-json
bash deploy/run_error_detection.sh full
ls -l data/report/panic_sell_defense/panic_sell_defense_$(TZ=Asia/Seoul date +%F).json
```

## 장후 확인 절차

`build_codex_daily_workorder --slot POSTCLOSE`는 이 절차를 `PostcloseAutomationHealthCheckYYYYMMDD`로 자동 포함한다. 이 항목은 날짜별 개별 구현 backlog가 아니라 `Runbook 운영 확인` 큐다. 20:10 postclose wrapper 이후 자동 감시 범위는 병렬 기동된 `postclose_done_controller` completion, 20:05 EOD 데이터 갱신, 20:50/21:00 보관/로그 정리, 21:55 detector final window까지이며, `codex_workorder_runner`는 사용자 지시 또는 수동 opt-in 실행 결과가 있을 때만 별도 확인한다.

POSTCLOSE 최상위 감리는 `Tuning Chain Control State`(튜닝 체인 관제 상태)로 남긴다. 이 관제 상태는 EV 손익의 좋고 나쁨이 아니라 자동화체인이 매일 믿을 수 있게 수집, 분석, 해석, 라우팅, 반영, 피드백, DONE controller recovery까지 이어졌는지 보는 운영 판정이다. 새 리포트나 새 checklist 항목을 만들지 않고, 기존 `PostcloseAutomationHealthCheckYYYYMMDD` 실행 메모에 `상태 / 막힌 단계 / 영향 / 조치` 4요소만 기록한다.

## 20:05 데이터 갱신 확인 절차

`update_kospi.py`는 매매 runtime과 분리된 EOD 데이터 체인이다. DB 적재, swing recommendation, swing daily reports가 한 status JSON 안에 step별로 남는다.

1. `logs/update_kospi.log`에서 당일 `[START] update_kospi target_date=YYYY-MM-DD`와 `[DONE]` 또는 `[FAIL]` marker를 확인한다.
2. `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json`의 `status`, `failed_steps`, `warning_steps`, `recovered_steps`, `db_state.latest_quote_date`, `db_state.rows_on_latest_date`를 확인한다.
3. `status=completed_with_warnings`는 DB 장애와 동일하지 않다. `failed_steps`가 `recommend_daily_v2`, `swing_daily_reports` 중 어디인지 분리한다.
4. `recommend_daily_v2` 실패는 `data/daily_recommendations_v2.csv` 갱신 여부와 traceback을 같이 본다. 추천 모델 subprocess는 repo root `cwd`와 직접 실행 sys.path bootstrap을 요구한다.
5. `log_scanner`가 `_error.log` 안의 INFO성 `DB 일괄 삽입 성공`을 DB 장애로 해석하지 않도록, 실제 ERROR/traceback 후보 라인과 status JSON을 우선 본다.
6. `update_kospi` 실행은 보통 20~40분 걸릴 수 있다. 20:05 시작 후 detector window end 전 `START-only`는 `in_progress`로 본다.

표준 확인 명령:

```bash
tail -n 160 logs/update_kospi.log
STATUS_PATH="data/runtime/update_kospi_status/update_kospi_$(TZ=Asia/Seoul date +%F).json"
ls -l "$STATUS_PATH"
PYTHONPATH=. .venv/bin/python - "$STATUS_PATH" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print({k: payload.get(k) for k in ["status", "failed_steps", "warning_steps", "recovered_steps", "db_state"]})
PY
ls -l data/daily_recommendations_v2.csv data/daily_recommendations_v2_diagnostics.json
```

## real / sim / combined 판정 기준

`threshold_cycle_ev`, threshold calibration, performance tuning 리포트는 성과 source를 아래처럼 나눈다.

| 구분 | 포함 대상 | 사용 목적 | 금지 |
| --- | --- | --- | --- |
| `real` | 실제 브로커 주문 접수/체결이 발생한 포지션. `actual_order_submitted=true` 또는 실 주문 receipt/주문번호/체결 DB provenance가 있는 row | 실현 손익, 주문 실패율, partial/full fill, broker execution 품질, safety breach 판정 | sim 손익을 섞어 broker execution 품질로 해석 금지 |
| `sim` | 브로커 주문을 보내지 않은 가상 포지션. `scalp_sim_*`, `swing_sim_*`, `actual_order_submitted=false`, `simulation_book`/`simulation_owner` provenance가 있는 row. 수량은 기본 `SIM_VIRTUAL_BUDGET_KRW=10,000,000`을 가상 주문가능금액으로 두고 실주문 동적수량 산식으로 계산하며 실계좌 주문가능금액과 분리한다 | 실매매 없이 entry/holding/scale-in/exit threshold 후보의 EV, funnel, opportunity cost 수집 | 실현 PnL, 실주문 성공률, real buying power로 표시 금지 |
| `combined` | 같은 family/view에서 `real + sim`을 합친 분석 모집단. provenance field는 원본 source를 유지 | EV 극대화 튜닝 후보, trade-off score, sample 부족 완화, approval request 생성 입력 | provenance 제거, real/sim fill quality 합산, 자동 주문 허용 근거로 단독 사용 금지 |

운영 해석:

1. `combined`가 좋아지면 threshold/logic 후보를 만들 수 있다. 단, 적용은 기존 deterministic guard, safety floor, same-stage owner rule, 승인 정책을 통과해야 한다.
2. `real`만 나빠지고 `sim`이 좋은 경우는 broker execution, 주문가, 체결/취소, 호가 유동성 문제를 먼저 본다.
3. `sim`만 나쁘고 `real`이 좋은 경우는 신호 확장 후보의 false-positive risk 또는 simulator fill policy를 확인한다.
4. 스윙 `approved_live`는 dry-run runtime env 반영이라는 뜻이지 실주문 허용이 아니다. `combined` EV가 좋아도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`를 끄는 근거가 되지 않는다.

### 스캘핑 영역별 사용 기준

스캘핑은 실매매가 열려 있는 영역과 `scalp_ai_buy_all_live_simulator`가 동시에 존재할 수 있다. 따라서 sim/combined는 EV와 opportunity-cost를 넓게 보기 위한 입력이고, 실제 브로커 execution 품질은 항상 real-only로 남긴다.

| 영역 | `sim` 사용 상황 | `combined` 사용 상황 | `real-only` 판정 |
| --- | --- | --- | --- |
| AI/Gatekeeper BUY 확정과 entry price 후보 | BUY 확정 후 실제 budget/latency/order-submit gate 이전에 `scalp_sim_*`로 모든 대상 종목의 signal-inclusive 가상 entry와 missed opportunity를 수집. quote touch 실패는 제외하지 않고 `would_limit_fill=false`로 남긴다 | entry threshold, AI score band, price guard, spread/latency trade-off 후보의 EV와 funnel sample 확대 | 실제 주문 reject, broker receipt, partial/full fill, 실체결 slippage |
| 보유/청산 threshold | sim holding이 시작되고 sell signal 또는 가상 청산이 닫힌 경우 MAE/MFE, defer cost, soft-stop/holding-flow 후보 근거로 사용 | 보유/청산 EV, downside tail, exit timing trade-off 산출 | 실제 매도 주문 실패, 체결 지연, 계좌 잔고/주문번호 정합성 |
| 추가매수/scale-in | sim position에서 scale-in trigger와 quote-based fill 또는 blocked event를 수집 | AVG_DOWN/PYRAMID 후보의 opportunity EV와 tail risk 비교 | 실제 추가매수 주문 접수 품질, budget/position cap 침범, 주문 실패율 |
| 1주 cap 해제/position sizing | sim은 cap 때문에 놓친 EV와 활성 종목 폭을 추정하는 보조 입력으로 사용 | cap 유지 vs 해제의 전체 EV trade-off와 sample 부족 완화에 사용 | 실주문 체결 품질, 과대 주문 risk, 브로커/계좌 safety breach. 해제는 승인 요청 대상이지 sim 단독 자동 해제 대상이 아님 |
| broker execution 품질 | 사용하지 않음 | 사용하지 않음 | 실주문 receipt, 정정/취소, fill ratio, slippage, 주문 latency만 사용 |

### 스윙 영역별 사용 기준

스윙은 기본적으로 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`라 실매매가 차단되어 있다. 따라서 EV 극대화 후보와 승인 요청 생성은 closed lifecycle 기준의 sim/combined를 동급 입력으로 사용한다. 단, 실주문 허용 여부와 broker execution 품질은 별도 승인 계획 없이는 열지 않는다.

| 영역 | `sim` 사용 상황 | `combined` 사용 상황 | `real-only` 판정 |
| --- | --- | --- | --- |
| selection/model floor/top-k | `swing_sim_*`와 추천 DB 적재 이후 entered/open funnel을 사용해 selection 폭, model floor, top-k의 기회비용과 false-positive를 본다 | `swing_model_floor`, `swing_selection_top_k` 승인 요청의 주 EV/trade-off view로 사용 | fallback diagnostic 혼입, DB load gap, 추천 CSV/DB provenance 오염 여부 |
| gatekeeper/market regime sensitivity | gatekeeper reject, regime split, open/entered funnel을 dry-run lifecycle로 수집 | `swing_gatekeeper_reject_cooldown`, `swing_market_regime_sensitivity` 승인 요청 생성에 사용 | instrumentation gap, same-stage owner conflict, regime label 생성 오류 |
| entry/holding/exit | sim lifecycle이 청산까지 닫힌 row를 completed EV, downside tail, hold/defer cost, exit timing 후보로 사용 | entry/holding/exit trade-off score와 승인 요청 근거로 사용. 일부 soft metric이 부족해도 hard floor와 총점이 통과하면 요청 가능 | 실제 매수/매도 execution 품질은 현재 스윙 dry-run 상태에서는 판정하지 않음 |
| AVG_DOWN/PYRAMID/OFI-QI/AI contract | 관찰/제안 입력으로 사용하되 live env apply 대상은 아님 | workorder 또는 approval request 후보까지 허용 | 별도 family guard가 생기기 전까지 runtime live env 반영 차단 |
| 승인 요청 생성 | closed sim lifecycle과 real completed가 함께 hard floor 및 trade-off score 입력이 된다 | `overall_ev 45% + downside_tail 20% + participation/funnel 15% + regime_robustness 10% + attribution_quality 10%` 총점이 `0.68` 이상이면 요청 가능 | Pre-final dry-run 요청은 parsed AI Tier2 auto state가 있으면 artifact 없이 소비될 수 있다. Final-stage 요청은 approval artifact 없이는 preopen env 반영 금지. 별도 실주문 trial 경로는 approval/live 후보가 아니다 |
| 전체 실주문 전환 | 사용하지 않음 | 사용하지 않음 | 별도 2차 계획/승인, broker execution guard, dry-run 해제 승인 없이는 금지 |

### 스윙 실주문 전환 기준

스윙은 기본 dry-run이다. 현재 PREOPEN env나 broker submit 권한은 별도 실주문 trial request/artifact가 아니라 final full-live conversion path에서만 만들 수 있다. 실주문 전환은 complete Swing LDM parent bucket evidence, parsed review, source-quality gate, explicit user approval artifact, env mapping, runtime guard, rollback/post-apply attribution이 모두 닫힌 경우에만 검토한다.

## 신규 Approval Artifact 처리 절차

`approval_request`는 자동화체인이 만든 승인 요청이다. 요청 생성만으로 runtime 효과는 없다. 다음 PREOPEN apply가 소비하려면 지원되는 contract, approval artifact, env mapping, runtime guard, rollback/post-apply attribution이 모두 맞아야 한다.

### 1. Intake

확인 입력:

- `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.{json,md}`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}`
- `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.{json,md}`
- `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`
- `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`

핵심 확인 필드:

| 필드 | 확인할 것 |
| --- | --- |
| `approval_id` | 승인 요청 식별자. artifact에 그대로 보존한다 |
| `policy_id` / `family` | 지원되는 approval contract인지 확인한다 |
| `calibration_state` | pre-final dry-run auto인지, final-stage 사용자 승인이 필요한지 구분한다 |
| `candidate_codes` / `candidate_rows` | 승인 범위 밖 종목이나 arm을 artifact에 넣지 않는다 |
| `recommended_values` | cap, allowlist, dry-run 유지 조건이 policy와 맞는지 확인한다 |
| `approval_contract_status` | `ready`가 아니면 approval artifact를 만들지 않고 workorder 또는 보류로 닫는다 |
| `approval_artifact_path` / `approval_artifact_approved` | 이미 승인된 요청은 중복 생성하지 않고 target date와 request id만 확인한다 |
| `blocked_reason` / `block_reasons` | blocker가 남아 있으면 승인하지 않는다 |
| `dry_run_required` | 스윙 dry-run 유지 계약을 위반하지 않는지 확인한다 |

### 2. 사람 승인 판정

| 판정 | 조건 | 다음 액션 |
| --- | --- | --- |
| `approval_artifact_required` | final-stage 요청이고 contract가 ready이며 blocker가 없음 | operator가 artifact 생성 여부를 결정한다 |
| `approval_artifact_created` | artifact가 있고 `approved=true`, request id가 일치 | 다음 PREOPEN selected/blocked reason을 확인한다 |
| `approval_artifact_missing` | 요청은 있으나 사용자가 승인하지 않음 | env 미반영을 정상 차단으로 기록한다 |
| `blocked_by_policy` | contract missing, source-quality blocker, sample 부족, severe downside, same-stage conflict | artifact 생성 금지. workorder 또는 관찰로 라우팅한다 |
| `observe_only` | report-only/proposal-only 요청 | live/env/order 변경 없이 관찰만 유지한다 |

금지선:

- approval artifact를 만든다고 장중 runtime이 바뀌지 않는다. 소비 시점은 다음 PREOPEN apply다.
- approval request만 보고 env 파일을 직접 수정하지 않는다.
- `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`를 approval artifact로 해제하지 않는다.
- panic, position sizing, 신규 runtime 후보처럼 contract가 없는 축은 먼저 loader, env mapping, runtime guard, rollback test를 구현해야 한다.

### 3. 현재 지원되는 artifact 형식

Final-stage swing runtime approval은 아래 경로와 형식을 사용한다.

```json
{
  "target_date": "YYYY-MM-DD",
  "approved_requests": [
    {
      "approval_id": "swing_runtime_approval:YYYY-MM-DD:swing_gatekeeper_reject_cooldown",
      "approved": true,
      "approved_by": "user_chat_YYYY-MM-DD"
    }
  ]
}
```

저장 경로:

```text
data/threshold_cycle/approvals/swing_runtime_approvals_YYYY-MM-DD.json
```

### 4. 다음 장전 확인

1. `deploy/run_threshold_cycle_preopen.sh`가 `[DONE] threshold-cycle preopen target_date=YYYY-MM-DD`로 종료됐는지 확인한다.
2. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`의 `swing_runtime_approval.approved`, `blocked`, `selected`, `decisions`를 확인한다.
3. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`의 `selected_families`와 `env_overrides`에 승인 축이 들어갔는지 확인한다.
4. `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 유지되는지 확인한다.
5. artifact가 있는데 selected되지 않았다면 blocked reason을 checklist에 남기고 env 수동 override는 하지 않는다.

### 5. Checklist/Project 반영

POSTCLOSE `HumanInterventionSummaryYYYYMMDD`에는 `approval_id`, `family`, 후보 범위, artifact path, 판정, 다음 PREOPEN 확인 항목을 남긴다. 미래 재확인이 필요하면 날짜별 checklist에 parser-friendly checkbox로 추가한다.

## 신규 Code Improvement Order 처리 절차

`code_improvement_order`는 pattern lab과 postclose source들이 만든 machine-readable 작업지시다. 생성 자체는 runtime 효과가 없으며, runtime 변경 권한도 없다. postclose wrapper는 이를 Markdown 작업지시서로 자동 변환하지만, postclose DONE controller 이후 `codex_workorder_runner`를 자동 실행하지 않는다. safe-scope `implement_now` 항목의 Codex SDK 구현/검증/커밋은 사용자가 Codex 구현을 명시적으로 지시하거나 `POSTCLOSE_DONE_CONTROLLER_RUN_CODEX=true`로 수동 opt-in한 경우에만 별도 처리한다. 사람/operator가 남는 지점은 구현 지시 여부, SDK/auth/package gap, forbidden-use blocker, 또는 real runtime authority가 필요한 항목을 어떻게 처리할지 결정하는 단계다.

### 1. Intake

입력 artifact:

- `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json`
- `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.md`
- `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.json`
- `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.md`
- `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_YYYY-MM-DD.json`
- `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_YYYY-MM-DD.md`
- `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.md`
- `data/report/swing_threshold_ai_review/swing_threshold_ai_review_YYYY-MM-DD.md`
- `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.json`
- `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.json`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`
- `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.md`
- `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json`
- `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`

확인 필드:

| 필드 | 의미 | 처리 |
| --- | --- | --- |
| `generation_id` | 해당 workorder snapshot 식별자 | 같은 날짜 재생성/재실행 시 최종 보고에 남겨 어떤 snapshot을 구현했는지 고정 |
| `source_hash` | 입력 source 파일 fingerprint의 hash | source report가 바뀌어 새 작업이 생긴 것인지, 동일 snapshot 재실행인지 구분 |
| `lineage.new_order_ids` | 이전 generation 대비 새로 생긴 order | 2-pass 재생성 후 새 `runtime_effect=false` 항목만 추가 구현 대상으로 본다 |
| `lineage.removed_order_ids` | 이전 generation 대비 사라진 order | 이미 해소되었거나 분류가 바뀐 항목으로 보고 임의 구현하지 않는다 |
| `lineage.decision_changed_order_ids` | 이전 generation 대비 판정이 바뀐 order | 변경 전/후 evidence를 비교한 뒤 구현/보류를 재판정한다 |
| `order_id` | 구현 작업 식별자 | checklist/commit/test 이름에 그대로 보존 |
| `target_subsystem` | 영향 영역 | entry, holding_exit, runtime_instrumentation, report 등으로 owner 분리 |
| `lifecycle_stage` | 스윙/스캘핑 생명주기 단계 | selection, db_load, entry, holding, scale_in, exit, ai_contract 등으로 구분 |
| `threshold_family` | 연결 threshold family | existing family 입력 보강인지 new family 설계인지 판정 |
| `intent` | 개선 목적 | EV 개선, 계측 보강, family 설계 중 무엇인지 분류 |
| `evidence` | Claude/EV 근거, Gemini는 manual/archive-only일 때만 보조 근거 | 단일 lab 단독 근거면 priority를 낮추고 runtime 후보 금지 |
| `expected_ev_effect` | 기대 효과 | daily EV의 어떤 metric으로 확인할지 연결 |
| `files_likely_touched` | 예상 변경 파일 | 실제 diff scope의 시작점으로 사용 |
| `acceptance_tests` | 완료 조건 | 구현 전 테스트 계획으로 변환 |
| `runtime_effect` | lab order 자체 runtime 영향 | 항상 `false`여야 하며, `true`면 artifact 오류로 본다 |
| `allowed_runtime_apply` | 자동 runtime 적용 허용 여부 | 신규 family/설계 후보는 `false`여야 하며, `true`면 guard 근거와 registry metadata를 확인 |
| `priority` | 실행 우선순위 | safety/instrumentation > existing family input > new family design 순으로 재정렬 가능 |

수동 생성/재생성 명령:

```bash
TARGET_DATE=$(TZ=Asia/Seoul date +%F)
PYTHONPATH=. .venv/bin/python -m src.engine.build_code_improvement_workorder --date "$TARGET_DATE" --max-orders 12
```

같은 날짜 workorder를 재생성하면 `generation_id`, `source_hash`, `lineage` diff를 먼저 확인한다. 동일 source hash면 같은 snapshot 재실행으로 보고, source hash가 바뀌었으면 postclose 산출물 변화로 새 follow-up이 생긴 것으로 분리한다. LDM `entry_bucket_attribution.code_improvement_workorders`가 존재하면 `lifecycle_decision_matrix_entry_bucket_attribution` order가, `scale_in_bucket_attribution.code_improvement_workorders`가 존재하면 `lifecycle_decision_matrix_scale_in_bucket_attribution` order가 생성되어야 하며, 누락은 postclose verifier fail 사유다.

### 1.1 2-pass 구현 기준

운영 지시는 “2-pass”로 통일한다. 내부 단계는 아래 네 단계로 닫는다.

1. Pass 1: `implement_now` 중 instrumentation/report/provenance 구현만 먼저 수행한다. runtime threshold, 주문 guard, provider routing을 직접 바꾸지 않는다.
2. Regeneration: 관련 postclose report와 `build_code_improvement_workorder`를 재실행해 `generation_id/source_hash/lineage` diff를 확인한다.
3. Pass 2: 재생성 후 `lineage.new_order_ids` 또는 판정 변경으로 드러난 `runtime_effect=false` 항목만 추가 구현한다.
4. Final freeze: 최종 답변과 commit message에 구현한 `generation_id`, `source_hash`, 신규/삭제/판정변경 order를 남기고, `기존 구현`, `신규 구현`, `보류 항목`을 분리 보고한다.

표준 사용자 지시문:

```text
code_improvement_workorder_YYYY-MM-DD.md implement_now를 2-pass로 처리해줘.
1차: instrumentation/report/provenance 구현
2차: 관련 리포트 재생성 후 workorder diff 확인
신규 implement_now 중 runtime_effect=false만 추가 구현
마지막에 기존 구현/신규 구현/보류 항목을 분리 보고
```

### 1.2 비-implement 항목 재판정 시점

`attach_existing_family`, `design_family_candidate`, `defer_evidence`는 자동 runtime 반영 대상이 아니다. 다만 작업지시서에 남은 이상 자동 runner 또는 operator가 다시 판단할 수 있어야 하므로, 장후 controller는 `CodeImprovementWorkorderReview`와 별도로 비-implement 항목 triage artifact를 둔다.

| 판정 | 사람이 다시 보는 시점 | 확인할 것 | 닫는 방식 |
| --- | --- | --- | --- |
| `attach_existing_family` | 다음 영업일 POSTCLOSE code-improvement triage | 기존 threshold family의 report/calibration 입력으로 흡수됐는지, 다음 `threshold_cycle_ev`/family report에 source metric이 보이는지 | `attached_to_existing_family`, `needs_codex_instrumentation`, `stale_no_action` 중 하나 |
| `design_family_candidate` | 다음 영업일 POSTCLOSE code-improvement triage | 새 family 설계가 필요한 반복 패턴인지, `allowed_runtime_apply=false`, sample floor, safety guard, env key, rollback guard가 정의됐는지 | `design_backlog_required`, `merge_into_existing_family`, `reject_or_defer` 중 하나 |
| `defer_evidence` | 다음 영업일 POSTCLOSE code-improvement triage | 새 표본이 추가되어 `implement_now` 또는 `attach_existing_family`로 승격됐는지, 여전히 stale/sample 부족인지 | `promoted`, `continue_defer`, `drop_stale` 중 하나 |

장기 반복 항목은 별도 재판정이 필요하다. `quiet_gap`/`source_dimension_rollup`/explicit `not_applicable` evidence처럼 설계상 계속 visibility만 유지해야 하는 상위 rollup은 `keep_visible_by_design`으로 남긴다. 반대로 `implemented` 또는 terminal non-implement 상태라도 `next_postclose_metric`이 여전히 다음 actionable implement_now 생성, blocker attribution closure, stale/missing ratio 감소 같은 downstream closure를 요구하며 최근 10일 창에서 3회 이상 반복되면 `repeat_unresolved_structural_blocker`로 다시 승격한다. 이 승격은 runtime mutation이 아니라 postclose triage 강화이며, source-only safe scope 구현/검증 대상으로만 surface된다.

이 triage 자체는 runtime 변경을 자동 수행하지 않는다. 결과가 `needs_codex_instrumentation` 또는 `promoted`이고 safe-scope 조건을 통과하더라도 사용자가 Codex 구현을 명시적으로 지시하거나 runner를 수동 opt-in한 뒤 `code_improvement_workorder.orders`의 선택 order로 들어온 경우에만 구현 후보가 된다. `non_selected_orders`에 남은 항목은 같은 cycle에서 실행, 승격, merge, push하지 않고 terminal-disposition evidence로만 닫는다. `attach_existing_family`는 명시적인 `needs_codex_instrumentation` marker가 없으면 `no_code_required`/기존 family 귀속으로 닫고, 다음 threshold-cycle/daily EV 산출물에서 재평가되도록 두며 runtime threshold나 주문 guard를 수동 변경하지 않는다. `design_backlog_required`는 source-only 설계 backlog로 남긴다.

### 2. 승격 판정

`build_code_improvement_workorder`가 각 order를 아래 중 하나로 deterministic 분류한다.

| 판정 | 조건 | 다음 액션 |
| --- | --- | --- |
| `implement_now` | safety, receipt/provenance, report source 누락, 기존 family calibration을 막는 계측 결함 | 생성된 Markdown의 상위 구현 대상으로 배치 |
| `attach_existing_family` | 이미 존재하는 threshold family의 source/input/provenance 보강 | 해당 family report/calibration 테스트와 함께 구현 |
| `design_family_candidate` | 기존 family에 매핑되지 않는 반복 패턴 | `auto_family_candidate.allowed_runtime_apply=false` 유지. registry/metadata/test 설계 후 별도 구현 |
| `defer_evidence` | lab stale, sample 부족, 단일 lab solo finding | EV report warning 또는 next postclose 재평가로 유지 |
| `reject` | fallback 재개, shadow 재개, safety guard 우회, 현재 폐기축 부활 | `rejected_findings` 또는 checklist 판정 메모에 사유만 남김 |

승격 기준:

- `runtime_effect=false`인 order만 intake한다.
- runtime을 바꿀 수 있는 패치는 반드시 기존 `auto_bounded_live` guard 또는 별도 feature flag를 통과해야 한다.
- 새 family는 처음부터 runtime 적용 후보가 아니다. `allowed_runtime_apply=false`로 시작하고, source metric, sample floor, safety guard, target env key, tests가 닫힌 뒤에만 threshold registry에 승격한다.
- `shadow` 재개를 요구하는 order는 현재 원칙과 충돌하므로 그대로 구현하지 않는다. Codex는 이를 `report_only_calibration` 또는 `bounded canary` 설계안으로 번역하고, live enable은 하지 않는다.

### 3. 구현 작업 만들기

구현 착수 시 문서/코드에 남길 최소 정보:

- 원본 `order_id`
- 원본 artifact path와 date
- target subsystem과 touched files
- runtime 영향 여부: `runtime_effect=false`, `report_only`, `feature_flag_off`, `auto_bounded_live_candidate` 중 하나
- acceptance tests
- daily EV에서 확인할 metric

날짜별 checklist에 등록할 때 형식:

```markdown
- [ ] `[OrderIdYYYYMMDD] 원본 order title 요약` (`Due: YYYY-MM-DD`, `Slot: POSTCLOSE`, `TimeWindow: HH:MM~HH:MM`, `Track: RuntimeStability`)
  - Source: [scalping_pattern_lab_automation_YYYY-MM-DD.json](/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json)
  - 판정 기준: 원본 `order_id`, `target_subsystem`, `expected_ev_effect`, `acceptance_tests`를 구현 완료 조건으로 사용한다.
  - 범위: runtime 직접 변경 없음 또는 feature flag/auto_bounded_live guard 경유.
  - 다음 액션: 구현, 테스트, postclose EV report에서 metric 확인.
```

기본 운영에서는 위 checklist 등록을 사람이 직접 하지 않는다. generator가 만든 `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`와 JSON artifact는 사용자 지시 또는 수동 opt-in runner 실행의 입력이다. runner가 구현한 경우에는 원본 order id를 runner artifact와 commit message에 남긴다. 단, 미래 재확인이나 특정 시각 검증이 필요하면 날짜별 checklist에 자동 파싱 가능한 항목으로 남긴다.

### 4. 구현과 검증

구현 순서:

1. `files_likely_touched`를 시작점으로 실제 call path를 확인한다.
2. report-only 보강인지 runtime 후보인지 먼저 분리한다.
3. runtime 후보면 feature flag, threshold family metadata, provenance field, safety guard, same-stage owner rule을 같이 닫는다.
4. acceptance tests를 repo 테스트로 변환한다.
5. 관련 문서와 report README/runbook/checklist를 같은 변경 세트로 갱신한다.

필수 검증:

```bash
PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
git diff --check
```

threshold/postclose 체인에 영향을 주면 추가 검증:

```bash
bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py
```

### 5. 자동화 체인 재투입

구현 완료 후에도 즉시 성과를 단정하지 않는다.

- report/instrumentation order: 다음 `16:00` postclose report와 daily EV에서 source freshness, sample count, warning 감소를 확인한다.
- existing family input 보강: 다음 `16:00` postclose calibration에서 해당 family의 `calibration_state` 변화를 확인한다.
- new family design: `auto_family_candidate.allowed_runtime_apply=false`를 유지하다가 registry metadata, sample floor, safety guard, tests가 닫힌 뒤에만 `allowed_runtime_apply=true` 후보로 승격한다.
- runtime 후보: 다음 장전 `auto_bounded_live` apply plan에서 selected/blocked reason과 runtime env provenance를 확인한다.

완료 기준:

- 원본 `order_id`가 구현 PR/commit/checklist 판정에 남아 있다.
- acceptance tests가 자동화 테스트 또는 report 검증 명령으로 닫혔다.
- daily EV 또는 postclose artifact에 기대 metric이 나타난다.
- runtime 변경이 있다면 threshold version/family/applied value가 pipeline event 또는 runtime env JSON에서 복원 가능하다.

## Python 코드 포맷 검증

- Python 포맷 기준은 `pyproject.toml`의 Black 설정을 단일 source로 사용한다. 현재 고정값은 Python 3.11, Black `26.5.1`, line length `88`이다.
- 로컬 변경은 `.venv/bin/black --check .`로 확인하며, 포맷이 필요할 때만 대상 경로를 명시해 `.venv/bin/black <path...>`를 실행한다.
- GitHub Actions의 `Black` workflow는 모든 push와 pull request에서 Python 3.11 및 `black==26.5.1`로 `black --check .`을 실행한다.
- 포맷 커밋에는 runtime report/cache, 주문·provider·threshold·bot 상태 변경을 포함하지 않는다. 대형 실시간 주문 모듈은 AST 동등성, compile, 대응 producer/consumer 테스트, `git diff --check`까지 통과한 뒤 독립 커밋으로 닫는다.

## 실주문 SCALPING AI 입력 preflight

- 2026-07-24부터 enhanced AI 입력은 `ai_market_snapshot_v1`과 `ai_input_preflight_v1`을 사용한다. provider·model·threshold·P1 가격·중앙 수량 owner는 기존 값을 유지한다.
- 초기 보호 mode는 `KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE=baseline_v1`이다. clean baseline 이후 real 이벤트와 당일 source-quality audit로 `data/report/ai_input_quality_baseline/ai_input_quality_baseline_YYYY-MM-DD.json`을 생성한다. legacy field는 source-quality proxy일 뿐 exact venue provenance가 아니며, 정책은 provider 호출·scale-in support·exit defer·overnight HOLD 권한을 줄일 수만 있다.
- `exact_v2` target-date artifact는 `data/report/entry_context_intraday_probe/entry_context_intraday_probe_YYYY-MM-DD.json`이다. `venue_preflight_matrix.overall_status=ready`, 모든 required row의 valid rows 1건 이상, cross-venue contamination/missing-as-zero/provider-called-while-blocked 0건을 확인한 뒤에만 mode 승격을 검토한다.
- session/effective venue cohort는 `PREMARKET_KRX_LIKE`, `KRX`, `NXT_REGULAR_OVERLAP`, `NXT_AFTERMARKET`, `OVERNIGHT`로 분리한다. 주문 `broker_route=KRX|NXT|SOR`, 시세 `market_data_route=krx_only|nxt_only|krx_nxt_integrated`, 실제 event venue는 별도 직교 차원이다. `SOR`는 venue cohort가 아니다.
- 실주문 SCALPING의 canonical route 계약은 `KRX 정규장 -> broker_route=SOR`, `PREMARKET_KRX_LIKE -> broker_route=NXT`, `NXT -> broker_route=NXT`다. `broker_route=KRX`는 명시적 direct-route 요청의 기록값일 수는 있지만 KRX 정규장 기본 SCALPING route 또는 정상 position-reconciliation 근거로 간주하지 않는다. SOR 주문 route 자체는 venue 오염이 아니다. `_AL` 통합 시세는 0B/0D별 underlying exchange를 증명하지 않으므로 `underlying_event_venue=UNKNOWN`, `underlying_event_venue_source=not_provided`, `venue_attribution_allowed=false`를 유지한다. 다만 현행 bounded `SOR execution-view`는 `effective_venue=KRX + session_bucket=krx_regular + KRX 정규장 clock`, 계획 주문 route `SOR`, 동일 종목의 fresh-consistent `_AL` candle, fresh 0B/0D `_AL` integrated route, explicit NXT event 부재를 모두 만족한 `entry_context|entry_screen|gatekeeper`와 broker 보유수량·평단이 확인된 holding/overnight 입력에 한해 provider source view로 허용한다. 이 허용은 event venue 증명이나 KRX/NXT 성과 귀속이 아니며 venue별 EV·threshold 판단, post-probe/probe-recheck/leg-reprice, submit-safety·broker/account/order/quantity/cooldown guard 우회에 사용할 수 없다. 조건 결손, explicit NXT, symbol/route conflict는 fail-closed하고 exact venue 귀속이 필요한 소비자는 계속 per-event venue 증명을 요구한다.
- `KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED=true`인데 선택 mode의 artifact가 없거나 `not_ready`이면 provider 호출과 enhanced context 권한은 fail-closed다. `baseline_v1`은 orthogonal route matrix와 payload 계약 replay가 통과하기 전에는 활성화하지 않고, `exact_v2`의 부족한 자연 표본과 decision point는 matrix의 `not_ready_rows`로 보고한다.
- 실행 중 새로 생성된 PASS artifact는 현재 PID에서 `ready_pending_restart`로 유지한다. 해당 artifact보다 나중에 시작된 단일 graceful restart PID에서만 `ready` handoff를 인정한다.
- holding-flow/overnight는 주기 계좌 동기화의 `kt00005 + ka10075` broker position/open-order snapshot과 실제 entry broker route를 대사한다. 결손·60초 초과·venue mismatch에서는 AI가 scale-in을 지지하거나 deterministic exit/`SELL_TODAY`를 유예할 수 없다.
- 검증 명령:

  ```bash
  PYTHONPATH=. .venv/bin/python \
    -m src.engine.scalping.ai_input_quality_baseline_replay \
    --target-date "$(TZ=Asia/Seoul date +%F)"

  PYTHONPATH=. .venv/bin/python -m src.engine.scalping.entry_context_intraday_probe \
    --date "$(TZ=Asia/Seoul date +%F)" --write
  ```

- 선택 mode report가 `not_ready`이면 봇 재기동으로 강제 통과시키지 않는다. provider 호출 payload는 schema, SHA-256, byte size, snapshot ID, venue/broker/market-data route, canonical candle owner를 남긴다. 같은 분봉을 summary/raw/context로 중복 전송하지 않는다. 첫 자연 표본의 exact snapshot/preflight/provider provenance와 payload hash를 확인한 뒤 당일 exact matrix로 정책을 고도화한다. review gate, parser, provider `none=0`, PID/env handoff를 모두 확인한 한 번의 graceful restart만 허용한다.
- `KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED`는 기본 `true`인 source-only 계측 kill switch다. 판단 trace는 `data/ai_decision_trace`, exact user input은 `data/ai_decision_payloads`, prompt registry는 `data/ai_decision_prompts`, pending/mature outcome은 `data/ai_decision_outcomes`에 일자별 JSONL로 저장한다. 계측은 provider/model/threshold/order/price/quantity/exit 권한을 갖지 않는다.
- 다음 기동의 첫 자연 AI 표본에서 trace ID가 payload/prompt hash, exact snapshot, pipeline event 및 probe bundle까지 이어지는지 확인한다. payload/prompt에 redaction이 발생하면 secret 값이 파일에 남지 않았는지 확인하고 해당 행은 `replay_exact=false`로 제외한다. write failure나 schema 결손은 `instrumentation_gap`으로 처리하며 실주문 경로를 중단하거나 fallback action을 변경하지 않는다.

## 장애 대응 기준

| 증상 | 우선 판정 | 다음 액션 |
| --- | --- | --- |
| preopen runtime env 미생성 | guard 차단 또는 전일 postclose 산출물 누락 | apply plan의 blocked reason 확인 후 postclose 산출물 복구. 수동 env override 금지 |
| intraday AI correction 실패 | AI proposal unavailable | deterministic calibration artifact가 생성됐으면 `warning`으로 기록하고 live runtime은 변경하지 않는다. postclose에서 fallback 상태 확인 |
| OpenAI AI correction 장시간 대기 | 고품질 모델 응답 지연 또는 key/model fallback | 15분 이내 실행 중이면 `not_yet_due`, 15분 초과 미완료면 `warning`으로 기록한다. deterministic calibration artifact가 이미 있으면 runtime 변경 없이 유지하고, 반복 초과 시 provider/timeout 보강 workorder로 분리 |
| postclose threshold report 실패 | 다음 장전 apply 입력 누락 | `logs/threshold_cycle_postclose_cron.log`와 checkpoint 확인 후 같은 date로 wrapper 재실행 |
| Sentinel `RUNTIME_OPS` 반복 | 운영/계측 문제 후보 | snapshot, model latency, receipt/provenance, pipeline event append 상태 확인. threshold 변경으로 처리하지 않음 |
| safety breach 발생 | safety revert 후보 | hard/protect/emergency stop 지연, 주문 실패, provenance 손상, severe loss guard 여부를 daily EV와 checklist에 남김 |
| pattern lab stale 또는 lab subprocess 실패 | lab freshness/source-quality 경고 | EV report와 pattern lab automation의 warning으로 관리하고 postclose 후단 산출물은 계속 생성. 동시에 lab 자체는 별도 incident로 원인, 입력 크기, 메모리/timeout 여부, fresh 복구 결과를 남긴다. runtime family 자동 적용 후보로 승격하지 않음 |

## 동기화 규칙

문서/checklist를 수정했으면 parser 검증은 AI가 실행한다. GitHub Project와 Google Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## IPO 상장첫날 YAML-gated Runner 절차

`ipo_listing_day_runner`는 threshold-cycle에 포함하지 않는 별도 YAML-gated 실주문 도구다. Kiwoom token, WS, 주문 유틸, OpenAI REPORT tier를 재사용하지만, 스캘핑/스윙 `ACTIVE_TARGETS`, threshold-cycle, Sentinel, daily EV, Project/Calendar 동기화에는 연결하지 않는다.

운영 원칙:

- 실행 승인 artifact는 `configs/ipo_listing_day_YYYY-MM-DD.yaml`이다. 파일이 없으면 `deploy/run_ipo_listing_day_autorun.sh`는 주문을 시도하지 않고 `skipped/config_missing` status만 남긴다.
- cron은 평일 `08:59 KST`에 `deploy/run_ipo_listing_day_autorun.sh`를 호출한다. 설치/갱신은 `deploy/install_ipo_listing_day_autorun_cron.sh`가 소유한다.
- Kiwoom access token은 `data/runtime/kiwoom_token_cache.json`과 `data/runtime/kiwoom_token_cache.lock`을 통해 공유 캐시를 먼저 재사용한다. 캐시가 없거나 만료됐을 때만 lock 안에서 새 token을 발급한다.
- 종목별 `budget_cap_krw`는 YAML 입력값을 받되, runner의 effective 상한은 `5,000,000 KRW`다. 원 입력값과 `effective_budget_cap_krw`를 artifact에 같이 남긴다.
- `data/ipo_listing_day/STOP` 파일이 있으면 신규 진입 주문은 즉시 차단한다.
- 산출물은 `data/ipo_listing_day/YYYY-MM-DD/`, `data/ipo_listing_day/status/ipo_listing_day_YYYY-MM-DD.status.json`, `logs/ipo_listing_day/ipo_listing_day_YYYY-MM-DD.log`, `logs/ipo_listing_day_autorun_cron.log`에서만 확인한다. threshold-cycle/daily EV/pipeline event와 섞지 않는다.
- KRX 상장 첫날 가격범위 `60%~400%`를 참고하되, runner 기본 진입 상한은 공모가 대비 `premium_guard_pct=250` 초과 보류다.

사전 준비/검증:

1. 당일 상장 예정 종목의 `code`, `name`, `listing_date`, `offer_price`, `budget_cap_krw`를 확인하고 `configs/ipo_listing_day_YYYY-MM-DD.yaml`을 만든다. API key나 계좌 비밀번호는 YAML에 넣지 않는다.
2. YAML 선택 결과만 먼저 확인한다. 이 명령은 WS 연결과 주문을 시작하지 않는다.

   ```bash
   PYTHONPATH=. .venv/bin/python -m src.engine.ipo_listing_day_runner \
     --config configs/ipo_listing_day_$(TZ=Asia/Seoul date +%F).yaml \
     --dry-select
   ```

3. `trade_date`가 오늘 KST 날짜와 맞는지, enabled target이 기본 `active_symbol_limit=1` 안에 있는지, `offer_price`, `budget_cap_krw`, `premium_guard_pct`, `enabled=true`가 의도와 맞는지 확인한다.
4. STOP 파일이 남아 있으면 신규 주문을 보내지 않는다. 주문 허용 전에는 의도적으로 남긴 STOP인지 확인한다.

실행/주문 gate:

1. 자동 실행은 `08:59 KST` cron이 소유한다. 수동 실행은 필요한 경우 `08:59:40~08:59:50 KST` 사이에 아래 명령으로만 수행한다.

   ```bash
   PYTHONPATH=. .venv/bin/python -m src.engine.ipo_listing_day_runner \
     --config configs/ipo_listing_day_$(TZ=Asia/Seoul date +%F).yaml
   ```

2. runner는 `08:59:50`부터 WS snapshot을 기록하고, 실제 매수 주문은 `09:00:00~09:00:30 KST` 안에서만 허용한다.
3. 진입 전 gate는 STOP 파일, 일손실 cap, 주문 실패 cap, global buy pause, premium guard, quote age, VI/호가공백, top 1~3호가 depth, OpenAI REPORT tier entry risk 순서로 본다. OpenAI `risk_score >= 80`일 때만 AI risk로 진입을 차단한다.
4. 첫 주문 실패/미응답은 한 번만 retry한다. retry는 IOC 성격으로 `best_ask + 1 tick` 한도에서 재가격을 산출한다.
5. 최초 체결, 손절, 미체결 종료 이후 같은 종목 재진입은 금지한다.

보유/청산/중지:

1. `-10%` hard stop은 AI 판단보다 항상 우선한다.
2. 첫 체결 후 최대 보유시간은 30분이다.
3. `+20%` 최초 도달 시 보유수량 30%를 분할익절 후보로 만든다. AI `hold_confidence >= 75`이고 `continuation_reasons`가 2개 이상일 때만 이 익절을 보류할 수 있다.
4. 20% 일부 익절 이후 잔여 수량은 peak profit 대비 `8%p` 하락 시 trailing 청산한다.
5. 즉시 신규 주문을 막으려면 아래 STOP 파일을 만든다.

   ```bash
   mkdir -p data/ipo_listing_day
   touch data/ipo_listing_day/STOP
   ```

장후 확인:

1. `summary.md`의 `status`, `realized_pnl_krw`, `reason`을 확인한다.
2. 각 종목 `*_decision.json`에서 진입 허용/차단 사유, `budget_cap_krw`, `effective_budget_cap_krw`, `max_budget_cap_krw`, premium, depth, AI risk를 확인한다.
3. `events.jsonl`에서 `ipo_entry_order_submitted`, `ipo_exit_order_submitted`, `ipo_entry_order_failed`, `ipo_exit_order_failed`를 확인한다.
4. 실제 체결/잔고는 Kiwoom 계좌 화면 또는 계좌 조회 유틸로 별도 대사한다. IPO runner artifact만으로 broker execution 품질을 확정하지 않는다.
5. IPO runner 결과로 당일 스캘핑 threshold, spread cap, provider routing, Sentinel, swing dry-run guard를 변경하지 않는다. 개선이 필요하면 threshold-cycle candidate가 아니라 별도 code review/workorder로 남긴다.

## ADM/LDM 운영 확인 요약

ADM은 특정 의사결정면의 action 품질을 보는 matrix이고, LDM은 entry, submit, holding, scale-in, exit stage를 묶는 상위 runtime owner다. 둘 다 기본 산출물은 postclose report/provenance이며, selected PREOPEN env가 있을 때만 runtime policy로 사용된다.

운영 확인 순서:

1. `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.{json,md}`에서 Entry ADM source-quality, lookup 분류, action bucket, joined sample을 확인한다.
2. `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}`에서 Holding/Exit ADM의 보유, 청산, scale-in bias 상태를 확인한다.
3. `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_YYYY-MM-DD.{json,md}`에서 lifecycle stage별 complete flow, ADM bridge complete, active seed/key lineage, submit attribution을 확인한다.
4. `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.{json,md}`와 `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`에서 selected family, blocked reason, runtime env mapping을 확인한다.
5. runtime 적용 여부는 `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{json,env}`와 bot PID env로만 확정한다.

항상 아래 우선순위를 따른다.

```text
hard safety veto
-> account/order/broker guard
-> lifecycle matrix runtime policy
-> existing ADM adapter
-> baseline fixed threshold fallback
```

ADM/LDM이 BUY, HOLD, AVG_DOWN, PYRAMID 쪽으로 bias를 주더라도 stale quote, price freshness, hard stop, account/order/cooldown/qty guard를 우회할 수 없다. sample 부족, unknown bucket, new/unseen token은 즉시 rollback 사유가 아니라 source-quality, workorder, 다음 tuning loop 입력으로 분리한다.
