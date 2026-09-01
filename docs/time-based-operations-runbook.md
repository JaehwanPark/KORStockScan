# Time-Based Operations Runbook

작성 기준: `2026-08-20 KST`
목적: 장전, 장중, 장후 자동화 체인의 실행 주체, 산출물, 확인 기준을 간결하게 고정한다.

이 문서는 실행 절차 runbook이다. 튜닝 원칙과 active owner는 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 작업 소유권은 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 산출물 추적성은 [report-based-automation-traceability.md](./report-based-automation-traceability.md), threshold-cycle 공통 산출물 정의는 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)를 기준으로 한다.

튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 이 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 본다. EV, rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다. `threshold_cycle_preopen_status`와 `threshold_cycle_postclose_status`는 운영 freshness status artifact라 이 제한에서 제외한다.

## 운영 원칙

- 기본 흐름은 무인 자동화다. 장전에는 전일 postclose artifact와 deterministic guard가 만든 `auto_bounded_live` 후보만 runtime env로 반영한다.
- 장중 threshold runtime mutation은 금지한다. 장중 산출물은 source-quality, incident, 다음 장전 후보 입력으로만 쓴다.
- AI reviewer는 제안과 감리 계층이다. 최종 state/value는 deterministic guard, source-quality gate, approval contract가 결정한다.
- broker submit guard, stale quote, price freshness, hard/protect/emergency stop, account/order/cooldown/quantity guard는 항상 최상위 safety다. ADM, LDM, bridge, approval artifact는 이 guard를 우회할 수 없다.
- `lifecycle_decision_matrix_runtime`은 ADM 확장 owner다. selected PREOPEN env가 있을 때만 기존 ADM adapter를 감싸며, 기본 산출물은 `runtime_effect=false`인 report/provenance다.
- `lifecycle_bucket_discovery`와 `runtime_apply_bridge`는 complete lifecycle bucket이 실제 runtime 후보가 될 수 있는지 확인하는 계약 계층이다. entry-only source dimension, source-only 후보, blocked contract gap은 live env로 해석하지 않는다.
- Swing postclose가 operator OFF이면 `runtime_approval_summary`, `runtime_apply_gap_audit`, `key_lineage_ledger`, `conversion_lane`에도 `--exclude-swing` scope를 동일하게 전달한다. OFF/retired/cooldown source의 부재를 runtime defect나 conversion blocker로 세지 않는다. `producer_gap_discovery` 기본 OFF도 runtime approval warning에서 `disabled_by_default`로 구분한다.
- 자정 이후 완료된 scalping pattern lab은 `run_date=target_date+1`과 `history_coverage_end=target_date`가 일치하면 timing-fresh다. `history_coverage_ok=false`이면 timing과 별개로 findings 소비는 source-quality blocked다.
- `producer_gap_discovery`, `time_window_regime_counterfactual`, pattern lab, sentinel류 report는 source-only 또는 report-only다. workorder와 후속 분석을 만들 수 있지만 실주문, threshold, provider, bot, cap을 직접 바꾸지 않는다.
- sim-first lifecycle은 기존 threshold-cycle 자동화체인의 관찰 범위다. sim/probe/dry-run row는 `actual_order_submitted=false`, `broker_order_forbidden=true` 계약을 유지한다.
- 스윙은 기본 dry-run이다. pre-final dry-run auto approval은 다음 PREOPEN env 후보가 될 수 있지만, final full-live conversion은 별도 사용자 승인 artifact와 runtime guard가 닫힌 경우에만 열린다.
- `entry_cancel_wait_runtime`, `entry_reprice_after_submit_runtime`, panic gap weight, submit drought quote freshness 보강처럼 real-only 운영축은 각 축의 runtime family와 operator lock 기준을 따른다. 일반 LDM/ADM EV와 섞어 자동 승격하지 않는다.
- BUY Telegram은 브로커 BUY 주문 제출 성공 이후에만 발송한다. AI confirmed, sim/probe, pre-submit 분석은 Telegram 알림 대상이 아니다.
- 사람이 개입하는 지점은 운영 장애, final full-live/cap/provider/bot/hard-safety 승인, Codex runner 차단 해소, 문서 backlog Project/Calendar 동기화다. safe-scope `runtime_effect=false` workorder는 사용자 지시 또는 수동 opt-in runner에서만 구현한다.
- 이 문서에서 “확인”은 artifact, log, source-of-truth 문서를 읽고 `pass|warning|fail|not_yet_due`로 분류하는 행위다. 확인만으로 live env, runtime threshold, broker 주문 상태를 변경하지 않는다.
- postclose 기본 실행은 실매매 판단, source-quality, AI review, PREOPEN apply에 직접 필요한 producer로 제한한다. `codebase_performance_workorder_report`, `time_window_regime_counterfactual`, `producer_gap_discovery`, `stage_hook_workorder_discovery`, `stage_hook_runtime_scaffold`는 기본 OFF이며, 필요한 날짜에 대응하는 `THRESHOLD_CYCLE_RUN_*` env를 명시적으로 켠 경우에만 실행한다. OFF artifact는 당일 freshness 필수 산출물로 취급하지 않는다.

## Kiwoom WS/REST 공식 참조 게이트

- 키움 WS/REST 호출, parser, 실시간 FID, REG/REMOVE·재연결, 인증, 계좌·주문, continuation 코드를 작성하거나 수정하기 전에 공식 [`Kiwoom-Securities/Kiwoom-REST-API`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 현재 revision과 관련 `kiwoom_docs`를 반드시 확인한다.
- 상세 source 우선순위, 확인 항목, 공식 자료 충돌 처리와 로컬 safety 경계는 [Kiwoom API Data Contract](./kiwoom-api-data-contract.md)의 `Official Kiwoom Reference Gate`가 소유한다. 변경 증적에는 확인한 upstream commit SHA, 문서/코드 경로, 확인 시각을 남긴다.
- REST는 path, `api-id`, header, request/response field, sign/unit/time, `cont-yn`/`next-key`, real/demo를 확인한다. WS는 URL, login/control packet, realtime type/FID, item/suffix/route, REG/REMOVE, reconnect/resubscribe와 공식 limit를 확인한다.
- 공식 `examples`는 샘플이다. 주문 예제를 검증 목적으로 실행하지 않고, 샘플을 근거로 stale/conflict, broker/account/order/quantity/cooldown 또는 hard-safety를 완화하지 않는다.
- 공식 문서, SDK/spec, portal 또는 실수신 evidence가 충돌하면 추정으로 semantic authority를 만들지 않는다. raw provenance와 `source_quality_gap`을 남기고 관련 contract/parser test가 닫힐 때까지 fail-closed한다.

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
- `wait6579_ev_cohort`는 LDM entry provenance/source-quality 입력으로만 유지한다. 별도 entry-only runtime bridge family는 제거됐으며 PREOPEN live env 후보나 재활성화 경로가 없다.
- counterfactual-only, missed-entry, source-only 후보는 provenance로 보존하고 live 적용 근거로 쓰지 않는다.

확인 순서:

1. 장후 `data/report/runtime_apply_bridge/runtime_apply_bridge_YYYY-MM-DD.{json,md}`를 확인한다.
2. 후보가 surfaced 되었는지 확인한다. 성과 후보가 있었는데 `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, `runtime_apply_bridge`, `threshold_cycle_postclose_verification` 중 어디에도 없으면 `automation_handoff_gap`으로 본다.
3. 각 후보의 `bridge_candidate_state`를 확인한다.

| 상태 | 의미 | 처리 |
| --- | --- | --- |
| `live_auto_apply_ready` | contract, env key, runtime hook, post-apply attribution, parsed AI review가 닫힘 | 다음 PREOPEN live auto apply 후보로 소비 가능 |
| `sim_auto_approved` | sim policy 적용 조건이 닫힘 | 다음 PREOPEN sim policy 후보로 소비 |
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
| `07:55` | cron | `src/run_bot.sh`를 tmux `bot` 세션에서 실행 | bot runtime log, source된 runtime env echo | Kiwoom API service start에 맞춰 `runtime_env` 적용 여부와 봇 기동 여부를 확인한다. env가 없으면 `run_bot.sh`가 `deploy/run_threshold_cycle_preopen.sh`로 local env 생성을 시도하고, 이후에도 없으면 최대 `KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_WAIT_SEC` 동안 대기한다 | runtime env 파일이 없으면 봇을 먼저 띄우지 않는다. bootstrap/대기 timeout 시 local preopen apply 실패로 보고 원인을 확인한다 |
| `08:00~09:00` | operator/guard | PREOPEN 안정 구간 | 없음 | checklist 상단 `오늘 목적/강제 규칙`과 전일 EV report를 읽고 불일치가 있으면 `warning`으로 기록 | full monitor snapshot build는 wrapper가 차단한다. 새 workorder 없는 live toggle 금지 |

`run_bot.sh`의 `dated_runtime_auto_renew_v1` allowlist는 persistent/operator
layer에서 `ENABLED=true`인 기존 reviewed dated runtime의 active date를 기동
당일로 갱신한다. 당일 dated operator override가 `ENABLED=false`를 명시하면
자동연장하지 않으며, entry-split fallback/market-first 등 allowlist 밖의 OFF
설정도 변경하지 않는다. PID env의
`KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_{POLICY_VERSION,TARGET_DATE,ACTIVE_KEYS,ACTIVE_COUNT}`
와 launcher log를 적용 provenance로 사용한다. 자동연장은 효용성 승인이나
threshold 재튜닝이 아니며, family별 실제 호출·실주문 영향·EV·순이익 검증과
명시적 OFF rollback은 [intraday monitoring task instructions](./intraday-monitoring-task-instructions.md)의
`당일 ON runtime` 계약을 따른다.
| `08:58~15:31` | systemd timer | `korstockscan-widget-research-watch-collector` | `data/monitoring/widget_research_watch/widget_research_watch_CODE_YYYYMMDD.jsonl`, `data/runtime/widget_research_watch/CODE.json` | 사용자 지시로 누적 등록한 최대 15개 `research_watch`의 KRX quote/BBO/완성 1분봉, 종목별 source report SHA, 공유 총예산 분당 15회 이하, 종목별 source error 격리 확인. 15종목에서는 budget pacing으로 한 cycle이 약 180초다. | shared cached token만 사용한다. advisory/ENTRY/EXIT/policy/order/account/quantity/provider/bot/cap/broker/hard-safety 권한과 자동승격은 없다 |
| `09:00~09:05` | runtime | 장 시작 후 runtime/sim/probe 이벤트 수집 시작 | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | 봇 연결, 계좌/잔고/주문 가능 상태, `actual_order_submitted` provenance split 확인 | threshold 변경, provider 라우팅 변경 금지. 실계좌 예수금 부족을 sim/probe 후보 제외 사유로 쓰지 않는다 |
| `09:00~15:30` | cron | `deploy/run_system_metric_sampler_cron.sh` 1분 주기 | `logs/system_metric_samples.jsonl`, `logs/system_metric_sampler_cron.log`, `tmp/system_metric_sampler_state.json` | CPU busy, load, memory, swap, disk 사용률과 sampler stale 여부를 확인한다. error detector resource_usage의 입력 source다 | resource pressure를 전략 threshold/order guard 변경으로 해석하지 않는다 |
| `09:05~15:20`, `16:00~19:20` | cron | `deploy/run_buy_funnel_sentinel_intraday.sh` 5분 trigger, 기본 `BUY_FUNNEL_SENTINEL_USE_CACHE=1`, `BUY_FUNNEL_SENTINEL_USE_SUMMARY=1`; `deploy/install_stage2_ops_cron.sh`가 KRX/NXT trigger를 소유한다 | `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}`, `data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_YYYY-MM-DD.*`, `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`, `data/pipeline_event_summaries/pipeline_event_summary_manifest_YYYY-MM-DD.json`, `logs/run_buy_funnel_sentinel_cron.log` | `UPSTREAM_AI_THRESHOLD`, `SUBMIT_DROUGHT_CRITICAL`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `RUNTIME_OPS` 추세와 `followup.route`, `operator_action_required=false` for submit drought, `runtime_effect=auto_workorder_no_intraday_mutation`, cache `rebuilt=false`/append rows, summary `status=ok` 또는 fallback 확인. NXT window는 venue/session을 KRX와 합치지 않고 16시 이후 append event를 같은 일자 report에 갱신한다 | Submit drought는 postclose workorder/LDM handoff로 자동 승격한다. Sentinel 결과만으로 score/spread/fallback/restart 자동 변경 금지. summary는 diagnostic aggregation이며 raw suppression이 아니다 |
| `08:00~19:55` | cron | `deploy/run_rising_missed_intraday_feedback.sh` 5분 trigger + 성공 완료 기준 cooldown 1500초(실효 약 30분) | `data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_YYYY-MM-DD.{json,md}`, `logs/run_rising_missed_intraday_feedback_cron.log` | growing pipeline 전체 재구성의 실행시간·RSS, source-quality/provenance 및 후단 workorder 입력 freshness 확인 | source-only이다. 장중 runtime/threshold/order/provider/bot mutation 권한이 없다 |
| `08:00~19:55` | cron | `deploy/run_scalping_pyramid_intraday_feedback.sh` 5분 trigger + 성공 완료 기준 cooldown 720초(실효 약 15분) | `data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_YYYY-MM-DD.{json,md}`, `logs/run_scalping_pyramid_intraday_feedback_cron.log` | `pyramid_feedback_row_count`, blocker별 `recovered_or_extended_rate`, `reversal_or_flat_rate`, `blocked_then_recovered_rate`, 전체 one-share event 기반 `one_share_pyramid_opportunity_rows`/missed-upside/opportunity-cost, required provenance(`actual_order_submitted`, `broker_order_forbidden`, `runtime_effect`, `decision_authority`, `forbidden_uses`) 확인 | 장중 runtime prior 보조 입력일 뿐이다. threshold/env mutation, broker/order/stale quote/cooldown/quantity/cap/price guard 완화, provider/bot 변경 금지 |
| `09:05~15:20` | cron | `deploy/run_bd_fbuy_accum_pre_intraday.sh` 10분 주기 | `data/runtime/bd_fbuy_accum_pre/BD_FBUY_ACCUM_PRE_V1_YYYY-MM-DD.json`, `logs/bd_fbuy_accum_pre_intraday_cron.log`, `data/runtime/kiwoom_ws_snapshot/latest.json` | DB-first `BD_FBUY_ACCUM_PRE_V1` 후보 수, star score, source_quality, WS snapshot freshness, `runtime_effect=false`, `broker_order_forbidden=true` 확인 | 조회/source-quality 화면 전용이다. 결과로 broker 주문, threshold/env/provider 변경, bot restart, runtime approval/workorder 자동 연결 금지 |
| `09:05~15:20`, `16:00~19:20`; 장후 workorder 직전 source-binding finalize | cron + main postclose wrapper | `deploy/run_intraday_ws_freshness_monitor.sh` 5분 trigger, 기본 `INTRADAY_WS_FRESHNESS_MONITOR_ONLY=true`; growing JSONL 재탐색 부하를 제한하기 위해 성공 완료 기준 기본 cooldown 720초(실효 약 15분)를 사용하며 KRX/NXT가 같은 정책을 공유한다. main postclose는 기존 incremental state를 한 번 finalize하고 workorder보다 먼저 종료한다. exact-date 공식 symbol master가 있으면 결속하고, 선행 main-AI 단계가 fail-closed해 master가 없으면 wrapper를 중단하지 않고 `official_symbol_master_binding.status=missing` source-quality blocker를 최종 report에 보존한다 | `data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_YYYY-MM-DD.{json,md}`, `data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_YYYY-MM-DD.json`, `logs/run_intraday_ws_freshness_monitor_cron.log` | 최초 실행은 memory-bounded full streaming rebuild, 이후 실행과 장후 finalize는 안전 byte offset 이후 append row만 누적한다. 파일 교체·축소, schema/stale threshold 변경, invalid aggregate는 자동 full rebuild한다. `input_processing.mode`, `appended_event_count`, `incremental_state_reason`, source offset, `official_symbol_master_binding.status=verified`를 확인한다. `subscription_stale`, `trade_tick_quiet`, both-WS-stale, scout/submit 영향, `provider=none` incident를 분리 확인한다. NXT 구간에서는 통합 0B/0D route, 직접 체결가 결측, 0D quote proxy 복구, unresolved source gap을 별도 확인한다. 장중과 finalize 모두 monitor-only라 docs workorder를 직접 갱신하지 않는다 | source-quality/report-only이다. finalize는 새 WS 수집이나 runtime mutation이 아니라 이미 수집된 state와 exact-date master의 최종 결속이다. master 결손은 결손값 보간이나 wrapper 조기종료가 아니라 downstream tuning-input 차단과 workorder 근거다. NXT 결과를 KRX threshold에 혼입하거나 stale submit/broker guard를 우회하지 않는다. NXT threshold 변경은 별도 NXT runtime family와 근거가 있을 때만 허용한다. `THRESHOLD_CYCLE_RUN_INTRADAY_WS_FRESHNESS_FINALIZE`는 main AI-quality R0→R3가 ON일 때 기본 ON이며, provider·threshold·bot·order 권한을 만들지 않는다 |
| `08:00~19:55` | cron | `deploy/run_market_opportunity_census_intraday.sh` 5분 source-only capture; 08시는 NXT, 09:00~15:30은 KRX+NXT, 15:35 이후는 NXT만 조회한다. `deploy/install_market_opportunity_census_cron.sh`가 설치된 exact 5개 trigger line과 wrapper SHA-256을 `data/runtime/market_opportunity_census/installed_trigger.json`에 원자 기록한다 | `data/market_opportunity_census/market_opportunity_census_YYYY-MM-DD.jsonl`, `data/report/market_opportunity_census/market_opportunity_census_YYYY-MM-DD.{json,md}`, `logs/run_market_opportunity_census_intraday_cron.log` | 매 5분 capture는 append-only이고 growing pipeline/AI lineage report는 `09:15·12:00·15:15·19:45 KST`에만 낮은 I/O/CPU 우선순위로 갱신한다. producer는 receipt 내용만 신뢰하지 않고 현재 설치 crontab의 exact line, wrapper path/hash/executable, 300초 계약을 재검증한다. 각 venue/panel은 같은 유효 session 안에서 3회 이상이며 연속 gap이 360초 이하인 실제 capture가 있어야 cadence floor를 통과한다. 기존 pipeline의 ranked source/candidate, WATCHING 저장, runtime attach, trusted AI, entry authority, submit-safety, submit을 `scanner_promotion_id+runtime_record_id+venue+session`으로 결속한다 | `source_only_scanner_coverage_audit`이다. trigger/report는 scanner pool·rank·watch·promotion, threshold, provider/bot, 주문·가격·수량/cap, broker/account/order/cooldown, stale/hard/protect/emergency guard를 변경하거나 restart 권한을 만들지 않는다. exact executable BBO outcome label이 없으면 recall 정상 판정을 fail-closed한다 |
| `09:05~15:30`, `16:00~19:20` | cron | `deploy/run_holding_exit_sentinel_intraday.sh` 5분 trigger, 기본 `HOLDING_EXIT_SENTINEL_USE_CACHE=1`; `deploy/install_stage2_ops_cron.sh`가 KRX/NXT trigger를 소유한다 | `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}`, `data/runtime/sentinel_event_cache/holding_exit_sentinel_events_YYYY-MM-DD.*`, `logs/run_holding_exit_sentinel_cron.log` | `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `AI_HOLDING_OPS`, `SELL_EXECUTION_DROUGHT` 추세와 real/non-real exit split, `followup.route`, `operator_action_required`, `runtime_effect=report_only_no_mutation`, cache `rebuilt=false`/append rows 확인. NXT holding/exit event는 venue/session과 real/sim authority를 유지한 채 16시 이후 append 갱신한다 | Sentinel 결과로 자동 매도, threshold mutation, bot restart 금지 |
| `09:05~15:30` | cron | `deploy/run_panic_sell_defense_intraday.sh` 2분 주기 | `panic_sell_defense`, `market_panic_breadth`, `market_weakness_observations`, `tmp/market_weakness_observer_state.json`, cron log | pipeline JSONL은 single-pass memory-bounded streaming으로 읽고 exit/non-real provenance만 보존한다. 반복 exit signal은 broker order identity별 1회로 축약한다. 시장 약세 알림은 기본 2회 활성화·3회 해제이며, source-hash/OOS review가 닫힌 exact-date 정책이 있으면 activation 2~4·release 2~5 범위의 현재값을 observation에 고정해 사용한다. KOSPI·KOSDAQ과 최소 3개 업종 row, 60초 spacing, 명시적 recovery margin 계약은 변하지 않는다. 동일 observation 재사용, 60초 미만 재관찰, source-quality·authority·release-margin 결손, 날짜·policy hash 불일치는 streak를 전진시키지 않는다. 한 세션에서 최초 소비한 policy source/hash·activation/release/spacing은 고정하며 뒤늦게 다른 정책이 나타나도 기존 streak와 섞지 않는다. `2026-08-31` 사용자 승인 `WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2`는 current-session `active|release_pending` market latch와 verified listing market이 일치하는 위젯·에피소드 신규·추가 BUY를 veto하고, 당일 exact owner 원주문을 broker reconciliation으로 확인한 경우에만 미체결 잔량을 취소한다 | notifier/attribution 자체로 score/stop threshold, 주문 취소·자동매도, bot restart, 스윙 실주문 전환 금지. 별도 live consumer도 수동·main bot·다른 owner 주문, SELL/target, 체결수량·보유, 수량 resize·가격·provider·broker guard를 변경하지 않으며 source/market scope 또는 현재 잔량 대사가 불명확하면 취소하지 않는다. rollback env는 `KORSTOCKSCAN_WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_GUARD_ENABLED=0` |
| `09:30~11:00` | cron | `src.engine.buy_pause_guard evaluate` 5분 주기 | `logs/buy_pause_guard.log` | pause guard 반복 발동 여부와 `[DONE] buy_pause_guard target_date=YYYY-MM-DD` marker 확인 | pause guard를 진입 threshold 튜닝 근거로 단독 사용 금지 |
| `09:35~12:00` | cron | monitor snapshot `intraday_light` only; 12:00도 full 대신 jitter 없는 `intraday_light`를 실행하고 full은 15:45 scheduler에 단일 owner로 둔다 | `data/report/monitor_snapshots/*_YYYY-MM-DD.json`, `logs/run_monitor_snapshot_cron.log`, `data/runtime/monitor_snapshot_completion_*.json` | snapshot failure, async timeout, manifest status, completion artifact 확인. 완료 Telegram 발송은 기본 제거하고 로그/산출물 기준으로 판정한다 | 장중 growing raw에 대한 full 재구성을 금지하고, 장전 full build 차단을 우회하지 않는다 |
| `15:10` | cron | `deploy/run_scalp_sim_overnight_preclose.sh` with OpenAI `overnight_v1` | `data/report/scalp_sim_overnight/scalp_sim_overnight_YYYY-MM-DD.{json,md}`, `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `logs/scalp_sim_overnight_preclose_cron.log` | active 스캘핑 sim position이 `scalp_sim_overnight_decision`으로 판정되고 `SELL_TODAY`는 sim 가상청산, `HOLD_OVERNIGHT`는 active carry로 남는지 확인한다. `active_undecided_count`, `decision_coverage_rate`, `source_quality_status`, OpenAI provenance를 확인한다. postclose report-only 재생성은 당일 JSONL을 `streaming_stage_filter`로 읽고 `full_source_materialized=false`를 남긴다 | sim-only source다. 실주문, 자동매도, threshold apply, provider route 변경, bot restart 근거로 쓰지 않는다. state lock 경합 시 `scalp_sim_overnight_lock_skipped` source-quality blocker로 보고 postclose verifier에서 닫는다 |
| `15:10~15:30` | runtime/cron | 오버나이트 flow, 미체결 청산 복구, HOLD/EXIT sentinel final window | pipeline events, holding sentinel, order receipts | `SELL_TODAY`, `HOLD_OVERNIGHT`, force-exit/safety 이벤트와 SELL_TODAY 주문의 접수/체결/취소/롤백 상태를 확인한다 | flow `TRIM`을 부분청산 구현 없이 HOLD로 해석 금지. 15:20 이후 신규 판정보다 미체결 복구와 잔량 확인을 우선한다 |
| `15:45` | `bot_main` scheduler | `monitor_archive`를 named async thread로 중복 방지한 뒤, heavy full snapshot은 `deploy/run_monitor_snapshot_safe.sh` 동기 worker subprocess로 격리 실행 | full snapshot manifest, monitor snapshot artifacts, performance sync, archived logs | wrapper의 nice/ionice/CPU affinity와 fresh full manifest를 확인한다. 각 snapshot stage는 start/complete·duration·process max RSS를 남기며, `missed_entry_counterfactual`은 multi-GB pipeline JSONL을 streaming compact projection으로 읽어 전체 source를 메모리에 materialize하지 않는다. KRX 거래 종료 공백의 heartbeat stale 자체를 missed EV로 합산하지 않되, 작업이 16:00 NXT 재개까지 메인 heartbeat·WS attach·메모리를 방해하지 않았는지 확인한다 | 메인 프로세스에서 full snapshot을 직접 materialize하지 않는다. timeout/OOM/SIGTERM을 동일 workload로 즉시 재시도하지 않으며 실패 completion evidence를 보존한다. wrapper 실패·lock skip·stale manifest를 성공으로 처리하지 않는다 |
| `20:05` | cron | `update_kospi.py` | `logs/update_kospi.log`, `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json`, `data/daily_recommendations_v2.csv` | NXT 종료 직후 EOD DB 갱신을 시작한다. `[START]/[DONE]/[FAIL]` marker와 status JSON의 `status`, `failed_steps`, `warning_steps`, `recovered_steps`, 최신 DB quote 상태 확인. detector window end 전 `START-only`는 in-progress로 본다 | 매매 runtime과 무관한 데이터 갱신으로 취급. Swing daily/bottom-rebound 후속 작업은 기본 OFF이며 `KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE=true`인 명시적 운영 지시에서만 실행한다. `completed_with_warnings`는 DB 적재 실패와 동일하지 않으며 후속 step 실패를 분리 확인 |
| `20:10` | cron | `deploy/run_threshold_cycle_postclose.sh` with OpenAI correction, 기본 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop`, `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false` | postclose threshold-cycle reports, scalping ADM/LDM, source-quality audit, rising missed feedback/scout workorder, entry AI gate backtest, PYRAMID feedback/calibration, entry cancel-wait tuning, 저가 기계 후보 추천·어드민 Telegram, code improvement workorder, runtime approval summary, postclose verification, 다음 영업일 checklist | `[START]/[DONE]/[FAIL]` marker, bot stop/isolation marker, required report freshness, AI review parsed 여부, source-quality gate, rising missed feedback/scout outcome coverage, entry AI gate `single_cumulative_quality_update` 후보가 0~1건인지, PYRAMID feedback/calibration, entry cancel-wait evidence state, 저가 후보 report가 clean baseline 전체·최신 16거래일 holdout·신규종목/기존종목 미구현시간대 lane·source-only authority·Telegram delivery 계약을 충족하는지, workorder handoff, verifier status를 확인한다. 저가 후보 Telegram 설정 누락·3회 전송 실패·authority 위반은 조용히 건너뛰지 않고 postclose FAIL로 닫는다. entry AI 계약 누락·복수 후보·clean-baseline cumulative window 불일치는 PREOPEN fail-closed한다. 2026-08-01부터 무효 반복하던 rising-missed bridge discovery, first-touch calibration, AI-score aggregate backtest는 producer·consumer·wrapper에서 제거하고 기존 산출물은 archive evidence로만 남긴다. standalone `quote_consistency_report`도 actionable 소비자가 없어 제거됐으며 실시간 `quote_consistency_normalization` 안전 로직은 유지한다 | swing OFF 상태를 개별 child flag로 우회하지 않는다. report/proposal/verification/추천 산출물만으로 실주문, 기계 생성·기동, provider, bot restart, cap, hard-safety를 변경하지 않는다 |
| `20:10` | systemd timer | `deploy/run_widget_evaluation.sh` | widget advisory/auto-trade calibration, symbol signal research, exact next-session runtime policy | wrapper 시작 시 latest completed KRX date를 한 번 확정하고 네 producer에 각각 `--target-date`/`--end-date`로 전달한다. persistent timer의 장전 catch-up에서도 research와 runtime-policy가 동일 source date를 사용하며, 어느 단계든 실패하면 unit을 fail로 유지한다 | report/policy generation only; account/order/token/process-control authority 없음 |
| `20:10` | cron | `deploy/run_postclose_done_controller.sh` with bounded predecessor timeout `43200s` | controller artifact, verifier final pass, optional source refresh/rerun | `postclose_done_controller_YYYY-MM-DD.{json,md}`, controller log, verifier pass/fail, recoverable warning closure를 확인한다. controller는 postclose wrapper와 병렬로 시작하고, predecessor가 running/missing이면 최대 12시간 내부 wait로 대기하므로 복구 attempt를 소모하지 않는다. `limit_down_watch_report` 기본값은 runtime observer `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=ON` 또는 대상일 candidate-source 파일 존재 중 하나를 만족할 때만 ON이다. 따라서 observer OFF·source 없음이면 빈 `source_blocked` 산출물을 만들지 않고, postclose cron이 PREOPEN env를 상속하지 않아도 실제 source가 있으면 리포트를 누락하지 않는다. 명시적 `THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT`는 이 자동 판정보다 우선한다. report ON 실행에서는 candidate/event source invalid·source-quality blocked·source-blocked를 verifier warning과 evidence-readiness blocker로 계속 노출하되 controller `DONE`을 막지 않는다 | 기본값에서는 Codex runner를 실행하지 않고 runner 완료를 `[DONE]` 조건으로 요구하지 않는다. opt-in runner도 `runtime_effect=false` safe scope만 처리한다. `limit_down_watch` 경고 허용은 sim/live/runtime 승인이나 source-quality 통과로 해석하지 않는다 |
| `20:10` | cron | `deploy/run_tuning_monitoring_postclose.sh` with `TUNING_MONITORING_PREDECESSOR_WAIT_SEC=43200` | Parquet/DuckDB late-pass refresh status, verified-source archive, `data/report/tuning_monitoring/status/*` | postclose wrapper와 병렬로 시작하고 같은 날짜 postclose DONE/pass를 최대 12시간 기다린다. 자정 이후 tail-repair가 완료돼도 동일 프로세스가 DONE을 소비해 후속 단계를 시작하며, bounded wait가 끝나기 전에는 실패 산출물로 닫지 않는다. parquet 생성이 성공하면 같은 wrapper에서 `compress_db_backfilled_files --days 0 --date TARGET_DATE`를 실행한다. pipeline raw/snapshot은 기존 parquet/backfill 검증 후, canonical AI context와 pipeline summary는 D+1 JSONL/manifest 검증 후, threshold partition은 완료 checkpoint가 있는 D+30 이후에만 atomic gzip으로 전환한다. `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`인지 확인한다 | 선행 postclose/controller 완료 전 Parquet/DuckDB refresh·raw 압축 금지. pattern lab 중복 실행 금지. 미검증 raw 강제 삭제 금지 |

장시간 실행되는 `run_threshold_cycle_postclose.sh`는 시작 시 현재 wrapper를 같은 디렉터리의 임시 파일로 복사하고 `bash -n`을 통과한 immutable snapshot을 `exec`한다. 실행 중 repository wrapper가 교체돼도 현재 run은 시작 시점의 동일 inode만 읽으며, 임시 snapshot은 provider·report 작업 전에 unlink한다. snapshot 생성·구문 검증 실패는 status fail로 닫고 controller가 재실행 여부를 판정하며, 서로 다른 revision의 line을 섞어 실행하거나 이를 정상 DONE으로 처리하지 않는다.

20:10 threshold-cycle wrapper와 자동 복구 controller는 늦은 NXT 청산을 포함한 exact trade performance fact를 먼저 동기화한 뒤 `daily threshold calibration -> threshold EV` 순서로 생성한다. EV만 나중에 재생해 낡은 calibration 거래 수를 그대로 소비하는 것은 정상 완료로 인정하지 않는다.

20:10 threshold-cycle wrapper는 기본값 `THRESHOLD_CYCLE_RUN_SAMSUNG_MACHINE_ENTRY_TUNING=true`에서 삼성전자 오전·midday·오후 독립 기계의 당일 state를 `samsung_machine_entry_tuning` JSON/Markdown과 다음 거래일 candidate로 원자 생성한다. 과거 시세/API를 조회하지 않고 `2026-06-05` 이후 자기 이전 actual-state 일별 observation 전부와 당일 observation을 단일 `clean_baseline_cumulative` 창으로 누적한다. 기계 도입 전 또는 observation 미생성 거래일은 coverage gap으로 공개하되 outcome으로 보간하거나 historical replay로 대체하지 않는다. `observation_source_quality_audit.tuning_input_allowed=true`, clean-baseline cumulative complete episode/leg floor와 양의 EV, `HELD`·미해결 guard를 모두 요구한다. candidate 자체는 runtime effect가 없고 오전은 baseline-only, midday/오후는 전체 동일 entry stage에서 하루 한 기계·한 axis tightening만 허용한다.

같은 wrapper의 기본값 `THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_TUNING=true`는 exact target-date 실제 profile state를 종목·시간대별로 서로 섞지 않고 `low_price_two_leg_tuning`으로 누적한다. exact-date inventory는 `2026-08-19=20`, `2026-08-21=27`, `2026-08-24=35`, `2026-08-25~26=40`, `2026-08-27=45`, `2026-08-28~30=46`, `2026-08-31 이후=48` profile 세대를 사용하며 `profiles_for_target_date()`와 applied-policy inventory가 권한을 소유한다. 과거 시세를 재조회하지 않으며 `2026-06-05` 이후 생성된 actual profile observation 전부를 단일 `clean_baseline_cumulative` 창에 넣는다. 전일 carry가 후일 자연청산되면 durable state를 원 거래일에 명시적으로 재귀속하며, 미관측 거래일은 coverage로만 공개하고 outcome으로 보간하지 않는다. 이 창에서 completed leg 20, 후보 EV가 0보다 크면서 현 정책 EV보다 큼, source-quality PASS, `HELD`·미해결 0을 모두 요구한다. 전체 regular-entry stage에서 기존 Samsung candidate까지 포함해 하루 한 machine/profile·한 tightening axis만 다음 PREOPEN candidate가 될 수 있다. Samsung candidate가 먼저 유효 mutation을 소유하거나 같은 날짜 artifact가 invalid이면 lower-price family는 전 profile을 carry-forward한다. 신규 진입 수량은 profile별 10주×2 leg(20주), 50:50 진입 offset, profile별 고정 target/validity, SOR, 무손절·미청산 보유와 broker guard로 고정된다.

그 다음 기본값 `THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION=true`는 clean baseline `2026-06-05`부터 target date까지 전 KRX 거래일을 사용한다. 최신 16거래일은 untouched holdout으로 고정하고 이전 전 거래일을 expanding calibration으로 평가한다. 검토 universe에서 이미 구현된 종목을 신규 lane에서 제외하고, 구현 종목은 active symbol/session pair를 제외한 미구현 regular-session lane으로 이동한다. 모든 source의 integrated-SOR 분봉 거래일과 source quality가 일치하고 표본·양의 notional EV·held/fill 25% 이하·held mark -3% 이상·최신 종가 10만원 이하를 통과한 종목×시간대만 source-only 순위로 만든다. active unrealized는 completed-only EV에 합산하지 않는다. cached token 또는 공통 source 계약이 막히면 `source_quality_blocked` 보고서와 추천 미산출 admin 안내를 보내고 다른 장후 producer는 계속한다. JSON/Markdown 원자 기록 뒤 `ADMIN_ONLY` Telegram을 최대 3회 시도하며 target-date state로 recovery 중복을 차단한다. Telegram 설정 누락·전송 실패·authority 위반은 postclose FAIL이고, 정상 추천은 기계 생성, timer 설치, PREOPEN policy, 주문 또는 runtime mutation 권한이 아니다.

이후 기본값 `THRESHOLD_CYCLE_RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION=true`는 target-date 위젯 calibration/symbol-research/collector-expansion과 lower-price active/expanded profile inventory를 다시 읽어 `machine_microstructure_attribution` JSON/Markdown을 생성한다. 종목 확장은 코드 상수에 고정하지 않고 당일 owner/research report에서 자동 발견한다. 20:10 wrapper의 1차 산출 뒤 21:15 widget expansion recommendation service가 같은 날짜 artifact를 원자 갱신해 늦게 생성된 위젯 후보도 포함한다. 새 종목의 micro 0B/0D partition·symbol·anchor window가 비어 있으면 scope별 producer/consumer gap으로 기록하며 수익률 0으로 보간하지 않는다. 이 결손은 supplemental micro context만 사용 불가로 만들고 기존 위젯·episode 튜닝과 policy candidate는 계속된다. 일반 micro 산출물은 diagnostic-only다. 다만 사용자 승인된 약세 hysteresis 하위 체인은 같은 attribution 안의 차단/실행 신호 executable-BBO 반사실을 clean-baseline부터 누적하고, 10거래일·50신호·시장별 10신호·latest 3거래일 OOS 및 EV/p10/오분류 guard를 모두 통과한 경우에만 현재 activation/release 값에서 한 축을 ±1 이동한 다음 거래일 exact-date 정책을 발행한다. 표본 또는 review 미달이면 현재 exact policy를 유지하고, exact policy/source hash 결손이면 2/3 baseline으로 fail closed한다. 같은 날 hot mutation과 breadth/spacing·main bot·가격·수량·target·holding/exit 변경은 없다.

같은 producer는 repairable micro gap을 다음 KRX 거래일 exact-date `scalp_micro_reversion_collection_targets`로 되먹임한다. 일회 복구 뒤 표본이 끊기지 않도록 현재 위젯·episode 동적 universe도 `micro_policy_sample_accumulation` 후보로 합쳐 기본 일 4종목 안에서 계속 회전한다. active owner를 우선하고 prospective owner 1자리를 보장하며 날짜별 hash로 overflow를 회전한다. main bot은 observer가 활성화된 경우에만 이 artifact를 boot에서 읽고 KRX/plain, NXT/`_NX`, SOR/`_AL` route에 `0B/0D`만 source-only 등록한다. 수동관리 제외종목은 수집·평가에서 제외하지 않는다. 수집 tick은 micro collector 뒤에서 trading event 전파를 중단하며, 같은 code가 정상 runtime target이 되면 trading subscription으로 승격하고 target 종료 후 collection set이 유효하면 다시 source-only로 유지한다. 다음 exact-date set은 이전 source-only set을 교체하므로 일별 구독이 누적되지 않는다. WS 전체 item budget과 collector storage self-disable/projection guard는 그대로 적용하며 budget overflow는 매매 구독을 밀어내지 않는다.

이 daily attribution과 collection feedback은 policy를 바꾸지 않는다. micro-conditioned policy review는 동일 owner/symbol/session에서 최소 5거래일·matched anchor 20건, BBO 95% 이상, depth window 90% 이상, invalid contract row 0을 만족한 뒤 동일 anchor의 현 정책과 단일 micro-conditioned axis를 paired 비교할 때만 열린다. 비용 반영 `source_quality_adjusted_ev_pct`가 rolling 5/10/20일 모두 양수이고 20일 net profit 양수, primary EV 상대 개선 1% 이상, p10 downside와 HELD/unresolved가 악화되지 않아야 한다. 최초 runtime 연결은 신규 bounded family mapping·rollback·사용자 명시 승인을 요구하며, 승인 이후 후보만 기존 postclose→exact-date PREOPEN chain을 따른다.

조건을 통과한 후보는 `machine_microstructure_policy_approval` 영속 대기열에 넣어 source report가 없는 다음 날에도 유지한다. 20:10 postclose와 21:15 final refresh는 candidate hash를 동기화하고, 후보별 POSTCLOSE/PREOPEN 각 날짜·phase당 한 번만 관리자 Telegram으로 `DESIGN_REQUIRED`, `REVIEW_READY`, 승인 후 handoff, `HOLD`, attribution 미완료 `APPLIED` 상태를 알린다. 21:15 service는 `deploy/run_machine_microstructure_final_refresh.sh` 단일 `ExecStart`로 expansion→attribution→market-weakness-hysteresis→entry-timing→approval/`--notify-objective-followups`→완료된 machine source date checklist builder를 실행한다. weakness-hysteresis와 entry-timing은 attribution이 성공한 경우에만 실행하며 attribution 실패 때의 두 rc=0은 성공이 아니라 `skipped_due_to_attribution_failure`로 판정한다. 앞 단계가 실패해도 가능한 후속 단계와 builder를 모두 실행하고 각 return code를 journal에 남기며, 실패 반환 우선순위는 `builder > policy > weakness-hysteresis > entry-timing > attribution > expansion`이다. approval artifact missing/unreadable/schema·phase·date·authority 불일치는 source-gap으로 fail closed한다. 다음 거래일 checklist generator는 미결 candidate를 PREOPEN 항목으로, 후보 생성 전 빠른 회전 목적 부채를 POSTCLOSE objective followup으로 자동 추가한다. objective followup은 exact objective/followup binding과 요구 gap을 실제로 해소한 queue candidate만 handoff로 닫고, `POST_APPLY_ATTRIBUTED` completion receipt가 검증되기 전에는 complete로 닫지 않는다. candidate의 `runtime_registry_verified=true` 자기선언은 권한이 아니며 실제 PREOPEN consumer·receipt owner와 함께 source-owned trusted registry에 등록된 family, same-stage 단일 축, bounded before/after, rollback, post-apply attribution이 모두 일치하기 전에는 승인할 수 없다. candidate hash가 바뀌면 이전 승인은 만료된다. 명시 승인 artifact가 생겨도 공통 PREOPEN wrapper는 runtime env를 직접 변경하지 않으며 exact-date authorization handoff만 기록한다. 해당 날짜에 적용하지 못한 handoff는 다음 거래일로 자동 이월하지 않고 대기 상태와 알림으로 재검토한다. 실제 family consumer의 guard-passed apply receipt와 post-apply attribution receipt가 각각 `APPLIED`, `POST_APPLY_ATTRIBUTED`를 소유하며 ledger는 handoff·receipt 파일·trusted registry를 재검증한다. 첫 guarded apply가 끝난 뒤에만 동일 family/stage/axis/bounded-contract 후속 후보가 기존 장후→PREOPEN 자동화 체인 자격을 얻는다. rolling paired producer는 현 owner outcome과 60/120/180초 same-epoch past-only 매도 1호가·0D 수량 충족 timeout 대안을 비용 반영 비교하며 floor 미달이면 `EVIDENCE_ACCUMULATING`과 구체 gap만 출력한다. floor를 모두 통과해도 단 하나의 source-only candidate를 미등록 family의 `DESIGN_REQUIRED`로만 인계한다. trusted registry가 비어 있거나 후보가 floor를 통과하지 못하면 promotion list는 비어 있으며, 어느 경우에도 연구 산출물 자체에는 runtime 효과가 없다.

21:15 final-refresh wrapper는 시작 시 `resolve_completed_machine_target_date()`를 정확히 한 번 호출하고, 그 explicit target date를 expansion·attribution·market-weakness-hysteresis·entry-timing·approval·completed-refresh checklist builder 여섯 단계에 동일하게 전달한다. Persistent timer catch-up이 20:00 경계를 지나더라도 단계별 default date를 다시 계산하거나 서로 다른 거래일 산출물을 한 체인으로 소비하지 않는다.

Repository unit 변경만으로 설치된 systemd unit이 자동 교체되지는 않는다. `systemctl cat korstockscan-widget-expansion-recommendation.service`가 단일 final-refresh wrapper를 가리키고 daemon-reload가 끝난 상태를 확인하기 전에는 objective 알림/checklist finalization이 운영 반영됐다고 판정하지 않는다. unit 반영은 bot 재기동이나 매매권한 변경이 아니지만 별도 운영 변경이므로 code review/commit만으로 실행하지 않는다.

각 Samsung PREOPEN wrapper는 7일 이내 최신 prior candidate를 `data/threshold_cycle/samsung_machine_entry_policy/applied/samsung_machine_entry_policy_YYYY-MM-DD.json`으로 최초 한 번 고정한다. 후보 없음/기간 만료는 baseline, 최신 후보 또는 당일 artifact 손상은 fail-closed다. 이후 같은 날 preflight는 검증된 artifact를 재사용하고 덮어쓰지 않으며 service는 exact-date schema/hash를 읽은 뒤에만 broker gateway를 만든다. 신규 진입 수량 10주×2 leg(20주), 50:50 leg, 사용자 승인 +3틱, five-bar validity, 무손절·미청산 보유, provider/bot/cap/broker guard는 자동 튜닝으로 변경하지 않는다.

삼성 오전은 `korstockscan-samsung-morning-one-share.timer` 하나가 07:57에 live service를 시작하고, 그 service의 `Requires`/`After`가 preflight oneshot을 같은 systemd transaction 안에서 정확히 한 번 선행시킨다. 별도 preflight timer는 oneshot 성공 뒤 2차 dependency start를 만들 수 있어 retired됐으며 installer가 기존 설치본을 disable/remove한다. preflight는 당일 KRX 거래일 여부를 먼저 확인하고, 평일 휴장일이면 authority를 만들지 않은 채 dependency를 fail-closed한다. 그 뒤에도 `tmux` 세션 존재만으로 통과하지 않고 exact-date threshold runtime env를 실제 로드한 단일 `bot_main.py` PID에 대해 `threshold_cycle_preopen_apply --verify --pid`가 pass한 뒤에만 authority v7에 PID와 검증 상태를 결속한다. `/proc/<bot-pid>/environ` 재검증의 fs credential 계약 때문에 preflight와 morning live unit은 `User=ubuntu`, `Group=ubuntu`로 main bot과 primary user/group을 맞춘다. 다른 primary group 또는 procfs 접근 실패는 per-key missing으로 펼치지 않고 `runtime_env_pid_unreadable`로 fail-closed하며, installer는 두 installed unit의 User/Group을 검증한 뒤에만 timer를 enable한다. PREOPEN이 늦으면 기존 NXT 08:00~08:10을 소급 실행하지 않고 SOR 09:00~09:30 계약 안에서만 bounded wait하며, 09:25 hard deadline 이후에는 authority를 만들지 않고 fail-closed한다. repository unit의 `TimeoutStartSec=5400`은 이 bounded wait만 허용하며 bot 기동·재기동, threshold/provider/order 변경 권한을 만들지 않는다. 설치 unit 반영은 별도 운영 변경이다.

아래 profile timer 열거는 운영 예시와 과거 전환 기록이며 current authoritative set 전체를 수동으로 소유하지 않는다. 현재 전체 set과 exact `OnCalendar`는 `profiles_for_target_date()`, `deploy/systemd/korstockscan-low-price-two-leg-*.timer`, reviewed installer manifest의 3자 일치로 판정한다. 2026-08-28 세대는 46개, 2026-08-31 세대는 48개이며 후자는 기존 5개 로직 수정과 `fan_ocean_morning`, `fan_ocean_late_morning` 신규 2개를 포함한다.

Lower-price profile PREOPEN wrapper도 같은 순서로 `low_price_two_leg_policy_apply -> profile preflight -> live service`를 실행한다. 제주반도체는 09:05/09:09, 한세실업 morning은 09:10/09:14, 카카오 morning·두산에너빌리티 morning·삼성중공업 morning은 09:15/09:19, 미래에셋증권 morning은 09:30/09:34, 삼성E&A morning은 09:40/09:44, SK이터닉스 morning은 09:45/09:49, 카카오 late-morning·한화오션·삼성E&A late-morning은 10:00/10:04, 두산에너빌리티 late-morning은 10:10/10:14, SK텔레콤 late-morning은 10:40/10:44 preflight/service timer가 소유한다. TYM·미래에셋증권·삼성중공업·SK이터닉스 midday는 13:10/13:14, CJ CGV·카카오 midday는 13:15/13:19, 한국전력 afternoon·삼성중공업 afternoon·SK이터닉스 afternoon은 13:55/13:59, 삼성E&A afternoon은 14:00/14:04, CJ CGV afternoon은 14:10/14:14, 한세실업 afternoon은 14:15/14:19, SK텔레콤 afternoon은 14:20/14:24, TYM afternoon은 14:25/14:29다. 2026-08-18 승인 추천 14개는 2026-08-19 exact-date PREOPEN부터 20-profile 세대로 적용한다. 2026-08-19 승인 추천 11개는 같은 8월 21일 전환의 staged base로 보존하고, 2026-08-20 승인 추천 9개(기존 개선 5개+신규 4개)를 덮어쓴 결합 27-profile 세대를 2026-08-21부터 적용하며 이전 날짜 applied/state 원장은 이전 세대로 검증한다. 신규 4개 profile의 timer 8개는 코드 구현과 별개인 reviewed installer 실행 전에는 운영 활성으로 간주하지 않는다. profile별 manual-operator exclusion, 연구 evidence, exact-date applied hash, shared token, main bot active 조건 중 하나라도 빠지면 해당 profile만 시작하지 않는다. 동일 종목의 profile끼리도 process/state/order ledger를 공유하지 않으며, 두산·한화 episode service는 같은 종목의 widget owner state/order/quantity를 읽거나 취소·매도하지 않는다. 상세 계약과 설치/rollback은 [lower-price two-leg machines](./low-price-two-leg-machines.md)가 소유한다.
| `20:15` | operator-disabled | `deploy/run_swing_live_dry_run_report.sh` cron 미설치 | 기존 산출물은 archive/audit evidence | 스윙 매매 비운영 기간에는 실행·freshness를 요구하지 않는다. 명시적 운영 지시 후 `KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE=true`로 installer를 실행한 경우에만 cron을 복원한다 | 자동 복원 금지. 스윙 dry-run 결과로 runtime guard 완화 금지 |
| `20:50` | cron | dashboard DB archive, `deploy/run_dashboard_db_archive_cron.sh 0` | `logs/dashboard_db_archive_cron.log`, `logs/dashboard_db_archive.log` | `DASHBOARD_ARCHIVE_*` 통계와 `skipped_unverified` 확인. 같은 날짜 verified/backfilled raw/snapshot 압축을 시도한다 | 미검증 파일 강제 삭제 금지. 이 archive는 저장소 운영 보강이며 threshold/order/provider/bot 변경 권한이 없다 |
| `21:00` | cron | `deploy/run_logs_rotation_cleanup_cron.sh 30` | `logs/log_rotation_cleanup_cron.log`, `tmp/log_rotation_cleanup_writer_defer_state.json` | `archive_generation_compressed/verified`, `archive_writer_active_deferred(_bytes)`, `writer_defer_tracked/escalated/max_consecutive/state_failures`, `report_artifact_{actions,compressed,failures,retention_candidates,retention_candidate_bytes}`, `immutable_source_artifact_{count,bytes}`, checkpoint/provider-ledger census, 기타 retention·micro-storage 지표 확인 | 당일 장애 분석 전 로그 수동 삭제 금지. 숫자 slot은 archive identity가 아니며 `name.log.N`의 원문 SHA-256으로 숫자를 제거한 `name.log.generation_<hash>.gz`를 no-clobber 원자 게시·복원검증한다. plain source와 legacy `name.log.N.gz`는 덮어쓰거나 삭제하지 않는다. writer/open/recent/압축 중 변경 slot은 `deferred_writer_active`로 분리하고 최초·일시 defer는 DONE-by-design이다. 동일 로그 계열의 연속 defer만 상태 파일에 누적하며 기본 3회부터 `[WRITER_DEFER_ESCALATED]`와 최종 `[FAIL]`로 승격하고, 중간 stable pass가 있으면 누적을 초기화한다. 압축 무결성·state·micro lock/producer·find producer 실패는 즉시 실패로 집계하되 peer lane은 계속한다. exact-date P2 report JSON은 명시 basename allowlist와 닫힌 날짜만 SHA-256/gzip roundtrip 후 압축하며 실행일·당일은 보호한다. 실행 없는 닫힌 날짜도 immutable paired/prepared/bridge/source/materialized/label은 개별 압축할 수 있지만 incomplete execution result와 checkpoint journal은 재개를 위해 보존한다. 기본 90일 초과 artifact는 count/bytes만 집계하고 full compressed audit를 자동 삭제하지 않는다. generic retention/source unlink는 기존 owner-pending 정책을 유지하고, 원본 `data/pipeline_events`와 clean-baseline quarantine/raw audit evidence는 cleanup 대상이 아니다 |
| `21:10` | operator-disabled | `KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE=true auto_retrain_pipeline.sh` cron 미설치 | 기존 model/retrain 산출물은 archive/audit evidence | 스윙 매매 비운영 기간에는 retrain·promotion freshness를 요구하지 않는다. 명시적 운영 지시 후 `KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE=true`로 installer를 실행한 경우에만 cron을 복원한다 | 자동 복원·auto-promote 금지. 스윙 dry-run 해제, threshold/floor env 작성, 브로커 주문 허용 근거로 쓰지 않는다 |
| `07:00~21:55/5` | cron | `bash deploy/run_error_detection.sh full` | `data/report/error_detection/error_detection_YYYY-MM-DD.json`, `logs/run_error_detection.log` | wrapper가 `logs/run_error_detection.log`를 보장하고 `[START]/[DONE]/[FAIL]` marker를 남기는지 확인. 7개 detector (process health, cron, log, Kiwoom auth 8005 recovery, artifact, resource, stale lock). 4개 report-only, 3개 filesystem/runtime recovery mutation (각 flag/cap/cooldown gated). 각 invocation은 고유 `run_id` 보고서를 먼저 원자 생성하고 mode/date/detector accounting/runtime 권한 계약 검증 후에만 canonical report로 승격·알림·DONE 처리한다. `summary_severity=fail`이면 bot daemon이 떠 있지 않아도 wrapper가 관리자 Telegram 직접 알림을 시도한다 | 탐지 결과로 runtime threshold/spread/주문 자동 변경 금지. Telegram 알림은 report-only 운영 알림이며 자동 복구/재시작 권한이 아니다 |

Postclose backfill 명령의 stdout에는 API 초기화 안내가 JSON보다 먼저 기록될 수 있다. `run_threshold_cycle_postclose.sh`는 마지막 유효 JSON object를 backfill summary로 해석하며, 유효 JSON summary가 없거나 `status`가 실패이면 hard fail로 종료한다. 이 경우 controller를 먼저 DONE으로 강제하지 말고 wrapper 실패 로그와 backfill stdout을 확인한 뒤 wrapper/controller 순서로 복구한다.

Cron/internal active log의 반복 writer defer는 cleanup에 unknown-writer rename 권한을 주어 해소하지 않는다. 설치된 error detector, panic-sell defense, rising-missed feedback, threshold preopen/postclose와 cleanup cron은 `run_with_owned_log.sh` 또는 내부 wrapper에서 `run_owned_log_rotation.sh`를 호출해 실제 writer가 파일을 열기 전에 자기 log만 rollover한다. per-path owner lock, open inode 0건, preflight metadata/SHA-256 불변을 통과한 경우에만 active pathname을 rename하고 같은 mode의 빈 active file을 생성한다. 원문 SHA-256과 decoded gzip SHA-256이 일치하는 `name.log.generation_<hash>.gz`를 no-clobber 게시한 뒤 `data/report/log_writer_rollover_receipts/log_writer_rollover_YYYY-MM-DD.jsonl`에 `rotated_verified` receipt를 남긴다. open/changed/collision은 0 mutation `deferred_writer_active|error`로 보존한다. 이 계약은 filesystem instrumentation이며 `runtime_effect=false`, order/provider/threshold/bot 권한이 없다. Generic cleanup의 active rename·truncate·numeric shift 금지는 유지한다.

Postclose resource guard는 최신 system metric sample이 자정·주말 cron window 전환으로 stale/missing이 된 경우에만 공식 `run_system_metric_sampler_cron.sh`를 최대 60초 간격으로 호출해 관측값을 갱신한다. 갱신 성공 자체를 guard 통과로 간주하지 않고 다음 loop에서 memory/swap/disk/CPU/load와 freshness를 다시 검사하며, 실제 resource fail은 기존 timeout까지 fail-closed로 유지한다. `THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER=false`로 자동 갱신만 rollback할 수 있고 이 계약은 `runtime_effect=false`인 운영 계측 보완이다.

Postclose trigger decision은 wrapper의 실제 enable flag를 함께 받아야 한다. 명시적 OFF 또는 기본 OFF step은 `disabled_success`로 기록하고 output/source 누락을 실행 사유나 `source_missing`으로 집계하지 않는다. force refresh는 enabled step의 freshness만 무시하며 OFF step을 다시 켜지 않는다. wrapper는 `disabled_success`를 정상 skip marker로 소비한다. 이전 동일 날짜 wrapper 상태가 `failed`인 복구 실행에서는 opening-rotation, avg-down recovery, one-share opportunity의 JSON/Markdown과 target/report contract가 모두 유효하고 재시도·실패·source-blocked 상태가 없을 때만 완료 checkpoint를 재사용한다. 정상 재실행, 다른 날짜, 입력 변경 판정 또는 불완전 artifact에는 이 재사용을 적용하지 않는다. `THRESHOLD_CYCLE_REUSE_COMPLETED_REPORT_STEPS=false`로 복구 재사용만 rollback할 수 있으며 runtime/order/provider/threshold 권한은 없다.

### Pipeline Event Verbosity/Retention Policy

`data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`은 당일 forensic raw stream이고, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl`은 threshold-cycle이 읽는 compact decision stream이다. raw stream 증가는 `logs/` rotation으로 해결되지 않으며, disk pressure 원인 판정 시 두 경로를 분리한다.

1. 당일 raw stream은 postclose snapshot/DB/parquet 검증 전까지 수동 삭제하지 않는다. 주문 제출, 체결, exit, safety, threshold family, provenance, source-quality 이벤트는 손실 없이 보존한다.
2. `strength_momentum_observed`, `blocked_strength_momentum`, `blocked_swing_score_vpw`, `blocked_overbought`, `blocked_swing_gap`처럼 고빈도 diagnostic stage는 기본 decision authority가 없다. 반복 tick 단위 raw 기록을 live threshold/order guard 근거로 직접 쓰지 않고, stage/date/stock/source-quality 단위 summary 또는 sampling artifact를 먼저 만든다. BUY Sentinel v1은 이 5개 stage만 `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`로 1분 bucket 집계하고, 원문 raw 기록은 줄이지 않는다.
3. verbosity/throttle code change는 lossless decision-stage allowlist 또는 raw 보존 shadow 계측으로 시작한다. pass/order/safety/source-quality transition은 throttle 대상에서 제외하고, suppressed count/first_seen/last_seen을 별도 metric으로 남겨야 한다. producer-side compaction V2의 기본값은 `PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE=shadow`이고, `shadow`는 raw JSONL/DB upsert를 보존한 채 `data/pipeline_event_summaries/pipeline_event_producer_summary_YYYY-MM-DD.jsonl`과 manifest만 생성한다. `off`는 장애 대응용 비활성 옵션이다. `suppress`는 코드가 있어도 기본 비활성이며 V1 raw-derived summary와 2영업일 이상 parity 통과, 별도 workorder/approval owner 전에는 사용하지 않는다.
4. 보관/압축은 `compress_db_backfilled_files`가 소유한다. 20:50 정규 archive는 조기 성공 시도를 담당하고, postclose가 길어진 날은 `run_tuning_monitoring_postclose.sh`가 parquet 생성 직후 같은 검증 압축을 다시 수행한다. pipeline parquet 생성은 기본 5,000행 chunked writer와 임시 파일 원자 교체를 사용하며 날짜 전체 raw/DataFrame materialization을 금지한다. canonical AI context consumer와 pipeline summary consumer는 plain/gzip을 스트리밍하며, 과거 summary를 명시적으로 재생성·append할 때는 archive를 먼저 plain으로 복원해 gzip/plain 분기 손실을 막는다. threshold partition은 완료 checkpoint가 있는 D+30 이상만 gzip으로 전환한다. 모든 전환은 JSONL row 검증 및 gzip 복원 검증 후 원본을 제거한다. 검증되지 않은 raw는 skip되며, 운영자가 수동 정리할 때는 dry-run으로 verified/backfilled 대상과 `skipped_unverified`를 먼저 확인한다. 미검증 파일 강제 삭제는 금지한다.
5. scanner 고빈도 관찰 중 `scalping_scanner_runtime_target_attach`와 `scalping_scanner_watching_runtime_skip`은 structured `fields`를 손실 없이 보존하되 `text_payload`만 핵심 18개 필드로 제한한다. WATCHING 동일 skip reason의 기본 재기록 간격은 60초다. 주문·체결·safety transition과 promotion generation provenance는 생략하지 않는다.
6. 이 정책은 운영 저장소/verbosity 정책이며 runtime threshold, provider route, 주문가/수량 guard, bot restart 권한이 없다. 구현 필요 시 `pipeline_event_verbosity_compaction_workorder`로 code improvement owner를 열어 장후 처리한다.
7. 장후 raw-derived producer parity는 `counts_only_v1`로 생성해 bucket identity/count/coverage만 보존한다. per-second count, sample event, numeric stats, raw offset은 parity 판단에 불필요한 중복이므로 저장하지 않는다. raw와 producer의 coverage end가 다르면 더 이른 coverage end의 완료 분 경계까지만 `completed_common_minute` 비교를 추가하고, 미완료 tail은 별도 제외 건수로 남긴다. common-watermark parity가 통과해도 tail pending 동안 full parity와 suppress eligibility는 통과시키지 않는다. `pipeline_event_verbosity` JSON/Markdown이 raw source, producer summary/manifest, report/summary 코드보다 모두 새롭고 JSON 검증도 통과할 때만 복구 실행에서 재사용하며, 입력·코드가 하나라도 바뀌면 다시 생성한다. Entry ADM, lifecycle bucket daily/rolling, latency recommendation의 wrapper stdout은 `--print-summary`로 제한하되 파일 산출물은 기존 full schema를 유지한다. 이 최적화는 `runtime_effect=false`이고 raw suppression을 활성화하지 않는다.

## System Error Detector 사용 절차

System Error Detector는 전략 튜닝 도구가 아니라 운영 감시 도구다. 사용 목적은 봇/cron/log/artifact/resource/lock 상태를 조기에 발견하고 `pass`, `warning`, `fail`로 분류하는 것이다. 탐지 결과는 incident, instrumentation gap, runtime ops 확인으로 라우팅하며, score threshold, spread cap, 주문 guard, provider routing, bot restart를 자동 변경하지 않는다.

Telegram 알림은 detector id·severity·동적 숫자/시각을 정규화한 summary class의 incident fingerprint를 사용한다. 동일 incident가 활성 상태인 동안 5분 주기 재탐지는 state의 `last_seen`만 갱신하고 중복 발송하지 않으며, 새 fingerprint만 별도로 알린다. fail/warning이 사라진 정상 report가 active set을 해제한 뒤 같은 incident가 재발하면 새 incident로 다시 알린다. fingerprint state는 원자 교체하며, 이 억제는 탐지 결과·health artifact·복구 판단을 숨기지 않고 Telegram 중복만 줄인다.

### 신규 기능 detector coverage 의무

새 recurring runtime, cron wrapper, 장중/장후 report, 장기 실행 thread/daemon을 추가하거나 runbook 시간표에 새 행을 추가하면 같은 변경 세트에서 detector coverage를 반드시 선언한다. coverage 선언 없이 운영 기능만 추가하는 변경은 미완료로 본다.

필수 등록 기준:

| 신규 기능 유형 | 필수 조치 | 검증 기준 |
| --- | --- | --- |
| cron/wrapper/정기 실행 job | [cron_completion.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/cron_completion.py)의 `CRON_JOB_REGISTRY`와 [error_detector_coverage.py](/home/ubuntu/KORStockScan/src/engine/error_detector_coverage.py)의 `REQUIRED_CRON_JOB_IDS`에 같은 `id` 등록 | `src/tests/test_error_detector_coverage.py` 통과. 설치 crontab marker가 없는 registry job은 `disabled_not_installed`로 닫고, crontab 조회 실패 시에는 감시 기대값을 유지한다. |
| report/artifact 생성 기능 | [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py)의 `ARTIFACT_REGISTRY`와 `REQUIRED_ARTIFACT_IDS`에 같은 `id` 등록 | artifact path, window, critical 여부가 runbook 실행시각과 일치. parent cron flag가 false인 산출물은 `disabled_by_parent`, 해당 step의 당일 `[SKIP]` marker가 있으면 `pass_terminal_skip`으로 닫는다. |
| 장기 실행 thread/daemon | [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py)의 `write_heartbeat(component=...)` 호출 추가, `REQUIRED_HEARTBEAT_COMPONENTS` 반영 | heartbeat file에 component가 남고 process health dry-run이 fail하지 않음 |
| 새 health domain | `src/engine/error_detectors/*.py`에 `@register_detector` detector 추가, [error_detector.py](/home/ubuntu/KORStockScan/src/engine/error_detector.py)에서 import | `--mode full --dry-run` 결과에 detector 포함 |
| 감시 제외 대상 | `DETECTOR_COVERAGE_EXEMPTIONS`에 제외 사유 등록 | installer/one-off/manual replay처럼 반복 운영 대상이 아님이 명확해야 함 |

`cron_completion` 감시 대상은 wrapper 또는 직접 실행 스크립트가 같은 날짜의 완료 marker를 반드시 남겨야 한다. 표준 marker는 `[START] <job_id> target_date=YYYY-MM-DD started_at=...`, `[DONE] <job_id> target_date=YYYY-MM-DD finished_at=...`, `[FAIL] <job_id> target_date=YYYY-MM-DD ...`이며, log redirect 후 stdout/stderr에 기록되어야 한다. 실행 본문이 정상 종료돼도 detector log에 `[DONE]`과 `target_date`가 없으면 `no completion marker` 운영 결함으로 본다. 다만 설치되지 않은 cron, 명시적으로 false인 parent enable flag, exit code 0의 `skipped/disabled` status artifact는 정상 비실행이다. postclose 내부 step의 `[SKIP]`은 artifact별 step token이 정확히 일치할 때만 해당 artifact 성공으로 인정하며 전체 wrapper 완료 marker를 대신하지 않는다.

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

nproc 기반 CPU profile로 bot hot path와 report-only job 경합을 줄인다. 공통 profile은 [cpu_affinity_profile.sh](/home/ubuntu/KORStockScan/deploy/cpu_affinity_profile.sh)가 소유한다. 4 vCPU 이상에서는 [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)의 기본 `KORSTOCKSCAN_BOT_CPU_AFFINITY`가 `0-1`, report-only wrapper 기본값이 `2-3`, health/sampler 기본값이 `3`이다. 2~3 vCPU 환경에서는 bot `0`, wrapper `1` 또는 `1-2` 계열로 축소되고, 1 vCPU 또는 `taskset` 부재 환경에서는 affinity 없이 실행한다. 적용 대상은 `run_error_detection.sh`, `run_buy_funnel_sentinel_intraday.sh`, `run_holding_exit_sentinel_intraday.sh`, `run_panic_sell_defense_intraday.sh`, `run_system_metric_sampler_cron.sh`, `run_rising_missed_intraday_feedback.sh`, `run_scalping_pyramid_intraday_feedback.sh`, `run_intraday_ws_freshness_monitor.sh`, `run_monitor_snapshot_cron.sh`, `run_monitor_snapshot_incremental_cron.sh`, `run_monitor_snapshot_midcheck_safe.sh`, `run_monitor_snapshot_safe.sh`, `run_threshold_cycle_calibration.sh`, `run_threshold_cycle_postclose.sh`이며, 각각의 wrapper별 `*_CPU_AFFINITY`로 override할 수 있다. growing pipeline을 재탐색하는 rising-missed/pyramid/WS source-only 작업의 성공 완료 cooldown 기본값은 각각 1500/720/720초이고, 5분 trigger와 조합한 실효 간격은 약 30/15/15분이다. panic sell wrapper 내부의 `market_panic_breadth_collector`도 같은 panic wrapper affinity/nice/ionice와 shared lock/fresh artifact 재사용 계약을 따른다. 이 설정은 CPU 배치와 source-only 보고 주기만 바꾸며 threshold, 주문 guard, provider 변경 권한은 없다. 단 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart`는 15:45 장후 postclose resource isolation 전용 운영 재기동이며, strategy/runtime threshold 변경으로 해석하지 않는다.

`run_error_detection.sh`의 직접 Telegram 알림은 `KORSTOCKSCAN_ERROR_DETECTION_TELEGRAM_NOTIFY_ENABLED=false`로 비활성화할 수 있다. 동일 fail signature는 `tmp/error_detection_telegram_notify_state.json` 기준 10분 cooldown으로 중복 전송을 막는다. wrapper는 실행별 임시 report의 `schema_version/report_type/mode/run_id/target_date`, 예상 detector 집합과 생성 실패 accounting, `runtime_effect=false/runtime_mutation=none`을 검증한다. 여기서 `runtime_mutation=none`은 `trading_strategy_runtime` 범위이며, flag/cap/cooldown 안에서 실제 수행된 restart flag·token cache invalidation·log rotation·stale-lock cleanup은 `operational_mutations`로 별도 기록한다. 누락·이전 실행 파일·부분 JSON·detector silent drop은 canonical report로 승격하거나 `[DONE]`으로 닫지 않고 `[FAIL]`로 종료한다. canonical report와 bot daemon report는 모두 atomic replace로 기록해 동시 reader가 부분 JSON을 읽지 않게 한다.

Error detector가 resource pressure로 cleanup을 호출해도 owner-integrated active rollover 권한을 대리하지 않는다. Active rollover는 다음 실제 writer의 pre-open owner gate에서만 수행하고, error detector/cleanup은 receipt와 deferred state를 감사한다.

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
| `process_health` | KRX 거래일 `07:55~20:10 KST` bot expected runtime window 안에서 main loop, daemon thread heartbeat stale 또는 PID 불일치. 일반 thread가 `alive=false`를 기록하면 age timeout을 기다리지 않고 즉시 FAIL한다. 단, 스나이퍼 owner가 `20:00 KST` 이후 동일 거래일 heartbeat에 `terminal_reason=market_close`를 명시한 정상 종료만 `expected_terminal` PASS로 분리한다. reason 누락·다른 thread·20:00 이전·과거 날짜 marker는 계속 FAIL한다. 삼성 morning expected set은 07:57 전 `not_yet_due`, 07:57~08:04 exact-date authority/live start 대기를 `bounded_wait` WARNING, 08:05부터 authority v7의 exact target/관찰·만료시각/runtime 계약, 당일 preflight와 당일 active 또는 terminal-success live 실행이 모두 없으면 FAIL로 분류한다. active live 경로는 authority에 결속된 `bot_main.py` PID 생존을 계속 요구하지만 당일 terminal-success 뒤 계획된 main bot 종료는 이전 PID 사망만으로 다시 FAIL하지 않는다. 전일 terminal result는 당일 success로 재사용하지 않고 main heartbeat와 삼성 finding을 함께 보존한다. systemd unit query 실패·미설치, timer disabled·잘못된 trigger, preflight/live `ubuntu:ubuntu` credential drift, stale authority, preflight/live failure도 FAIL이며 runtime mutation은 없다. 비거래일 또는 bot 시간창 밖의 dead/stale heartbeat는 `expected_stopped`로 닫고 fail 알림 대상이 아니다. expected start 직후 `ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC` 동안은 tmux/run_bot/heartbeat 갱신 race를 fail이 아니라 startup grace warning으로 본다. `restart.flag` 기반 graceful restart 직후 `ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC` 이내의 dead PID + fresh heartbeat는 handoff warning으로 보고 즉시 재시작하지 않는다. 20:10 postclose wrapper가 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop`으로 bot을 의도적으로 내리면 `tmp/postclose_bot_isolation.json` marker를 쓰며, marker가 신선한 동안 dead/missing/stale heartbeat는 장애 FAIL이 아니라 postclose isolation warning이다 | expected window 안이면 heartbeat owner와 실제 tmux/process 상태 확인. 삼성 morning FAIL이면 exact-date authority와 동일 systemd transaction의 preflight/live job을 확인하되 중복 owner를 시작하지 않는다. `expected_terminal`은 정상 장 종료이므로 재기동하지 않는다. expected window 밖이면 정상 스케줄 종료로 본다. startup/restart grace warning은 grace 이후 재확인에서 pass/fail로 닫는다. postclose isolation warning은 장후 의도적 정지로 보고 다음 PREOPEN `07:55` 기동까지 재기동하지 않는다 | 자동 restart, threshold 변경 |
| `cron_completion` | 필수 cron log의 당일 DONE 누락 또는 FAIL 최신 marker. 거래일 전용 cron은 KRX 비거래일에 `skip_non_trading_day`로 닫는다 | 해당 cron log와 산출물 재확인 후 같은 date 재실행 여부 판단 | 실패를 threshold 성과로 해석 |
| `log_scanner` | error log burst 또는 신규 error pattern. `ERROR`/`CRITICAL`/traceback/exception/에러/오류/실패 같은 에러 후보 라인만 분류하며, `_error.log`에 섞인 INFO/WARNING성 DB 성공·업로드 로그는 운영 incident에서 제외한다. `TEST`, `123456`, `_DummySession`, `bus fail`처럼 pytest fixture signature가 붙은 라인도 제외한다. memory/OOM 분류는 `MemoryError`, 독립 단어 `memory`/`oom`, `out of memory`, `cannot allocate memory`만 인정하고 `kiwoom_*` 같은 logger/module 이름 내부 문자열은 OOM으로 보지 않는다 | stack trace/source artifact 확인 후 incident 또는 code workorder로 분리. fixture noise나 INFO성 운영 로그가 runtime error log에 섞이면 test/log sink 분리 또는 scanner ignore rule 보강으로 닫는다 | 에러만 보고 live guard 완화 |
| `kiwoom_auth_8005_restart` | fresh runtime log에서 `8005 Token이 유효하지 않습니다` 계열 인증 실패 감지. 기존 offset 이전 로그, pytest fixture signature, `run_error_detection*` meta log는 제외한다. graceful PID handoff 뒤 발견된 timestamp가 새 PID 시작보다 앞선 행은 이전 PID 종료 구간으로 귀속해 소비한다. 같은 runtime scan window에서 timestamped 8005 뒤 same-request retry 성공 token handoff가 있고 그 뒤 8005/recovery failure가 없으면 `recovered_without_restart`로 소비한다. timestamp가 없거나 handoff 뒤 재발한 행은 계속 actionable이다 | live-engine 시작은 KST 당일 발급 shared token만 재사용하고 전일/미상 발급 cache는 binding 전에 1회 갱신한다. actionable 8005는 `restart.flag` 기반 graceful restart 후 새 PID, WS 수신, REST 시세/잔고 응답 회복을 확인한다. 하루 3회까지 restart 복구를 허용하고 이후에는 fail artifact/Telegram으로 operator 확인을 요구한다. REST/account/order 호출 지점은 8005 응답에 한해 force-refresh, same-request 1회 retry를 수행하며 성공 handoff를 process-local replacement map에 등록한다 | threshold/spread/order guard 변경, provider route 변경, retry loop 확장 |
| `artifact_freshness` | 시간창 기준 필수 report/artifact stale/누락 또는 JSON status 값 비정상. 장중 `pipeline_events`는 09:00~09:05 startup grace를 두고, `threshold_events` compact stream은 sparse stream이라 stale을 warning으로 본다. 07:35에 producer와 detector가 동시에 실행되는 `threshold_runtime_env`/`threshold_apply_plan`은 첫 detector 주기 300초 동안 이전 장후 target-date handoff의 stale을 `startup_grace`로 처리하되, 유예 이후에도 갱신되지 않으면 기존 critical fail을 유지한다. `threshold_cycle_ev`와 `swing_daily_simulation` 같은 one-shot postclose artifact는 완료 후 age만으로 재실행하지 않는다. `daily_recommendations_v2.csv`와 diagnostics는 장전 입력 특성상 mtime만 보지 않고 내부 `date`/`latest_date`, row/count 계약이 통과하면 `pass_content_date`로 닫는다 | window, startup grace, trading_day skip, upstream cron 실패, status JSON의 `failed_steps`/`recovered_steps`, content date/count 확인 | 누락 artifact를 수동 값으로 대체 |
| `resource_usage` | CPU/memory/swap/load/disk threshold 위반, sampler stale. CPU busy fail 기준은 `ERROR_DETECTOR_CPU_BUSY_MAX_PCT=95.0`이며 90% 구간부터 warning으로 본다. KRX 비거래일에는 system metric sampler stale만 `skip_non_trading_day`로 제외하고 disk/memory/load 같은 host resource check는 유지한다 | resource pressure 원인 확인. disk-low면 log rotate 결과와 cooldown state 확인. swap만 높고 `mem_available`이 충분한 경우는 즉시 장애보다 reclaim/캐시 잔존 가능성을 먼저 본다 | 전략 runtime parameter 변경 |
| `stale_lock` | 오래된 lock 발견 또는 cleanup 실패 | active lock인지 확인. 반복되면 wrapper lock lifecycle 보강 | 실행 중인 process lock 강제 삭제 |

### 코드수정 필요 에러 처리 절차

`summary_severity=fail` 또는 반복 `warning`이 코드 결함, instrumentation gap, wrapper 계약 불일치로 보이면 사람이 Codex에 수정 작업을 지시한다. detector 결과만으로 live threshold, spread cap, 주문 guard, provider routing, bot restart를 임의 변경하지 않는다. 단, Kiwoom auth 8005 복구는 인증/runtime data path 예외로 처리한다. 호출 지점은 8005 응답에 한해 token cache invalidation, force-refresh, same-request 1회 retry를 수행할 수 있다. `kiwoom_auth_8005_restart` detector는 retry 성공 handoff로 닫히지 않은 fresh 8005에만 daily cap/cooldown 계약 안에서 `restart.flag` 생성 또는 fail artifact/Telegram 표면화를 수행한다.

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
- `resource_usage`: disk free가 `ERROR_DETECTOR_DISK_FREE_MIN_MB` 미만이고 `ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=True`이며 dry-run이 아닐 때 `deploy/run_logs_rotation_cleanup_cron.sh 30`을 호출한다. generic unknown-writer active/numeric archive/raw-row에 대해서는 destructive authority가 없다. oversized active는 `disabled_pending_writer_owner`로 보존·FAIL하고, numeric archive는 quiet/open/metadata/hash·gzip roundtrip 검증을 통과한 no-clobber gzip copy만 게시하며 plain source를 authoritative로 남긴다. existing gzip content conflict는 세대를 추측하거나 덮어쓰지 않고 둘 다 보존하며 FAIL한다. active/archive retention, archive plain unlink, `raw_row_exclusion` duplicate/backup delete·manifest mutation, sentinel/snapshot source unlink은 각각 `disabled_pending_writer_owner|storage_owner`의 candidate count/bytes로만 보고하고 deferred backlog 자체는 DONE-by-design이다. repo tmp/cache와 owner-locked `system_metric_samples.jsonl` 정리는 기존 postcondition census를 유지한다. micro observation은 예외적으로 writer가 file open 전~fsync/close 후 trade-date shared lock과 per-file exclusive/no-follow regular-file open을, maintenance가 closed-date의 session group preflight~gzip publish~manifest~source unlink 전체에 exclusive non-blocking lock을 사용할 때만 compaction한다. ownership/preflight의 manifest/shard overlap·invalid·symlink·open·changed group은 0 mutation으로 차단한다. publish 후 실패는 source를 보존하고 실제 applied action·unresolved candidate bytes·recovery_required를 남기며 peer session/date/lane을 계속한다. market path/stream late writer는 gzip logical shard를 재생성하지 않고 새 plain shard/mixed manifest를 게시하며, 단일 canonical 파일만 소유하는 event-reference writer는 압축 후 late append를 명시 실패해 gzip을 변경하지 않는다. `PathStoragePolicy.retention_days=14` 초과 partition purge는 별도 운영 승인 후 `MICRO_REVERSION_STORAGE_PURGE_ENABLED=true`와 CLI `--purge-expired`가 함께 있을 때만 tree open/stability 재검증 후 가능하며 기본은 census-only다. exact-date P2 report artifact는 별도 allowlist에 한해 종료일 plain JSON을 verified gzip으로 전환하고 `MICRO_REVERSION_REPORT_ARTIFACT_RETENTION_DAYS` 기본 90일 초과분을 삭제 없이 census한다. partial tree 삭제는 `purge_partial`, 남은 candidate bytes, `recovery_required`와 최종 FAIL로 표면화한다. global/date lock, `find`/sort producer, compression, micro 실패는 peer lane을 계속한 뒤 `[FAIL]`로 집계하고 `[DONE]`을 남기지 않는다. 이 경로는 storage-only이며 order/provider/threshold/bot/runtime 권한이 없다. 성공한 호출만 `tmp/error_detector_last_log_rotate_ts.txt`에 기록하며 30분 cooldown 중에는 `log_rotate_trigger=cooldown_active`로 보고한다.
- micro-reversion source-quality exclusion의 물리 정리는 날짜 전체 purge와 분리한다. 사용자가 명시적으로 요청한 경우에만 `storage_maintenance --purge-source-exclusions <validated-manifest> --apply`를 사용하며, 기존 exclusion manifest의 `trade_date+venue+session+sequence_epoch`와 예상 stream/reference 행 수가 실제 closed-date 파일과 정확히 일치해야 한다. maintenance는 trade-date exclusive lock, open/stability 검사, filtered gzip roundtrip, 원본 hard-link rollback, manifest byte 갱신을 통과한 stream/reference만 교체한다. 같은 날짜의 정상 epoch와 depth stream, 현재 거래일, exclusion manifest 자체는 보존한다. count mismatch·writer active·현재/미래 날짜·부분 publish는 fail-closed이며 threshold/provider/bot/order/runtime 권한이 없다.
  - sentinel/snapshot의 `*_compressed`는 이번 run이 새 no-clobber gzip copy를 게시한 수만 뜻한다. 기존 일치 gzip 재검증은 `*_verified_existing_source_preserved`로 별도 계수하며 재실행 때 신규 압축 수를 반복 증가시키지 않는다. micro 결과 parser는 허용 action taxonomy와 action/failure row에서 count·bytes·recovery를 재계산해 top-level 불일치를 `invalid_result`와 wrapper `[FAIL]`로 차단한다.
- `kiwoom_auth_8005_restart`: live-engine 시작은 KST 당일 `issued_at`인 valid shared token만 재사용한다. 전일/미상 발급 cache는 shared lock 안에서 1회 갱신한 뒤 장수 REST/WS owner를 bind하고, 같은 날의 재기동은 당일 token을 재사용한다. detector는 fresh runtime `8005` 인증 실패를 감지하되, timestamped 8005 이후 같은 scan window에 `api_8005_retry:*:retry_success` handoff가 있고 그 뒤 8005 또는 refresh/retry failure가 없으면 cache invalidation·경보·flag 없이 pass로 소비한다. untimestamped 행, handoff 뒤 재발, refresh/retry 실패는 actionable이다. graceful restart 요청 이후 새 PID가 시작되기 전에 이전 PID가 남긴 timestamped 8005는 `prior_runtime_auth_8005_count`로 소비한다. actionable incident는 동일 120초 cooldown 중 중복 flag를 억제하고 하루 누적 3회까지 restart 복구를 허용하며, 이후에는 fail artifact/Telegram만 남긴다. 호출 지점별 REST/account/order helper는 force-refresh token으로 같은 요청을 1회만 재시도하고, 성공한 갱신은 process-local bounded handoff로 장수 caller까지 수렴시킨다. WS `805004` 복구도 이전 token과 새 token의 handoff를 등록한다. 이 계약은 token 발급·retry 횟수·주문 권한을 늘리지 않으며 반복 실패는 auth incident로 남긴다.

maintenance mutation도 전략 runtime 변경이 아니다. 실패하거나 반복되면 `warning/fail`로 보고 원인 복구를 진행하며, 매매 threshold를 수동 조정하지 않는다.

### R0→R3 P2 검증·용량 운영 계약

- Current A/B/C Provider replay는 activation 이후 최근 30 calendar-day canonical window에서 KRX 거래일 5일, complete common parent 20개, verified unique KOSPI/KOSDAQ 보통주 10개가 모두 확인될 때만 시작한다. floor validator는 각 날짜의 materialized/source/prepared/bridge/paired 5-artifact lineage를 strict-read·canonical rebuild하고 result/checkpoint/R2/R3 hash에 결속한다. 다섯 companion 중 일부만 남은 orphan generation은 자연 결손이 아니라 fail-closed source gap이다. rolling R2/R3에서는 겹치는 날짜 generation을 한 번만 읽고 검증한 뒤 full payload가 아닌 compact hash·parent/symbol census만 invocation-local cache에 유지하며, 반환 직전 모든 plain/gzip physical identity를 다시 확인한다. R3는 독립 검증된 동일 날짜 rolling R2의 exact artifact hash와 provider-floor binding을 함께 가져야 한다. 변경·symlink·plain/gzip divergence·중복 key·malformed/non-object/non-finite JSON/JSONL은 즉시 차단한다.
- Scheduled bridge는 `micro_prepared_requests`의 target/hash/count로 결속된 exact trace census만 처리한다. Broad trace 전체 실행은 수동 진단 경로에만 남는다. Bridge가 처음 읽은 0B/0D/reference relevant rows는 `data/cache/micro_reversion_relevant_source_index`의 SQLite cache에 staging+atomic rename으로 저장하고 source-bundle이 같은 raw/config/window generation을 재사용한다. Raw descriptor hash와 partition-path census는 산출 직전에 다시 확인하며 append/replace/symlink swap/new partition, metadata·SQLite hash/integrity·coverage 불일치는 fail closed 또는 cache-only rebuild다. Complete cache는 전체 최신 3개, partial은 24시간만 보존한다. 이 cache는 삭제 가능한 성능 계층이고 raw/report 감사 증거를 대체하거나 삭제하지 않는다. Future-outcome source pool은 process당 한 번 검증한 view를 row rebuild에 재사용하지만 exact row reference/outcome/authority 검증은 생략하지 않는다.
- source bundle, materialized request, action-neutral label, Provider batch와 각 schema attempt 직전에 canonical capacity artifact와 직접 `disk_usage` snapshot을 함께 검사한다. free space `5 GiB` 미만은 low, `1 GiB` 미만은 critical이다. critical은 신규 대용량 artifact/Provider call을 0건으로 닫고, low/critical 어느 경우도 매매 runtime·주문·provider route를 바꾸지 않는다.
- Provider leaf는 canonical exact-date owner report와 canonical policy/manifest/pricing raw generation의 hash·size·KST generated-at·보통주 census·50% budget basis를 재검증한다. 호출 전 전체 batch provider/model을 census하고 Bedrock은 physical model ID와 region까지 reviewed price generation에 결속한다. KST execution-day canonical ledger에서 하루 130 parent, 390 logical request/attempt, USD 1을 초과하는 caller cap/path는 거부한다. 첫 Provider call 전에 capacity가 닫히면 checkpoint를 만들지 않는다. 유효 raw response를 받은 schema-rejected attempt 뒤 retry capacity가 닫히면 raw Provider receipt·capacity receipt·attempt hash chain을 partial checkpoint에 먼저 보존하고 다음 실행에서 동일 request의 다음 attempt부터 재개한다. Provider envelope 반환 후 receipt binding/parse validator가 거부한 경우에는 raw output base64를 rejected custody로 checkpoint한 뒤 batch를 중단하며 자동 retry/evaluation/R2/R3 사용을 금지한다. checkpoint의 record directory/sidecar lock은 real-directory/no-symlink dirfd custody와 cross-process exclusive `load -> append -> manifest` transaction을 사용한다.
- Scheduled Provider replay는 current date 호출보다 먼저 reviewed 30-calendar-day floor union의 미완료 과거 날짜를 oldest-first로 처리한다. 과거 날짜마다 한 번에 A/B/C 한 parent만 선택하고, physical KST day의 130-parent·390-attempt·USD 1 공통 ledger를 사용하며 current date용 retry-worst-case 한 parent slot을 항상 남긴다. Complete generation은 0-call skip하고, exact checkpoint에 결속된 `provider_capacity_blocked_before_retry` prefix만 다음 attempt부터 재개한다. `schema_rejected`, `provider_receipt_rejected`, `provider_failed` 같은 terminal state, checkpoint 없는 prior-ledger reservation, checkpoint와 physical ledger의 identity 불일치는 이후 물리일에도 영구 0-call로 닫는다. Cycle과 direct `micro_reversion_execute --execute-candidate` leaf는 Provider client·신규 reservation 전에 동일 prior-ledger/checkpoint census를 실행한다. Historical backfill과 resume은 offline source-only이며 runtime/order/provider-route/PREOPEN apply 권한이 없다.
- Current holding/holding-flow/exit `TRIM`은 원 action을 진단에 남기되 평가 exposure에서는 현 runtime처럼 `HOLD`로 정규화하여 parent/손실 outcome을 제외하지 않는다. Tactical source는 exact causal market/depth/event-reference 전체의 최신 native positive epoch을 semantic validation보다 먼저 선택한다. 새 reconnect epoch에 depth/reference만 있고 market이 아직 없으면 이전 epoch로 후퇴하지 않고 `past_market_row_missing`, 동일 최신 timestamp competing epoch이면 ambiguous로 닫는다. 현재 source-audit/economic/storage/Provider/composed-chain blocker가 하나라도 있으면 rolling gate 통과와 무관하게 current R2 blocker hash를 남기고 R3 candidate를 0건으로 강제한다.
- Materializer의 current-source census는 bridge outcome label-ready 전체를 기계적으로 요구하지 않는다. External bridge가 `ask_depletion_sidecar_status`와 sidecar schema/hash/context/source-quality에서 같은 canonical 실패 reason을 증명한 parent만 A/B/C source exclusion으로 허용하고, valid bridge row를 source bundle exclusion으로 바꾼 재봉인은 전체 fail이다. B→C는 byte-identical candidate input을 유지하면서 `system_prompt`, response schema와 `response_schema_application`을 포함한 명시적 prompt/response-contract 필드만 달라질 수 있다. Provider/model/temperature/reasoning/retry hint나 신규 요청 field 차이는 prompt-only axis 위반이다.
- 21:00 storage maintenance의 P2 JSON allowlist는 정확히 17개 owner basename이다: source bundle, materialized requests, action-neutral labels, terminal execution results, bridge, prepared requests, control driver, rolling R2, R3 candidates, cycle receipt, counterfactual entry diagnostic, Provider ablation floor, storage capacity, paired replay, economic reference, reviewed cost profile, symbol master. 닫힌 날짜의 schema/hash/roundtrip을 통과한 artifact만 gzip으로 전환한다. incomplete/resumable checkpoint와 실행일·당일은 plain으로 보존한다. 추가로 exact AI payload/trace/outcome/request/prompt JSONL과 outcome-label JSON 6개 root를 generation lock·embedded-date/schema/dual-generation gate로 검증해 닫힌 날짜만 no-clobber gzip으로 전환한다. micro-reversion daily policy owner tree는 bytes/hash/retention candidate census만 수행한다. 모든 범위의 90일 초과분은 자동 삭제/offload하지 않고 count/bytes만 보고하며 장기 owner는 `[MainAIQualityP2RetentionCapacityOwner0826]`가 OPEN으로 소유한다.
- Current A/B/C는 exact OpenAI entry와 strict receipt-bound Bedrock Nova Lite v2 holding/exit만 평가한다. `entry_price` Qwen3 32B/Nova Lite v2 price-value route는 별도 source-only exclusion이며 별도 paired owner가 닫히기 전에는 이 체인의 완료 범위로 보고하지 않는다.
- 2026-08-25 최종 권한 gate는 `main_ai_quality_legacy_runtime_authority_fail_closed`다. Legacy main-AI PREOPEN publisher는 queue·lock·activation artifact를 읽거나 쓰기 전에 `blocked_fail_closed`, `runtime_effect=false`, `allowed_runtime_apply=false`로 종료하고 CLI는 비정상 종료를 반환한다. Live selector도 기존 activation/apply/handoff/master 유무와 무관하게 configured control prompt로 fallback한다. 장후 source 수집·A/B/C 평가·R2/R3 source-only 후보·queue 보고는 계속 실행한다. 이 gate의 해제는 운영 env toggle이나 artifact 수동 수정으로 수행하지 않으며, canonical handoff 시각 인과성, exact enrollment의 first-apply/R6 transitive receipt, 재기동 PREOPEN 재검증, rollback/post-apply attribution을 갖춘 별도 신규 family의 구현·리뷰·승인이 필요하다.

### Graceful bot restart

수동 또는 detector 복구로 봇 재기동이 필요한 경우 표준 경로는 `restart.flag` handoff다.

```bash
./restart.sh
```

이 스크립트는 `restart.flag`를 원자적으로 생성하고 `bot_main.py`의 기존 감지 루프가 자체 종료하도록 둔다. 이후 기존 PID 종료와 `src/run_bot.sh` supervisor가 올린 신규 PID를 제한시간 안에서 기다리고, 신규 PID에 대해 당일 `threshold_runtime_env_YYYY-MM-DD.env` handoff 검증 artifact까지 갱신한다. 실행 중인 PID의 `KORSTOCKSCAN_RUNTIME_LAUNCHER_RUN_BOT_SHA256`가 현재 `src/run_bot.sh`와 다르면 기존 child가 완전히 종료된 뒤에만 tmux `bot` supervisor를 교체한다. 이 경로는 장수 supervisor가 이전 launcher 함수나 env 정규화를 재사용하는 것을 막으며, 기존 child가 살아 있는 동안 두 번째 봇을 시작하지 않는다. 소스 변경을 반영하는 재기동은 review gate와 targeted validation을 닫고 로컬 커밋을 만든 뒤 수행해 신규 프로세스의 `KORSTOCKSCAN_RUNTIME_GIT_COMMIT`과 launcher commit/hash가 실제 로드 소스와 일치하고 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`가 되게 한다. PID handoff verify가 실패하면 `restart.sh`도 실패로 종료하며 완료로 간주하지 않는다. `pkill -9`, 직접 `nohup python src/engine/kiwoom_sniper_v2.py`, 텔레그램 매니저 별도 중복 기동, provider/threshold/order env hot mutation은 금지한다. 재시작 후에는 새 `bot_main.py` PID, `logs/bot_history.log`, heartbeat, Kiwoom WS/REST 회복, `/proc/<pid>/environ`의 commit/source-dirty와 당일 runtime env 반영 여부, verify artifact의 `status=pass`를 확인한다.

### Scanner deadline scheduler 단계별 적용

Scanner queue starvation 개선은 startup-only mode로 적용한다.

- 1단계 `scanner_deadline_scheduler_v1`은 `KORSTOCKSCAN_SCANNER_SCHEDULER_MODE=deadline_v1`과 `KORSTOCKSCAN_SCANNER_SCHEDULER_VENUES=KRX,PREMARKET_KRX_LIKE,NXT`를 함께 사용한다. callback은 immutable promotion envelope만 inbox에 기록하고 `ACTIVE_TARGETS` attach/refresh와 generation 등록은 main runtime이 수행한다.
- deadline mode에서는 `order/receipt -> WS-only fast precheck -> real holding -> REST recovery -> heavy evaluation` 순서와 각 lane deadline을 사용한다. 기존 promotion-age `queue_lag`와 full-eval count/pressure는 parser archive/legacy rollback surface이며 watch eviction 또는 heavy-eval dispatch 권한을 갖지 않는다.
- KRX, `PREMARKET_KRX_LIKE`, NXT는 동일 scheduler 구조를 사용하지만 attribution, p95/max, source-quality 제외와 rollback은 venue별로 분리한다. canonical venue가 없거나 충돌한 generation은 성과 판정에서 제외하고 다른 venue로 보간하지 않는다.
- 재기동 전 review gate, targeted tests, compile, clean-baseline replay와 16-symbol stress가 통과해야 한다. 재기동은 별도 operator 승인 후 위의 graceful path만 사용하며 실행 중 mode/env hot mutation은 금지한다.
- 1단계 acceptance는 유효 generation `attach_to_first_precheck_sec p95<=7`, `max<=10`, fast precheck가 blocking heavy job 둘보다 더 뒤로 밀리지 않는 것이다. 한 번의 `PREMARKET_KRX_LIKE -> KRX -> NXT` 전체 운영주기에서 order/receipt 및 fast-exit cadence 비악화도 확인한다.
- 2단계 `scanner_async_eval_commit_v1`/`async_v1`은 1단계 전체 운영주기 attribution과 별도 구현·리뷰·승인을 닫은 뒤에만 startup mode로 활성화한다. async worker는 immutable market-data/AI preparation만 수행하고, main thread는 generation·venue/source·fresh quote·position/pending·cooldown 및 기존 broker guard 재검증 후 기존 submit owner를 호출한다. 동일 generation의 heavy recheck는 async transport가 pending/COMMIT-ready인 동안 coalesce하며, current/BBO/strength/누적거래량의 일반 틱 변화도 최소 15초 재시도 창을 우회하지 못한다. 새 scanner promotion은 새 generation을 만들고 평가 cadence를 초기화하므로 즉시 평가할 수 있으며, COMMIT·RECOVERY lane과 stale/conflict 및 broker safety 우선순위는 이 제한의 영향을 받지 않는다. COMMIT dispatch deadline은 worker 완료 시각이 아니라 main-thread result handoff부터 계산하며, worker 완료→commit 지연은 별도 attribution으로 유지한다. 미승인 `async_v1` 요청은 `deadline_v1`으로 fail-closed 처리한다.
- rollback은 신규 scanner work commit을 중단하고 pending scheduler result를 폐기한 뒤 broker snapshot/reconciliation을 수행한다. 2단계는 `async_v1 -> deadline_v1`, 1단계는 `deadline_v1 -> legacy`로만 되돌린다. stale/superseded broker 도달, 동일 generation 중복 submit, hard exit/receipt 지연, 가격·수량 불변식 위반, venue 혼입 또는 provider/failback 계약 위반은 즉시 rollback 조건이다.

Replay는 다음 read-only 명령으로 실행한다. 결과의 `decision_authority=diagnostic_replay_only_no_runtime_activation`을 유지하며 결손 venue·attach action·promotion ID는 보간하지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.scanner_scheduler_replay
```

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

장후 `one_share_threshold_opportunity`의 probe 귀속은 정상 잔량 제출을 `residual_submitted` 이벤트에서, 잔량 미제출 종결을 `entry_split_probe_terminal_outcome=residual_not_submitted`에서 record lineage로 결합한다. terminal outcome 도입 전 artifact는 `residual_blocked`, `entry_split_probe_phase=aborted`, residual submit 미관측이 동시에 성립할 때만 `legacy_aborted_phase_fallback`으로 복원하고 source count를 별도 공개한다. probe-first submit 표본이 없으면 `no_natural_sample`, split provenance 또는 두 종결 원천이 빠지면 `instrumentation_gap`, 모든 표본이 종결되면 `observed`로 판정한다. clean-baseline 누적 집계와 `probe_to_residual_by_entry_date`/`target_date_probe_to_residual`을 함께 내보내 계측 도입 전 과거 결손과 당일 신규 표본을 분리한다. 이 집계는 source-only 실행 품질 귀속이며 threshold/runtime/provider/order guard 변경 권한이 없다.

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

1. `logs/threshold_cycle_preopen_cron.log`에서 preopen apply `[DONE]` marker와 runtime env 생성 여부를 확인한다. 동시에 `data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_YYYY-MM-DD.status.json`의 `status=succeeded`, `apply_plan_path`, `runtime_env_path`, `runtime_env_manifest_path`, `apply_plan_exists`, `runtime_env_exists`, `runtime_env_manifest_exists`를 확인한다. `reason=operator_runtime_env_lock_preserved_missing_source_report`는 canonical source report는 없지만 explicit operator runtime env lock으로 live runtime env handoff가 성립한 예외 성공이다. lock busy나 command fail이 exit 0 로그처럼 지나가도 status artifact가 `skipped|failed|running`이면 apply 완료로 보지 않는다. 선택된 entry/scale-in split policy의 실제 파일 schema·version·freshness·`runtime_apply_allowed`·refresh evidence가 handoff 작성 직전 preflight에서 불일치하면 해당 family만 `runtime_policy_preflight_failed:*`로 제외하고, 검증 불가 policy를 이전 값으로 암묵 복원하거나 강제 적용하지 않는다.
2. `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json`에서 스윙 추천 생성/empty/fallback diagnostic 분리를 확인한다. detector 기준 완료 marker는 `final_ensemble_scanner target_date=YYYY-MM-DD`가 포함된 `[DONE]` 로그다.
3. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`에서 selected family와 blocked family를 본다.
4. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`이 있으면 `runtime_change=true` family와 env key를 확인한다. 파일이 없으면 apply plan의 `blocked_reason`을 읽고 `warning` 또는 `fail`로 분류한다.
5. `src/run_bot.sh` 기동 로그에서 당일 runtime env 파일 source 여부를 확인한다. 봇 기동 시각이 env 생성 시각보다 빠르면 `pre_env_boot_gap=true`로 보고, env 생성 후 재기동 또는 `run_bot.sh` 대기 동작이 있었는지 확인한다. PREOPEN artifact는 local `data/threshold_cycle/**`의 apply/env/runtime manifest만 기동 authority로 사용한다.
6. apply plan의 `swing_runtime_approval` 섹션에서 `requested`, `approved`, `blocked`, `selected`, `dry_run_forced`를 확인한다. `dry_run_auto_apply_ready`는 parsed AI Tier2 contract가 있어야 통과하며, `approval_required`는 final-stage 사용자 승인 artifact 없으면 정상 차단이다. Final full-live approval 밖의 과거 실주문 요청/산출물은 env override를 생성하지 않아야 한다.
7. 스윙 approved env가 있더라도 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 runtime env에 포함되어야 한다. 장전에는 주문 guard를 완화하거나 `SWING_LIVE_ORDER_DRY_RUN_ENABLED`를 임의로 끄지 않는다.
8. apply plan의 `runtime_apply_bridge` 또는 blocked reason에서 bridge 후보 상태를 확인한다. scale-in 또는 complete-lifecycle bridge는 `bridge_candidate_state=live_auto_apply_ready`, `allowed_runtime_apply=true`, target env mapping, runtime hook/provenance mapping, parsed AI Tier2 review가 모두 맞는 후보만 selected될 수 있다. `ai_two_pass_review_status`가 `parsed`가 아니면 pre-final live-auto는 fail-closed 차단하고 다음 postclose review로 넘긴다. `bootstrap_pending`, `blocked_source_quality`, `blocked_rolling_conflict`, `runtime_blocked_contract_gap`, `code_patch_required`, 명시적 AI contract/safety block은 env 미생성이 정상이다.
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
6. 패닉셀 급변 구간은 `panic_sell_defense_report`로 `panic_state`, broker-order identity로 중복 제거한 stop-loss cluster, active sim/probe 회복률, post-sell rebound를 분리 확인한다. `PANIC_SELL`만 패닉 시작 상태이며 `RECOVERY_WATCH`와 단일시장 약세는 별도 `market_weakness` 관찰 owner다. 시장 약세는 KOSPI·KOSDAQ과 최소 3개 업종 row가 갖춰진 `BROAD_WEAKNESS|SINGLE_MARKET_WEAKNESS` 고유 snapshot 2회 연속으로 활성화하고, `release_margin.passed=true`인 `RECOVERY_EVIDENCE` 3회 연속으로만 해제한다. 60초 미만 재관찰, `NORMAL` 또는 약세 임계치 바로 위의 `NEAR_WEAKNESS_BOUNDARY`만으로 해제하지 않는다. producer/notifier/attribution은 `report_only_no_mutation`이다. 별도 `WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2` consumer만 사용자 승인 범위에서 위젯·에피소드의 신규·추가 BUY를 listing-market별로 차단하고 해제 후 신호를 재평가한다. 같은 consumer가 당일 exact owner 주문번호, 같은 listing market, broker-confirmed current remaining quantity를 모두 확인한 BUY만 잔량 취소하며 부분체결 수량과 보유는 유지한다. 수동·main bot·다른 owner 주문, SELL/target, 보유·수량 resize·가격, score/stop threshold, 자동매도, 봇 재기동, 스윙 실주문 전환 권한은 없다.
7. `RUNTIME_OPS`, snapshot failure, model call timeout, 주문 receipt/provenance 손상이 있으면 전략 threshold 문제가 아니라 운영 장애로 분류한다.
8. safety breach가 아니라 목표 미달이면 rollback이 아니라 postclose calibration 입력으로 넘긴다.

`12:05` threshold-cycle intraday calibration cron은 운영 대상이 아니다. next-preopen apply의 authoritative source는 전일 postclose artifact이며, intraday phase artifact는 명시 수동 forensic run이 있을 때만 생성할 수 있고 cron completion/장중 runbook 필수 확인 대상이 아니다.

표준 확인 명령:

```bash
tail -n 80 logs/run_buy_funnel_sentinel_cron.log
tail -n 80 logs/run_holding_exit_sentinel_cron.log
tail -n 80 logs/run_panic_sell_defense_cron.log
ls -l data/pipeline_events/pipeline_events_$(TZ=Asia/Seoul date +%F).jsonl
ls -l data/threshold_cycle/threshold_events_$(TZ=Asia/Seoul date +%F).jsonl
PYTHONPATH=. .venv/bin/python -m src.engine.panic_sell_defense_report --date $(TZ=Asia/Seoul date +%F) --print-json
bash deploy/run_error_detection.sh full
ls -l data/report/panic_sell_defense/panic_sell_defense_$(TZ=Asia/Seoul date +%F).json
```

## 장후 확인 절차

`build_codex_daily_workorder --slot POSTCLOSE`는 이 절차를 `PostcloseAutomationHealthCheckYYYYMMDD`로 자동 포함한다. 이 항목은 날짜별 개별 구현 backlog가 아니라 `Runbook 운영 확인` 큐다. 20:10 postclose wrapper 이후 자동 감시 범위는 병렬 기동된 `postclose_done_controller` completion, 20:05 EOD 데이터 갱신, 20:50/21:00 보관/로그 정리, 21:55 detector final window까지이며, `codex_workorder_runner`는 사용자 지시 또는 수동 opt-in 실행 결과가 있을 때만 별도 확인한다.

POSTCLOSE 최상위 감리는 `Tuning Chain Control State`(튜닝 체인 관제 상태)로 남긴다. 이 관제 상태는 EV 손익의 좋고 나쁨이 아니라 자동화체인이 매일 믿을 수 있게 수집, 분석, 해석, 라우팅, 반영, 피드백, DONE controller recovery까지 이어졌는지 보는 운영 판정이다. 새 리포트나 새 checklist 항목을 만들지 않고, 기존 `PostcloseAutomationHealthCheckYYYYMMDD` 실행 메모에 `상태 / 막힌 단계 / 영향 / 조치` 4요소만 기록한다.

## 20:05 데이터 갱신 확인 절차

`update_kospi.py`는 매매 runtime과 분리된 EOD 데이터 체인이다. DB 적재와 recommendation은 기본 경로이며, swing daily reports와 bottom-rebound sim 후속 체인은 `KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE=true`일 때만 실행한다. OFF 상태에서는 두 step을 `skipped_disabled`, `runtime_effect=false`로 status JSON에 남긴다.

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

2026-07-31 이후 workorder는 `duplicate_order_warnings=[]`, selected order ID 유일성, 그리고 open root-cause order마다 완전한 `root_cause_followup_contract`를 필수로 한다. 계약에는 `root_cause_signal`, `acceptance_test`, `next_repair_action`, `closure_requires_new_evidence=true`, `implementation_only_closure_allowed=false`가 있어야 한다. 선언 누락, summary/실제 order count 불일치, ID 충돌 또는 계약 결손은 `threshold_cycle_postclose_verification` fail 사유이며 최종 DONE 전에 보완·재생성해야 한다.

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

- report/instrumentation order: 다음 `20:10` postclose report와 daily EV에서 source freshness, sample count, warning 감소를 확인한다.
- existing family input 보강: 다음 `20:10` postclose calibration에서 해당 family의 `calibration_state` 변화를 확인한다.
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
- `baseline_v1`은 prompt baseline이 아니라 legacy proxy 기반 보호용 input-preflight 정책이다. `exact_v2`는 exact snapshot, venue/session, route, payload provenance가 신뢰 가능한지를 판정하는 입력 계약이다. 두 이름을 prompt version으로 사용하지 않는다.
- 다중분봉 문맥의 runtime payload 소유자는 entry-side `entry_candle_context_v1`과 holding/scale-in/exit/overnight-side `holding_decision_context_v1`이다. 두 schema는 같은 venue/session-normalized candle source와 `input_bundle_version=scalping_multi_timeframe_context_v1` 파생 feature를 공유한다. `scalping_multi_timeframe_context_v1`을 세 번째 병렬 model payload로 만들거나 entry context를 holding prompt에 재사용하지 않는다.
- 다중분봉 문맥이 PREMARKET 검증 후 전 장에 전면 적용되면 두 context family의 master, PREMARKET/KRX/NXT cohort, holding stage keys를 한 promotion transaction으로 모두 활성화한다. 이후 별도 session/stage/endpoint 승격 gate를 두지 않는다. 현행 stage별 prompt, model, provider route를 그대로 유지하고 두 canonical context schema와 shared `input_bundle_version=scalping_multi_timeframe_context_v1`을 새 control 입력 기준선으로 고정한다. 전면 적용 전 payload와 `baseline_v1` proxy 행은 원인 탐색에는 사용할 수 있지만 신규 control의 primary paired cohort와 합산하지 않는다.
- AI 입력 외부검증의 KRX 일봉 primary는 인증형 KRX Open API `stk_bydd_trd`/`ksq_bydd_trd`이며 request header의 `AUTH_KEY`에만 인증값을 넣는다. 해석 우선순위는 `KRX_OPEN_API_AUTH_KEY` 환경변수, `KRX_OPEN_API_KEY` 환경변수, `data/config_prod.json`의 같은 두 키 순서다. 키·인증 헤더는 trace/report에 저장하지 않고 출처명과 설정 여부만 남긴다. 두 endpoint가 모두 401/403이면 `krx_open_api_unauthorized`로 기록하며, Data Marketplace에서 인증키 발급뿐 아니라 각 주식 일별매매정보 서비스 활용승인이 완료됐는지 운영자가 확인한다. 세션 의존 MDC `getJsonData.cmd`는 `HTTP 400 LOGOUT`을 정상적인 데이터 부재나 값 불일치로 해석하지 않고 기본 호출 경로에서 제외한다. Open API 키가 없거나 endpoint가 unavailable이면 Naver 일봉 OHLC만 secondary로 비교하고 일봉 volume은 `NOT_COMPARABLE`; KRX/NXT 단독 basis가 아닌 값은 venue별 strict match에 쓰지 않는다.
- 실제 판단 개선은 별도 `decision_quality_v1` offline chain이 소유한다. 순서는 `exact trace/payload -> mature stage/venue outcome -> control error taxonomy -> stage Prompt V2 -> identical-payload control/candidate paired replay -> review -> stage-level runtime candidate -> post-apply attribution`이다. outcome label은 prompt 입력에 넣지 않고 평가 join에만 사용한다.
- `decision_quality_v1` primary cohort는 `replay_exact=true`, `request_capture_status=captured`, `preflight_mode=exact_v2`, 동일 canonical context schema, 동일 `input_bundle_version`, 동일 eligible trace ID/payload hash, mature horizon, fresh conflict-free source를 요구한다. Primary baseline horizon은 entry/entry-price/post-probe `10m`, scale-in `20m`, holding/exit `30m`, overnight `60m`로 고정해 서로 다른 성숙 구간을 같은 stage bucket에 섞지 않는다. Entry 후보는 `entry_candle_context_v1`, holding/exit 후보는 `holding_decision_context_v1` 내부에서 각각 control과 paired replay하며 서로 합치지 않는다. Control과 candidate는 같은 provider/model/temperature/reasoning budget을 사용한다. AI 호출·parse 성공률은 운영 지표이며, 승격 판단은 stage·venue·session별 `source_quality_adjusted_ev_pct`, missed-upside, adverse-first BUY, loss tail, exit giveback을 사용한다. Net profit과 scale-in add/no-add incremental EV는 notional·fill counterfactual join이 완료되기 전에는 `not_available`로 유지한다.
- 일일 Control은 endpoint별 최신 eligible Exact V2의 `prompt_version + prompt_sha256 + response schema + provider + model + temperature + reasoning effort` 전체 서명을 고정한다. 같은 버전명 아래 hash가 바뀐 이전 자연호출은 conflict로 당일 전체를 버리지 않고 `control_signature_not_selected`로 제외한다. 명시적으로 버전만 고정한 수동 control 명령은 서로 다른 hash가 남으면 계속 conflict로 닫는다.
- `decision_quality_v2_10_bounded_opportunity`는 offline entry paired replay 전용이다. Candidate BUY는 full-entry나 주문이 아니라 기존 submit guard 앞의 counterfactual 1주 passive-probe 노출이다. fresh/route-consistent source, normal 또는 fresh observable-wide spread, 독립 edge fact, non-blocking low/moderate/high risk와 비용후 reward/risk `>=1.00`을 요구한다. `high`를 낮춰 쓰지 않으며 `blocking`, unavailable/extreme spread, source unusable, stale/conflict, venue/session mismatch는 차단한다. Control의 live `entry_probe_intent=true`도 같은 exposure와 conservative cost로 계산해 후보 개선폭을 과대평가하지 않는다. Candidate exposure 0건 또는 missed-upside 감소 0건이면 위험회피로 EV가 개선돼도 quality gate는 통과하지 않는다.
- `decision_quality_v2_11_clean_continuation_probe`는 V2.10의 fail-closed blocker를 유지하면서 fresh dual source, normal spread, completed 3/5/10분 양수, structural edge, 얕은 drawdown, reference reclaim, 독립 precursor와 낮은 실행비용이 함께 있는 좁은 cohort만 비용후 reward/risk `>=0.75`의 offline 1주 passive-probe로 재평가한다. 모델이 정직하게 WAIT/DROP하면 schema reject나 BUY 강제로 처리하지 않고 clean cohort no-exposure coverage와 missed opportunity에 귀속한다. Cohort EV, Candidate 노출 EV, 노출률, adverse-first를 함께 보고하며 이 산출물에는 live prompt·threshold·주문 권한이 없다.
- 과거 target date의 retained forward-price window만으로 기존 mature cohort가 재현되지 않을 때는 detailed offline replay에서만 `--outcome-recovery-report PATH`를 명시할 수 있다. Source는 동일 날짜·trace·exact payload hash·venue/session, route-qualified Kiwoom completed-1m PASS, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 모두 충족해야 한다. 복구 경로는 primary outcome 요약만 재사용하고 source report path/hash, 대체된 현재 label 수, metric conflict 수를 남긴다. Exact payload나 candidate 응답을 과거 report에서 재구성하거나 일일 primary label artifact가 복구됐다고 간주하지 않는다.
- PREMARKET 전면 승격은 `src.engine.automation.ai_multi_timeframe_context_promotion --mode evaluate`의 fail-closed 판정과 리뷰 artifact를 먼저 확인한다. 판정 증거는 당일 NXT PREMARKET 고정 표본 exact payload/core endpoint와 지정 KRX 골든일의 source match를 분리하며, 당일 KRX 정규장 exact/source는 09:20부터 post-apply 필수 검증한다. 리뷰 artifact의 `reviewed_source_hash`는 승격 모듈과 실제 context producer/consumer 소스의 현재 결합 해시와 일치해야 하며, 소스가 바뀌면 재리뷰 전까지 차단한다. 같은 명령의 `--mode apply`가 runtime env/manifest를 원자 갱신한 뒤 hash-verified promotion commit marker를 마지막에 기록한다. 실행 중 프로세스는 이 marker를 context hook에서 읽을 수 있으므로 승격을 위해 bot restart를 요구하지 않는다. 첫 자연 호출은 `--mode observe`로 점검하고, 신규 문맥 결함 또는 09:20 이후 당일 KRX 검증 실패 시 `--mode rollback`으로 multi-timeframe context 키만 비활성화하며 주문·threshold·provider·bot·hard safety 값은 유지한다.
- 표준 장후 경로는 `src.engine.scalping.ai_decision_quality --date YYYY-MM-DD --mode postclose --write`를 한 번 실행해 `control -> mature -> baseline -> paired request preparation`을 같은 원천 읽기에서 순서대로 생성하고 각 산출물을 원자 기록한다. 개별 `control|mature|baseline|paired` mode는 수동 진단·복구용으로 유지한다. Eligible exact mature 표본은 1건부터 cumulative learning과 paired request 준비에 넣고, runtime 후보 승격에 필요한 다중 row/symbol floor는 `promotion_evidence_floor`로 별도 유지한다. `paired`는 exact payload와 stage Prompt V2 offline 요청을 준비할 뿐 live prompt를 교체하거나 candidate API를 호출하지 않는다. Candidate API 실행은 `--execute-candidate`를 명시한 별도 offline runner에서만 같은 provider/model/temperature/reasoning budget으로 수행하고, 결과 리뷰 전 runtime 권한은 계속 false다. 산출물 생성 성공은 판단품질 성과가 아니다. 목적은 모든 위험을 제거해 비노출을 최대화하는 것이 아니라 감당 가능한 위험에서 positive edge 탐색을 늘리고 one-share probe, fresh submit guard, post-probe resolver, holding/exit 및 hard-safety와 결합해 누적 수익을 높이는 것이다. 성과는 missed-upside 감소, adverse-first 비증가, exposure EV 및 notional/fill join 이후 순이익으로 판정한다.

- 표준 Exact-V2 산출 직후에는 기본 `THRESHOLD_CYCLE_RUN_MAIN_AI_QUALITY_R0_R3=true`가 `src.engine.scalping.micro_reversion.ai_quality_cycle --date YYYY-MM-DD --write`를 실행한다. 순서는 source-quality preflight -> effective-dated economic source owner -> reviewed broker fee/tax/symbol resolution -> prepared request -> past-only micro bridge -> source bundle -> A/B/C materialization -> action-neutral label -> bounded offline Provider replay -> exact-ID main lifecycle -> rolling R2/R3 source-only manifest다. `2026-08-18`부터 source owner는 `data/config/micro_reversion_economic_policy.json`을 읽고 공식 KIS KOSPI/KOSDAQ master ZIP을 당일 다시 받아 원문·내부 member SHA-256/size를 보존한다. 공식 master의 `증권그룹구분코드=ST(주권)`와 `우선주구분코드=0(보통주)`를 모두 만족하는 6자리 종목만 평가하며 ETF·ETN·REIT·우선주·DR·외국주권과 비표준 코드는 제외한다. 매수·매도 수수료는 각각 1.5bps, 매도 세금은 20bps, 불확실성 가산은 0bps다. raw source bytes SHA-256·size·effective window·scope·authority가 하나라도 맞지 않으면 durable blocked artifact를 남기고 호출하지 않는다. 종목명/코드 패턴 기반 상품유형 추정과 수동 `verified=true`는 금지한다.
- Forward collector의 0B 관찰·0D depth ingress queue 기본값은 각각 50,000건이다. bounded queue full/drop은 worker·writer·storage·authority failure와 구분한다. queue loss는 collector 전체를 장중 영구 종료하지 않고 이후 clean window 수집을 계속하지만, 현재 canary receipt가 손실 scope를 exact symbol·venue·session·epoch로 특정하지 못하므로 그 날짜의 Provider replay/promotion은 fail closed한다. worker/writer/storage 오류, liveness mismatch, authority 누출, latency guard 위반은 기존처럼 즉시 observer auto-stop이다. 장중 조기 stop과 row-exclusion canary도 exact-date daily archive에 `diagnostic_only=true`, `promotion_evidence_eligible=false`로 보존한다. R0→R3 cycle은 exact-date canary와 bridge/lifecycle census를 결합해 `past_market_row_missing`, integrated-route proof, broker execution provenance를 각각 blocker 및 source-only workorder로 표면화한다. Queue loss가 전혀 없는 날짜 또는 향후 exact scoped exclusion receipt가 구현된 범위만 Provider replay에 들어갈 수 있다.
- Provider replay 기본 상한은 `THRESHOLD_CYCLE_MAIN_AI_QUALITY_PARENT_CAP=130`, `THRESHOLD_CYCLE_MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP=390`, `THRESHOLD_CYCLE_MAIN_AI_QUALITY_DAILY_USD_CAP=1.0`이다. 근거는 `2026-08-10~2026-08-14` 메인 봇의 평가 완료 호출 `[676,369,781,1113,999]`, 중앙값 781회이며 A/B/C 논리 요청 최대 390회는 중앙값의 약 49.94%다. OpenAI/Bedrock 단가는 operator-reviewed accounting 기준으로 input/output 모두 USD 0이며, USD cap보다 390회 attempt cap이 실제 circuit breaker다. request bound는 A/B/C 한 parent를 원자 단위로 선택하며 한두 arm만 실행하지 않는다. 각 correction/schema attempt는 KST 일일 append-only ledger에 먼저 예약한다. OpenAI SDK retry와 budgeted Bedrock key rotation은 0이며, Bedrock 내부 key 재시도도 별도 예약 없이는 실행되지 않는다. timeout/transport/usage 결손은 환불하지 않고 attempt를 유지한다. 재시도로 인해 A/B/C가 완성되지 않은 parent는 checkpoint resume evidence로만 남고 R2/R3에는 들어가지 않는다. cap exhaustion, partial result, provider provenance 실패는 execution complete가 아니며 wrapper에 warning을 남긴다. `THRESHOLD_CYCLE_MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY=false`로 Provider 호출만 중지해도 source bundle/materialization/lifecycle/R2-R3 관찰은 유지된다.
- `main_lifecycle_paired`는 `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl[.gz]` base와 자정 경계 이후의 immutable overlay `pipeline_events_YYYY-MM-DD.late.jsonl[.gz]`를 logical-partition shared lock 아래 결정적으로 한 번씩 streaming scan하고 explicit `main_lifecycle_id + record_id + stock_code + scanner attempt_id`가 있는 allowlisted transition만 연결한다. byte-identical gzip/plain crash pair는 한 번만 census하고, 내용이 다른 legacy rollover pair는 모두 읽는다. late overlay는 paired source-only evidence owner이며 generic parquet/archive consumer가 자동으로 읽는다고 간주하지 않는다. scanner/entry/submit/fill/holding/scale-in/exit 중 하나라도 missing이거나 final exit가 broker-reconciled가 아니면 promotion evidence에서 제외한다. 체결 row는 공식 Kiwoom WebSocket type `00`의 원문 FID `9203/9001/913/900/902/903/905/907/908/909/910/911/914/915/2134/2135/2136`과 raw-envelope marker를 normalized custody 값과 별도로 보존한다. 이 source-only 원문은 lifecycle evidence에만 전달되며 주문·보유·청산 판단에는 사용하지 않는다. type `00` marker가 없거나 raw FID가 누락·변형·충돌하면 custody는 기존 normalized receipt 경로를 유지하되 해당 execution row만 promotion evidence에서 fail closed한다. 매 receipt마다 raw slot 전체를 교체해 이전 체결과 현재 체결을 혼합한 proof를 만들지 않는다. 거래빈도는 실제 session exposure, holding duration은 first fill부터 reconciled final exit, 자본시간은 실제 open notional 적분을 사용한다. 1표본을 3600건/시간으로 환산하거나 label horizon을 실제 보유시간으로 쓰지 않는다.
- Main/S15 SELL 취소는 `kt10003` 호출 전에 exact SELL generation·context hash·원주문번호에 결속된 cancel intent를 common pending journal에 fsync한다. S15 stop cancel의 crash-retry marker도 같은 세 값에 결속한다. 재기동 시 strict `ka10075`가 단 하나의 exact open SELL을 code/order/requested quantity/remaining quantity/route로 확인할 때만 최대 1회 재호출하고, 주문 부재와 durable intent/ACK가 함께 있으면 재호출 없이 common terminal proof로 넘긴다. `kt00007`/`ka10075`가 일치하지 않는 blank order binding, `kt00009` 상태문자 추정, 단일 venue 잔고, generation/context drift는 모두 no-call `RECOVERY_REQUIRED`다. 자연 acceptance는 review된 clean commit을 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`로 기동한 다음 표본만 인정하며, 테스트를 위해 주문·취소·재기동을 만들지 않는다.
- R0→R3 producer 자체는 source-only에서 끝난다. `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`이며 R3 산출물만으로 prompt/runtime/order를 바꾸지 않는다. 기존에 별도 등록된 `main_ai_quality_entry_prompt_contract_v1` family와 standing matcher는 exact `tuning_axis=prompt_contract_effect`만 소비한다. 이번 A/B/C가 생성하는 `tuning_axis=prompt_contract_effect_on_ask_depletion_context`는 별개의 조건부 단일축이므로 기존 family 이름이나 standing intent로 매핑하지 않으며 operator decision receipt, generic approval handoff, PREOPEN activation/apply receipt를 자동 생성하지 않는다. 이 신규 축은 reviewed bounded registry entry, exact candidate-bound standing approval, same-stage conflict guard, PREOPEN consumer와 rollback/post-apply attribution 계약이 별도로 구현·리뷰되기 전까지 source-only blocker 상태다. 그 전에는 live selector의 `hot_v1 -> decision_quality_v2_6` 전환 경로에 들어가지 않는다. 기존 family 역시 provider/model, order price/quantity, threshold/cap, bot, broker/account/order/cooldown, hard/protect/emergency safety를 바꾸거나 주문을 제출하지 않는다.
- 과거 `prompt_contract_effect` family에 계산했던 `2026-09-14` 최초 후보·`2026-09-15` 최초 적용 예상일과 `2026-10-16T09:30+09:00` one-shot standing-intent 만료는 신규 ask-depletion 조건부 축의 적용 일정이나 승인으로 재사용하지 않는다. 신규 축의 첫 runtime 적용일은 아직 정해지지 않았으며, clean common-parent 5/10/20일 floor와 A→B 비열화 방지·A→C EV/tail gate를 통과한 exact R3 후보가 생긴 뒤 별도 registry/standing approval 및 다음 exact-date PREOPEN handoff가 닫혀야 정할 수 있다. 최초 apply receipt만으로 auto-chain enrollment를 열지 않고 post-apply complete lifecycle·positive cost-adjusted EV·p10/severe-tail·HELD/unresolved continuation gate를 모두 재검증해야 하며, 실패 시 configured prompt를 유지한다.
- V2.14 setup-risk의 full-day candidate 실행은 21:05 KST 별도 runner `deploy/run_ai_entry_setup_paired_replay_postclose.sh`가 소유한다. 이 runner는 main postclose controller의 target-date `succeeded`를 최대 12시간 기다린다. 대기 중 `failed/error/blocked/missing`은 tail-repair로 복구 가능한 중간 상태이며 즉시 종료하지 않는다. 12시간 안에 `succeeded`가 되면 60분 outcome 성숙을 확인한 뒤 KRX 정규장과 NXT 애프터마켓을 분리하고, 끝까지 복구되지 않으면 `blocked_predecessor_timeout`으로 종료한다. 고정 runner의 bounded wait보다 predecessor tail-repair가 늦게 끝나는 경우를 위해 `deploy/run_postclose_done_controller.sh`는 target-date 21:05 이후 controller 성공 직후 같은 runner를 fail-fast follower로 다시 호출한다. 이미 `completed_offline_only` batch가 있고 KRX candidate reference가 있으면 source date, status, candidate 본문 재계산 self-hash, batch reference artifact hash와 candidate 파일을 함께 검증한 뒤 중복 Provider 실행 없이 건너뛴다. follower가 0으로 끝났는데 terminal batch가 없으면 controller wrapper는 DONE을 출력하지 않고 fail-closed한다. 각 cohort는 outcome을 읽지 않는 symbol round-robin 방식으로 신규 candidate를 최대 30건 실행한다. 전체 eligible 수가 잔여 cap 이하이면 `complete_eligible_census`를 허용하되 `deferred=0`, `selected=eligible`, `distinct<=cap`, outcome-blind 계약을 모두 검증한다. 결과가 있는 요청만 checkpoint report에 넣어 일부 실행을 `missing result` 결함으로 오판하지 않는다. Transient provider/schema 실패는 이미 검증된 결과 checkpoint를 재사용해 기본 2회까지만 재시도한다. OpenAI key/provider preflight 실패나 `provider=none`, schema/selection contract 결손은 fail-closed이다.
- V2.14의 누적 승격 표본은 candidate exposure 10건/3종목이다. 준비 요청 30건/10종목 floor와 혼합하지 않는다. 승격 판단은 positive cost-adjusted exposure EV, net missed-upside **value**, 완전한 execution-cost provenance, bounded probe risk budget을 함께 사용한다. missed-upside 건수는 진단값으로만 남겨 작은 기회 여러 건의 포기 때문에 더 큰 순기회 회복이 기계적으로 차단되지 않게 한다. KRX gate가 통과하면 batch가 다음 KRX 거래일 candidate를 자동 생성하고, 07:35 PREOPEN이 원본 batch/detailed hash와 authority 계약을 재검증해 date-scoped activation을 기록한다. 이때 bot launcher와 같은 `threshold runtime env -> persistent operator override -> dated operator override` 순서로 파일을 비실행 파싱하고, 당일 runtime apply date와 configured V2.13/probe 계약을 검증한다. 같은 PID의 실시간 선택도 당일 runtime handoff, configured V2.13 owner, KRX 정규장 provenance, activation/candidate hash, WAIT-probe handoff, probe quantity 1, probe-first `DAILY|target_date`, post-probe resolver를 다시 확인한다. 하나라도 실패하거나 전일 PID가 당일 env 없이 남아 있으면 V2.13으로 자동 복귀한다. NXT는 자체 승격 gate 전까지 V2.13 control이다.
- 활성 V2.14는 AI risk 결과를 직접 BUY/점수 하드게이트로 쓰지 않는다. 결정론적 setup composer가 entry probe intent를 만들고, live adapter는 이를 기존 `WAIT + eligible_wait_probe` 경로에 고정 호환 prior로 전달한다. 따라서 one-share probe-first, fresh submit guard, post-probe reprice/residual 판단, holding/exit, account/order/quantity/cooldown, hard/protect/emergency guard는 그대로 유지된다. provider/model, entry price, 주문 수량·cap, broker guard, bot state, NXT prompt, exit owner는 바꾸지 않는다. 운영자가 `KORSTOCKSCAN_ENTRY_SETUP_V2_14_KRX_CANARY_ENABLED=false`를 명시하면 다음 호출부터 V2.13 fallback이다.
- Prompt V2는 stage별로 분리하고 `edge_state=EDGE|NO_EDGE|INSUFFICIENT_DATA`, 예상 상승·하락폭, `trend/liquidity/tape/risk/uncertainty` 구조화 근거와 canonical reason codes를 반환한다. Candidate replay는 `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다. 입력 bundle 전면 적용과 Prompt V2 runtime 승격은 별도 판단이며, Prompt V2는 한 stage/version 변경으로 귀속한 뒤 적용한다.

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
