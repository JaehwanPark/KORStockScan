# 2026-09-23 Stage2 To-Do Checklist

## 오늘 목적

- 전일 family별 원천·경제성·정책·런타임 직접 소비 결과와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- 공통 Daily/EV 튜닝 및 generic workorder는 퇴역 상태를 유지하고 family owner의 직접 근거만 사용한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-22", "sources": {"runtime_approval_summary": {"sha256": "993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6"}, "stage_collector_recommendation": {"sha256": "8ca2d735707afd87cb2b73a60b3b7eefb7aef1d4829aa6fe1f98c0b7a0875376"}, "stage_episode_policy": {"sha256": "655b13c2aef8bb4248ce550f688cd7ed36211ee76dd0dac26c985b091fd5b2e8"}, "stage_legacy_machine_report": {"sha256": "0903a530e1eb2d1c454ee81c8d6fb722aacf4b893d800676e24e0ba3cf38d51d"}, "stage_legacy_policy_approval": {"sha256": "5c25e358003a59337ed787875e08399bcfa703b2c3b15f1e406225d38373778a"}, "stage_machine_attribution": {"sha256": "350ab203eb069f25dcc7c4808469f1680539e50d08b109ce618036b0509635b9"}, "stage_machine_timing": {"sha256": "77af654f182f8956775221c78c7dc8712811785627721580b6df7233802fbb6b"}, "stage_main_auxiliary_policy": {"sha256": "d85a1df956522b46f763c3d29e997de19946c33d4096ef1d37df87ab0dae3566"}, "stage_main_machine_policy": {"sha256": "700a1272786c572ebd26a2a75986336f41bffbdd7ba35c971c9d694a1cafc30c"}, "stage_market_weakness": {"sha256": "34d9d459e4e110070ced6bccc68294b5f963384217884d74336a0841990dd69e"}, "stage_outcome_labels": {"sha256": "89a6c7e0e757dab4641fbabae34ba6f3acb7cb212385a50dcdeb24165e7adaa4"}, "stage_research_allocation": {"sha256": "303eb56b0f98e29c30460d9f9730059b0e47398c217029555243c182e3059062"}, "stage_research_capacity": {"sha256": "d6a7d04fe97985a7e56d4fe47b2249e474fcb84b90eaa3befcc05592545497ec"}, "stage_widget_policy": {"sha256": "e78eee27d68b2d133c604d159c8c24b5b46ca438c7ea763ab87d5fa048fc1f1c"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"allowed_runtime_apply": false, "apply_date": "2026-09-23", "expected_state": "verified", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-23.json", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "74cc713674b79c5363924f6c500634aadaad7336f7254d94d8d6f60fe0b98b77", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "80572acfa29c97e232623d4417e16d7e9ccf01b1133ffcf23430d696ca45c032", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "6790d83409002561144a28813658efaf8e0cce5db373d3ee7b1b08bdadfbd2c4", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": "fb7b9f587b86371615dcfcb2c0243e975a79b0f255200b55fcd7463d5d092537", "valid": true}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "da464100a27261866f5b5197fb35f40709e3b819be0fdb519ac11edc78c9616e", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": "b4d54a66b71f2f211781f5ef69a64ae9cd61834df2abe4d97c844f57cb417ab4", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "74cc713674b79c5363924f6c500634aadaad7336f7254d94d8d6f60fe0b98b77", "valid": false}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "fe3722d6a8f8643c918019a320bb921a446deed2e14cc461d6e7a8569fd6e98a", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "5fce08335e2c0da8240112e7f338241e333f593d69576059abe8c178f3df21b4", "valid": true}], "runtime_effect": false, "schema": "direct_family_future_handoff_v1", "source_date": "2026-09-22", "source_preopen_state": "verified", "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-23.json"} -->

## Family 직접 증거 상태

- source date: `2026-09-22`; next apply date: `2026-09-23`.
- direct source: `11/11`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `verified`; natural acceptance: `pending`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `scale_in_split` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `machine_entry` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `mixed` | `blocked` | `producer_contract_repair` |
| `low_price_expansion` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `unsupported_scope` | `blocked` | `scope_contract_decision` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[PostcloseFinalizerControllerTerminalReceipt] controller terminal 영수증을 검증한 뒤 장후 마감` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 21:55~23:20`, `Track: RuntimeStability`)
  - Source: [Postclose handoff contract](../report-based-automation-traceability.md#complete-recommendation-and-terminal-summary-handoff-source-date-2026-09-09-onward).
  - 완료 기준: exact-date main 및 설치된 widget/machine predecessor가 성공한 뒤 controller canonical/attempt 영수증이 이번 finalizer 실행 이후 생성되고 byte-identical이며, `status=done`, `whole_native_chain_done_claimed=true`, `require_independent_producers=true`, strict verifier `pass`임을 확인한다. 불일치·`summary_verified`·오래된 report면 cleanup 전에 실패하고 final detector에 넘긴다. 최종 finalizer/detector terminal marker까지 확인한다.
  - 권한 경계: 성공 상태나 terminal receipt를 합성하지 않는다. threshold·정책·주문·provider·봇·cleanup 범위는 바꾸지 않는다.

- [ ] `[PostcloseWidgetEodSlotAdmission] Widget EOD 대기의 계산 슬롯 분리와 신규 원천 자연 검증` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:40`, `Track: RuntimeStability`)
  - Source: [장후 장시간 작업 최적화 계획](../proposals/postclose-long-running-work-quality-preserving-optimization-plan-2026-09-23.md).
  - 완료 기준: EOD 미준비 시 stage가 계산 슬롯을 잡지 않고 `waiting_for_source`로 대기하며, 완료 후 기존 worker의 날짜·행수 검사를 통과해 같은 모집단·grid·정책 해시를 산출한다. 첫 신규 원천 실행의 stage wall/child CPU/RSS, EOD 대기 시간, source hash와 최종 validator receipt를 별도로 확인한다. 9/22 복구 stage의 `succeeded`는 신규 계산의 성능 수용 근거가 아니다.
  - 권한 경계: 입력·후보·threshold·정책 적용·주문 권한은 변경하지 않는다. source 실패 또는 날짜 불일치 시 기존 정책을 유지한다.

- [ ] `[DirectFamilyScopeDecisionMainMechanisticEntry] main_mechanistic_entry 직접 family 지원 범위 계약 확정` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-22.json)
  - 증거: runtime_summary_sha256=`993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-22.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`scope_contract_decision`, comparison_status=`unsupported_scope`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_policy_selected_portfolio_economics_separate`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`natural_machine_policy_outcomes`. policy_receipt_valid=`False`, source_date=`2026-09-22`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-22.json)
  - 증거: runtime_summary_sha256=`993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-22.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`exact_stop_distance_missing_or_invalid`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 기존 owner/exact-stop basis와 독립된 AI 10분 고정경로 basis를 구분한다. 실제 PASS 양성 경로를 같은 attempt의 label/hash로 연결하고 good-PASS retention·전이·기계정책과 같은 보정승률/EV/paired 순위를 보고한다. 결정론적 후보의 추가 provider call은 0건이며, 비용·경로·label provenance 결손 행은 성공으로 간주하지 않는다. 오늘 적격 후보가 생기면 현재 machine/AI parent CAS로 장중 AI component만 활성화하고, 후보가 없으면 carry한다. 다음 장전 dated AI 후보도 preopen CAS 영수증을 확인한다. policy_receipt_valid=`True`, source_date=`2026-09-22`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-22.json)
  - 증거: runtime_summary_sha256=`993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-22.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`execution_producer_census_unsealed`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-09-22`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-22.json)
  - 증거: runtime_summary_sha256=`993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-22.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`2026-06-05 clean-baseline 전체 적격 제출·체결·terminal 모집단; 동일 frozen scope의 completed-cost model calibration/holdout 후 paired candidate calibration/holdout`. 전체 clean-baseline 진단일별 operating attempt census, frozen seed/replay, owner parent-child-fill-terminal, completed-cost receipt와 model-comparable coverage를 분리 보존한다. 미기록일·미완료 outcome·원천 결손은 0으로 추정하지 않고 seed-build blocker도 향후 제출 원천에 기록한다. 9/22 현재 census(29 plan: seed 20 missing, plan 9 invalid; completed-cost artifact missing)는 historical gap으로 보존하고 새 계측으로 소급 복구하지 않는다. policy_receipt_valid=`True`, source_date의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairPreSubmitDelay] 최초 BUY 제출 전 지연의 독립 평가·정책·소비 계약 구현` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [메인 진입 실행 장후 EV 평가·장중 정책 소비 구현계획](../proposals/main-entry-downstream-postclose-profitability-closure-plan-2026-09-23.md).
  - 완료 기준: `pre_submit_delay_tuning`이 2026-06-05 이후 전체 clean-baseline 적격 날짜를 누적 집계하고 날짜별 source coverage·census·제외·fingerprint를 기록한다. 같은 exact intent의 0초 비교군과 30/60/120/180초 후보를 동일 분모에서 비용 후 EV·시간순 holdout 또는 시점/경로별 정확한 source gap으로 평가한다. 진입 의도 시점에 동결한 유형별 유효 정책을 보고한다. 0초는 대조군이며 정책 기본값/선정/carry로 발행하지 않는다. 유효한 양수 정책만 후속 후보가 검증될 때까지 승계하고, 근거가 없으면 정책 미선정 source gap을 발행한다. 독립 dated `pre_submit_delay_policy`와 loader·비차단 intent·실제 PID 소비를 날짜/hash로 검증한다. 분할 정책 파일·후보·승격 상태는 변경하지 않으며 독립 stage/terminal과 장후 실행시간을 확인한다.
  - 권한 경계: 기계/AI 진입 판정·분할 형태·cancel wait·원 수량을 변경하지 않는다. fresh AI/quote/route·가격 상한·broker/account/order/cooldown·hard safety를 우회하거나 EV null을 0으로 바꾸지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-22.json)
  - 증거: runtime_summary_sha256=`993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-22.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_sample_floor`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-22`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairScaleInSplit] scale_in_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-22.json)
  - 증거: runtime_summary_sha256=`993d46a23ae3ab7f48515b306ce1db314c1d54547ff29e95b3f09cc1855567a6`, source_artifact=`/home/ubuntu/KORStockScan/data/report/scale_in_split_order_plan/scale_in_split_order_plan_2026-09-22.json`.
  - 상태: family=`scale_in_split`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`scale_in_split_order_plan`, closure_test=`eligible_add_fill_terminal_clock_cost_and_independent_paired_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-22`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:405e66485399e5c9e4a4e32b2f977d7a8d09e4bb71b4cab4f03d36452be9356f -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-22; 발행 2026-09-22; 적용 2026-09-23. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `3fee4ae87fba8dcd5198e4d29a8e1398fcb243934678edea86b6a3ea84b87895`; 정책 bundle `afe46b5c30722e6cbc37ab021ec8e251f8600feadfe3b473185dafe36c3bab12`; consumer `31438f3df7946785ec0babe9de6fb5a4ed940989fec34910bdbd7f1574a9fb70`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
