# Time-Based Operations Runbook

작성 기준: `2026-05-21 KST`
목적: 장전, 장중, 장후 자동화 체인의 시간대별 실행 주체, 산출물, 운영 확인 기준을 한 장으로 고정한다.

이 문서는 실행 절차 runbook이다. 튜닝 원칙과 active owner는 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 작업 소유권은 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 산출물 추적성은 [report-based-automation-traceability.md](./report-based-automation-traceability.md), threshold-cycle/apply/daily EV 공통 산출물 정의는 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)를 기준으로 한다. 이 공통 정의는 스캘핑과 스윙이 threshold-cycle, daily EV, code-improvement workorder 체인에 들어오는 부분에 적용한다. 스윙 전용 lifecycle 산출물은 이 runbook의 `15:45`/장후 확인 절차와 `swing_lifecycle_audit`, `swing_improvement_automation`, `swing_runtime_approval`, `swing_pattern_lab_automation` artifact 정의를 함께 기준으로 본다.

## 운영 원칙

- 기본 흐름은 무인 자동화다. 사람의 장전 승인 없이 `auto_bounded_live` guard를 통과한 threshold만 runtime env로 반영한다.
- 장중 threshold runtime mutation은 금지한다. 장중 산출물은 다음 장전 apply 후보 입력으로만 쓴다.
- AI correction은 수정안 제안 layer다. 최종 threshold state/value는 deterministic guard가 결정한다.
- `lifecycle_decision_matrix_runtime`은 ADM 확장 umbrella owner다. Entry ADM, Holding/Exit ADM, submit 관찰, scale-in bias adapter를 stage별 weighted ADM policy로 감싸지만 기본 OFF이며, selected될 때만 다음 PREOPEN runtime env에 policy file/version/promote cap을 쓴다. `entry_bucket_attribution`과 `scale_in_bucket_attribution`의 downstream 누락은 postclose verifier fail이다. hard safety, account/order/broker guard, stale quote, price freshness, stop, qty guard는 항상 matrix보다 우선한다.
- `runtime_apply_bridge`는 report/workorder/approval 후보와 실제 runtime env 사이의 연결 계약을 검증하는 중간 계층이다. 현재 구현 범위는 사용자가 선택한 `Entry+Scale full`이므로 LDM entry/scale-in bucket만 bridge 후보로 다룬다. 다른 bucket이 자동으로 추가 개발 대상이라는 뜻은 아니며, holding/exit, provider route, position sizing, panic 같은 bucket은 별도 owner, approval contract, env mapping, runtime hook, rollback/post-apply attribution이 새로 정의된 경우에만 bridge 확장 대상으로 본다. bridge report는 `runtime_effect=false`이며, `bridge_candidate_state=ready_for_approval`, `allowed_runtime_apply=true`, 등록된 approval contract, target env mapping, runtime hook, rollback/post-apply attribution이 모두 닫힌 뒤 별도 approval artifact가 있을 때만 다음 PREOPEN apply가 env 후보로 소비한다. `bootstrap_pending`, `blocked_source_quality`, `blocked_rolling_conflict`, artifact missing, unknown family는 정상 차단 상태이며 수동 env override로 해석하지 않는다.
- 기존 fixed threshold는 role contract로 재분류한다. broker submit/stale quote/price freshness/stop/account/order/qty/cooldown은 `hard_safety`, `BUY_SCORE_THRESHOLD`와 entry score cutoff/VPW/strength/momentum은 `baseline_prior`, latency caution/score65_74/soft stop/holding/scale-in price guard는 `bounded_tunable`, fallback/legacy latency/shadow 축은 `legacy_archive`다. score는 matrix feature일 뿐 score 단독 BUY/WAIT/DROP 확정 권한이 아니다.
- `latency_classifier_runtime_profile`은 제출 고갈(submit drought)의 primary tuning owner다. `latency_classifier_recommendation`의 `would_pass_events`는 런타임 `SAFE` 통과만 의미하고, `latency_fallback_deprecated`는 기본 runtime reject인 `CAUTION`으로 수집한다. recovery 후보는 `recommended_action=bounded_apply`와 `allowed_runtime_apply=true`일 때만 다음 PREOPEN 제한 카나리(bounded canary) env로 연결한다. `pre_submit_price_guard`는 후행 가격품질 guard이며 `latency_pass=0`의 primary owner로 쓰지 않는다.
- Pattern lab은 `code_improvement_order`와 `auto_family_candidate`만 생성한다. runtime/code를 직접 변경하지 않는다. postclose chain에서 lab subprocess가 실패해도 후단 daily EV/workorder/runtime summary 생성을 보호하되, 실패 자체는 같은 checklist/runbook incident에 root cause, 재실행 결과, fresh 복구 여부를 남겨야 한다. `pattern_lab_currentness_audit`는 랩 코드/README/schema/source mode/stale-output 위험을 `runtime_effect=false` workorder 후보로 만들고, `pattern_lab_propagation_audit`는 lab automation -> code workorder -> threshold EV -> runtime summary 연결을 source-quality audit로만 검증한다.
- sim-first lifecycle은 새 독립 체인이 아니라 기존 threshold-cycle 자동화체인의 입력 범위 확장이다. 스캘핑과 스윙 모두 BUY/선정 가능 후보를 `selection -> entry -> holding -> scale_in -> exit -> attribution` 전주기 가상 관찰 대상으로 최대한 남기고, 실계좌 예수금 부족, 1주 cap, 현재 selected runtime family 여부, approval artifact 부재를 sim/probe 후보 생성 제외 사유로 쓰지 않는다.
- 스윙은 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True` 기본값에서 live 선정-진입-보유-추가매수-청산 로직을 실행하되 브로커 주문 접수만 차단한다. `SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True`이면 진입 전 block stage에서 `swing_probe_*` virtual holding을 생성해 live 보유 이후 데이터를 observe-only로 수집한다. `SWING_ENABLE_AVG_DOWN_SIMULATION=True`와 `SWING_SCALE_IN_DYNAMIC_QTY_ENABLED=True`는 dry-run/probe 안에서 AVG_DOWN/PYRAMID 후보와 `would_qty`/`effective_qty`를 남긴다. `swing_scale_in_real_canary_phase0`는 별도 approval artifact가 있을 때만 승인된 real swing holding의 AVG_DOWN/PYRAMID 추가매수 1주 주문을 허용하며, sim/probe/dry-run 포지션과 OFI/QI `RISK_BEARISH`/stale quote는 fail-closed로 차단한다. `swing_sim_*`/`swing_probe_*` stage와 `actual_order_submitted=false`는 실제 `order_bundle_submitted`/`sell_order_sent`와 분리해서 본다.
- 추가매수 arm은 공통 master gate와 arm별 gate를 분리해서 판정한다. `ENABLE_SCALE_IN=False`는 AVG_DOWN/PYRAMID를 모두 닫는 공통 차단이고, 스캘핑은 `REVERSAL_ADD_ENABLED`(AVG_DOWN)와 `SCALPING_ENABLE_PYRAMID`(PYRAMID), 스윙 sim/probe는 `SWING_ENABLE_AVG_DOWN_SIMULATION`(AVG_DOWN)와 `SWING_ENABLE_PYRAMID`(PYRAMID)로 한쪽 arm만 열 수 있다. 스윙 scale-in real canary는 별도 approval artifact의 `allowed_actions`와 `SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS`가 일치한 arm만 허용한다.
- 스윙 self-improvement는 `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` 전체 lifecycle을 대상으로 하며, DB load gap, OFI/QI, AI contract, AVG_DOWN/PYRAMID 관찰축은 report-only/proposal-only다.
- 스윙 runtime 반영은 `proposal -> approval_required -> approved_live(dry-run)`만 허용한다. `swing_runtime_approval`이 hard floor와 EV trade-off score로 승인 요청을 만들 수 있지만, `approval_required`만으로 env를 쓰지 않는다. 사용자가 approval artifact를 남긴 경우에만 다음 장전 preopen apply가 env를 생성하며, 이때도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`와 브로커 주문 차단은 유지한다.
- 스윙 1주 real canary는 별도 approval-required 축이다. 전체 dry-run 해제가 아니라 승인된 극소수 스윙 후보에만 실제 1주 BUY/SELL을 보내 broker execution 품질을 수집하는 경로이며, phase0에서는 추가매수/AVG_DOWN/PYRAMID 실주문을 열지 않는다.
- 스캘핑 simulator와 스윙 dry-run 성과는 `real`, `sim`, `combined`로 분리해 본다. `real`은 실제 브로커 주문이 접수된 포지션/체결, `sim`은 `actual_order_submitted=false`인 가상 체결, `combined`는 둘을 합친 calibration view다. sim/probe 수량은 기본 `SIM_VIRTUAL_BUDGET_KRW=10,000,000` 가상 주문가능금액과 실주문 동적수량 산식으로 계산하며 실계좌 주문가능금액과 분리한다. tuning 후보 산출에는 combined를 사용할 수 있지만, provenance와 execution-quality 평가는 real/sim을 절대 섞지 않는다.
- OFI/QI source-quality, DeepSeek data-quality, workorder lineage 같은 report-only 값은 자동화 체인의 입력으로 쓸 수 있다. 단, source-quality blocker나 workorder 생성 자체는 runtime mutation 권한이 아니며, approval artifact 또는 `auto_bounded_live` guard 없이 live env/order guard로 승격하지 않는다.
- Sentinel은 Telegram 알림 기능을 제거한 운영 감시/report-only 축이다. 이상치는 mutation이 아니라 threshold source bundle, incident, instrumentation gap, normal drift로 라우팅한다.
- BUY 신호 Telegram은 신호 감지 안내로만 보낸다. 브로커 주문이 접수됐지만 아직 체결되지 않은 상태를 "주문 제출" 완료처럼 알리지 않으며, BUY 신호 외의 실거래 알림은 실제 체결 receipt가 확인된 종목만 대상으로 한다.
- 사람이 반드시 개입하는 지점은 운영 장애, 생성된 approval request를 검토해 approval artifact 생성 여부를 결정하는 단계, 생성된 code improvement workorder를 Codex 세션에 넣어 구현을 요청하는 단계, 문서 backlog Project/Calendar 동기화다. `runtime_apply_bridge` 때문에 사용자가 눌러야 할 승인 종류가 새로 늘어난 것은 아니다. 다만 기존 `workorder 승인`과 `approval artifact 승인` 사이에 자동화가 `bridge ready 여부`를 명시하므로, 사용자는 `ready_for_approval`이 아닌 후보를 승인하지 않고, ready 후보에 대해서만 기존 방식대로 approval artifact 생성 여부를 결정한다.
- `build_codex_daily_workorder`는 이 runbook의 장전/장중/장후 확인절차를 `Runbook 운영 확인` 블록으로 자동 포함한다. 단, 같은 날짜 checklist에 `PreopenAutomationHealthCheckYYYYMMDD`/`IntradayAutomationHealthCheckYYYYMMDD`/`PostcloseAutomationHealthCheckYYYYMMDD` 운영 확인 기록이 남은 슬롯은 이미 처리된 것으로 보고 같은 날짜 workorder에서 제외한다. 같은 확인 큐는 `RunbookOps` track으로 GitHub Project와 Google Calendar에도 동기화되어 operator가 놓치지 않게 한다. GitHub Project 동기화가 rate limit 등으로 지연돼도 workorder는 기본값 `CODEX_WORKORDER_INCLUDE_LOCAL_DOCS=true`로 로컬 checklist 미완료 항목을 병합한다.
- 이 문서에서 “확인”은 artifact, log, source-of-truth 문서를 읽고 아래 `판정 상태 정의` 중 하나로 분류하는 행위다. 확인만으로 live env, runtime threshold, broker 주문 상태를 변경하지 않는다.

## 역할/권한 경계

| 주체 | 할 일 | 하지 말 일 | 증적 |
| --- | --- | --- | --- |
| cron/runtime wrapper | 정해진 시각에 preopen/intraday/postclose job 실행, artifact와 log 생성 | 임의 threshold 변경, broker 주문 가드 우회, 실패 은폐 | `data/report/**`, `data/threshold_cycle/**`, `data/pattern_lab/**`, cron log |
| deterministic guard | threshold family별 bounds, max step, sample floor, rollback guard를 적용해 최종 state/value 산출 | AI 제안을 그대로 live 적용, 장중 runtime mutation 수행 | apply plan JSON, runtime env JSON, daily EV report |
| runtime apply bridge | LDM bucket 후보를 named runtime family 후보로 정규화하고 approval contract/env mapping/runtime hook/post-apply attribution 준비 여부를 판정 | bridge report만으로 env 생성, `runtime_effect=false` bucket 직접 적용, not-ready 후보 수동 승인 | `runtime_apply_bridge_YYYY-MM-DD.{json,md}`, approval contract, target env keys, blocked reasons |
| 자동 AI reviewer | threshold/logic/prompt 개선 후보를 proposal-only로 작성 | live env 변경, 주문 판단 직접 변경, deterministic guard 대체 | `swing_threshold_ai_review`, AI correction artifact, strict JSON schema 결과 |
| swing runtime approval | 스윙 approval request 생성, approval artifact 소비, dry-run runtime env 후보 연결 | 승인 artifact 없이 env 반영, dry-run 해제, 브로커 주문 허용 | `swing_runtime_approval`, `threshold_apply_YYYY-MM-DD.json`, runtime env JSON |
| swing one-share real canary | 별도 승인된 후보에 한해 1주 실제 BUY/SELL execution 품질 수집 | 스윙 전체 실매매 전환, phase0 scale-in 실주문, approval artifact 밖 주문 | `swing_one_share_real_canary`, 실주문 receipt, real-only execution metrics |
| Codex | 사용자가 요청한 범위에서 코드/문서 수정, artifact 검증, parser/test 실행, workorder 작성 또는 구현 | GitHub Project/Calendar 동기화 실행, 사용자 승인 없는 live guard 완화, broker 주문 제출, 임의 패키지 설치 | 변경 파일, 테스트 결과, 최종 답변 |
| 사람/operator | 장전/장중/장후 판정 검토, approval request 승인 여부와 approval artifact 생성 여부 결정, 외부 동기화 명령 실행, 운영 장애 복구 판단, 생성 workorder의 구현 지시 여부 결정 | 자동화 artifact만 보고 이미 live 변경됐다고 간주, approval artifact 없이 env를 수동 작성, 출처 없는 수동 threshold 변경 | approval artifact, 수동 실행 명령, Project/Calendar 상태, 운영 메모 |

## 판정 상태 정의

- `pass`: 필수 artifact가 존재하고, 필수 필드가 유효하며, 금지된 runtime 변경이나 provenance 누락이 없다.
- `warning`: artifact는 존재하지만 sample 부족, stale/missing 관찰축, retry, 일부 보조 산출물 지연처럼 다음 관찰이 필요한 상태다. 이 상태만으로 live threshold를 변경하지 않는다.
- `fail`: 필수 artifact 누락, schema/parse 실패, cron/wrapper 실패, runtime provenance 누락, 금지된 runtime 변경 징후가 있는 상태다. 조치는 운영 장애 복구, instrumentation 보강, 또는 workorder 생성이지 즉시 threshold 수동 변경이 아니다.
- `not_yet_due`: 정해진 실행 시각이 아직 지나지 않았거나, 장후 장시간 job이 허용 대기시간 안에서 실행 중인 상태다.

## 체크리스트 반영 기준

- 날짜별 `stage2 todo checklist`는 구현/판정/미래 재확인처럼 소유자가 필요한 작업항목만 체크박스로 소유한다.
- 장전/장중/장후 반복 운영 확인은 날짜별 체크박스가 아니라 `build_codex_daily_workorder --slot PREOPEN|INTRADAY|POSTCLOSE`가 생성하는 `Runbook 운영 확인` 블록과 `sync_docs_backlog_to_project`가 생성하는 `RunbookOps` Project/Calendar 항목이 소유한다. 완료 기록이 남은 슬롯은 이후 같은 날짜 workorder/Project backlog에서 다시 열지 않는다.
- 날짜별 checklist의 장전/장중 섹션이 신규 수동 작업 없음으로 비어 있어도 runbook 운영 확인은 생략된 것이 아니다. 해당 섹션에는 runbook 확인절차 참조 문구를 남긴다.
- runbook의 반복 확인 artifact, 시간표, 금지사항을 바꾸면 [build_codex_daily_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_codex_daily_workorder.py)의 `build_runbook_operational_checks`와 관련 테스트를 같은 변경 세트로 맞춘다.
- 새 recurring operational check는 `RunbookOps` track으로 Project/Calendar에 동기화한다. 특정 날짜에만 확인해야 하거나 사람이 구현해야 하는 후속은 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 별도 등록한다.

## Runtime Apply Bridge 사용 절차

`runtime_apply_bridge`는 사용자가 매일 별도 판단을 하나 더 해야 하는 승인 단계가 아니라, 기존 approval request가 실제 매매 runtime까지 연결될 수 있는지 자동화가 증명하는 계약 산출물이다. 현재 bridge 구현은 LDM `entry`와 `scale_in` bucket의 runtime 적용 가능성만 검증한다. 다른 bucket은 bridge가 없다는 이유만으로 즉시 개발 대상이 되지 않고, 해당 bucket을 runtime 적용 후보로 열겠다는 별도 workorder/owner가 있을 때만 bridge 확장 대상으로 분류한다. 후보 bucket 발굴과 분류는 operator 기억이 아니라 postclose 자동화체인이 소유한다. `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, `runtime_apply_gap_audit`, `HumanInterventionSummary`는 성과/필요성/source-quality/contract gap을 기준으로 `source_only_keep_collecting`, `workorder_needs_codex_implementation`, `approval_contract_ready`, `runtime_apply_blocked_contract_gap` 중 하나로 표면화해야 한다. surfaced 되지 않은 bucket을 사용자가 별도로 기억해 수동 지시할 필요는 없으며, surfaced 되었는데 checklist/Project에 누락되면 그것은 자동화체인 gap으로 본다. bridge가 없는 후보는 workorder나 approval request가 있어도 `source-only` 또는 `implementation-needed`로 남고, 다음 장전 env로 들어가지 않는다.

1. 장후에는 `data/report/runtime_apply_bridge/runtime_apply_bridge_YYYY-MM-DD.{json,md}`를 확인한다.
2. 먼저 postclose 산출물이 runtime 적용 후보 bucket을 자동으로 surfaced 했는지 확인한다. 후보 발견 자체는 사용자가 기억해서 수행하지 않는다. `runtime_apply_gap_audit` 또는 `HumanInterventionSummary`에 후보가 없으면 그날은 runtime 적용 후보가 없거나 source-quality/표본 부족으로 닫힌 것이다. 성과 후보가 있었는데 surfaced 되지 않았다면 `runtime_apply_blocked_contract_gap` 또는 automation handoff gap으로 기록한다.
3. 각 후보의 `bridge_candidate_state`를 본다.
   - `ready_for_approval`: contract, env key, runtime hook, post-apply attribution 경로가 닫혔다. 사용자가 적용을 원하면 기존 approval artifact 생성 여부를 결정한다.
   - `bootstrap_pending`: 표본/rolling 확인이 부족하다. 승인하지 않고 다음 표본을 기다린다.
   - `blocked_source_quality`: join/provenance/source-quality 결함이 있다. 데이터 보강 또는 instrumentation workorder로 닫는다.
   - `blocked_rolling_conflict`: rolling/cumulative 결론이 충돌한다. live apply가 아니라 추가 확인 또는 후보 축소로 닫는다.
   - `blocked_contract_gap`: approval contract, env mapping, runtime hook, rollback/post-apply attribution 중 하나가 없다. Codex 구현 workorder 대상이다.
4. 사용자가 개입하는 경우는 두 가지뿐이다.
   - `blocked_contract_gap` 또는 구현 누락이면 Codex에 구현을 지시한다. 이것은 `workorder 승인`이며 runtime 변경 승인이 아니다.
   - `ready_for_approval` 후보를 실제 다음 PREOPEN에 적용하려면 해당 family의 approval artifact 생성을 승인한다. 이것은 기존 `approval artifact 승인`이며 bridge 승인이라는 별도 의미로 묶지 않는다.
5. 다음 장전 `threshold_cycle_preopen_apply`는 bridge approval artifact를 읽더라도 `bridge_candidate_state=ready_for_approval`, `allowed_runtime_apply=true`, approval contract match, target env mapping이 모두 맞을 때만 env를 생성한다. 하나라도 빠지면 `runtime_apply_blocked_bridge_not_ready`, `runtime_apply_not_allowed`, `approval_artifact_missing`, `contract_missing` 같은 blocked reason으로 닫는 것이 정상이다.
6. bridge가 env를 만들더라도 hard safety, broker/account/order/cooldown/qty guard, stale quote, price freshness, stop guard를 우회하지 않는다. bridge는 entry/scale-in bucket 후보를 runtime hook으로 연결할 수 있게 해주는 계약이지, 주문 안전장치 완화 권한이 아니다.

## 시간대별 Runbook

`panic_entry_freeze_guard`는 패닉셀 V2 1차 후보지만, runbook상 즉시 적용 대상이 아니다. `data/threshold_cycle/approvals/panic_entry_freeze_guard_YYYY-MM-DD.json` approval artifact, `KORSTOCKSCAN_PANIC_ENTRY_FREEZE_GUARD_*` env key mapping, stale source/owner conflict/provenance rollback guard가 모두 구현되기 전에는 `panic_sell_defense`가 `PANIC_SELL`이어도 신규 BUY를 자동 차단하지 않는다. `panic_regime_mode=NORMAL|PANIC_DETECTED|STABILIZING|RECOVERY_CONFIRMED`는 report/approval source이며, V2.0 신규 BUY pre-submit freeze, V2.1 미체결 진입 주문 cancel, V2.2 holding/exit context, V2.3 강제 축소/청산은 서로 다른 owner다. approval/rollback guard 없이 mode 전환만으로 주문 취소, 자동매도, stop/TP/trailing/threshold/provider/bot restart를 수행하지 않는다.

| 시간대 KST | 실행 주체 | 실행/트리거 | 산출물 | 운영 확인 기준 | 금지/주의 |
| --- | --- | --- | --- | --- | --- |
| `07:20` | cron | `final_ensemble_scanner.py` | `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json` | 스캐너 실패/빈 결과, fallback diagnostic 혼입, 추천 CSV/DB 적재 gap 여부만 확인 | 스캐너 결과만으로 floor/threshold 수동 변경 금지 |
| `07:30` | cron | 기존 `tmux bot` 세션 종료 | tmux session 상태 | 기존 세션이 남아 있으면 `tmux ls` 확인 | 장중 실행 중 강제 종료 금지 |
| `07:35` | cron | `deploy/run_threshold_cycle_preopen.sh` with `THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live`, `THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true` | `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}`, `logs/threshold_cycle_preopen_cron.log` | 실패 시 apply plan의 `blocked_reason`, AI guard, same-stage owner 충돌, `swing_runtime_approval.requested/approved/blocked`를 확인한다. `lifecycle_decision_matrix_runtime`이 selected이면 policy file/version/promote cap/env key와 fixed threshold contract가 함께 기록됐는지 확인한다 | 실패했다고 수동으로 env 값을 직접 덮어쓰지 않는다. 스윙 approval artifact 없이는 승인 요청만 보고 적용하지 않는다. lifecycle matrix selected 전에는 직접 ADM/fixed threshold 역할을 장중 변경하지 않는다 |
| `07:40` | cron | `src/run_bot.sh`를 tmux `bot` 세션에서 실행 | bot runtime log, source된 runtime env echo | `runtime_env` 적용 여부와 봇 기동 여부 확인. env가 없으면 `run_bot.sh`가 `deploy/run_threshold_cycle_preopen.sh`를 먼저 실행해 env 생성을 시도하고, 그래도 없으면 최대 `KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_WAIT_SEC` 동안 대기한다 | runtime env 파일이 없으면 봇을 먼저 띄우지 않는다. bootstrap/대기 timeout 시 preopen apply 실패로 보고 원인 확인 |
| `08:00~09:00` | operator/guard | PREOPEN 안정 구간 | 없음 | checklist 상단 `오늘 목적/강제 규칙`과 전일 EV report를 읽고 불일치가 있으면 `warning`으로 기록 | full monitor snapshot build는 wrapper가 차단한다. 새 workorder 없는 live toggle 금지 |
| `09:00~09:05` | runtime | 장 시작 후 runtime/sim/probe 이벤트 수집 시작 | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | 봇 연결, 계좌/잔고/주문 가능 상태, `actual_order_submitted` provenance split 확인 | threshold 변경, provider 라우팅 변경 금지. 실계좌 예수금 부족을 sim/probe 후보 제외 사유로 쓰지 않는다 |
| `09:00~15:30` | cron | `deploy/run_system_metric_sampler_cron.sh` 1분 주기 | `logs/system_metric_samples.jsonl`, `logs/system_metric_sampler_cron.log`, `tmp/system_metric_sampler_state.json` | CPU busy, load, memory, swap, disk 사용률과 sampler stale 여부를 확인한다. error detector resource_usage의 입력 source다 | resource pressure를 전략 threshold/order guard 변경으로 해석하지 않는다 |
| `09:05~15:20` | cron | `deploy/run_buy_funnel_sentinel_intraday.sh` 5분 주기, 기본 `BUY_FUNNEL_SENTINEL_USE_CACHE=1`, `BUY_FUNNEL_SENTINEL_USE_SUMMARY=1` | `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}`, `data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_YYYY-MM-DD.*`, `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`, `data/pipeline_event_summaries/pipeline_event_summary_manifest_YYYY-MM-DD.json`, `logs/run_buy_funnel_sentinel_cron.log` | `UPSTREAM_AI_THRESHOLD`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `RUNTIME_OPS` 추세와 `followup.route`, `operator_action_required`, `runtime_effect=report_only_no_mutation`, cache `rebuilt=false`/append rows, summary `status=ok` 또는 fallback 확인 | Sentinel 결과로 score/spread/fallback/restart 자동 변경 금지. summary는 diagnostic aggregation이며 raw suppression이 아니다 |
| `09:05~15:30` | cron | `deploy/run_holding_exit_sentinel_intraday.sh` 5분 주기, 기본 `HOLDING_EXIT_SENTINEL_USE_CACHE=1` | `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}`, `data/runtime/sentinel_event_cache/holding_exit_sentinel_events_YYYY-MM-DD.*`, `logs/run_holding_exit_sentinel_cron.log` | `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `AI_HOLDING_OPS`, `SELL_EXECUTION_DROUGHT` 추세와 real/non-real exit split, `followup.route`, `operator_action_required`, `runtime_effect=report_only_no_mutation`, cache `rebuilt=false`/append rows 확인 | Sentinel 결과로 자동 매도, threshold mutation, bot restart 금지 |
| `09:05~15:30` | cron | `deploy/run_panic_sell_defense_intraday.sh` 2분 주기, 5분 배수 분 제외 offset, wrapper cooldown 90초. report 생성 전 `market_panic_breadth_collector`를 nproc 기반 report-only CPU affinity/nice/ionice로 best-effort 실행하되 `PANIC_MARKET_BREADTH_MAX_AGE_SEC` 안의 fresh artifact가 있거나 shared lock이 잡혀 있으면 재사용한다 | `data/report/panic_sell_defense/panic_sell_defense_YYYY-MM-DD.{json,md}`, `data/report/market_panic_breadth/market_panic_breadth_YYYY-MM-DD.json`, `logs/run_panic_sell_defense_cron.log`, `tmp/panic_state_telegram_notify_state.json` | `panic_state`, stop-loss cluster, active sim/probe 회복률, post-sell rebound, weighted composite `risk_off_advisory`/`risk_on_advisory`, `single_market_risk_off_advisory`, `canary_candidates`, `runtime_effect=report_only_no_mutation`, panic 시작/해제 Telegram transition, CPU/resource spike 반복 여부 확인 | panic 결과로 score/stop threshold 변경, 자동매도, bot restart, 스윙 실주문 전환 금지. Telegram은 시작/해제 안내만 전송하며 runtime 기본 audience는 전체, dry-run/test는 admin only다. 2분 전환 후 resource fail이 반복되면 5분 주기로 rollback |
| `09:05~15:30` | cron | `deploy/run_panic_buying_intraday.sh` 2분 주기, panic sell defense보다 1분 늦게 staggered 실행, 5분 배수 분 제외 offset, wrapper cooldown 90초. report 생성 전 `market_panic_breadth_collector`는 shared lock/fresh artifact를 재사용한다 | `data/report/panic_buying/panic_buying_YYYY-MM-DD.{json,md}`, `data/report/market_panic_breadth/market_panic_breadth_YYYY-MM-DD.json`, `logs/run_panic_buying_cron.log`, `tmp/panic_state_telegram_notify_state.json` | `panic_buy_state`, `panic_buy_regime_mode`, 패닉바잉 active/소진 count, weighted composite `risk_on_advisory`/`risk_off_advisory`, `single_market_risk_on_advisory`, TP counterfactual, `panic_buy_runner_tp_canary`, `runtime_effect=report_only_no_mutation`, panic 시작/해제 Telegram transition, CPU/resource spike 반복 여부 확인 | panic buying 결과로 TP 정책, trailing, score/threshold, provider route, 자동매수/자동매도, bot restart 변경 금지. `panic_buy_regime_mode`는 runner TP, 추격매수 차단, exhaustion cleanup, cooldown 후보를 source bundle에 분리하는 값일 뿐 approval artifact 전 runtime 권한이 없다. Telegram은 시작/해제 안내만 전송하며 runtime 기본 audience는 전체, dry-run/test는 admin only다. 2분 전환 후 resource fail이 반복되면 5분 주기로 rollback |
| `09:30~11:00` | cron | `src.engine.buy_pause_guard evaluate` 5분 주기 | `logs/buy_pause_guard.log` | pause guard 반복 발동 여부와 `[DONE] buy_pause_guard target_date=YYYY-MM-DD` marker 확인 | pause guard를 진입 threshold 튜닝 근거로 단독 사용 금지 |
| `09:35~12:00` | cron | monitor snapshot incremental/full | `data/report/monitor_snapshots/*_YYYY-MM-DD.json`, `logs/run_monitor_snapshot_cron.log`, `data/runtime/monitor_snapshot_completion_*.json` | snapshot failure, async timeout, manifest status, completion artifact 확인. 완료 Telegram 발송은 기본 제거하고 로그/산출물 기준으로 판정한다 | 장전 full build 차단을 우회하지 않는다 |
| `12:05` | cron | `deploy/run_threshold_cycle_calibration.sh` with `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai` | `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_intraday.json`, `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_intraday.{json,md}`, `logs/threshold_cycle_calibration_intraday_cron.log` | `[START]/[DONE]/[FAIL] threshold-cycle calibration target_date=YYYY-MM-DD phase=intraday` marker와 `calibration_state`, `safety_revert_required`, `ai_status`, `guard_reject_reason` 확인. OpenAI correction이 `parsed`가 아니면 wrapper는 제한 횟수 재시도 후 `[FAIL]`로 닫는다 | 장중 calibration 결과를 당일 runtime에 적용 금지 |
| `15:20` | cron | `deploy/run_scalp_sim_overnight_preclose.sh` with OpenAI `overnight_v1`, Bedrock Nova Lite shadow | `data/report/scalp_sim_overnight/scalp_sim_overnight_YYYY-MM-DD.{json,md}`, `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_YYYY-MM-DD.jsonl`, `logs/scalp_sim_overnight_preclose_cron.log` | active 스캘핑 sim position이 `scalp_sim_overnight_decision`으로 판정되고 `SELL_TODAY`는 sim 가상청산, `HOLD_OVERNIGHT`는 active carry로 남는지 확인한다. `active_undecided_count`, `decision_coverage_rate`, `source_quality_status`, OpenAI provenance, Nova Lite shadow row를 확인한다 | sim-only source다. 실주문, 자동매도, threshold apply, provider route 변경, bot restart 근거로 쓰지 않는다. state lock 경합 시 `scalp_sim_overnight_lock_skipped` source-quality blocker로 보고 postclose verifier에서 닫는다 |
| `15:20~15:30` | runtime/cron | 오버나이트 flow, HOLD/EXIT sentinel final window | pipeline events, holding sentinel | `SELL_TODAY`, `HOLD_OVERNIGHT`, force-exit/safety 이벤트 확인 | flow `TRIM`을 부분청산 구현 없이 HOLD로 해석 금지 |
| `15:45` | cron | `deploy/run_swing_live_dry_run_report.sh` 기본 `SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT=false`, `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none` | `data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.{json,md}`, status JSON, `logs/swing_live_dry_run_cron.log` | `swing_sim_*` stage, `actual_order_submitted=false`, `recommendation_db_load.db_load_skip_reason`, 15:45 lightweight selection/funnel completion, status `lifecycle_audit_mode=postclose_deferred` 확인 | 15:45 wrapper는 운영 봇과 리소스 경합을 피하기 위해 lifecycle/AI review/runtime approval을 기본 실행하지 않는다. 스윙 lifecycle/approval 산출물은 16:10 postclose chain에서 생성한다. 스윙 dry-run 결과로 당일 runtime guard 완화 금지 |
| `16:10` | cron | `deploy/run_threshold_cycle_postclose.sh` with OpenAI correction, 기본 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none`, cron 기본 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart` | threshold partition, `market_panic_breadth`, postclose `panic_sell_defense`, postclose `panic_buying`, `openai_ws_stability`, `threshold_cycle_YYYY-MM-DD.json`, sim post-sell evaluation, `scalp_entry_action_decision_matrix`, `lifecycle_decision_matrix`, `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative`, postclose AI review, swing lifecycle automation, swing runtime approval, pattern lab automation, pattern lab currentness audit, pipeline event verbosity report, observation source-quality audit, codebase performance workorder source, code improvement workorder, daily EV report, pattern lab propagation audit, runtime approval summary, postclose verification, 다음 영업일 stage2 checklist | `logs/threshold_cycle_postclose_cron.log`, bot stop/restart marker, resource guard log lines, `market_panic_breadth_YYYY-MM-DD.json`, `panic_sell_defense_YYYY-MM-DD.md`, `panic_buying_YYYY-MM-DD.md`, `openai_ws_stability_YYYY-MM-DD.md`, `scalp_entry_action_decision_matrix_YYYY-MM-DD.md`, `lifecycle_decision_matrix_YYYY-MM-DD.md`, `swing_lifecycle_audit_YYYY-MM-DD.md`, `swing_threshold_ai_review_YYYY-MM-DD.md`, `swing_improvement_automation_YYYY-MM-DD.md`, `swing_runtime_approval_YYYY-MM-DD.md`, `pattern_lab_currentness_audit_YYYY-MM-DD.md`, `pipeline_event_verbosity_YYYY-MM-DD.md`, `observation_source_quality_audit_YYYY-MM-DD.md`, `codebase_performance_workorder_YYYY-MM-DD.md`, `pattern_lab_propagation_audit_YYYY-MM-DD.md`, `threshold_cycle_ev_YYYY-MM-DD.md`, `runtime_approval_summary_YYYY-MM-DD.md`, `threshold_cycle_postclose_verification_YYYY-MM-DD.md`, real/sim/combined split, sim-first lifecycle coverage, lifecycle matrix fixed threshold contract, swing/scalping automation freshness, currentness/propagation audit status, `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`, 다음 영업일 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`를 확인하고 지연/누락은 `warning` 또는 `fail`로 분류 | wrapper는 시작 시 bot 세션이 살아 있으면 postclose resource isolation을 위해 종료하고, wrapper 성공/실패/인터럽트 후 이전에 bot이 살아 있었던 경우 tmux `bot` 세션을 재기동한다. 이 재기동은 장후 리소스 격리이며 threshold/order/provider 변경 권한이 아니다. wrapper는 direct predecessor artifact가 없으면 `THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC` 동안 대기하고 JSON 검증 후에만 후행 단계를 실행한다. OpenAI correction이 `parsed`가 아니면 제한 횟수 재시도하고, 최종 실패 시 `threshold_cycle_postclose_verification`이 runtime-applicable candidate를 blocker로 표면화해 `fail`을 반환한다. 스윙 threshold AI review artifact는 계속 생성하지만 기본 provider가 `none`이라 OpenAI 호출은 하지 않는다. 명시적으로 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=openai`를 준 경우에만 스윙 AI reviewer를 호출한다. heavy report 단계는 `THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_GUARD=true` 기본값으로 fresh sampler, `MemAvailable`, swap free/used, iowait, CPU busy, load를 확인하고, `nice`/`ionice`/background CPU affinity를 적용한다. compact backfill도 낮은 우선순위로 실행하며 `paused_by_availability_guard`는 `THRESHOLD_CYCLE_COMPACT_AVAILABILITY_WAIT_SEC` 동안 checkpoint 유지 후 대기/재개한다. postclose wrapper는 threshold-cycle report 전에 market breadth, panic, OpenAI WS report를 생성하고, compact sim post-sell evaluation 직후 scalp entry ADM과 lifecycle decision matrix를 생성한다. 15:45에서 defer된 swing lifecycle/runtime approval도 여기서 실행한다. `panic_regime_mode`와 `panic_buy_regime_mode`는 source bundle/workorder/runtime approval summary로만 전달하며 approval artifact 전 runtime 변경 권한이 없다. `threshold_cycle_ev`는 workorder source용 pre-pass, workorder summary refresh용 post-pass, propagation audit summary refresh용 post-pass로 생성될 수 있다. scalping/swing pattern lab 실행 실패는 lab freshness/source-quality 경고로 흡수하고 후단 daily EV/workorder/runtime summary 생성을 보호한다. `scalp_entry_action_decision_matrix`, `lifecycle_decision_matrix`, `holding_exit_decision_matrix`, `pattern_lab_currentness_audit`, `pattern_lab_propagation_audit`, `pipeline_event_verbosity_report`, `observation_source_quality_audit`, `codebase_performance_workorder_report`, `threshold_cycle_postclose_verification`은 산출물 자체로는 report/proposal/verification 계층이다. 단, selected PREOPEN env가 명시하면 lifecycle matrix runtime policy가 기존 ADM adapter를 감싸 stage별 action proposal에 사용된다 |
| `17:30` | cron | `KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE=true auto_retrain_pipeline.sh` | `data/report/swing_model_retrain/swing_model_retrain_YYYY-MM-DD.json`, `data/report/swing_model_retrain/diagnosis_YYYY-MM-DD.json`, `data/report/swing_model_retrain/bull_period_ai_review_YYYY-MM-DD.json`, `data/report/swing_model_retrain/status/swing_model_retrain_YYYY-MM-DD.status.json`, `logs/swing_model_retrain_cron.log` | `[START]/[DONE]/[FAIL] swing_model_retrain target_date=YYYY-MM-DD` marker, status, diagnosis, promotion guard, current registry 갱신 여부를 확인한다 | auto-promote는 model artifact promotion guard만 통과할 수 있다. 스윙 dry-run 해제, threshold/floor env 작성, 브로커 주문 허용 근거로 쓰지 않는다 |
| `20:05` | cron | `deploy/run_tuning_monitoring_postclose.sh` | Parquet/DuckDB refresh status, `data/report/tuning_monitoring/status/*` | `threshold_cycle_postclose` 최신 terminal marker가 같은 날짜 `[DONE]`인지 먼저 확인하고, `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`인지 확인 | 선행 postclose 완료 전 Parquet/DuckDB refresh 금지. pattern lab 중복 실행 금지 |
| `18:30~19:00` | checklist checkpoint | 날짜별 checklist의 스윙 실주문/floor 후속 판단 항목 | `swing_runtime_approval`, `swing_live_dry_run` status, `swing_daily_simulation`, `threshold_cycle_ev` | 실주문 전환은 `global dry-run 유지`/`one-share real canary approval request`/`hold_sample\|freeze` 중 하나로만 닫고, floor 변경은 `approval_required\|hold_sample\|freeze`로 닫는다 | 전체 스윙 실주문 전환과 approval artifact 없는 floor env 작성 금지 |
| `21:00` | cron | `update_kospi.py` | `logs/update_kospi.log`, `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json`, `data/daily_recommendations_v2.csv` | `[START]/[DONE]/[FAIL]` marker와 status JSON의 `status`, `failed_steps`, `warning_steps`, `recovered_steps`, 최신 DB quote 상태 확인. detector window end 전 `START-only`는 in-progress로 본다 | 매매 runtime과 무관한 데이터 갱신으로 취급. `completed_with_warnings`는 DB 적재 실패와 동일하지 않으며 추천/대시보드/스윙 일일 리포트 후속 step 실패를 분리 확인 |
| `22:55` | cron | 봇 tmux 세션 종료 | tmux session 상태 | 장 종료 후 잔여 세션 확인 | 장중 세션 종료와 혼동 금지 |
| `23:10` | cron | dashboard DB archive | `logs/dashboard_db_archive_cron.log` | archive skipped/error 확인 | 미검증 파일 강제 삭제 금지 |
| `23:20` | cron | log rotation cleanup | `logs/log_rotation_cleanup_cron.log` | deleted/size 추세 확인 | 당일 장애 분석 전 로그 수동 삭제 금지 |
| `*:00/5` | cron | `bash deploy/run_error_detection.sh full` | `data/report/error_detection/error_detection_YYYY-MM-DD.json`, `logs/run_error_detection.log` | wrapper가 `logs/run_error_detection.log`를 보장하고 `[START]/[DONE]/[FAIL]` marker를 남기는지 확인. 6개 detector (process health, cron, log, artifact, resource, stale lock). 4개 report-only, 2개 filesystem maintenance mutation (flag gated). `summary_severity=fail`이면 bot daemon이 떠 있지 않아도 wrapper가 관리자 Telegram 직접 알림을 시도한다 | 탐지 결과로 runtime threshold/spread/주문 자동 변경 금지. Telegram 알림은 report-only 운영 알림이며 자동 복구/재시작 권한이 아니다 |

### Pipeline Event Verbosity/Retention Policy

`data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`은 당일 forensic raw stream이고, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl`은 threshold-cycle이 읽는 compact decision stream이다. raw stream 증가는 `logs/` rotation으로 해결되지 않으며, disk pressure 원인 판정 시 두 경로를 분리한다.

1. 당일 raw stream은 postclose snapshot/DB/parquet 검증 전까지 수동 삭제하지 않는다. 주문 제출, 체결, exit, safety, threshold family, provenance, source-quality 이벤트는 손실 없이 보존한다.
2. `strength_momentum_observed`, `blocked_strength_momentum`, `blocked_swing_score_vpw`, `blocked_overbought`, `blocked_swing_gap`처럼 고빈도 diagnostic stage는 기본 decision authority가 없다. 반복 tick 단위 raw 기록을 live threshold/order guard 근거로 직접 쓰지 않고, stage/date/stock/source-quality 단위 summary 또는 sampling artifact를 먼저 만든다. BUY Sentinel v1은 이 5개 stage만 `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`로 1분 bucket 집계하고, 원문 raw 기록은 줄이지 않는다.
3. verbosity/throttle code change는 lossless decision-stage allowlist 또는 raw 보존 shadow 계측으로 시작한다. pass/order/safety/source-quality transition은 throttle 대상에서 제외하고, suppressed count/first_seen/last_seen을 별도 metric으로 남겨야 한다. producer-side compaction V2의 기본값은 `PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE=shadow`이고, `shadow`는 raw JSONL/DB upsert를 보존한 채 `data/pipeline_event_summaries/pipeline_event_producer_summary_YYYY-MM-DD.jsonl`과 manifest만 생성한다. `off`는 장애 대응용 비활성 옵션이다. `suppress`는 코드가 있어도 기본 비활성이며 V1 raw-derived summary와 2영업일 이상 parity 통과, 별도 workorder/approval owner 전에는 사용하지 않는다.
4. 보관/압축은 `compress_db_backfilled_files`가 소유한다. 우선 dry-run으로 verified/backfilled 대상과 `skipped_unverified`를 확인한 뒤, 기본 `--days 7` 기준의 검증 완료 raw/snapshot만 압축한다. 미검증 파일 강제 삭제는 금지한다.
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
| bot daemon | 장중 빠른 health alert | `bot_main.py` 내부 `error_detection_loop` | 동일 report 갱신, fail 전환/summary 변경 시 `SYSTEM_HEALTH_ALERT` |
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

nproc 기반 CPU profile로 bot hot path와 report-only job 경합을 줄인다. 공통 profile은 [cpu_affinity_profile.sh](/home/ubuntu/KORStockScan/deploy/cpu_affinity_profile.sh)가 소유한다. 4 vCPU 이상에서는 [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)의 기본 `KORSTOCKSCAN_BOT_CPU_AFFINITY`가 `0-1`, report-only wrapper 기본값이 `2-3`, health/sampler 기본값이 `3`이다. 2~3 vCPU 환경에서는 bot `0`, wrapper `1` 또는 `1-2` 계열로 축소되고, 1 vCPU 또는 `taskset` 부재 환경에서는 affinity 없이 실행한다. 적용 대상은 `run_error_detection.sh`, `run_buy_funnel_sentinel_intraday.sh`, `run_holding_exit_sentinel_intraday.sh`, `run_panic_sell_defense_intraday.sh`, `run_panic_buying_intraday.sh`, `run_system_metric_sampler_cron.sh`, `run_monitor_snapshot_cron.sh`, `run_monitor_snapshot_incremental_cron.sh`, `run_monitor_snapshot_midcheck_safe.sh`, `run_monitor_snapshot_safe.sh`, `run_threshold_cycle_calibration.sh`, `run_threshold_cycle_postclose.sh`이며, 각각 `ERROR_DETECTION_CPU_AFFINITY`, `BUY_FUNNEL_SENTINEL_CPU_AFFINITY`, `HOLDING_EXIT_SENTINEL_CPU_AFFINITY`, `PANIC_SELL_DEFENSE_CPU_AFFINITY`, `PANIC_BUYING_CPU_AFFINITY`, `SYSTEM_METRIC_SAMPLER_CPU_AFFINITY`, `MONITOR_SNAPSHOT_CPU_AFFINITY`, `THRESHOLD_CYCLE_CALIBRATION_CPU_AFFINITY`, `THRESHOLD_CYCLE_POSTCLOSE_CPU_AFFINITY`로 override할 수 있다. panic sell/buy wrapper 내부의 `market_panic_breadth_collector`도 같은 panic wrapper affinity/nice/ionice와 shared lock/fresh artifact 재사용 계약을 따른다. 이 설정은 CPU 배치만 바꾸며 threshold, 주문 guard, provider 변경 권한은 없다. 단 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart`는 16:10 장후 postclose resource isolation 전용 운영 재기동이며, strategy/runtime threshold 변경으로 해석하지 않는다.

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
| `process_health` | KRX 거래일 `07:40~22:55 KST` bot expected runtime window 안에서 main loop, daemon thread heartbeat stale 또는 PID 불일치. 비거래일 또는 이 시간창 밖의 dead/stale heartbeat는 `expected_stopped`로 닫고 fail 알림 대상이 아니다. expected start 직후 `ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC` 동안은 tmux/run_bot/heartbeat 갱신 race를 fail이 아니라 startup grace warning으로 본다. `restart.flag` 기반 graceful restart 직후 `ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC` 이내의 dead PID + fresh heartbeat는 handoff warning으로 보고 즉시 재시작하지 않는다 | expected window 안이면 heartbeat owner와 실제 tmux/process 상태 확인. 장애면 운영 복구 playbook으로 분리. expected window 밖이면 정상 스케줄 종료로 본다. startup/restart grace warning은 grace 이후 재확인에서 pass/fail로 닫는다 | 자동 restart, threshold 변경 |
| `cron_completion` | 필수 cron log의 당일 DONE 누락 또는 FAIL 최신 marker. 거래일 전용 cron은 KRX 비거래일에 `skip_non_trading_day`로 닫는다 | 해당 cron log와 산출물 재확인 후 같은 date 재실행 여부 판단 | 실패를 threshold 성과로 해석 |
| `log_scanner` | error log burst 또는 신규 error pattern. `ERROR`/`CRITICAL`/traceback/exception/에러/오류/실패 같은 에러 후보 라인만 분류하며, `_error.log`에 섞인 INFO/WARNING성 DB 성공·업로드 로그는 운영 incident에서 제외한다. `TEST`, `123456`, `_DummySession`, `bus fail`처럼 pytest fixture signature가 붙은 라인도 제외한다. memory/OOM 분류는 `MemoryError`, 독립 단어 `memory`/`oom`, `out of memory`, `cannot allocate memory`만 인정하고 `kiwoom_*` 같은 logger/module 이름 내부 문자열은 OOM으로 보지 않는다 | stack trace/source artifact 확인 후 incident 또는 code workorder로 분리. fixture noise나 INFO성 운영 로그가 runtime error log에 섞이면 test/log sink 분리 또는 scanner ignore rule 보강으로 닫는다 | 에러만 보고 live guard 완화 |
| `kiwoom_auth_8005_restart` | fresh runtime log에서 `8005 Token이 유효하지 않습니다` 계열 인증 실패 감지. 기존 offset 이전 로그, pytest fixture signature, `run_error_detection*` meta log는 제외한다 | `restart.flag` 기반 graceful restart 후 새 PID, WS 수신, REST 시세/잔고 응답 회복을 확인한다. 하루 3회 이상이면 operator가 token 발급/캐시/WS reconnect 경로를 별도 incident로 본다 | hot-refresh, 주문 retry, threshold/spread/order guard 변경 |
| `artifact_freshness` | 시간창 기준 필수 report/artifact stale/누락 또는 JSON status 값 비정상. 장중 `pipeline_events`는 09:00~09:05 startup grace를 두고, `threshold_events` compact stream은 sparse stream이라 stale을 warning으로 본다. `threshold_cycle_ev`와 `swing_daily_simulation` 같은 one-shot postclose artifact는 완료 후 age만으로 재실행하지 않는다. `daily_recommendations_v2.csv`와 diagnostics는 장전 입력 특성상 mtime만 보지 않고 내부 `date`/`latest_date`, row/count 계약이 통과하면 `pass_content_date`로 닫는다 | window, startup grace, trading_day skip, upstream cron 실패, status JSON의 `failed_steps`/`recovered_steps`, content date/count 확인 | 누락 artifact를 수동 값으로 대체 |
| `resource_usage` | CPU/memory/swap/load/disk threshold 위반, sampler stale. CPU busy fail 기준은 `ERROR_DETECTOR_CPU_BUSY_MAX_PCT=95.0`이며 90% 구간부터 warning으로 본다. KRX 비거래일에는 system metric sampler stale만 `skip_non_trading_day`로 제외하고 disk/memory/load 같은 host resource check는 유지한다 | resource pressure 원인 확인. disk-low면 log rotate 결과와 cooldown state 확인. swap만 높고 `mem_available`이 충분한 경우는 즉시 장애보다 reclaim/캐시 잔존 가능성을 먼저 본다 | 전략 runtime parameter 변경 |
| `stale_lock` | 오래된 lock 발견 또는 cleanup 실패 | active lock인지 확인. 반복되면 wrapper lock lifecycle 보강 | 실행 중인 process lock 강제 삭제 |

### 코드수정 필요 에러 처리 절차

`summary_severity=fail` 또는 반복 `warning`이 코드 결함, instrumentation gap, wrapper 계약 불일치로 보이면 사람이 Codex에 수정 작업을 지시한다. detector 결과만으로 live threshold, spread cap, 주문 guard, provider routing, bot restart를 임의 변경하지 않는다. 단, `kiwoom_auth_8005_restart`는 인증/runtime data path 복구 예외로 fresh 8005 감지 시 `restart.flag` 생성만 허용한다.

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

6. detector 자체 장애로 bot 기동을 방해할 때만 `KORSTOCKSCAN_ERROR_DETECTOR_ENABLED=false`를 임시 사용한다. 적용 시 날짜별 checklist 또는 운영 메모에 사유, 복구 기준, 재활성화 확인 명령을 남긴다.

### 허용된 filesystem maintenance

7개 detector 중 4개는 순수 report-only다. 아래 3개만 운영 filesystem/runtime maintenance mutation을 허용한다.

- `stale_lock`: `ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=True`이고 dry-run이 아닐 때, `tmp/*.lock` 중 `ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC`를 넘고 `fcntl` non-blocking lock 획득에 성공한 파일만 삭제한다.
- `resource_usage`: disk free가 `ERROR_DETECTOR_DISK_FREE_MIN_MB` 미만이고 `ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=True`이며 dry-run이 아닐 때 `deploy/run_logs_rotation_cleanup_cron.sh 7`을 호출한다. 성공한 호출만 `tmp/error_detector_last_log_rotate_ts.txt`에 기록하며, 30분 cooldown 중에는 `log_rotate_trigger=cooldown_active`로 보고한다.
- `kiwoom_auth_8005_restart`: fresh runtime `8005` 인증 실패를 감지하고 dry-run이 아닐 때 `restart.flag`만 생성한다. 동일 auth incident 120초 cooldown 중에는 중복 flag 생성을 억제하고, 하루 누적 3회 이상이면 `fail`로 올려 operator 확인을 요구한다.

maintenance mutation도 전략 runtime 변경이 아니다. 실패하거나 반복되면 `warning/fail`로 보고 원인 복구를 진행하며, 매매 threshold를 수동 조정하지 않는다.

### Env override

| env var | 효과 | 사용 기준 |
| --- | --- | --- |
| `KORSTOCKSCAN_ERROR_DETECTOR_ENABLED=false` | bot daemon health detector 비활성화 | detector 자체 장애로 bot 기동을 방해할 때 임시 차단 |
| `KORSTOCKSCAN_ERROR_DETECTOR_DAEMON_INTERVAL_SEC=<sec>` | bot daemon 실행 주기 변경 | alert 과다/부하 조정이 필요할 때 |
| `KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED=false` | `process_health`의 bot expected runtime window gate 비활성화 | 24시간 bot 운영으로 바뀐 경우에만 사용 |
| `KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_START_HHMM=07:40`, `KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_END_HHMM=22:55` | bot 정상 기동/종료 스케줄 기준. window 밖 dead/stale heartbeat는 `expected_stopped` pass | runbook의 `07:40` 기동, `22:55` 종료 스케줄과 함께 변경 |
| `KORSTOCKSCAN_ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC=180` | bot expected start 직후 tmux/run_bot/heartbeat 갱신 race를 fail이 아닌 warning/recheck로 낮추는 유예 시간 | 실제 장중 process death를 숨기지 않도록 짧게 유지. grace 이후에도 heartbeat/PID가 죽어 있으면 fail |
| `KORSTOCKSCAN_ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC=<sec>` | resource sampler stale 기준 변경 | sampler 주기 변경과 함께만 조정 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=false` | stale lock 자동 삭제 차단 | lock lifecycle 조사 중 cleanup을 멈출 때 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC=<sec>` | stale lock age 기준 변경 | wrapper별 lock 보존시간이 다른 경우 |
| `KORSTOCKSCAN_ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=false` | disk-low 자동 log rotate 차단 | 장애 분석을 위해 로그 보존이 우선일 때 |

Env override는 운영 안전장치 조정이다. 적용/해제 시 runbook 또는 날짜별 checklist에 이유와 복구 기준을 남긴다.

## 장전 확인 절차

`build_codex_daily_workorder --slot PREOPEN`은 이 절차를 `PreopenAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. `logs/threshold_cycle_preopen_cron.log`에서 preopen apply `[DONE]` marker와 runtime env 생성 여부를 확인한다. 동시에 `data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_YYYY-MM-DD.status.json`의 `status=succeeded`를 확인한다. lock busy나 command fail이 exit 0 로그처럼 지나가도 status artifact가 `skipped|failed|running`이면 apply 완료로 보지 않는다.
2. `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json`에서 스윙 추천 생성/empty/fallback diagnostic 분리를 확인한다. detector 기준 완료 marker는 `final_ensemble_scanner target_date=YYYY-MM-DD`가 포함된 `[DONE]` 로그다.
3. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`에서 selected family와 blocked family를 본다.
4. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`이 있으면 `runtime_change=true` family와 env key를 확인한다. 파일이 없으면 apply plan의 `blocked_reason`을 읽고 `warning` 또는 `fail`로 분류한다.
5. `src/run_bot.sh` 기동 로그에서 당일 runtime env 파일 source 여부를 확인한다. 봇 기동 시각이 env 생성 시각보다 빠르면 `pre_env_boot_gap=true`로 보고, env 생성 후 재기동 또는 `run_bot.sh` 대기 동작이 있었는지 확인한다.
6. apply plan의 `swing_runtime_approval` 섹션에서 `requested`, `approved`, `blocked`, `selected`, `dry_run_forced`를 확인한다. `approval_required` 요청만 있고 approval artifact가 없으면 `approval_artifact_missing`은 정상 차단이다.
7. 스윙 approved env가 있더라도 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 runtime env에 포함되어야 한다. 장전에는 주문 guard를 완화하거나 `SWING_LIVE_ORDER_DRY_RUN_ENABLED`를 임의로 끄지 않는다.
8. apply plan의 `runtime_apply_bridge` 또는 blocked reason에서 bridge 후보 상태를 확인한다. `bridge_candidate_state=ready_for_approval`와 approval artifact가 모두 있는 후보만 selected될 수 있으며, `bootstrap_pending`, `blocked_source_quality`, `blocked_rolling_conflict`, `blocked_contract_gap`, `approval_artifact_missing`은 env 미생성이 정상이다.
9. bridge selected env가 있으면 `runtime_apply_bridge_family`, `bridge_candidate_id`, `source_bucket_key`, `approval_id`, `actual_runtime_effect` provenance가 runtime env JSON 또는 post-apply attribution 입력에 남는지 확인한다. provenance가 없으면 적용 성공이 아니라 `warning`으로 닫는다.
10. 실패 시 수동 approve가 아니라 `safety_revert_required`, `hold_sample`, `hold_no_edge`, `AI instrumentation_gap/incident`, same-stage owner 충돌 중 어느 차단인지 판정한다.

### 장중 명시적 Entry Unlock Override 절차

이 절차는 사용자가 장중 runtime 적용을 명시적으로 승인한 경우에만 쓴다. 자동화체인의 기본 원칙은 여전히 장중 threshold mutation 금지이며, 이 절차는 기존 runtime family의 bounded env를 재생성하고 봇을 재기동해 source된 env를 확인하는 운영 override다.

1. 신규 family를 만들지 않는다. `score65_74_recovery_probe`처럼 이미 registry와 env key가 닫힌 기존 family만 대상이다.
2. `threshold_cycle_calibration_YYYY-MM-DD_intraday.json`에서 `calibration_state=adjust_up`, `allowed_runtime_apply=true`, rolling primary sample floor, positive missed EV/close/MFE, `panic_state=NORMAL`, `order_bundle_submitted=0`을 확인한다.
3. apply plan은 `threshold_cycle_preopen_apply --source-phase intraday --include-family <family>`로 생성해 명시 family만 선택한다.
4. 기존 장전 selected runtime family가 있으면 runtime env를 merge해 보존한다. 장중 override가 기존 swing approval, dry-run guard, holding/exit selected family를 제거하면 안 된다.
5. `restart.flag` 기반 graceful restart 후 `/proc/<pid>/environ`에서 기존 selected env와 신규 family env가 모두 로드됐는지 확인한다.
6. 오후 결과는 post-restart cohort로만 본다. `score65_74_recovery_probe`, `wait6579_probe_canary_applied`, `budget_pass`, `latency_block`, `order_bundle_submitted`, `buy_order_sent`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 기존 오전 cohort와 섞지 않는다.
7. env 로드 확인만으로 닫지 않는다. runtime path에서 `family applied -> intended downstream consumer reached` 또는 `intended safety/source-quality block`이 남는지 확인한다. probe/canary가 `action`, `armed`, `source`를 세운 뒤 공통 score/budget/latency/order/exit gate에서 원래 의도와 다르게 재차단되면 `runtime_apply_contract_bug`로 분리한다.
8. rollback은 효과 미약이 아니라 safety breach 기준이다. 주문 실패/receipt 손상, stale quote submit, hard/protect/emergency stop 지연, severe loss guard breach가 있으면 즉시 OFF 후보로 닫는다.

### 장중 명시적 Scalp Pre-AI Gate Override 절차

이 절차는 사용자가 스캘핑 pre-AI gate 재설계를 당일 runtime 운영 override로 명시한 경우에만 쓴다. 자동화체인의 기본 원칙은 여전히 장중 mutation 금지이며, 이 override는 operator 지시로 코드와 runtime env를 함께 반영한 별도 cohort다.

1. `strength_momentum`, `blocked_vpw`, `overbought`, `liquidity`는 AI 전 terminal block이 아니라 `metric_role=risk_context`, `decision_authority=source_quality_only`, `runtime_effect=false` 관찰 이벤트로 남긴다.
2. `insufficient_history`, stale quote/context, 극단적 매도 우위는 source-quality pre-AI blocker로 계속 fail-closed한다.
3. `liquidity_pre_submit_guard_p1`은 AI/counterfactual을 허용하되 `MIN_SCALP_LIQUIDITY` 미만이면 broker submit 직전 `pre_submit_liquidity_guard_block`으로 차단한다.
4. `overbought_pullback_guard_p1`은 AI/counterfactual을 허용하되 pullback/rebreak가 확인되지 않으면 broker submit 직전 `pre_submit_overbought_pullback_guard_block`으로 차단한다.
5. runtime env에는 `KORSTOCKSCAN_SCALP_PRE_AI_SOFT_GATE_ENABLED=true`, `KORSTOCKSCAN_SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=true`, `KORSTOCKSCAN_SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED=true`, `KORSTOCKSCAN_SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED=true`를 명시한다.
6. `restart.flag` 기반 graceful restart 후 `/proc/<pid>/environ`에서 위 4개 env와 기존 selected family env가 모두 로드됐는지 확인한다.
7. post-restart cohort는 `blocked_strength_momentum|blocked_vpw|blocked_overbought|blocked_liquidity gate_action=risk_context_only`, `ai_confirmed`, `scalp_sim_entry_armed`, `budget_pass`, `latency_pass|latency_block`, `order_bundle_submitted`, `pre_submit_liquidity_guard_block`, `pre_submit_overbought_pullback_guard_block`, `buy_order_sent`, `COMPLETED + valid profit_rate`를 분리 집계한다.
8. 이 override는 score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제 권한이 아니다.
9. rollback은 `KORSTOCKSCAN_SCALP_PRE_AI_SOFT_GATE_ENABLED=false` 또는 개별 pre-submit guard env 해제로 수행하되, source-quality blocker 증가, stale submit, guard breach, severe loss, receipt/provenance 손상이 있으면 즉시 OFF 후보로 닫는다.

### 장중 명시적 Scalp Entry/Holding ADM Runtime Override 절차

이 절차는 사용자가 스캘핑 Entry ADM 또는 보유/청산 ADM을 운영 override로 즉시 열라고 명시한 경우에만 쓴다. 산출물은 여전히 report/source bundle이지만 runtime env가 켜져 있으면 AI action을 직접 보정한다. ADM은 broker submit owner가 아니며 stale quote, liquidity, overbought, latency, price freshness, hard stop, emergency stop, account cap, cooldown, qty cap safety guard를 우회하지 않는다.

1. runtime env에는 `KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED=true`, `KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=true`, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=true`, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=true`, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=true`를 명시한다. 기본값은 context-only 안전값(false)이므로, 이 절차는 사용자가 직접 runtime bias override를 승인한 경우에만 적용한다.
2. AI entry prompt에 `[Entry ADM Advisory Context]`, holding/exit flow prompt에 `[ADM Advisory Context]`가 append되는지 확인한다. 기존 `entry_v1`/`holding_exit_flow_v1` 응답 schema는 바꾸지 않는다.
3. cache key에는 `entry_adm:<matrix_version>:<bucket_token>`이 포함되어 ADM context 변경 후 stale cache가 재사용되지 않아야 한다.
4. entry ADM은 matched bucket이 최소 sample/joined sample 기준을 통과한 경우에만 dominant action이 `WAIT_REQUOTE/SKIP_STALE`이면 `BUY -> WAIT`, `NO_BUY_AI/SKIP_SOURCE_QUALITY/SKIP_PRE_SUBMIT_SAFETY`이면 `BUY -> DROP`, `BUY_NOW/BUY_DEFENSIVE` bucket의 `source_quality_adjusted_ev_pct < 0`이면 `BUY -> WAIT`로 보정한다. hypothesis fallback은 기본 provenance-only이며 `KORSTOCKSCAN_SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED=true`가 별도로 켜진 경우에만 WAIT/DROP으로 보정한다.
5. holding/exit ADM은 `prefer_exit`이면 `HOLD/TRIM -> EXIT`, `prefer_avg_down_wait` 또는 `prefer_pyramid_wait`이면 `EXIT/DROP/SELL -> HOLD`로 보정할 수 있다. `TRIM -> HOLD`는 기본 차단이고 `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED=true`에서만 허용한다. matrix가 비어 있으면 loss/AI 회복 구간은 `holding_exit_matrix_avg_down_bias`, profit/AI 강세 구간은 `holding_exit_matrix_pyramid_bias`로 scale-in evaluator에 전달한다.
6. `scalp_entry_action_decision_snapshot` 이벤트가 AI 판단 직후부터 submit 전까지 남는지 확인한다. 필수 필드는 `candidate_id`, `record_id`, `sim_record_id`, `ai_score`, `chosen_action`, `eligible_actions`, `rejected_actions`, risk/stale/price/liquidity/overbought/time bucket, `actual_order_submitted`, `broker_order_forbidden`, `entry_adm_runtime_effect`다. holding/exit pipeline에는 `holding_exit_matrix_runtime_effect`, `holding_exit_matrix_forced_action`, `holding_exit_matrix_scale_in_bias`를 남긴다.
7. sim/probe/no-buy/counterfactual 표본은 `actual_order_submitted=false`로 유지한다. ADM 산출물 자체는 `runtime_effect=false`로 닫되, runtime env override가 실제 AI action 보정 권한을 갖는 것으로 분리 기록한다.
8. rollback은 `KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=false`, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=false`, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=false`로 수행한다. 주문 실패, stale submit, receipt/provenance 손상, severe loss가 있으면 기존 submit/safety owner 기준으로 incident를 분리한다.

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
2. `12:05` 장중 calibration은 anomaly correction 후보와 source freshness만 확인한다. `cron_completion` 기준 완료 marker는 `logs/threshold_cycle_calibration_intraday_cron.log`의 `[DONE] threshold-cycle calibration target_date=YYYY-MM-DD phase=intraday`다. 산출물이 존재하고 marker만 없으면 runtime 장애가 아니라 wrapper/log 계약 결함으로 분류한다.
3. `pipeline_events_YYYY-MM-DD.jsonl` append가 멈추지 않았는지 확인한다. `threshold_events_YYYY-MM-DD.jsonl`는 threshold-family 대상 stage만 남는 sparse compact stream이므로, stale은 fatal runtime 중단이 아니라 source coverage warning으로 분류한다.
4. 스윙 dry-run은 실전 판단 흐름 관찰용이다. `swing_sim_*`, `swing_probe_*`, `blocked_swing_score_vpw`, `swing_entry_micro_context_observed`, `swing_scale_in_micro_context_observed`, `swing_sim_scale_in_order_assumed_filled`, `swing_probe_scale_in_order_assumed_filled`, `holding_flow_ofi_smoothing_applied`가 보이면 주문 제출 여부와 별도로 provenance만 본다. `swing_probe_*`는 `data/runtime/swing_intraday_probe_state.json`에서 재시작 복원되며, open cap/일일 cap 초과 시 `swing_probe_discarded`로 닫힌다.
5. 스캘핑 live simulator는 실전 주문이 아니라 BUY 신호 전체 관측용 `signal_inclusive_best_ask_v1` 가상 체결이다. quote touch/timeout은 진입 허들이 아니라 `would_limit_fill`, `fill_source`, `limit_fill_price` 진단 필드로만 본다. 장중에는 `scalp_sim_*` stage와 Kiwoom WS 유지 여부만 확인하고, sim 손익만으로 당일 threshold를 바꾸지 않는다.
6. sim/probe 수량과 lifecycle 생성은 실계좌 주문가능금액이 아니라 `SIM_VIRTUAL_BUDGET_KRW`와 동적수량 산식 provenance를 기준으로 본다. `active_count=0`, `post_sell_joined_candidates=0`, AVG_DOWN/PYRAMID completed `0`은 실주문/시뮬레이션 source split과 lifecycle arm별 blocker를 먼저 확인한 뒤 병목으로 분류한다.
7. 패닉셀 급변 구간은 `panic_sell_defense_report`로 `panic_state`, stop-loss cluster, active sim/probe 회복률, post-sell rebound를 분리 확인한다. 이 리포트는 `report_only_no_mutation`이며 score/stop threshold 변경, 자동매도, 봇 재기동, 스윙 실주문 전환 권한이 없다.
8. `RUNTIME_OPS`, snapshot failure, model call timeout, 주문 receipt/provenance 손상이 있으면 전략 threshold 문제가 아니라 운영 장애로 분류한다.
9. safety breach가 아니라 목표 미달이면 rollback이 아니라 postclose calibration 입력으로 넘긴다.

표준 확인 명령:

```bash
tail -n 80 logs/run_buy_funnel_sentinel_cron.log
tail -n 80 logs/run_holding_exit_sentinel_cron.log
tail -n 80 logs/run_panic_sell_defense_cron.log
tail -n 80 logs/run_panic_buying_cron.log
tail -n 80 logs/threshold_cycle_calibration_intraday_cron.log
grep -n "threshold-cycle calibration target_date=$(TZ=Asia/Seoul date +%F)" logs/threshold_cycle_calibration_intraday_cron.log || true
ls -l data/pipeline_events/pipeline_events_$(TZ=Asia/Seoul date +%F).jsonl
ls -l data/threshold_cycle/threshold_events_$(TZ=Asia/Seoul date +%F).jsonl
ls -l data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_$(TZ=Asia/Seoul date +%F)_intraday.md
PYTHONPATH=. .venv/bin/python -m src.engine.panic_sell_defense_report --date $(TZ=Asia/Seoul date +%F) --print-json
PYTHONPATH=. .venv/bin/python -m src.engine.panic_buying_report --date $(TZ=Asia/Seoul date +%F) --print-json
bash deploy/run_error_detection.sh full
ls -l data/report/panic_sell_defense/panic_sell_defense_$(TZ=Asia/Seoul date +%F).json
```

## 장후 확인 절차

`build_codex_daily_workorder --slot POSTCLOSE`는 이 절차를 `PostcloseAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

POSTCLOSE 최상위 감리는 `Tuning Chain Control State`(튜닝 체인 관제 상태)로 남긴다. 이 관제 상태는 EV 손익의 좋고 나쁨이 아니라 자동화체인이 매일 믿을 수 있게 수집, 분석, 해석, 라우팅, 반영, 피드백까지 이어졌는지 보는 운영 판정이다. 새 리포트나 새 checklist 항목을 만들지 않고, 기존 `PostcloseAutomationHealthCheckYYYYMMDD` 실행 메모에 `상태 / 막힌 단계 / 영향 / 조치` 4요소만 기록한다.

### Runbook 운영 확인 완료 기록

- `[PostcloseAutomationHealthCheck20260521] 장후 자동화체인 상태 확인` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~20:45`)
  - 판정: `warning`
  - Tuning Chain Control State: `YELLOW`
  - blocked_stage: `chain_completion`
  - impact: 16:10 postclose wrapper는 `daily_threshold_cycle_report` 단계에서 OS kill로 terminal `[DONE]` marker 없이 종료됐다. 이후 수동 복구로 `threshold_cycle_ev`, `runtime_approval_summary`, `lifecycle_decision_matrix`, `code_improvement_workorder`, `threshold_cycle_postclose_verification` 산출물과 downstream handoff는 복원됐으므로 다음 PREOPEN 입력은 artifact 기준으로 읽을 수 있지만, 원천 wrapper 완료성은 경고로 남긴다.
  - 근거: [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log)는 `deploy/cpu_affinity_profile.sh ... Killed taskset ... daily_threshold_cycle_report`를 남겼다. [threshold_cycle_postclose_verification_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-21.json)은 `status=pass_with_pending_done_marker`, `missing_required_artifacts=[]`, `missing_downstream_links=[]`, `entry/scale_in/overnight handoff=pass`다. `error_detector --mode full --dry-run` 기준 process/resource/artifact freshness는 pass이며, 남은 warning은 preclose overnight log 미도래/미생성 계열이다.
  - 다음 액션: 다음 16:10 postclose에서 bot restart isolation이 `[DONE]` marker까지 닫히는지 확인한다. `daily_threshold_cycle_report` peak RSS는 streaming/chunked aggregation workorder로 줄이고, 이 운영 경고를 threshold/order/provider/bot restart 전략 효과 근거로 쓰지 않는다.

| 상태 | 의미 | 닫는 기준 |
| --- | --- | --- |
| `GREEN` | R0~R6, workorder, approval/runtime routing, post-apply attribution이 모두 복원 가능 | 다음 PREOPEN 입력으로 사용할 수 있으며, 별도 신규 조치 없음 |
| `YELLOW` | 체인은 완료됐지만 일부 판단이 표본/품질/계약/미래 quote/provenance 문제로 보류 | `blocked_stage`, 원인, 영향 범위, 다음 확인 owner를 남기고 observe/workorder/approval 중 하나로 라우팅 |
| `RED` | artifact 누락, parser 실패, wrapper fail, lineage 깨짐, runtime provenance 손상 등 다음 튜닝 판단을 믿으면 안 되는 상태 | 원천 artifact 복구, postclose 재생성, incident/playbook 또는 instrumentation workorder로 닫음 |
| `GRAY` | 아직 due 전이거나 postclose chain이 실행 중 | 완료 예정 시각과 재확인 owner만 남김 |

관제 단계는 아래 6개로 고정한다. 상세 리포트가 여러 개여도 최종 메모에는 문제가 발생한 단계만 `blocked_stage`로 적는다.

| 단계 | 확인 초점 | 대표 근거 |
| --- | --- | --- |
| `input_health` | source freshness, source-quality, provenance split | error detector, `observation_source_quality_audit`, source load diagnostics |
| `chain_completion` | postclose wrapper, predecessor, verification 완료 | wrapper status, `[DONE]` marker, `threshold_cycle_postclose_verification` |
| `decision_integrity` | `selected/blocked/hold_sample/freeze/contract_gap` 해석이 금지선과 맞는지 | `threshold_cycle_ev`, `runtime_approval_summary` |
| `disposition` | apply/workorder/approval/observe-only/next-checklist 중 하나로 라우팅됐는지 | `code_improvement_workorder`, `HumanInterventionSummary`, approval artifact |
| `runtime_uptake` | 적용된 축이 runtime env와 pipeline provenance로 복원 가능한지 | apply plan, runtime env, runtime event provenance |
| `feedback_closure` | attribution 또는 다음날 확인 항목으로 닫혔는지 | post-apply attribution, 다음 checklist, workorder lineage |

1. `threshold_cycle_postclose`가 완료됐는지 먼저 확인한다.
   - `paused_by_availability_guard`로 compact collection이 멈춘 경우는 자동 재시도되지 않는다. wrapper는 `[PAUSED]`와 `[FAIL]` marker를 남기며, I/O 부하가 낮아진 뒤 같은 날짜로 재실행한다. 단, checkpoint가 이미 source 끝까지 처리된 재실행은 availability sampler로 다시 실패시키지 않고 `completed` replay로 통과해야 한다.
   - postclose wrapper는 immutable snapshot을 날짜별 최신 1개만 유지하고, 같은 날짜 중복 snapshot 및 retention(`THRESHOLD_CYCLE_SNAPSHOT_RETENTION_DAYS`, 기본 7일) 초과 snapshot을 자동 정리한다.
   - wrapper 자체의 조용한 skip/fail을 막기 위해 `data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_YYYY-MM-DD.status.json`을 함께 확인한다. `status=succeeded`만 정상 완료이며 `running`, `skipped`, `failed`는 postclose 산출물 freshness와 별개로 운영 경고/실패 입력이다.
2. 제출 기준은 `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`다.
   - `cron_completion`이 `threshold_cycle_postclose=in_progress`인 동안 `artifact_freshness`가 `threshold_cycle_ev` missing을 먼저 보고하면 job 완료 전 조기 확인으로 분류하고 `warning`으로 둔다.
   - window end(`17:00`)를 지난 뒤에도 `threshold_cycle_postclose` wrapper가 `[START]`만 있고 아직 `[DONE]/[FAIL]`가 없는 경우 `artifact_freshness.threshold_postclose_report_status=warning`, `upstream_status=in_progress_after_window`로 유지한다. 완료 marker 후에도 산출물이 없으면 그때 `fail`이다.
   - `threshold_cycle_ev`는 장후 1회성 제출 artifact다. 파일이 생성되고 JSON parse 검증이 끝난 뒤에는 장중 stream처럼 계속 갱신되지 않아도 `pass_one_shot`으로 본다. 생성 후 age가 `max_staleness_sec`를 넘었다는 이유만으로 재실행/재기동하지 않는다. 단, `.json` 파일이 깨졌거나 dict payload가 아니면 one-shot fresh로 통과시키지 않고 critical source 품질 실패로 닫는다.
3. 스캘핑/스윙 판정 요약은 `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.md`에서 먼저 본다. `Gate 분류`와 `튜닝 경로` 컬럼으로 legacy hard gate, intentional safety guard, runtime contract gap, same-stage owner conflict, sample/source-quality gap을 분리한다. 이 artifact는 `threshold_cycle_ev`와 `swing_runtime_approval`을 읽기만 하며 runtime flow 조정, 적용, 차단 권한이 없다.
   - `threshold_cycle_ev`와 `runtime_approval_summary`의 `source_load_diagnostics`가 비어 있지 않으면 입력 artifact parse 오류가 report 내부 warning으로 보존된 상태다. 같은 date로 원천 artifact를 복구한 뒤 EV -> runtime summary -> postclose verification 순서로 재생성한다.
   - `latency_classifier_runtime_profile`은 `entry_funnel.latency_submit_routing`, `recommended_action`, `counterfactual_ev_pct`, `missed_winner_recovered`, `avoided_loser_lost`, `stale_quote_override_events`, `broker_guard_bypass_candidates`를 같이 확인한다. `recommended_action=hold|reject`이면 다음 PREOPEN latency env를 만들지 않는다. `selected_auto_bounded_live=true`가 과거 당일 적용 이력으로 남아 있어도 신규 적용 판단은 최신 `latency_classifier_recommendation`과 PREOPEN apply artifact의 `allowed_runtime_apply`가 우선한다.
4. threshold 후보의 상세 원인은 `threshold_cycle_YYYY-MM-DD.json`, AI correction은 `threshold_cycle_ai_review_*_postclose.md`, lab order는 `scalping_pattern_lab_automation_YYYY-MM-DD.md`, 스윙 lifecycle order는 `swing_improvement_automation_YYYY-MM-DD.json`, 스윙 승인 요청은 `swing_runtime_approval_YYYY-MM-DD.json`을 본다.
   - latency submit drought를 점검할 때는 `latency_classifier_recommendation_YYYY-MM-DD.json`을 함께 본다. 이 report는 grid/quantile profile별 `SAFE pass`, `CAUTION reject`, 제한 복구 카나리(recovery canary), `hard reject`, counterfactual EV, missed/avoided label을 계산한다. `pre_submit_price_guard`는 이 값을 소비할 수 있지만 소유권은 latency classifier에 있다.
5. `threshold_cycle_ev_YYYY-MM-DD.{json,md}`에서 `real`, `sim`, `combined` split과 `scalp_simulator.post_sell_join`을 확인한다. combined는 tuning 후보 산출용 통합 EV view이고, broker execution 품질과 주문 실패율은 real만으로 별도 판정한다.
6. sim 청산 후 MFE/MAE는 `data/post_sell/sim_post_sell_candidates_YYYY-MM-DD.jsonl`과 `sim_post_sell_evaluations_YYYY-MM-DD.jsonl`에서 확인한다. 기존 실주문 `post_sell_candidates/evaluations`와 섞지 않고, join 누락은 `instrumentation_gap` 또는 `source_quality_blocker`로 분류한다.
7. 스캘핑 Entry ADM은 `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.{json,md}`에서 확인한다. `joined_sample < sample_floor`, `missing_action_bucket`, `prompt_context_not_loaded`는 runtime apply 후보가 아니라 instrumentation/report workorder로만 닫고, `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, `scalping_pattern_lab_automation` source link가 이어졌는지 본다.
8. sim-first lifecycle coverage는 스캘핑 `scalp_ai_buy_all`/missed-entry counterfactual과 스윙 dry-run/probe가 entry, holding, scale-in, exit arm을 만들었는지, 각 결과가 daily EV, threshold cycle, code-improvement workorder, runtime approval summary consumer에 들어갔는지로 확인한다. 누락은 `consumer_gap`, `lifecycle_arm_gap`, `source_quality_blocker`, `sample_floor_gap` 중 하나로 닫는다.
8. 스윙 postclose는 먼저 `deploy/run_swing_daily_simulation_report.sh`로 `swing_daily_simulation_YYYY-MM-DD.{json,md}`와 status artifact를 생성한 뒤 `swing_lifecycle_audit`를 읽는다. 해당 artifact가 실제로 존재하고 JSON 검증이 끝날 때까지 대기한 뒤 `swing_lifecycle_audit`/`swing_runtime_approval`을 갱신한다.
9. 스윙 postclose는 `recommendation_db_load`, `scale_in_observation`, `ai_contract_metrics`, `ofi_qi_summary`, `runtime_effect=false`, `allowed_runtime_apply=false`, `approval_requests`, `blocked_requests`를 확인한다.
10. `swing_runtime_approval`에서 hard floor 통과 여부와 `tradeoff_score >=0.68` 요청을 확인한다. 요청이 생성되어도 approval artifact가 없으면 다음 장전 env 반영은 금지된다.
11. DeepSeek 스윙 lab re-entry는 `run_manifest.json`의 `analysis_window.start == target_date == end`와 필수 JSON schema 유효성이 닫힌 경우에만 fresh로 본다. stale/range/malformed output은 warning만 남기고 order로 승격하지 않는다.
12. OFI/QI source-quality는 `stale_missing_flag` 단일 boolean으로만 보지 않고 `micro_missing`, `micro_stale`, `observer_unhealthy`, `micro_not_ready`, `state_insufficient` reason과 unique record count를 함께 본다. 스윙 scale-in micro context는 fresh WS quote가 있는데 observer가 비정상이면 `observer_gap_with_fresh_ws_quote`로 분리해 workorder/provenance 입력으로만 라우팅한다. 이 값은 `source_quality_blocked_families`와 approval/workorder blocker 입력으로 쓸 수 있지만, 단독 runtime mutation 근거는 아니다.
13. 스윙 실주문 전환 checkpoint는 전체 live 전환이 아니라 최대 `swing_one_share_real_canary` 승인 요청 여부만 판단한다. 승인 artifact가 없으면 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`를 유지한다.
14. 스윙 숫자 floor checkpoint는 `swing_model_floor` 후보를 `approval_required|hold_sample|freeze`로 닫는다. 사용자 approval artifact가 없으면 다음 장전 floor env를 쓰지 않는다.
15. `pipeline_event_verbosity_report`는 workorder 생성 전에 생성되어 raw size/line count, high-volume diagnostic share, V1 raw-derived summary와 producer-side summary parity, suppress eligibility를 남긴다. 이 artifact는 `diagnostic_aggregation` authority만 있고 threshold/order/provider/bot restart 권한이 없다.
16. `codebase_performance_workorder_report`는 `docs/codebase-performance-bottleneck-analysis.md`를 source로 읽어 accepted/deferred/rejected 성능개선 후보를 생성한다. accepted 후보도 사용자 별도 구현 지시 전에는 코드 변경이 아니며, 실주문/threshold/provider/관찰튜닝축/source-quality/forensic raw stream 변경 권한이 없다.
17. `pattern_lab_currentness_audit`는 scalping Gemini/Claude와 DeepSeek swing lab의 schema v2, metric contract, 금지어, Gemini remote source mode, Claude stale CSV guard, DeepSeek sim/probe provenance를 검사한다. 실패/경고는 tuning 후보가 아니라 `instrumentation_gap` 또는 `source_quality_blocker` 성격의 `runtime_effect=false`, `allowed_runtime_apply=false` workorder 후보로만 남긴다.
18. code improvement workorder는 same-day `threshold_cycle_ev`, `scalp_entry_action_decision_matrix`, `pipeline_event_verbosity`, `observation_source_quality_audit`, `codebase_performance_workorder`, `pattern_lab_currentness_audit`, `scalping_pattern_lab_automation`, `swing_improvement_automation`, `swing_pattern_lab_automation`을 source로 읽는다. postclose wrapper는 `threshold_cycle_ev` pre-pass artifact를 먼저 확인한 뒤 workorder를 만들고, workorder JSON/Markdown이 닫힌 다음 `threshold_cycle_ev`를 재생성해 workorder summary를 refresh한다.
19. `pattern_lab_propagation_audit`는 당일 lab automation, currentness audit, code improvement workorder, threshold EV, runtime approval summary source link를 점검한다. runtime summary는 audit 이후 생성되므로 같은 wrapper 안에서는 propagation audit 결과를 다시 `threshold_cycle_ev`에 refresh한 뒤 runtime summary가 읽는다.
20. 신규 code improvement order는 scalping/swing/source-quality/performance/currentness source를 병합해 자동으로 작업지시서로 변환된다. 사용자는 `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`를 Codex 세션에 넣고 구현을 요청한다.
21. `build_next_stage2_checklist`가 다음 KRX 영업일 checklist를 생성/갱신한다. 이 checklist가 사람 개입/판정/승인 요구사항의 source of truth이며, `codex_daily_workorder_*.md`는 checklist/Project/RunbookOps를 읽어 만든 downstream 전달물이라 자동화 입력으로 쓰지 않는다.
22. `threshold_cycle_postclose_verification_YYYY-MM-DD.{json,md}`는 postclose wrapper 마지막 단계에서 생성한다. 이 artifact가 latest `START` 이후 predecessor wait/timeout/fail, 필수 audit artifact, DONE marker flag, downstream source link, workorder `generation_id/source_hash/lineage`를 확인한다.
23. `17:30` swing model retrain은 `swing_model_retrain_YYYY-MM-DD.status.json`, diagnosis, promotion guard, current registry를 확인한다. auto-promote가 성공해도 model artifact promotion만 의미하며, 스윙 dry-run 해제, threshold/floor env 작성, 브로커 주문 허용으로 해석하지 않는다.
24. `20:05` tuning monitoring은 `threshold_cycle_postclose`의 같은 날짜 최신 terminal marker가 `[DONE]`이 아니면 대기하거나 fail-closed한다. postclose가 장시간화되어 20:05 이후에도 실행 중이면 Parquet/DuckDB refresh가 선행 산출물을 덜 소비하지 않도록 wrapper dependency를 우선한다.
25. 날짜별 checklist를 수정했다면 parser 검증 후 Project/Calendar 동기화 명령을 사용자에게 남긴다.
26. OpenAI AI correction은 품질 우선 `gpt-5.5` 경로라 수 분 단위로 걸릴 수 있다. 15분 이내 실행 중이면 `not_yet_due`, 15분 초과 미생성이면 cron log와 job 종료 여부를 확인해 `warning` 또는 `fail`로 분류한다. cron timeout은 이보다 짧게 잡지 않는다.

표준 확인 명령:

```bash
tail -n 120 logs/threshold_cycle_postclose_cron.log
ls -l data/report/threshold_cycle_ev/threshold_cycle_ev_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_selection_funnel/swing_selection_funnel_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_lifecycle_audit/swing_lifecycle_audit_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_threshold_ai_review/swing_threshold_ai_review_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_improvement_automation/swing_improvement_automation_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/swing_runtime_approval/swing_runtime_approval_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/swing_daily_simulation/swing_daily_simulation_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_model_retrain/status/swing_model_retrain_$(TZ=Asia/Seoul date +%F).status.json
ls -l data/report/swing_model_retrain/swing_model_retrain_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_$(TZ=Asia/Seoul date +%F).md
ls -l docs/code-improvement-workorders/code_improvement_workorder_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/runtime_approval_summary/runtime_approval_summary_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_$(TZ=Asia/Seoul date +%F).md
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

## 21:00 데이터 갱신 확인 절차

`update_kospi.py`는 매매 runtime과 분리된 EOD 데이터 체인이다. DB 적재, dashboard upload, swing recommendation, swing daily reports가 한 status JSON 안에 step별로 남는다.

1. `logs/update_kospi.log`에서 당일 `[START] update_kospi target_date=YYYY-MM-DD`와 `[DONE]` 또는 `[FAIL]` marker를 확인한다.
2. `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json`의 `status`, `failed_steps`, `warning_steps`, `recovered_steps`, `db_state.latest_quote_date`, `db_state.rows_on_latest_date`를 확인한다.
3. `status=completed_with_warnings`는 DB 장애와 동일하지 않다. `failed_steps`가 `recommend_daily_v2`, `upload_today_dashboard_files`, `swing_daily_reports` 중 어디인지 분리한다.
4. `recommend_daily_v2` 실패는 `data/daily_recommendations_v2.csv` 갱신 여부와 traceback을 같이 본다. 추천 모델 subprocess는 repo root `cwd`와 직접 실행 sys.path bootstrap을 요구한다.
5. `log_scanner`가 `_error.log` 안의 INFO성 `DB 일괄 삽입 성공`/`DB 업로드 완료`를 DB 장애로 해석하지 않도록, 실제 ERROR/traceback 후보 라인과 status JSON을 우선 본다.
6. `update_kospi` 실행은 보통 20~40분 걸릴 수 있다. detector window end 전 `START-only`는 `in_progress`로 본다.

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
| 승인 요청 생성 | closed sim lifecycle과 real completed가 함께 hard floor 및 trade-off score 입력이 된다 | `overall_ev 45% + downside_tail 20% + participation/funnel 15% + regime_robustness 10% + attribution_quality 10%` 총점이 `0.68` 이상이면 요청 가능 | approval artifact 없이는 preopen env 반영 금지. 반영되더라도 dry-run 유지 |
| 1주 real canary | EV 후보 선별과 approval request 생성에는 closed sim lifecycle을 사용 | 승인 대상 우선순위와 expected EV trade-off 산정에 combined 사용 | 실제 BUY/SELL receipt, order number binding, fill ratio, slippage, cancel/timeout, sell receipt는 real-only |
| 전체 실주문 전환 | 사용하지 않음 | 사용하지 않음 | 별도 2차 계획/승인, broker execution guard, dry-run 해제 승인 없이는 금지 |

### 스윙 1주 Real Canary 진행 기준

`swing_one_share_real_canary`는 스윙 dry-run 체계를 유지한 상태에서 broker execution 품질만 real source로 보강하는 phase0 축이다. 이 축은 `swing_runtime_approval`과 별도 approval artifact가 있어야만 다음 장전 preopen apply에서 열 수 있다.

| 항목 | phase0 기준 |
| --- | --- |
| 기본 상태 | OFF / approval-required |
| 전제 | `swing_runtime_approval` hard floor 통과, EV trade-off score 통과, DB load gap 없음, fallback diagnostic contamination 없음, critical instrumentation gap 없음, severe downside guard 통과, same-stage owner conflict 없음 |
| 승인 | `approval_required`만으로는 부족하다. 사용자가 `data/threshold_cycle/approvals/swing_one_share_real_canary_YYYY-MM-DD.json` approval artifact를 남긴 경우에만 다음 장전 적용한다 |
| env | `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_QTY`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT` |
| 수량/노출 | `qty=1`, `max_new_entries_per_day=1`, `max_open_positions=3`, `max_total_notional_krw=300000`, same-symbol active real canary 1개 |
| 주문 범위 | 승인 후보의 BUY와 해당 포지션 청산 SELL만 실제 주문. phase0에서는 AVG_DOWN/PYRAMID/scale-in 실주문 금지 |
| provenance | `actual_order_submitted=true`, `simulation_book` 없음, `cohort=swing_one_share_real_canary`, `canary_qty_cap=1`, 승인 id 기록 |
| real-only metric | broker receipt, order number binding, submit/reject, partial/full fill, slippage, cancel/timeout, sell receipt, 주문 실패율 |
| combined metric | realized PnL과 lifecycle outcome은 combined EV에 들어갈 수 있지만 sim fill quality와 real fill quality는 합산하지 않는다 |
| rollback | approval artifact 밖 실주문 1건, qty > 1, global dry-run 해제, receipt/order number mismatch, sell failure, price guard breach, daily/open/notional cap 초과, provenance 누락 |

`threshold_cycle_preopen_apply`는 artifact가 없으면 `one_share_real_canary_approval_artifact_missing`으로 env를 만들지 않는다. artifact가 있어도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`를 유지하고 승인 code allowlist 밖 초기 BUY는 runtime에서 fail-closed 차단한다.

운영자는 이 기준이 충족되어도 스윙 전체 실주문 전환으로 해석하지 않는다. real canary가 통과한 뒤 전체 dry-run 해제를 검토하려면 별도 2차 계획, broker execution guard, 사용자 승인이 필요하다.

### 스윙 Scale-In Real Canary 진행 기준

`swing_scale_in_real_canary_phase0`는 initial BUY/SELL real canary와 분리된 별도 approval-required 축이다. 이 축은 전체 스윙 실매매 전환이 아니라 이미 승인된 real swing holding에서 AVG_DOWN/PYRAMID 추가매수 주문 품질을 1주 cap으로 수집한다.

| 항목 | phase0 기준 |
| --- | --- |
| 기본 상태 | OFF / `KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ENABLED=false` |
| 승인 artifact | `data/threshold_cycle/approvals/swing_scale_in_real_canary_YYYY-MM-DD.json` |
| 허용 arm | `PYRAMID`, `AVG_DOWN` 중 arm별 hard floor를 통과하고 artifact의 `allowed_actions`에 포함된 arm만 허용 |
| 수량/노출 | `real_canary_actual_qty=1`, `max_orders_per_day=1`, `max_orders_per_position=1`, `max_daily_notional_krw=100000` |
| 주문 방식 | 시장가 금지. best bid 또는 defensive limit resolver 가격만 허용 |
| block | sim/probe/dry-run 포지션, 승인되지 않은 arm, stale quote, `orderbook_micro_ready=false`, OFI/QI `RISK_BEARISH`, pending add/sell, cap 초과 |
| provenance | `cohort=swing_scale_in_real_canary_phase0`, `actual_order_submitted=true`, `would_qty`, `effective_qty`, `real_canary_actual_qty=1`, `real_canary_qty_cap=1`, `qty_cap_reason=swing_scale_in_real_canary_phase0` |
| rollback | 승인 밖 주문, qty > 1, sim/probe real order attempt, receipt lifecycle mismatch, stale submit, OFI/QI bearish submit |

## 신규 Approval Artifact 처리 절차

`approval_request`는 자동화체인이 만든 사용자 승인 요청이다. 생성 자체는 runtime 효과가 없으며, approval artifact가 없으면 `threshold_cycle_preopen_apply`는 env를 쓰지 않는다. 사람/operator가 남는 지점은 장후 산출물에서 승인 요청을 검토한 뒤 다음 장전 apply에 넘길 approval artifact를 만들지 결정하는 단계다. 이 절차는 code improvement workorder 검토와 같은 POSTCLOSE 수동 triage 대상이다.

### 1. Intake

입력 artifact:

- `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.json`
- `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.md`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.json`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`
- `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.json`
- `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.md`
- `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`
- `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`

확인 필드:

| 필드 | 의미 | 처리 |
| --- | --- | --- |
| `approval_id` | 승인 요청 식별자 | approval artifact의 `approved_request_ids`에 그대로 보존 |
| `policy_id` / `family` | 승인 대상 축 | 지원되는 approval contract인지 확인. contract missing이면 artifact를 만들어도 live 반영 금지 |
| `calibration_state` | 승인 요청 상태 | `approval_required`만 artifact 검토 대상. `hold_sample`, `freeze`, `blocked_by_policy`는 승인하지 않는다 |
| `candidate_codes` / `candidate_rows` | 승인 후보 종목/대상 | allowlist와 일치해야 한다. 후보 밖 코드는 승인 artifact에 넣지 않는다 |
| `allowed_actions` | scale-in real canary 허용 arm | artifact의 `allowed_actions`는 request의 subset이어야 한다 |
| `recommended_values` | env 후보값 | cap, allowed codes, dry-run 유지 조건이 policy와 일치하는지 확인 |
| `approval_contract_status` | artifact loader/env/runtime guard 준비 여부 | `ready`가 아니면 approval artifact 생성 대신 workorder 또는 보류로 닫는다 |
| `approval_artifact_path` | 소비될 artifact 경로 | 해당 날짜 파일이 있어야 다음 PREOPEN apply가 소비한다 |
| `approval_artifact_approved` | 이미 승인 artifact가 있는지 | true면 중복 생성하지 않고 target date와 approved ids를 확인한다 |
| `blocked_reason` / `block_reasons` | 차단 사유 | 차단이 남아 있으면 artifact를 만들지 않는다 |
| `dry_run_required` / `global_swing_dry_run_must_remain_enabled` | dry-run 유지 계약 | approval artifact가 있어도 global dry-run 해제 금지 |

### 2. 사람 승인 판정

승인 triage는 `HumanInterventionSummaryYYYYMMDD`에서 code improvement workorder와 분리해 닫는다.

| 판정 | 조건 | 다음 액션 |
| --- | --- | --- |
| `approval_artifact_required` | `approval_required`, contract ready, blocker 없음, 후보/cap이 policy와 일치 | operator가 approval artifact 생성 여부를 결정한다 |
| `approval_artifact_created` | artifact가 생성되어 `approved=true`와 request id가 일치 | 다음 PREOPEN apply에서 selected/blocked reason을 확인한다 |
| `approval_artifact_missing` | 승인 요청은 있으나 사용자가 아직 승인하지 않음 | env 미반영이 정상 차단임을 기록하고 다음 영업일 재검토 |
| `blocked_by_policy` | contract missing, source-quality blocker, sample 부족, severe downside, same-stage conflict | artifact 생성 금지. workorder 또는 관찰로 라우팅 |
| `observe_only` | approval request가 없거나 요청이 report-only/proposal-only | live/env/order 변경 없이 관찰만 유지 |

금지선:

- approval artifact를 만든다고 장중 runtime이 바뀌지 않는다. 소비 시점은 다음 PREOPEN apply다.
- approval request만 보고 env 파일을 직접 수정하지 않는다.
- `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`를 approval artifact로 해제하지 않는다.
- `swing_one_share_real_canary_phase0` approval은 초기 BUY/해당 포지션 SELL 1주 execution 품질 수집만 허용한다. 전체 스윙 실매매 전환이나 scale-in 실주문 승인이 아니다.
- `swing_scale_in_real_canary_phase0` approval은 이미 승인된 real swing holding의 승인 arm만 허용한다. sim/probe/dry-run 포지션에는 실주문을 내지 않는다.
- panic/position-sizing 등 `approval_contract_missing` 축은 artifact를 만들어도 preopen env/runtime guard가 소비할 수 없으므로 먼저 code improvement workorder로 계약을 구현한다.

### 3. 현재 지원되는 Approval Artifact 작성 형식

아래 3가지는 `threshold_cycle_preopen_apply`가 현재 실제로 소비하는 approval artifact 형식이다. 단순 예시가 아니며, 이 형식과 경로를 벗어난 approval artifact는 현재 preopen env 반영 근거가 아니다. panic, position sizing, 기타 신규 runtime 승인 후보처럼 `approval_contract_missing`으로 분류되는 축은 approval request가 있더라도 artifact loader, env mapping, runtime guard, rollback test가 구현되기 전까지 approval artifact를 만들어도 소비되지 않는다.

스윙 1주 real canary:

```json
{
  "policy_id": "swing_one_share_real_canary_phase0",
  "approved": true,
  "target_date": "YYYY-MM-DD",
  "allowed_codes": ["000000"],
  "max_order_qty": 1,
  "max_new_entries_per_day": 1,
  "max_open_positions": 3,
  "max_total_notional_krw": 300000,
  "approval_source_report": "data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.json",
  "approved_request_ids": ["swing_one_share_real_canary:YYYY-MM-DD:phase0"],
  "approved_by": "user_chat_YYYY-MM-DD",
  "expires_after_target_date": true
}
```

저장 경로:

```text
data/threshold_cycle/approvals/swing_one_share_real_canary_YYYY-MM-DD.json
```

스윙 scale-in real canary:

```json
{
  "policy_id": "swing_scale_in_real_canary_phase0",
  "approved": true,
  "target_date": "YYYY-MM-DD",
  "allowed_actions": ["PYRAMID"],
  "max_order_qty": 1,
  "max_orders_per_day": 1,
  "max_orders_per_position": 1,
  "approval_source_report": "data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.json",
  "approved_request_ids": ["swing_scale_in_real_canary:YYYY-MM-DD:phase0"],
  "approved_by": "user_chat_YYYY-MM-DD",
  "expires_after_target_date": true
}
```

저장 경로:

```text
data/threshold_cycle/approvals/swing_scale_in_real_canary_YYYY-MM-DD.json
```

일반 스윙 runtime approval:

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

approval artifact 생성 후에도 완료 판정은 다음 PREOPEN에서 닫는다.

1. `deploy/run_threshold_cycle_preopen.sh`가 `[DONE] threshold-cycle preopen target_date=YYYY-MM-DD`로 종료됐는지 확인한다.
2. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`의 `swing_runtime_approval.approved`, `blocked`, `selected`, `decisions`를 확인한다.
3. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`의 `selected_families`와 `env_overrides`에 승인 축이 들어갔는지 확인한다.
4. `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 유지되는지 확인한다.
5. artifact가 있는데 selected되지 않았다면 blocked reason을 checklist에 남기고 env 수동 override는 하지 않는다.

### 5. Checklist/Project 반영

POSTCLOSE `HumanInterventionSummaryYYYYMMDD`는 approval artifact를 code improvement workorder와 동급으로 표면화한다. 최종 사용자 보고와 checklist에는 최소 아래 정보를 남긴다.

- `approval_id`
- `policy_id` / `family`
- 후보 종목 또는 승인 arm
- artifact path
- `approval_artifact_required|created|missing|blocked_by_policy|observe_only` 판정
- 다음 PREOPEN apply 확인 항목

다음 영업일 PREOPEN checklist에는 `SwingApprovalArtifactPreopenMMDD`가 자동 생성되어 artifact 존재 여부, selected env, blocked reason을 확인한다. 누락된 승인 검토가 있으면 날짜별 checklist에 parser-friendly checkbox로 추가한다.

## 신규 Code Improvement Order 처리 절차

`code_improvement_order`는 pattern lab이 만든 machine-readable 작업지시다. 생성 자체는 runtime 효과가 없으며, repo 파일을 직접 수정하지 않는다. postclose wrapper는 이를 Codex 세션 입력용 Markdown 작업지시서로 자동 변환한다. Codex는 사용자가 명시적으로 요청한 workorder만 구현하고 검증한다. 사람/operator가 남는 지점은 생성된 Markdown을 검토한 뒤 Codex 세션에 넣고 "이 작업지시서를 구현하고 검증해줘"라고 요청할지 결정하는 단계다.

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
| `evidence` | Gemini/Claude/EV 근거 | 단일 lab 단독 근거면 priority를 낮추고 runtime 후보 금지 |
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

`attach_existing_family`, `design_family_candidate`, `defer_evidence`는 자동 구현이나 자동 runtime 반영 대상이 아니다. 다만 작업지시서에 남은 이상 operator가 다시 판단할 수 있어야 하므로, 장후 checklist에는 `CodeImprovementWorkorderReview`와 별도로 비-implement 항목 triage를 둔다.

| 판정 | 사람이 다시 보는 시점 | 확인할 것 | 닫는 방식 |
| --- | --- | --- | --- |
| `attach_existing_family` | 다음 영업일 POSTCLOSE code-improvement triage | 기존 threshold family의 report/calibration 입력으로 흡수됐는지, 다음 `threshold_cycle_ev`/family report에 source metric이 보이는지 | `attached_to_existing_family`, `needs_codex_instrumentation`, `stale_no_action` 중 하나 |
| `design_family_candidate` | 다음 영업일 POSTCLOSE code-improvement triage | 새 family 설계가 필요한 반복 패턴인지, `allowed_runtime_apply=false`, sample floor, safety guard, env key, rollback guard가 정의됐는지 | `design_backlog_required`, `merge_into_existing_family`, `reject_or_defer` 중 하나 |
| `defer_evidence` | 다음 영업일 POSTCLOSE code-improvement triage | 새 표본이 추가되어 `implement_now` 또는 `attach_existing_family`로 승격됐는지, 여전히 stale/sample 부족인지 | `promoted`, `continue_defer`, `drop_stale` 중 하나 |

이 triage는 repo 수정을 자동 수행하지 않는다. 결과가 `needs_codex_instrumentation` 또는 `design_backlog_required`이면 operator가 별도 Codex 구현 지시를 내리거나 다음 영업일 checklist에 parser-friendly 항목으로 남긴다. 결과가 `attached_to_existing_family`이면 다음 threshold-cycle/daily EV 산출물에서 재평가되도록 두고, runtime threshold나 주문 guard를 수동 변경하지 않는다.

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

기본 운영에서는 위 checklist 등록을 사람이 직접 하지 않는다. generator가 만든 `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`가 Codex 입력이다. 사용자가 바로 구현을 지시한 경우에는 원본 order id를 final report와 commit message에 남긴다. 단, 미래 재확인이나 특정 시각 검증이 필요하면 날짜별 checklist에 자동 파싱 가능한 항목으로 남긴다.

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

- report/instrumentation order: 다음 `16:10` postclose report와 daily EV에서 source freshness, sample count, warning 감소를 확인한다.
- existing family input 보강: 다음 `12:05` intraday calibration과 `16:10` postclose calibration에서 해당 family의 `calibration_state` 변화를 확인한다.
- new family design: `auto_family_candidate.allowed_runtime_apply=false`를 유지하다가 registry metadata, sample floor, safety guard, tests가 닫힌 뒤에만 `allowed_runtime_apply=true` 후보로 승격한다.
- runtime 후보: 다음 장전 `auto_bounded_live` apply plan에서 selected/blocked reason과 runtime env provenance를 확인한다.

완료 기준:

- 원본 `order_id`가 구현 PR/commit/checklist 판정에 남아 있다.
- acceptance tests가 자동화 테스트 또는 report 검증 명령으로 닫혔다.
- daily EV 또는 postclose artifact에 기대 metric이 나타난다.
- runtime 변경이 있다면 threshold version/family/applied value가 pipeline event 또는 runtime env JSON에서 복원 가능하다.

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

3. `trade_date`가 오늘 KST 날짜와 맞는지, enabled target이 phase0 기본 `active_symbol_limit=1` 안에 있는지, `offer_price`, `budget_cap_krw`, `premium_guard_pct`, `enabled=true`가 의도와 맞는지 확인한다.
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

## ADM 작동 원리

ADM은 `Action Decision Matrix`이며, 단순히 나쁜 feature를 blacklist하는 계층이 아니다. 핵심 목적은 같은 후보에서 `지금 산다`, `호가를 다시 기다린다`, `stale/source-quality 때문에 버린다`, `방어적으로 진입한다`, `AI no-buy를 유지한다`, `보유한다`, `청산한다`, `물타기/불타기를 검토한다` 중 어떤 행동이 더 나았는지를 매일 outcome과 join해 다음 runtime 판단에 반영하는 것이다.

### 0. ADM과 LDM의 관계

ADM은 특정 의사결정면의 전문 matrix이고, LDM(`Lifecycle Decision Matrix`)은 여러 ADM과 sim/counterfactual source를 lifecycle stage로 묶는 상위 umbrella framework다. Entry ADM은 진입 action 품질을 보고, Holding/Exit ADM은 보유/청산 및 scale-in bias를 본다. LDM은 이 결과를 `entry`, `submit`, `holding`, `scale_in`, `exit` stage로 재분류해 stage별 weighted ADM policy를 만든다.

데이터 흐름은 아래 순서로 본다.

```text
pipeline_events / threshold_events / sim events / post-sell labels
  -> Entry ADM, Holding/Exit ADM, submit observation, scale-in adapter, panic/euphoria source
  -> LDM stage rows: entry / submit / holding / scale_in / exit
  -> threshold_cycle_ev / runtime_approval_summary / threshold_cycle_preopen_apply
  -> selected PREOPEN env가 있을 때만 bounded runtime policy로 사용
```

ADM artifact와 LDM artifact는 모두 기본적으로 `runtime_effect=false`인 postclose/source artifact다. Entry ADM 또는 Holding/Exit ADM runtime override가 명시적으로 켜진 경우에는 해당 ADM adapter가 AI action을 보정할 수 있다. LDM은 `lifecycle_decision_matrix_runtime` family가 selected된 다음 장전 env에 policy file/version/promote cap이 기록된 경우에만 기존 ADM adapter를 감싸 stage별 action proposal에 사용된다.

우선순위는 `hard safety veto -> account/order/broker guard -> lifecycle matrix runtime policy -> 기존 ADM adapter -> baseline fixed threshold fallback`이다. 따라서 ADM/LDM이 매수, 보유, 추가매수, 청산 방향의 bias를 제안하더라도 broker submit guard, stale quote, price freshness, hard/protect/emergency stop, 계좌/order/cooldown/qty guard를 우회할 수 없다.

### 0.1 ADM과 LDM의 판정 산출 구조

Entry ADM은 entry 관련 이벤트를 action bucket과 feature bucket으로 묶고 후행 outcome과 join해 action별 `source_quality_adjusted_ev_pct`, missed winner, avoided loser를 만든다. 주요 action은 `BUY_NOW`, `WAIT_REQUOTE`, `SKIP_STALE`, `BUY_DEFENSIVE`, `NO_BUY_AI`, `SKIP_SOURCE_QUALITY`, `SKIP_PRE_SUBMIT_SAFETY`다. joined sample이 충분하고 matched bucket의 dominant action이 확인되면 prompt context 또는 runtime bias가 AI `BUY`를 `WAIT`/`DROP`으로 보정할 수 있다. 양의 action bucket인 `BUY_NOW`/`BUY_DEFENSIVE`는 broker guard를 우회하는 강제 BUY 권한이 아니라 다음 bounded tuning 후보와 provenance 입력이다.

Holding/Exit ADM은 보유/청산 flow AI와 scale-in evaluator가 읽는 advisory matrix다. `prefer_exit`이면 `HOLD`/`TRIM`을 `EXIT`로 보정할 수 있고, `prefer_avg_down_wait` 또는 `prefer_pyramid_wait`이면 `EXIT`/`TRIM`을 `HOLD`로 보정할 수 있다. matrix가 비어 있거나 sample이 부족하면 `no_clear_edge`로 닫고, hypothesis fallback이 손실 회복 구간은 AVG_DOWN bias, 수익 확장 구간은 PYRAMID bias로 scale-in evaluator에 전달할 수 있다.

LDM은 source row마다 runtime feature와 label을 분리한다. runtime feature는 AI score/action, stale/source-quality, liquidity, price resolver, latency, OFI/QI, position PnL/peak/held_sec, risk context 같은 장중에 알 수 있는 값이다. label은 realized profit, MFE/MAE, close horizon, avoided loss, missed upside처럼 사후에만 알 수 있는 값이다. label은 postclose policy 산출에만 쓰고 runtime resolver 입력으로 넣지 않는다.

LDM의 stage별 policy는 joined row의 `stage_ev_composite_pct` 평균, sample floor, joined sample floor, confidence, source-quality gate로 산출한다. entry/submit EV가 양호하면 `BUY_DEFENSIVE` 또는 `ALLOW_SUBMIT`, entry EV가 음수면 `WAIT_REQUOTE`, holding/exit EV가 양호하면 `HOLD`, 음수면 `EXIT`, scale-in EV가 양호하면 `PYRAMID_BIAS`를 제안한다. sample 부족은 rollback이 아니라 `hold_sample` 또는 `NO_CHANGE`로 닫는다. 현재 promote-ready 경로는 entry `BUY_DEFENSIVE` micro canary 중심이며, 다른 stage의 좋은 방향성은 우선 source 수집과 후속 workorder/approval review로 남긴다.

### 1. Entry ADM

Entry ADM의 source artifact는 `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.{json,md}`다. postclose 체인은 entry snapshot, sim buy/sell, sim post-sell evaluation을 `candidate_id` 또는 `sim_record_id`로 join해 action별 `source_quality_adjusted_ev_pct`, missed upside, avoided loss를 만든다.

런타임 기본형에서는 `KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED=true`일 때 entry prompt에 `[Entry ADM Advisory Context]`가 붙지만 AI 결과를 직접 보정하지 않는다. `KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=true`는 명시적 운영 override에서만 AI 결과를 직접 보정한다. 기존 응답 schema는 유지하되 merge 단계에서 action만 보정하므로, downstream은 일반 AI 결과처럼 처리한다.

Entry ADM 보정 규칙은 아래 순서다.

1. matched bucket의 dominant action이 `WAIT_REQUOTE` 또는 `SKIP_STALE`이면 AI `BUY`를 `WAIT`로 바꾼다.
2. dominant action이 `NO_BUY_AI`, `SKIP_SOURCE_QUALITY`, `SKIP_PRE_SUBMIT_SAFETY`이면 AI `BUY`를 `DROP`으로 바꾼다.
3. dominant action이 `BUY_NOW` 또는 `BUY_DEFENSIVE`여도 `source_quality_adjusted_ev_pct < 0`이면 AI `BUY`를 `WAIT`로 바꾼다.
4. `KORSTOCKSCAN_SCALP_ENTRY_ADM_HYPOTHESIS_FALLBACK_ENABLED=true`이면 stale high, source-quality blocker, low liquidity, weak momentum + chase risk 조합을 provenance로 남긴다. joined sample 부족 상태에서 직접 `WAIT` 또는 `DROP`을 적용하려면 `KORSTOCKSCAN_SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED=true`가 별도로 필요하다.

따라서 Entry ADM의 설계 범위는 bad entry 방지에 한정되지 않는다. `BUY_NOW`는 즉시 진입이 더 나았던 bucket을 확인하는 축이고, `BUY_DEFENSIVE`는 진입은 허용하되 가격/호가 품질을 더 보수적으로 가져가야 하는 축이다. 다만 현재 runtime 직접 보정의 강한 영향은 `BUY -> WAIT|DROP`과 `buy_defensive_bias` provenance에 있고, `BUY_NOW`를 강제로 BUY로 승격하거나 broker submit guard를 우회하는 권한은 없다. 이 양의 action bucket들은 postclose ADM/EV/workorder를 통해 다음 runtime env 튜닝 후보로 올라와야 한다.

이 구조 때문에 HPSP처럼 `BUY` 직후 급락한 유형은 특정 종목명으로 차단하지 않는다. 대신 해당 후보가 속한 bucket의 negative EV 또는 weak momentum + chase risk, stale, low liquidity 조건이 확인되면 같은 유형의 다음 후보에서 `BUY -> WAIT|DROP`이 적용된다.

### 2. Holding/Exit ADM

Holding/Exit ADM의 source artifact는 `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}`다. 이 matrix는 보유/청산 flow AI와 scale-in evaluator가 같이 읽는다.

`KORSTOCKSCAN_HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=true`이면 holding/exit prompt에 `[ADM Advisory Context]`가 붙는다. 기본형은 advisory-only이며, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=true`는 명시적 운영 override에서만 flow AI 결과를 직접 보정한다.

Holding/Exit ADM 보정 규칙은 아래와 같다.

1. matrix bias가 `prefer_exit`이면 AI `HOLD` 또는 `TRIM`을 `EXIT`로 바꿀 수 있다.
2. matrix bias가 `prefer_avg_down_wait` 또는 `prefer_pyramid_wait`이면 AI `EXIT`, `DROP`, `SELL`을 `HOLD`로 바꿀 수 있다. `TRIM -> HOLD`는 기본 차단이며 `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED=true`가 별도로 필요하다.
3. matrix entry가 비어 있어도 hypothesis fallback이 손실 + AI 회복 구간을 `holding_exit_matrix_avg_down_bias`, 수익 + AI 강세 구간을 `holding_exit_matrix_pyramid_bias`로 scale-in evaluator에 전달한다.
4. 명시적 운영 override로 `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=true`가 켜진 경우에만 해당 bias나 LDM scale-in policy가 `AVG_DOWN` 또는 `PYRAMID` action 후보를 만들 수 있다. safety veto가 있으면 scale-in 후보를 만들지 않는다. lifecycle AI context v1에서는 scale-in은 관찰/provenance만 남기고 실제 scale-in action을 만들지 않는다.

손절 직전 물타기 경로는 `KORSTOCKSCAN_SCALP_LOSS_FALLBACK_ENABLED=true`, `KORSTOCKSCAN_SCALP_LOSS_FALLBACK_OBSERVE_ONLY=false`일 때 실주문 경로가 열린다. 다만 이 경우에도 scale-in 공통 gate, 계좌 cap, cooldown, price resolver, spread, qty cap, pending order guard를 모두 통과해야 한다.

### 3. Lifecycle Decision Matrix Runtime

Lifecycle Decision Matrix는 기존 ADM을 대체하는 새 단일 bucket 정책이 아니라 ADM 확장 umbrella다. postclose chain이 `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_YYYY-MM-DD.{json,md}`를 만들고, runtime feature와 label feature를 분리한다.

Runtime 입력 feature는 `ai_score`, AI action, buy pressure, tick accel, micro VWAP, spread, liquidity, latency, stale/source quality, price resolver, OFI/QI, position PnL, peak, held_sec, 현재 적용된 fixed threshold 값이다. `realized_profit`, `mfe_10m_pct`, `mae_10m_pct`, `close_10m_pct`, fill outcome, avoided loss, missed upside 같은 사후 label은 policy 학습/판정 근거에만 쓰고 runtime resolver 입력으로 넣지 않는다.

`entry_bucket_attribution`은 entry row를 `score_band/source_stage/chosen_action/stale_bucket/liquidity_bucket/strength_bucket/overbought_bucket/time_bucket/exit_rule/combo_entry_spot`으로 자동 분류한다. `scale_in_bucket_attribution`은 scale-in row를 `arm/blocker_namespace/blocker_reason/profit_band/peak_profit_band/held_bucket/ai_score_band/ai_score_source/supply_pass_bucket/price_guard_reason/qty_reason/time_bucket`으로 자동 분류하고 AVG_DOWN/PYRAMID namespace를 분리한다. 두 layer는 bucket별 `source_quality_adjusted_ev_pct`, joined sample, MFE/MAE/close label을 만들고, sample/EV/source-quality 조건에 따라 `runtime_approval_candidates`와 `code_improvement_workorders`를 생성한다. 이 layer는 `runtime_effect=false`, `allowed_runtime_apply=false`이며, 후보가 있으면 `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`까지 전달되어야 한다. 전달 누락은 `threshold_cycle_postclose_verification`의 `ldm_entry_bucket_handoff_missing` 또는 `ldm_scale_in_bucket_handoff_missing` FAIL이다. scale-in source row가 있는데 attribution 자체가 없으면 `ldm_scale_in_bucket_attribution_missing` FAIL이다.

selected PREOPEN env가 명시할 수 있는 key는 아래다.

```bash
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_FILE
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_VERSION
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE
KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED
KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED
KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_FILE
KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_VERSION
```

Runtime resolver의 proposal은 `policy_version`, `stage`, `matched_policy_key`, `confidence`, `selected_action`, `original_action`, `runtime_effect`, `reason`, `fixed_threshold_role`, `safety_passthrough`를 남긴다. `BUY_DEFENSIVE` 승격은 micro canary cap 안에서만 가능하고, cap 초과 또는 confidence 미달이면 `NO_CHANGE`다. submit stage는 가격/latency/source freshness context를 읽을 수 있지만 hard safety guard를 완화하지 않는다. context-only 운영에서는 `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED=false`가 LDM action mutation을 막고, `KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED=true`가 entry/holding/exit OpenAI prompt에만 `[Lifecycle AI Context]`를 붙인다.

기존 fixed threshold는 matrix 안에서 아래 역할로만 쓴다.

| 역할 | 대상 | runtime 사용 |
| --- | --- | --- |
| `hard_safety` | broker submit guard, stale quote submit block, price freshness, hard/protect/emergency stop, 계좌/order/cooldown/qty guard | matrix가 우회/완화 불가. proposal에 `safety_passthrough=true`만 기록 |
| `baseline_prior` | `BUY_SCORE_THRESHOLD`, VPW/strength/momentum, entry score cutoff | 후보 생성 prior와 feature. score 단독 action 확정 금지 |
| `bounded_tunable` | latency caution, score65_74 probe, soft stop/holding flow, scale-in price guard | policy arm이 추천할 수 있으나 bounds/max step/sample/source-quality gate를 통과해 다음 PREOPEN에만 반영 |
| `legacy_archive` | fallback scout/main, fallback single, latency fallback split-entry, legacy latency composite, closed shadow axes | framework 입력으로도 사용하지 않음. 재개는 별도 workorder/rollback guard 필요 |

### 4. Safety Guard 우선순위

ADM과 lifecycle matrix는 기본형에서는 OpenAI prompt context만 제공한다. 명시적 runtime bias override가 켜진 경우에도 broker submit guard를 우회하지 않는다. 우선순위는 항상 아래 순서다.

1. hard/protect/emergency stop, market closed, invalid feature, active sell order pending
2. stale quote submit block, price freshness, hard latency reject, liquidity hard block, account cap, cooldown, pending order, qty cap, scale-in price resolver
3. lifecycle decision matrix runtime policy
4. 기존 Entry/Holding ADM adapter
5. baseline fixed threshold fallback과 AI 원본 action

따라서 명시적 override에서 ADM이 `BUY`, `HOLD`, `AVG_DOWN`, `PYRAMID` 쪽으로 bias를 주더라도 safety guard가 차단하면 주문은 제출되지 않는다. 반대로 ADM이 `WAIT` 또는 `DROP`으로 보정하면 이후 submit 단계에 도달하지 않는다. context-only 운영에서는 이러한 직접 보정 자체가 발생하지 않는다.

### 5. Provenance와 판정 루프

Entry ADM은 `scalp_entry_action_decision_snapshot`에 `entry_adm_runtime_effect`, `entry_adm_forced_action`, `entry_adm_runtime_reason`, bucket token, risk/stale/liquidity/overbought/time bucket을 남긴다. Holding/Exit ADM은 holding pipeline에 `holding_exit_matrix_runtime_effect`, `holding_exit_matrix_forced_action`, `holding_exit_matrix_scale_in_bias`를 남긴다.

장후에는 sim/real/post-sell outcome과 join해 `forced WAIT/DROP이 missed upside를 만들었는지`, `강제 HOLD가 손실 확대인지 missed upside 회수인지`, `AVG_DOWN/PYRAMID bias가 실제 EV를 개선했는지`를 본다. 이 결과는 `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, pattern lab source bundle로 전달된다.

### 6. Rollback

ADM runtime override를 끄려면 아래 env를 false로 둔다.

```bash
KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=false
KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=false
KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=false
KORSTOCKSCAN_SCALP_LOSS_FALLBACK_OBSERVE_ONLY=true
```

rollback 사유는 severe loss, stale submit, order failure, receipt/provenance 손상, safety guard breach 중 하나로 분리해 기록한다. ADM 산출물 자체의 sample 부족이나 missing bucket은 rollback 사유가 아니라 postclose workorder 또는 다음 tuning loop 입력이다.

### 7. 실 API 검증과 개선 계획 누락 방지

ADM runtime override가 켜진 날에는 dry-run/mock만으로 닫지 않는다. 최소 1회는 실제 `data/config_prod.json`의 OpenAI API key를 로드해 `analyze_target` live 호출을 수행하고, 아래 필드를 키 값 없이 기록한다.

1. `result_source=live`, `ai_parse_ok=true`, `ai_parse_fail=false`
2. `openai_transport_mode=responses_ws` 또는 운영상 허용된 HTTP fallback
3. `openai_endpoint_name=analyze_target`, `openai_schema_name=entry_v1`
4. `entry_adm_prompt_applied=true`
5. `entry_adm_runtime_bias_enabled=true`
6. `entry_adm_cache_token`에 `entry_adm:<matrix_version>:<bucket_token>` prefix가 포함됨

실 API 검증은 AI 분석 호출까지만 수행한다. broker submit, threshold mutation, bot restart, provider 변경은 이 검증의 일부가 아니다. 입력 fixture는 실런타임 tick/candle schema를 맞춰야 하며, `time`, `dir`, `price`, `volume`, `strength`, `체결시간`, `시가`, `고가`, `저가`, `현재가`, `거래량` 누락으로 실패하면 API 실패가 아니라 fixture/schema gap으로 분리한다.

개선 계획은 다음 순서로 닫는다.

1. `entry_adm_runtime_effect`/`entry_adm_forced_action`이 신규 cohort에 실제 기록되는지 확인한다.
2. `prompt_applied_count>0`, `joined_sample>=sample_floor`, missing action bucket 축소를 확인한다.
3. `BUY_NOW`/`BUY_DEFENSIVE` positive bucket은 강제 BUY 승격이 아니라 다음 runtime env 튜닝 후보로만 올린다.
4. forced `WAIT/DROP`의 missed upside와 avoided loss를 10/30/60분 horizon으로 분리한다.
5. 위 네 항목 중 하나라도 비면 `order_scalp_entry_adm_daily_tuning_coverage` 또는 후속 code-improvement workorder로 남긴다.
