# 2026-09-28 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-23", "sources": {"runtime_approval_summary": {"sha256": "217322260aab303c475ceb696b74b18f275e95c4bcbbee084c6c25fe73f1ccb7"}, "stage_collector_recommendation": {"sha256": "671921fc1073e493cad0872a1f4769e40d106f7f4bf2a6257455f7b7346fc244"}, "stage_episode_policy": {"sha256": "a9b123b65c2bcb514344baa08597a4269025ee8982892e02a24a2b4fdb673ef7"}, "stage_legacy_machine_report": {"sha256": "abb60ab7d243f1f437c5053fe914113d776088b57f2c10918345c8bd731f08a5"}, "stage_legacy_policy_approval": {"sha256": "94af41f12ef563d64154cc52365bf9c0ee6197569a0ee604cbfe5fe2528cb09d"}, "stage_machine_attribution": {"sha256": "ef7b85b54c83d31a42aa53291907493a01cc8acc2ef446c4306c36d5656e06d9"}, "stage_machine_timing": {"sha256": "56614c1c9439b6a0bee9510765676d8109a492e2cf94a4801f3235ea6c76c10d"}, "stage_main_auxiliary_policy": {"sha256": "974c4fe5951d377ba52dcb95405949c35c87204dd1d87ae821f3287bef96c08e"}, "stage_main_machine_policy": {"sha256": "b435610415cbccb0a58273c6b2869bef3949831f3982eb40e82ddc7ff6b5ed80"}, "stage_market_weakness": {"sha256": "6257e09e8973100ec0a2e78af5b45750afd6a8d6c6f502c157e99d3d067c9654"}, "stage_outcome_labels": {"sha256": "a7c184d99fd993b46119987edddf20bf8445c92713ffbccfbae97ff622292821"}, "stage_pre_submit_delay": {"sha256": "4237e26547a5f7cc4a24093fd791127c8c8a2061abc729d7a09c18673d891a38"}, "stage_research_allocation": {"sha256": "450f57a8dee3b0f68e7b6aa4066da4e1bd976b0354f3aff947aac3d4ee5206ea"}, "stage_research_capacity": {"sha256": "d3201f6beeb9165225eebf7b774ccbb8fd7fcc1358e59ce0f8788d05b41d5fe4"}, "stage_widget_policy": {"sha256": "166a49e1e8a9abc76bf40057b37662ac5a3b1f75a3957daa5dde65ec4d982371"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"allowed_runtime_apply": false, "apply_date": "2026-09-28", "expected_state": "verified", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-28.json", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": null, "valid": false}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "47089473930773b790918430c677070cf486b424aed2e20d6e4f5f29b11425b6", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "916d586d4e9d511ce9683893008ecab9b1852865f2398ced8f6b512e83954f31", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": "b979aca48396cb68bab2e1c231fbd0240044dd8a86353a472a61ff2bd37ae0f0", "valid": true}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "a970299fcdc6b92851b20148d311a898660e6a61e2a6a84566b0491ab9329d3c", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": "5bd3098d2b5a0bc72fc2cc671f267f1765774917ac763cd9074de828280e4f5a", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "3b975975bd7bc1db919b00006187e293310a26d1ab77f8309cd75e8468a4e45a", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "8316daef3258837d2730ed261b3442a4f43b0dad652c91b7b4a251d2d39fd8ad", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "921f24753d488a389b2716d2640fd1bcd03784f3a54ac5c90b36b4a105573d77", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "6d2eb8a2bdb3931429e5ec0c35b864d31a76c7349cbdb73cfc153f0396aeb8a4", "valid": true}], "runtime_effect": false, "schema": "direct_family_future_handoff_v1", "source_date": "2026-09-23", "source_preopen_state": "verified", "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-28.json"} -->

## Family 직접 증거 상태

- source date: `2026-09-23`; next apply date: `2026-09-28`.
- direct source: `10/10`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `verified`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `source_gap` | `blocked` | `producer_contract_repair` |
| `scale_in_split` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `machine_entry` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `mixed` | `blocked` | `producer_contract_repair` |
| `low_price_expansion` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[HoldingProfitExitSemanticClosure0928] 익절 투표 정책·의미 감시의 첫 자연 소비 대사` (`Due: 2026-09-28`, `Slot: INTRADAY`, `TimeWindow: 08:05~19:50`, `Track: RuntimeStability`)
  - Source: [익절 추정 정책·의미 감시 구현계획](../proposals/holding-profit-exit-estimated-policy-and-semantic-closed-loop-plan-2026-09-26.md).
  - 완료 기준: 프리마켓 08:05부터 정규장·통합애프터마켓까지 `holding-exit-sentinel` selector 경유 trigger 6개와 날짜별 JSON의 `profit_exit_semantics`를 확인한다. 동일 대상일 15셀 임시 정책 파일→장후 summary/strict→bootstrap manifest/env→선택 release→실제 Main PID의 정책 hash 및 첫 crossing·신호 전 표·SELL terminal/비용을 서로 다른 영수증으로 대사한다. 자연 표본이 없으면 `valid_empty`/`source_gap`과 코드 폐루프 검증을 구분해 기록하며 실현 EV를 만들지 않는다.
  - 배포 기준: [9/26 코드 재검토·성능·배포 영수증](../audit-reports/2026-09-26-holding-profit-exit-semantic-rereview-deployment.md)의 구현 근거와 현재 `data/runtime/runtime_release_selection.json`의 선택 commit·cron 경유를 함께 확인한다. 메인 PID와 자연 v10 표는 9/28에 별도 수용한다.
  - 권한 경계: 보고 전용 감시 결과로 SELL, 임계치, provider, bot restart 또는 hard/protect/emergency 안전을 변경하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-23.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-23.json)
  - 증거: runtime_summary_sha256=`217322260aab303c475ceb696b74b18f275e95c4bcbbee084c6c25fe73f1ccb7`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-23.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_dispatch_or_parent_lineage_unclassified`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-09-23`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-23.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-23.json)
  - 증거: runtime_summary_sha256=`217322260aab303c475ceb696b74b18f275e95c4bcbbee084c6c25fe73f1ccb7`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-23.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-09-23`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-23.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-23.json)
  - 증거: runtime_summary_sha256=`217322260aab303c475ceb696b74b18f275e95c4bcbbee084c6c25fe73f1ccb7`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-23.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_sample_floor`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-23`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairPreSubmitDelay] pre_submit_delay 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-23.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-23.json)
  - 증거: runtime_summary_sha256=`217322260aab303c475ceb696b74b18f275e95c4bcbbee084c6c25fe73f1ccb7`, source_artifact=`/home/ubuntu/KORStockScan/data/report/pre_submit_delay_tuning/pre_submit_delay_tuning_2026-09-23.json`.
  - 상태: family=`pre_submit_delay`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`pre_submit_delay_tuning`, closure_test=`exact_attempt_submit_clock_quote_cost_terminal_and_independent_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-23`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairScaleInSplit] scale_in_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-23.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-23.json)
  - 증거: runtime_summary_sha256=`217322260aab303c475ceb696b74b18f275e95c4bcbbee084c6c25fe73f1ccb7`, source_artifact=`/home/ubuntu/KORStockScan/data/report/scale_in_split_order_plan/scale_in_split_order_plan_2026-09-23.json`.
  - 상태: family=`scale_in_split`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`scale_in_split_order_plan`, closure_test=`eligible_add_fill_terminal_clock_cost_and_independent_paired_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-23`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 물타기 공통 반등·체결 식별자 폐루프

- [ ] `[AvgDownSharedReboundReceiptClosure0928] 물타기 사전검사·재기동 체결 식별자·보유 건별 경제성 결속` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [구현계획](../proposals/avg-down-shared-rebound-receipt-and-pyramid-retirement-implementation-plan-2026-09-28.md), [9/18 퇴역·공통 반등 검토](../audit-reports/2026-09-18-pyramid-retirement-avg-down-shared-rebound-review.md).
  - 현재 결손: 대우건설 `047040`/보유 `48376`은 사전검사 차단의 세부 blocker·원천 시계가 이벤트에서 빠지고, 11:13경 재기동 후 `buy_fill_identity_missing`이 반복됐다. 최초 BUY 주문 `0029186`/체결 `131176`의 영속 원천과 복원 경로를 대사한다. 유효 ADD 투표·주문·체결·경제성은 아직 확인되지 않았다.
  - 구현 순서: exact BUY 체결 원천·보유 ID 대사 → 제한된 preflight blocker 기록 → 멱등 영속화/재기동 복원과 미복원 ADD 차단 → 같은 보유 건의 반등·투표·실제 제출/체결·청산/비용 join → PYRAMID 신규 판단·튜닝·정책 잔재 제거와 과거 미결 주문/SELL 정산 보존 → review·표적 회귀·성능 비교.
  - 완료 기준: 선택 release·설치 unit·실제 PID·정책 hash와 첫 자연 기회 영수증을 분리한다. 원천 적격/유효 반등/유효 투표/계획·제출·체결/정확 비용·완료의 단계별 분모와 ID 보존식이 성립하고, PYRAMID 신규 주문은 불가능하며 옛 주문 정산은 유지된다. 유효 자연 ADD·완료 표본이 없으면 수익성은 `null`, 수용은 `natural_first_use_pending`으로 이관한다.
  - 권한 경계: 본 항목은 구현계획 owner이며 코드 변경·배포·재기동·주문을 승인하지 않는다. `[DirectFamilySourceRepairScaleInSplit]`은 ADD 허가 뒤 수량·분할 방식만 별도 소유한다. 원천·체결 ID를 합성하거나 hard safety/SELL 우선권을 완화하지 않는다.

## 9/24 복구에서 이관된 자연 원천 수용

- [ ] `[PostcloseDashboardArchive0928] 장후 DB archive 예약 복구 후 첫 자연 terminal 확인` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 20:50~21:10`, `Track: RuntimeStability`)
  - Source: [9/26 통합 점검](../audit-reports/2026-09-26-integrated-worktree-review-and-next-session-readiness.md), [현행 장후 목록](../audit-reports/2026-09-05-postclose-work-inventory.md).
  - 완료 기준: 설치된 20:50 `archive` 예약의 선택 release·원천일과 wrapper의 `[START]`→`[DONE]`·압축/보존 결과를 대사한다. 9/16 이전 실행을 9/28 완료로 재사용하지 않는다.
  - 권한 경계: 보고·보존 owner이며 정책·주문·provider·bot을 변경하지 않는다.

- [ ] `[PostcloseFinalizerControllerTerminalReceipt] 다음 장후 controller·finalizer 실행 release 인계 확인` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~23:20`, `Track: RuntimeStability`)
  - Source: [9/24 전체 진단·복구](../audit-reports/2026-09-24-postclose-whole-result-diagnosis-and-recovery-plan.md), [9/24 완료 owner](2026-09-24-stage2-todo-checklist.md).
  - 이관 증거: 9/23 원천일은 v3 장후 stage·strict/controller·최종화 `[DONE]`으로 완결했다. 당시 widget/machine 장후 unit은 v3 `484129dc`, 당시 cron selector는 `41cdf32a`였다. 9/28 실행은 현재 selector와 각 독립 unit의 실제 pin·terminal을 다시 확인하고, 장전 bootstrap/loader와 실제 PID 소비도 분리한다.
  - 완료 기준: 다음 자연 장후 실행 전에 controller/finalizer의 실제 PID cwd·commit과 stage dispatcher의 최신 영수증 입력 계약·위젯 관측 전용 준비 판정을 대조한다. scoped postclose route를 바꿀 경우 운영 문서/checklist와 함께 review·검증하고 매매 release/PID·주문 권한을 임의로 변경하지 않는다. 실행 뒤 같은 원천일의 active stage→summary→strict→controller→cleanup→detector 최신 terminal과 비용·정책 분모를 확인한다.
  - 의미 감시 인계: [9/24 작업본 수리](../audit-reports/2026-09-24-machine-judgement-horizon-and-field-association-audit.md)의 `artifact_freshness.machine_result_semantics`가 실제 detector 실행 release에 포함됐는지 확인한다. 새 자연 원천에서 구조 적격·운영 paired·원천 계약 제외·compact 전량 제외의 경고/분모를 원본 보고서와 대사하고, `warning`을 경제성 0 또는 stage 실패로 치환하지 않는다. 기존 9/23 detector 영수증은 이 새 검사 소비 증거가 아니다.
  - 15:47 활성 원천 경합: 15:45 모니터 예약의 조기 fact sync가 3.61GB 활성 pipeline JSONL 변경을 strict reader에서 감지해 source-blocked 영수증 `b81d32cf`를 남겼고 독립 스냅샷/로그 보존도 시작하지 못했다. [원인·수정 리뷰](../audit-reports/2026-09-28-monitor-archive-live-source-deferral-review.md)에 따라 15:45는 보존 작업만, 정확 fact sync는 기존 20:10 장후 체인이 소유한다. 20:10 자연 source-stable 영수증과 snapshot/archive 실제 결과는 OPEN이다.

- [ ] `[HoldingExitPositionOutcomeLineageClosure] 보유·청산 비용·명시적 판단·완전 사후창의 새 자연 표본 확인` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [9/24 전체 진단·복구](../audit-reports/2026-09-24-postclose-whole-result-diagnosis-and-recovery-plan.md), [트레일링 단일화·생산자 계획](../proposals/scalp-trailing-runtime-simplification-and-producer-closure-plan-2026-09-24.md), [익절 임계치 원천 연결·정리](../proposals/scalp-trailing-postclose-threshold-lineage-and-pruning-plan-2026-09-24.md), [4축 시장별 계획](../proposals/scalp-trailing-four-axis-market-tuning-and-historical-evidence-plan-2026-09-25.md), [과거 원천 가용성](../audit-reports/2026-09-25-scalp-trailing-four-axis-historical-source-availability.md), [9/24 이관 owner](2026-09-24-stage2-todo-checklist.md).
  - 이관 증거: 9/23 완료 8건 중 직접체결·정확 비용 6건 -4,621원, 잔고대사·비용 결손 2건, `sell_completed` ID 8건 일치. 6건 사후 1/3/5/10분 관측은 `partial_window`, 2건 정확 fill time 결손; exit rule은 모두 추정, 유효 threshold/flow 개입 0, 전체 clean-baseline EV null.
  - 9/24 배포 영수증: 메인 선택 release `2a099e1acff0c975abc221fc2d37d629ab11e794`, 9/28 bootstrap verify `pass`이며 폐기 익절 env 키 34개를 제거했다. 실제 메인 PID는 없어서 코드·정책 소비와 자연 체결 성과는 아직 증명되지 않았다. [구현·배포 기록](../proposals/scalp-trailing-runtime-simplification-and-producer-closure-plan-2026-09-24.md)의 신뢰 가능한 `0B` 거래 시각·`0D`/REST bid 시각, 청산 판정 전이와 직접 신호를 다음 자연 표본에서 대사한다.
  - 후속 코드 수리: 네 익절값 bootstrap receipt, bounded 전이 원천, 구조화 JSONL→trade review→holding exit observation→sentinel/summary 대사와 폐기 `SCALP_TRAILING_LIMIT` 제거를 구현했다. [전체 변경 성능·리뷰·배포 기록](../audit-reports/2026-09-25-scalp-trailing-full-uncommitted-performance-review-deployment.md)과 `data/runtime/runtime_release_selection.json`으로 선택된 코드 세대를 확인하되, 실제 PID·자연 체결 소비로 간주하지 않는다. 새 자연 표본에서는 open/censored 분모, source gap, 실거래 terminal·정확 비용·사후창을 분리해 확인한다.
  - 9/25 작업본 검토 범위: 4축×3시장 bootstrap v3과 전이 quantization, 장후 단일·쌍·제한 조합 연구 블록은 코드 변경 사항이다. 9/23 보존 완료 329건은 현행 엄격 완료 모수가 아니며 9/23 projection 8건도 구조화 leg/직접 신호가 없어 정책 변경 근거가 아니다. 다음 자연일에는 12개 시장값·단일 hash, fast/normal 동일 소비, ID별 strict/원천 제외 및 4축 첫 crossing/비용/검열을 확인한다. 작업본·보고 전용 후보만으로 선택 정책이나 PID 적용을 선언하지 않는다.
  - 후속 진단: [과거 중립 추정 재생·리뷰](../audit-reports/2026-09-25-scalp-trailing-legacy-neutral-scenario-review.md)는 완료·유효 표시 329건에서 312건의 조건부 시나리오를 계산하고 MFE/규칙 추정·미식별 중립·비용/슬리피지 가정을 분리했다. 엄격 완료·비용 적격 0건과 현재 정책 미선택 상태는 유지한다. 주말 빈 보고서의 census 오판과 진입일 기준 검증 분할은 수리했으나 주중 원천 결손·구형 미봉인·후행 실행가격은 자연 수용에서 계속 확인한다.
  - 운영 입력 작업본: [17축 입력 민감도 재생·리뷰](../audit-reports/2026-09-25-scalp-trailing-operational-input-replay-review.md)는 polling/NXT·보유 AI·공유 quote/REST의 현행값과 진단 격자, 평가별 shadow hash, source gap·owner 안전 검토 상태를 장후 observation→sentinel/summary에 연결한다. 변경된 AI/시세·호출/체결의 비용 후 반사실과 선택 정책은 `null`로 유지한다. 다음 자연일에 exact ID·원천/정책 hash·fast/normal·3시장/route·성능과 공유 owner 안전 결과를 대사하고, 새 원천 이전의 작업본을 적용 증거로 승격하지 않는다.
  - 완료 기준: 신규 자연 완료 포지션 전량의 position→트레일링 arm/시세품질/강약/발동 전이→exit signal/effective threshold·AI/flow 실제 개입→order/fill 수량→exact fee-aware cost→terminal→1/3/5/10분 완전 관측을 동일 identity·원천일·hash로 검사한다. `trailing_threshold_readiness`의 네 축별 적격 ID와 source gap을 분리하고, paired replay·독립 holdout 전에는 임계치 후보나 자동 적용을 승인하지 않는다. 과거 2건과 미봉인 historical census는 소급 합성하지 않고 source gap으로 분리한다. 실제 정책/PID 소비는 별도 수용하며 hard safety·보유/청산 owner를 유지한다.
  - 강약 폐루프 v2 인계: [구현계획](../proposals/scalp-trailing-mechanical-strength-closed-loop-tuning-plan-2026-09-25.md)의 3시장×8 강약값과 3시장×3 수익값을 한 정책으로 대사한다. 장후 `postclose_exit`의 trade review→post-sell→holding observation 세 파일·manifest 해시와 terminal, M1 첫 관측 진입일 이후의 별도 완료 census·strict 비용·미배치 ID, 후보별 500/1000ms 원시 0B 재계산·분류기×폭·검열·독립 완료일 holdout을 확인한다. 다음 PREOPEN은 hold/carry 또는 결합 v2 선택 영수증, 부모 hash·운영자 lock·한 시장 canary, 무후보 날짜의 선택 hash 유지와 실제 PID의 적용 hash를 구분한다. 자연 M1 표본이 없으면 수익성은 미식별로 남기고 합성 성능·정합 통과를 경제성으로 대체하지 않는다.
  - 9/26 코드 배포: [재검토·성능·전환 영수증](../audit-reports/2026-09-26-scalp-trailing-mechanical-closed-loop-rereview-and-performance.md)의 구현 근거와 현재 `data/runtime/runtime_release_selection.json`의 선택 commit을 함께 확인한다. 메인 PID와 자연 M1 독립 검증은 9/28 실제 원천·정확 날짜 정책·완료 비용 결과와 분리 대사한다.

- [ ] `[PostcloseWidgetEodSlotAdmission] 새 자연일 EOD 대기·위젯 계산 슬롯·격리 성능 검증` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~21:55`, `Track: RuntimeStability`)
  - Source: [9/24 전체 진단·복구](../audit-reports/2026-09-24-postclose-whole-result-diagnosis-and-recovery-plan.md), [9/24 이관 owner](2026-09-24-stage2-todo-checklist.md).
  - 이관 증거: 9/23 EOD `completed_with_warnings`, 44 `UNKNOWN`; widget 100 선택/476 deferred·source 적격 97/격리 3과의 코드 교집합 0. 장후 전용 unit 2개는 immutable release `484129dc`의 유효 wrapper/commit으로 pin됐고 9/23 active stage 영수증은 전부 유효하다.
  - 완료 기준: 새 원천일의 EOD 미준비 `waiting_for_source`가 compute slot을 잡지 않는지, 완료 후 날짜·행수·원천 hash와 100개 선택/나머지 deferred·격리 사유·동일 모집단/grid·관측/실매매 권한을 대사한다. stage wall/child CPU/RSS·EOD 대기·최종 validator receipt를 구분하고 9/23의 21분 Main 개선을 위젯 성능으로 전이하지 않는다.

- [ ] `[MainEntryWinRateInitialPolicy0928] 승률 단독 Main 초기 정책의 다음 장전 적용` (`Due: 2026-09-28`, `Slot: PREOPEN`, `TimeWindow: 06:30~09:00`, `Track: RuntimeStability`)
  - Source: [승률 단독 초기 정책](../audit-reports/2026-09-24-main-entry-three-market-win-rate-only-initial-policy-v1.md), [구현계획](../proposals/main-entry-winrate-initial-daily-tuning-runtime-implementation-plan-2026-09-24.md).
  - 9/26 결손 보완계획: [전체 기계 임계치 장후·런타임 폐루프](../proposals/main-entry-machine-all-threshold-closed-loop-repair-plan-2026-09-26.md). 9/24·9/25 초기 frozen 재현 오류를 고친 검증 릴리스와 9/28 staged/parent hash 불변을 장전 activation 전에 확인한다. 전체 좌표의 계산 적격성은 초기 68.75bp 정책의 자동 확대 승인을 뜻하지 않는다.
  - 9/24 사전 영수증: [구현·추가 코드리뷰·배포](../audit-reports/2026-09-24-main-entry-winrate-implementation-review-deployment.md). 재검토 release `bd001179` 선택, 9/28 대기 정책 `4d08df81` 발행, 활성 parent `99cb0e3a` 유지. 장전 activation·실제 PID 소비는 미실행.
  - 완료 기준: `KRX|KRX_REGULAR`의 68.75bp·유효 VWAP 한정 `ENTER_NOW→BLOCK` 계약과 나머지 scope 불변을 구현·재검토·검증한 후, 9/28 immutable 초기 generation/source/parent/rollback hash를 발행한다. Plan Rebase의 main 기계 승률 권한 충돌을 적용 전에 수정하고, 날짜별 정책·`current.json`·장전 loader/bootstrap·선택 release·실제 PID의 exact scope hash와 효력 시작일을 대사한다. 실제 PID 증거 전에는 적용 완료로 닫지 않는다. 장전까지 검증이 닫히지 않으면 기존 정책을 유지하고 정확한 blocker를 기록한다.
  - 경계: 초기 채택에 후속 표본 허들을 소급하지 않는다. PREMARKET·통합 AFTERMARKET·NXT exact scope와 hard safety·AI 비승격·주문/수량/가격 owner를 유지한다.

- [ ] `[MainEntryWinRateDailyPostclose0928] 승률 후속 허들·전체 장후 실행·성능 수용` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~23:20`, `Track: RuntimeStability`)
  - Source: [구현계획](../proposals/main-entry-winrate-initial-daily-tuning-runtime-implementation-plan-2026-09-24.md), [장후 성능 기존 owner](../proposals/postclose-long-running-work-quality-preserving-optimization-plan-2026-09-23.md).
  - 9/26 결손 보완계획: [전체 기계 임계치 장후·런타임 폐루프](../proposals/main-entry-machine-all-threshold-closed-loop-repair-plan-2026-09-26.md). Registry 82좌표의 source/evaluated/not_reached_budget 분모와 공통 5개 런타임 소비를 대사하고, 고정 초기 검증과 후속 일일 평가를 분리한다. 저장소 달력상 비거래일인 9/24·9/25는 날짜별 원천 부재로 새 `source_gap` terminal·`deferred` stage를 기록했다. 이 두 날짜의 후행 strict·신규 EV는 완료 불가이며, 9/28 자연일의 후보 성과는 장후에만 판정한다.
  - 9/24 frozen 계측: 9/23 원천으로 새 승률 stage 계산 1분 45초, 최대 RSS 약 1.0GB, swap 0; 새 자연 원천일 전체 stage 성능 영수증은 9/28에 취득한다.
  - 완료 기준: 새 자연 원천일의 엄격 source/제외/기회·승패 분모에서 train/독립 holdout·승률 전용 후속 허들을 평가하고 합격 한 scope만 다음 거래일 CAS 발행, 미합격이면 마지막 검증된 활성 machine policy payload/hash를 유지한다. 전체 활성 stage의 최신 영수증·full strict `--require-summary-handoff`·controller/finalizer/cleanup/detector와 정책 직접 소비를 대사한다. stage별 compute wall/child CPU/peak RSS/swap·대기/재시도·후보/replay 수를 측정해 실제 병목만 결과 동등성 검증 후 최적화한다.
  - 경계: 후보 없음·승률 0/0·원천 결손을 승인 또는 손실 0으로 바꾸지 않는다. 기존 9/23 성공 영수증이나 frozen 성능 결과는 새 자연 원천일 완료 증거가 아니다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] 보조 AI 판정·장후·정책 소비 폐루프 결손 수리` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [보완 구현계획](../proposals/auxiliary-ai-opportunity-error-tuning-runtime-implementation-plan-2026-09-22.md), [9/23 이관 전 owner](2026-09-23-stage2-todo-checklist.md).
  - 현 상태: 9/23 고정 원천 74건 중 적격 11건에 대해 9/26 오프라인 실제 OpenAI 프롬프트 33회(기존 v3·opportunity·risk 각 11회)를 호출했다. 유효 응답은 9/11·11/11·9/11이었다. 계약 문구 보완 연구 프롬프트는 별도 11회 모두 유효했고 같은 날 고정 10분 비용반영 경로의 짝비교 EV는 기회당 +0.06668%p였으나 9/23 응답을 보고 설계했으므로 독립 holdout은 없다. 새 버전 `contract_v4`는 장후 후보로만 등록하고 운영 v3·기존 AI 정책을 유지한다. 9/28 자연 PID 소비와 새 정책 승격은 미확정이며 bootstrap의 `compact_auxiliary` receipt `valid=false`도 PREOPEN 정상 승격 근거가 아니다.
  - 9/26 코드 재검토: holdout의 후보 생성·중간/최종 순위 유입을 제거하고 prompt 입력/부모/모델/제공자 영수증을 묶었다. writer→trace→owner 해시 결손을 단계별로 노출하고 격리 holding 재생의 peak-state 원천을 동결했다. 희박 유형 leaf는 train 5기회 미만에서 생성하지 않는다. 관련 회귀 735건 PASS 및 leaf 회귀 2건 PASS; 9/23 고정 원천의 74/11/63과 기존 3×3 EV·전이는 동일하며 제공자 없는 격리 두 명령 재생은 약 3.89초(기존 HEAD 약 3.73초)로 정책은 incumbent carry다.
  - 9/26 코드 배포: `571210fa`를 메인·예약 장후용 불변 릴리스 `auxiliary-ai-four-axis-20260926-571210fa`로 선택했다. 릴리스 세트·cron 8개 경로·9/28 PREOPEN 라우팅 PASS이며 선택 당시 메인 PID는 없다. 별도 위젯·에피소드 기계 핀은 변경하지 않았다.
  - 9/26 추가 장전 검증: 실제 프롬프트 호출 중 발견된 장후 token ceiling 오류를 수리하고 계약 보완 v4를 장후 후보로 등록했다. 이전 정책 v3은 유지한다. 기존 9/23 발행 기계정책 v4가 현재 v5 점수 기준으로 소급 거절되던 loader를 역사적 계약 범위에서 수리했고 새 v5 후보 심사 기준은 유지한다. 최종 코드 릴리스 `auxiliary-ai-preopen-20260926-01017f46`를 메인·장후 선택기에 반영했다. 해당 릴리스에서 9/28 bootstrap 재생성·검증, 과거 기계정책 readback, 릴리스 세트 및 cron 8개 경로가 PASS다. 메인 PID 소비는 9/28 기동 후 대사한다.
  - 9/26 의미감시 보완: 장중 versioned AI raw→effective 전환·v2 profile 식별자/해시 형식·미호출 원인과 장후 AI stage 분모·holdout·선정 영수증을 보고 전용으로 구분한다. profile 내용 해시의 독립 대사와 PID 소비는 별도이며 `source_gap` 및 incumbent carry를 정책 승격으로 표시하지 않는다.
  - 의미감시 재검토: `main_auxiliary_policy` 완료 영수증의 원천일·해시와 AI stage 보고서의 실제 바이트를 대사하고, 완료 후 보고서 누락·후보 집합/유형별 분모·선정 정책 해시 결손을 경고한다. 기계 승률 sidecar만 남은 전체 보고서 결손, 보유·청산 Markdown만 남은 JSON 의미 영수증 결손도 드러낸다. 9/28 이전 보유·청산 보고서에는 신규 익절 의미 계약을 소급 적용하지 않는다. 감시기는 보고 전용이며 다음 자연일의 release/PID 소비·체결·비용은 별도 수용한다.
  - 감지기 예약 복구: 설치 목록에 없던 `ERROR_DETECTION_FULL` 두 5분 예약을 복원하고, 릴리스 라우터가 소유한 21:55 최종화 예약이 동일한지 설치 전후 대사한다. 장중 감지기는 검토된 workspace HEAD, 장후 최종 감지기는 선택 릴리스 commit을 확인하며 첫 자연 실행 report의 7 detector·고유 run ID·의미 상태를 별도로 수용한다.
  - 미종결 수용: 9/23은 독립 날짜 holdout과 자연 writer→trace→owner 완료 경제성이 없으며 9/28 bootstrap의 compact auxiliary receipt도 invalid다. 오프라인 제공자 응답은 자연 호출·실현손익 증거가 아니다. 다음 적격 자연일의 source·후단 결과·stage terminal 및 실제 메인 PID 소비를 확인하기 전에는 신규 AI 임계치 승격이나 실현 수익 개선을 주장하지 않는다.
  - 구현 완료 기준: 실제 machine `ENTER_NOW`의 `entry_execution_sizing_plan_sha256` writer→AI trace `entry_economic_plan_sha256`→owner replay seed와 exact input/응답·근거·판정 전 수치/유형·비용 label producer를 연결한다. 기존 근거 개수 두 축, 세 bounded-risk materiality 수치, 가격·tick/시가총액·유동성·변동성·구조 상태 selector, compact prompt 변형 **네 조정축 전부**의 후보·동일 basis 평가·독립 holdout·단일 AI component CAS·v1/신규 loader·parent fallback·rollback·stage/PREOPEN/장중 경로를 코드와 fixture로 닫는다. 같은 frozen source의 분모·행동·EV 동등성과 stage wall/CPU/RSS/I/O·provider budget·후속 handoff 성능을 대조한다. source gap은 해당 leaf의 승격만 carry하며 구현 누락을 완료 처리하지 않는다.
  - 운영 수용 기준: 자연일에서 네 축의 후보·선정/미선정·비용 EV와 stage terminal, 실제 PID의 AI 정책 hash·판정 변화·후단 주문 및 `COMPLETED + valid profit_rate`를 순서대로 대사한다. 적격 자연 근거가 없으면 원인별 `source_gap` 또는 `insufficient_independent_evidence`와 incumbent carry를 기록하고 운영·경제성 수용은 OPEN으로 남긴다.
  - 권한 경계: 이 항목은 계획·증거 owner이며 현재 문서 변경만으로 AI threshold, prompt/provider, 주문, hard guard 또는 봇 PID를 변경하지 않는다. 기계 BLOCK/RECHECK 및 타 family의 표본을 AI 승격 근거로 전용하지 않는다.

## 최초 수량 유형 정책

- [ ] `[InitialQuantityBaselinePid0928] 최초 수량 유형 기본정책의 장전·PID 소비 대사` (`Due: 2026-09-28`, `Slot: PREOPEN`, `TimeWindow: 07:35~09:30`, `Track: RuntimeStability`)
  - Source: [최초 수량 유형 정책 계획 §13–§14·§18·§21–§22](../proposals/scalping-initial-entry-quantity-type-policy-closed-loop-plan-2026-09-26.md), [초기 정책 릴리스 영수증](../audit-reports/2026-09-27-initial-quantity-baseline-release-selection.md), [장후 원천 수리 릴리스 영수증](../audit-reports/2026-09-27-initial-quantity-refresh-release-selection.md), [최초 가중 선택 수리 릴리스 영수증](../audit-reports/2026-09-27-initial-quantity-first-weighted-release-selection.md).
  - 순서: 초기 행동 동등 정책의 배포 전 검증·장후 source-only 수리·최초 형상 선택 허들 수리는 불변 릴리스 `c0d88893`에 포함된다. PID가 아직 없는 것은 이 선택의 결함이나 사전 승인 차단 사유가 아니다. 정상 PREOPEN 파일·env 확인 후 기동하고, 그 뒤에 PID 소비를 대사한다.
  - 완료 기준: 9/23까지 완료 거래 387건·익절 244건에서 생산한 초기 후보의 stage/replay/후행 원천 SHA → `data/runtime/initial_quantity/current.json` → 불변 초기 기본정책 파일 SHA → 9/28 bootstrap manifest/env/verify → 선택 release → 실제 Main PID의 파일·SHA 및 첫 자연 수량 유형 영수증을 각각 대사한다. 기본정책의 모든 유형은 기존 5단계 수량·주문 형상·프로필 시간을 유지한다. 장전 영수증만으로 주문 체결이나 비용 후 효과를 주장하지 않는다.
  - 권한 경계: 최초 정책에는 부모 대비 우월성·후속 갱신 표본 허들을 요구하지 않는다. 387건 전수 재생에서 익절 244건의 원화 가중 형상 재선택 결과는 6유형 모두 `parent`이고 replay 368.187초·peak RSS 154,752KB다. 후속 분할·총시간 변경은 순차 실주문 취소 terminal 안전 경로를 검증하기 전까지 활성화하지 않으며 broker/account/quantity/cap/hard safety와 AVG_DOWN 원진입 pin을 보존한다.

- [ ] `[InitialQuantityClosedLoop0928] 수량 유형별 후속 정책·순차 주문 시간의 폐루프 완성` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [최초 수량 유형 정책 계획 §23 완료 순서·§24–§28 구현·의미 감시·cap 체결 계약](../proposals/scalping-initial-entry-quantity-type-policy-closed-loop-plan-2026-09-26.md).
  - 9/27 배포 진행: 타임아웃 소유권 재리뷰를 마친 최종 코드 릴리스 `96c67f30`을 메인 selector에 선택하고 최초 v2 정책 파일 SHA `ba72d720…`을 `current.json`에 CAS 적용했다. release-set·cron 8경로·9/28 PREOPEN print-plan·9/28 정책 로더 PASS. 실데이터 결과 6유형 모두 부모 5단계·부모 분할·기존 프로필 시간이다. 9/28 기존 bootstrap은 구 정책 세대로 검증 실패하므로 정규 PREOPEN 재생성/verify와 Main PID 파일 SHA를 따로 대사한다. 9/27 선택 릴리스의 갱신 stage는 0건 `carry_parent`/validator PASS/wall 0.80초다. 유형별 ratio 자동 연구·정규 장후 전체 체인 성능과 journal OPEN 뒤 로컬 주문 소실의 자동 복구는 계속 OPEN이다.
  - 9/27 최신 배포: 재기동 중 `OPEN/PARTIAL/CANCEL_REQUESTED` journal과 로컬 주문 소실, 취소 intent 뒤 로컬 주문 잔존을 정확 broker·Main owner·계좌 terminal로 복구하는 불변 릴리스 `3ccd0b89`를 메인 selector에 선택했다. 영향 회귀 63건·compile·diff PASS, release-set·cron 8경로·9/28 PREOPEN print-plan PASS, 정책 SHA `ba72d720…`과 current SHA `a34d980f…` 유지. 증거 없는 취소 반복·후속 BUY는 금지된다. [최신 재리뷰](../audit-reports/2026-09-27-initial-quantity-closed-loop-review.md)를 기준으로 본다. 유형별 ratio 자동 선정과 정규 장후 전체 체인 성능은 계속 OPEN이며 9/28 정상 PREOPEN·실제 Main PID 소비는 아직 관측 전이다.
  - 9/27 가격 증거 보강: 원주문 `kt00007.ord_uv`와 계획된 제출가격(시장가 probe는 0)을 종결·취소 복구에 대사하도록 수리한 불변 릴리스 `ffe86509`를 당시 메인 selector에 선택했다. 종결/초기 bundle 회귀 63건, release-set·cron·9/28 PREOPEN print-plan PASS. 수량 정책 pointer는 그대로며 정상 PREOPEN·PID 소비, ratio 자동 선정과 장후 전체 체인 성능의 미관측 상태도 유지한다.
  - 9/27 갱신 자연 영수증 수리: 당시 메인 selector `363d170c`에서 장후 CLI가 PID/terminal 영수증을 전달하지 않아 갱신이 영구 carry되던 결함을 고쳤다. 거래별 수량 판정 PID와 그날의 PREOPEN 실제 PID/env 검증, 완료 비용 census를 자동 결속했다. 495건 영향 테스트, 387건·익절 244건 전수 재생(6유형 모두 부모), wall 372.228초·peak RSS 151,184KiB와 9/27 적용 후 0건 carry 검증이 통과했다. 정책 파일 SHA는 그대로다.
  - 9/27 재기동 PID 보존: 당시 메인 selector는 `db34188a`였다. 일별 최신 PID 검증 파일의 재기동 덮어쓰기 결함을 불변 날짜/PID 검증 archive와 거래별 검증 시각 결속으로 수리했다. 496건 영향 테스트, release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS. 유형별 ratio 후보 자동 선정과 정규 전체 장후 체인 성능은 OPEN이고 9/28 정상 PREOPEN·실제 Main PID 소비는 사후 수용한다.
  - 9/27 cap 원천 코드 선택: 당시 메인 selector는 `37223b46`이었다. 유형별 cap 후보에 필요한 최종 allocator 입력을 실제 진입 판정 이벤트에 source-only로 기록하고 장후 거래의 동일 주문·attempt·계획 SHA에 투영한다. 영향 496건 PASS, 387건·익절 244건 전수 재생 내용 SHA 불변, replay/후보/stage 검증 PASS, wall 373.741초·peak RSS 151,016KiB. release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS, 초기 v2 정책 SHA 불변이다. 대체 수량 체결 가정 결정 전에는 cap 수치를 변경하지 않는다. 9/28 정상 PREOPEN·Main PID 소비와 실제 postclose 전체 체인 자원/terminal은 배포 후 수용한다.
  - 9/27 사용자 결정·기동 전 후속 코드: 대체 cap 수량은 **당시 0D 호가 잔량·동일 route/epoch의 후행 0B 틱으로 보수적으로 체결 재생하고 부족분은 미체결**로 둔다. §28의 원천·비용·익절 순이익 가중·손실 포함·변조 방지 회귀를 검토하고, 실제 데이터 성능/결과 검증 후 불변 릴리스 선택을 확인한다. 9/28 정상 PREOPEN/PID·자연 주문·정규 장후 전체 chain 수용은 각각 실제 발생 뒤에만 판정한다.
  - 9/27 최종 cap 코드 선택: [재리뷰·성능 영수증](../audit-reports/2026-09-27-initial-quantity-cap-depth-replay-review.md)에 따라 불변 릴리스 `50ffc08e`를 메인 selector에 선택했다. 영향 238건, 선택 릴리스의 정책/주문 94건·진입 64건·cap 원천 2건 PASS; 387건 전체 replay validator PASS/wall 368.549초·peak RSS 111,992KiB/6유형 부모 형상 유지; 적용 세대 0건 `carry_parent` stage validator PASS/wall 0.401초다. release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS, 초기 v2 policy SHA `ba72d720…` 불변. 정상 9/28 PREOPEN의 manifest/env/verify, 실제 Main PID, 자연 cap 원천·terminal과 **정규 장후 전체 chain 성능**은 사후 수용한다.
  - 9/27 전체 미커밋 작업본 재검토·후속 선택: [검토·배포 영수증](../audit-reports/2026-09-27-uncommitted-worktree-review-deployment.md)에 따라 독립 최신 날짜 holdout 결손을 수리한 불변 릴리스 `9a03c939`를 당시 메인 selector로 선택했다. 이전 `50ffc08e` 선택 기록은 이력이며, 이후 통합 선택 commit은 `data/runtime/runtime_release_selection.json`이 소유한다. v2 정책 SHA는 유지했고 release-set·cron 확인은 PASS; 정상 PREOPEN·실제 Main PID·자연 terminal·경제성은 미관측이다.
  - 의미 감시 수용: 9/28 감지기의 `artifact_freshness.initial_quantity_semantics`에서 당일 적용 정책 SHA·6유형 ratio/형상/시간 모드, 날짜별 PID 검증 archive, 순차 bundle의 수량 보존·정책 형상/선정 T·leg terminal deadline, 정규 장후 stage의 `valid_empty/carry_parent/eligible_source_only/source_gap`을 대사한다. `policy_selected`/`verified_receipt`/`journal_terminal_observed`는 각각 코드·PID 파일·journal 근거이며 자연 broker 체결·비용 후 성과의 대체 증거가 아니다. 손상/기한 초과를 감지해도 감시기는 주문·취소·정책 CAS를 실행하지 않는다. 자연 detector report의 같은 날짜·고유 run ID를 사후 확인한다.
  - 9/27 의미 감시 코드 선택: 당시 메인 selector `964ed6d1`은 수량·분할·시간 의미 검사를 추가했다. 추가 리뷰에서 오래된 손상 journal을 당일 결함으로 귀속할 수 있던 문제를 고쳐 현재 selector를 `bee25b17`로 교체했다. 영향 181건·표적 6건 PASS, 9/28 사전 읽기 전용 검사 약 168ms, release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS. 정책값·current SHA는 유지한다. `ERROR_DETECTION_FULL` 두 5분 cron 행과 21:55 최종화 행이 설치돼 있음을 읽기 전용 확인했다. 첫 자연 detector 영수증과 PID·주문·장후 terminal/비용은 아직 미관측이다.
  - 진행 상태: 당시 선택 릴리스 `c0d88893`에 포함된 `538bad38`의 정규 장후 wrapper는 `effective_from` 이후 완료 거래 replay→익절 후행 `ka10080` 원천→같은 census의 1200초 타임아웃 연구→갱신 평가 source-only stage와 summary/strict 필수 입력을 연결한다. 체결 주문번호→제출 attempt ID·실행 계획 SHA→체결 전 수량 판정의 같은 attempt ID·계획 SHA·부모 정책 파일 SHA가 모두 이어지는 거래만 후속 갱신 적용 세대 표본으로 센다. 9/27 릴리스 실행에서 효력일 이후 완료 거래는 0건이라 유효한 `carry_parent`이며, 실제 PID 소비는 미확인이다. 후속 선택 릴리스 `9a03c939`에는 적격 stage의 정책 발행/CAS 경로가 포함되지만 자연 실행·정책 적용은 미확인이다. 새 9/28 원천일의 자연 실행 및 전체 체인 성능은 미확인이다.
  - 성능 근거: [387건 전체 실데이터 격리 측정](../audit-reports/2026-09-27-initial-quantity-shared-scan-performance.json.txt)은 수량 재생 372.255초·peak RSS 152,592KB, 동일 스캔을 재사용한 타임아웃 후보 34,056건 0.558초·추가 pipeline 스캔 0회를 기록했다. 외부 후행 API·정규 장후 전체 체인과 첫 자연 원천일의 성능은 별도 수용한다.
  - 비용 계약 재검토: [매도금액 단일 비용 재생](../audit-reports/2026-09-27-initial-quantity-cost-contract-rereplay.json.txt)에서 완료 387건·익절 244건 입력/유형 모수를 유지하고 6개 유형의 `parent` 선정과 연구용 최고 타임아웃 후보가 동일함을 확인했다. 수정 수량 재생 367.075초·peak RSS 154,960KB, 타임아웃 34,056건 0.555초다. 새 보고서는 비용 모델을 결속하며 구 경제 수치를 후속 승격에 재사용하지 않는다. 초기 행동 동등 정책의 기존 선택은 유지한다.
  - 순차 주문 코드 리뷰: 작업공간의 exact broker/owner/계좌 terminal bridge와 CAS journal에서 취소 intent 실패 후 broker 호출, 불확실 응답의 중복 취소, 계획 수량·가격·경로 불일치, 전량 체결의 취소 오분류를 수리했다. 새 bundle이 구 병렬 BUY loop로 들어오면 broker 호출 전 차단한다. 격리 14건·기존 주문 회귀 897건을 분리 실행해 통과했다. 최초 BUY intent 생성·후속 leg dispatcher·재시작 복구는 아직 없으므로 이 코드는 선택 릴리스에 포함하지 않았다.
  - 추가 구현·재리뷰: wrapper·summary의 갱신 시작을 선택 정책 `effective_from`/SHA로 결속하고 모든 새 갱신 stage에 동일 census 타임아웃 연구를 요구했다. 적격 후속 유형별 형상은 source-only 불변 후보 파일로 stage에 결속한다. 영속 `SUBMIT_INTENT/UNCERTAIN`은 재제출 없이 broker 재조회, `CANCEL_REQUESTED`는 terminal 재대사, 전량 체결은 `WAIT/CANCEL` 양쪽에서 정확 terminal 증명을 취소보다 먼저 시도하고 늦은 확인은 예산 초과로 기록한다. journal의 계획·종목·대상·전략을 대사하고 주문번호와 로컬 주문의 attempt·수량·가격·route·tag를 고정했다. 아래 대상별 index 복구 이전에는 메모리 bundle만 한 세대 앞선 journal의 부모 SHA로 복구했다. 영향 테스트 130건·당시 journal 및 기존 주문 회귀 905건 PASS, 9/27 실데이터 0건 `carry_parent` 격리 재생 wall 0.67초·peak RSS 133,812KB다. 클린 기준 9/23 전수 387건·익절 244건의 유형·선정·보고서 SHA가 이전 영수증과 일치했고 replay/후보/stage validator PASS, wall 369.77초·peak RSS 152,196KB다. 동일 replay의 외부 `ka10080` 193그룹 전체 수집은 모두 응답했고 후행 저가 관측 170·미도달 47·분봉 창 결손 27, 전체 프로세스 wall 124.98초·peak RSS 432,416KB이며 기존 원천과 상태·가중 결과가 같았다. 당시 `c0d88893`에는 실행 가능 v2 publisher/CAS·실제 순차 dispatcher·응답 불확실 주문의 broker/owner 복구가 포함되지 않았다. 후속 `9a03c939` 코드 선택 이후에도 정규 전체 장후 체인 성능·자연 주문/terminal·PID 소비는 OPEN이다.
  - 재기동 복구 추가: 대상별 CAS journal index로 메모리 bundle이 없는 `BUY_ORDERED`에서 동일 종목·대상·attempt를 재결속하고 broker 재조회만 요청한다. terminal 후 보유·체결 수량 대사로 `HOLDING/WATCHING` 인계하며 index는 영속 terminal 표식으로 남겨 인계 중 중단을 복구한다. 새 attempt는 terminal 표식 뒤에만 생성한다. journal·기존 주문 908건 PASS. 첫 BUY intent와 후속 leg 실주문 caller, 실행 가능 v2 정책, 전체 체인 성능은 여전히 OPEN이다.
  - 대상 index 결손 재리뷰: 손상 index의 메모리 유무 양쪽에서 신규 주문·취소를 보류하고 5초 제한 broker snapshot을 요청한다. indexed terminal도 index 파일이 없으면 보유 인계하지 않는다. 결손 회귀를 더해 journal·기존 주문 910건, compile·diff·print-only 파서 PASS. 첫 BUY intent·후속 leg dispatcher·실행 가능 v2 정책·응답 불확실 주문의 broker/owner 복구·정규 전체 체인 성능은 여전히 OPEN이다.
  - index 생성 중단 복구: 최초 journal만 저장되고 index가 없는 경우 동일한 세대 0·내용의 재시도만 허용하고, intent가 진행된 orphan은 차단한다. journal·기존 주문 911건 PASS. broker intent 이전 index 완료를 보장하는 실제 submit caller는 아직 OPEN이다.
  - 9/27 작업공간 추가: 첫 BUY 직전 영속 intent와 응답 불확실시 재제출 차단, 후속 순차 leg/P1 제출 및 broker owner 복구를 실제 caller에 연결했다. 변경 최초 후보의 부모 롤백 정책 생성과 v2 최초·갱신 불변 정책/parent CAS/PREOPEN 재귀 결속, 정규 장후 최종 strict 뒤 적격 stage만 release-set 잠금 아래 선택하는 경로를 구현했다. 선택 메인 릴리스는 여전히 `c0d88893`이며 이 작업공간 코드는 미배포다. 유형별 수량 ratio 연구·적용과 검증된 최적 총시간 선택, 전체 broker fixture/정규 장후 성능·재리뷰·새 불변 릴리스 선택은 OPEN이다.
  - 9/27 추가 재리뷰: v2/갱신 수량 결정의 유형 행 영수증과 갱신 부모 세대 상태명 불일치를 수리했다. cap 10/15/20% 수량 런타임, 영속 첫 주문 시각 장후 수집, 정확 시작·유형별 충분한 모수·3개 날짜·비용 후 우위가 있을 때만 1200초 이내 총시간을 선택하는 코드를 추가했다. 현재 자연 갱신 0건은 `carry_parent`이며 수치 정책 선택 근거가 아니다. 유형별 cap의 데이터 기반 선정, 전체 성능·브로커 fixture 재검증, 선택 릴리스 적용은 계속 OPEN이다.
  - 우선순위: 초기 행동 동등 정책의 정상 기동·PID 확인을 먼저 진행한다. 장후 source-only 수정은 주문 동작 변경 없이 독립 검증·릴리스할 수 있으며 후속 `T/n` 실주문 구현 완료를 기다리지 않는다.
  - 구현 순서: 기존 선택 릴리스의 사후 PID 수용과 병행해 같은 원모수의 최초/갱신 후보 → 불변 v2 정책·격리 CAS → 첫 BUY intent/순차 leg dispatcher → 정확 주문 취소·terminal/재시작 복구 → 정규 장후·PREOPEN 결속 → 데이터 성능·리뷰 재검증 순서로 닫는다. 새 수치 정책의 실제 pointer 전환은 안전 코드와 Plan Rebase §5 근거 계약 정합성 검증 후 선택 릴리스와 같은 인계 잠금에서 한다.
  - 완료 기준: 완료 실거래 전수와 익절 순이익 원화 가중 후행 원천을 정규 장후 producer→후속 갱신 평가/불변 정책 CAS→terminal/summary/strict→PREOPEN/PID에 같은 SHA로 연결한다. 실제 첫 주문 시작 기준 1200초 이내 유형별 총시간을 probe 포함 계획 leg 수로 정수 초 분배하고 순차 제출·취소 요청·broker/owner/계좌 최종 대사·재기동 복구·잔량 보존을 실주문 경로에서 검증한다. 봉인된 동일 전체 원모수로 결과 결함·벽시계/CPU/RSS/I/O·원천 결손과 후보 EV를 재검증하고 구 TTL·중복 장후 소비자의 도달성 0을 증명한 후에만 퇴역시킨다.
  - 배포 순서: **사전 gate**는 변경 정책 publisher/CAS·순차 주문/취소 terminal의 격리 검증·역사 데이터 재생·외부 후행 API 냉·온 및 장후 전체 성능·PREOPEN 파일/세대 검증이다. 이를 통과한 후 같은 잠금에서 불변 코드 릴리스와 정책 pointer를 선택하고 정상 PREOPEN·기동으로 적용한다. **사후 수용**은 실제 PID의 동일 SHA 소비, 첫 자연 주문/terminal·비용 및 그 적용 세대의 갱신 평가다. 아직 발생할 수 없는 사후 자연소비를 배포 승인 조건으로 사용하지 않는다. 자연 표본 0건은 `not_observed`로 남기고 코드·정책 배포 완료와 경제성 확인을 구분한다.
  - 권한 경계: 최초 행동 동등 기본정책의 PID 수용과 후속 변경 정책 승격을 분리한다. 새 분할·총시간은 실주문 terminal bridge와 데이터·성능 gate가 PASS하기 전까지 선택하지 않는다. `entry_cancel_wait`의 주문 시작 결정, P1 주문가·hard safety, AVG_DOWN/PYRAMID 및 타 owner는 유지한다.

## 장중 생산자–장후 소비자 전수 점검

- [x] `[IntradayPostcloseHandoffS0] 장중 생산자–장후 소비자 전체 경로·소유권 전수조사` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [단계별 전수조사·보완 계획 §3 S0·§4 S0](../proposals/intraday-producer-postclose-consumer-codebase-gap-repair-plan-2026-09-27.md).
  - 실행 범위: 첫 지시 시 S0만 실행하여 전체 `src`·`deploy`·설정/스케줄·등록 stage의 양방향 producer–artifact–consumer 목록과 활성/OFF/퇴역·owner·실제 dispatch를 대사한다. 기존 family별 OPEN owner는 유지한다. S1–S8은 S0 결과를 받은 뒤 각 단계 지시문으로 따로 착수한다.
  - 완료 기준: S0 실행일 보고서에 전수 발견 방법, 미분류/고아 경로, 선택 릴리스·PID 증거 수준, 다음 단계 결손 ID·owner가 있고 목록을 재검토했다. 이 항목의 완료는 결손 수리·정규 장후 실행·배포·자연 경제성 수용을 뜻하지 않는다.
  - 9/27 완료 증거: [S0 연결표·고아 후보·S1 인계](../audit-reports/2026-09-27-intraday-postclose-handoff-S0.md). S1–S5 조사와 실제 PID·자연 수용은 별도 OPEN 범위다.

## 시장 발견→기계 판정 제로베이스 재설계

- [ ] `[ScannerSemanticWatchReplacement0928] 시장 발견→기계 판정 새 대기열·조건검색/VCP/S15 퇴역` (`Due: 2026-09-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [9/28 제로베이스 재설계·배포 경로](../proposals/scalping-zero-base-discovery-machine-intake-plan-2026-09-28.md), [장기 점유·반전 부재 자연 재생](../proposals/scalping-scanner-semantic-watch-replacement-plan-2026-09-28.md), [상승 표본 1회 판정](../audit-reports/2026-09-28-kospi-positive-machine-one-pass-source-test.md). 기존 stable ID의 이전 감시퇴출 시험을 증거로 보존하고 새 발견·평가 대기열 owner로 범위를 이관한다.
  - 결정 근거: 11:25:30 고정 KOSPI 보통주 상승 관측 113종목 중 코드·시각 연결의 스캐너 풀 91·승격 41·풀 미승격 50이다. 이 수치는 scanner pool의 정확 route 적격률이 아니다. 미승격 50의 첫 제외는 일반 슬롯 29, 회차 신규 상한 18, 상승 예약석 1, cooldown 2였다. 9/28 11:13 Main PID 기동 시 감시 상한 22, 조건검색 ON, WS 등록 상한 56이었다. 13개 조건식 구독 요청에 비해 cutoff 전 같은 condition 세대의 제출 0건과 출처 식별 결손이 있다. VCP 3식은 실제 구독되었고 clean baseline 이후 VCP_CANDID 6건에서 매수·완료 및 SHOOTING/NEXT 전환은 확인되지 않았다. S15 두 식은 실제 이름과 `_01` 구독 키워드가 달라 미구독이며 S15 추천·성과 표본이 없다. 이 근거는 수익률 0/음수를 뜻하지 않는다. 113은 시장 전수가 아니며 미평가 종목을 기계 `BLOCK`으로 채우지 않는다.
  - 완료 기준: 공식 원천·route·시각·범위가 고정된 독립 발견 원장과 condition별 원시 유입→WS item/요청→유효 기계 입력/제출 원장을 만든다. 기존 스캐너와의 점수·상한·제출 수 비교로 선택하지 않는다. 새 `discovered→queued→probed→assessed→machine action→submitted→terminal` 큐의 공정성, 공유 5/4 읽기 예산, WS peak, source-gap, 주문·보유 custody 및 hard safety를 같은 세대에서 검증한다. VCP 3식과 S15 2식은 새 bootstrap/재연결 구독 및 신규 후보·주문 경로에서 제거하고, 전용 코드·복구/영수증/동기화 참조를 영향 리뷰와 회귀로 정리한다. 먼저 실제 PID cwd/env의 원장, DB·주문 소유권, 브로커 양 시장 미결·보유와 과거 WATCHING을 대사해 남은 청산/복구 소유권이 있으면 terminal까지 recovery-only 호환성을 보존한다. S15 작업공간 journal 원본과 역사적 DB/이벤트는 삭제하지 않는다. 다른 스캘핑 식은 유일 적격 기여와 WS 비용으로 별도 제거하며 swing과 기존 주문·보유 custody는 유지한다. 장기 점유 퇴출은 신선한 관측과 반전 부재가 확인된 세대에만 적용한다. 퇴역만 담은 불변 릴리스의 신구독 VCP/S15=0, 신규 VCP/S15 주문=0, custody 보전, 재활성 없는 롤백을 먼저 검증한 뒤 새 queue 릴리스의 영향 리뷰/회귀·PREOPEN을 닫는다. 장후 선택·정상 재기동·실제 PID 영수증 및 이후 제출·terminal·비용 후 결과를 각각 별도로 확인한다. 원천/판정 입력 결손은 `source_gap`으로 남긴다.
  - 13시대 작업공간 진행: 독립 패널·영속 큐·정확 route 0B/0D probe·provider 없는 기계판정·Main 임시 DB→WATCHING 편입을 연결했다. 새 모드에서 SCALPING condition 구독/유입은 중단하고 swing은 유지한다. VCP/S15 신규 경로와 S15 직접 BUY 함수를 제거했으며 custody 복구 코드는 보존한다. 공식 Kiwoom SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재확인했다. 이는 릴리스/PID/자연 경제성 수용이 아니다. 남은 POSTCLOSE 문턱은 전체 리뷰·회귀, 원시 source/부하 실측, 적용 직전 custody 대사, 두 불변 릴리스·PREOPEN/실제 PID 수용이다.
  - 14시대 재리뷰: 순수 VCP/S15 퇴역 릴리스 `53854ced`(신규 스캐너 코드 없음) 영향 회귀 1,545건과 새 발견 릴리스 `d525ece7` 확장 회귀 928건 및 예외·WS 재사용 보강 회귀 41/14건, S15 dead helper 제거 회귀 39건, 유동성 tie-break 회귀 13건 통과. source-only 4패널 실호출은 최대 200행씩 757개 관측/8.38초였고 전체 시장 전수는 아니다. 9/25·9/28 저장 패널의 큐 전용 재생에서 stale 120초 차단과 패널 사이 10초 dispatch를 검증했으나 실제 probe·제출 성과는 미관측이다. 14:00:49 KST 예비 custody는 VCP 과거 WATCHING 1건·매수 0, S15 journal 1개, 브로커 KRX/NXT 잔고 1·미결 0, VCP/S15 코드 중복 0이었다. 적용 직전 재대사가 필요하다. NXT 애프터마켓 체결은 20:00까지라 구조 재기동은 그 뒤의 POSTCLOSE 슬롯에서 수행한다.
  - 14:56 사용자 즉시 배포·route 정정: KRX/NXT 분리 패널은 잘못된 운영 계약으로 확인해 신규 스캐너를 퇴역 전용 `53854ced`로 즉시 롤백·PID `647108`을 검증했다. `ka10027 stex_tp=3` 통합 2패널, `_AL` WS/REST, 명시 `SOR` 주문 요청 및 주문 직전 route fail-closed로 수정한 `826f3d72`은 source-only 2/2 패널·400행·7.75초와 회귀 210건 후 배포해 PID `657079`의 자연 통합 queue·`_AL` REG/REMOVE·기계 `RECHECK` 1건을 확인했다. 신뢰 체결 방향 결손을 원천 결손으로 재분류한 `d619923a`를 후속 적용해 현재 PID `661520`, bootstrap/release-set PASS다. 기존 분리 queue는 보존하고 신규 통합 queue로 시작했다. 자연 `ENTER_NOW`/제출·체결·terminal·비용 후 EV는 계속 OPEN이다. 자세한 공식 SHA·경로·수정 리뷰는 [제로베이스 구현 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md)를 따른다.
  - 15:23 WS probe 대기 보완 릴리스 `71caed84`를 배포해 당시 Main PID `676594`, 당일 bootstrap/release-set PASS를 확인했다. 정확 `_AL` 0B·0D와 0B 5건을 기존 3초 한도 내에서 기다릴 기회를 주고 결손은 그대로 원천 결손으로 남긴다. 다른 세션 작업본 통합 리뷰 및 후속 선택 결과는 [통합 작업본 리뷰](../audit-reports/2026-09-28-integrated-worktree-review-and-deployment.md)를 따른다. 새 PID의 자연 제출·체결·terminal·비용 후 EV는 OPEN이다.
  - 15:44 전체 당일 작업 통합 커밋 `d8aa4a64`를 선택·정상 재기동해 현재 Main PID `688047`, 정확 릴리스 cwd, scanner flag=true, 당일 정책 handoff 및 release-set PASS를 확인했다. 2,044건 영향 회귀 통과, 중간 스캐너 릴리스 6개 정리, 기존 안정/퇴역 rollback 보존. 다른 세션의 3개 오래된 dirty worktree는 소유권·원천 계약을 검토해 원본 보존했다. 자연 제출·체결·terminal·비용 후 경제성은 OPEN이며 [통합 작업본 리뷰](../audit-reports/2026-09-28-integrated-worktree-review-and-deployment.md)에 단계별 영수증을 적었다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:16b563fe22da3238d334bf547845a7d83950dbb31ec2f2a8a287c036cd486f1e -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-23; 발행 2026-09-23; 적용 2026-09-28. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `7dc532a4ccb00821b4046d0f7abffa869733011ba75838d7e2187e6796aa136b`; 정책 bundle `7430a284d9c11220beebaa7cc7f19815fdb2460b2cf25dc5d8b3df26aa632cb1`; consumer `6c5ad4abad031cc5d81580d5c745c10150c038a27ca3d89ff45568940f7fd14c`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
