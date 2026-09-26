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
  - 미종결 수용: 9/23은 독립 날짜 holdout과 자연 writer→trace→owner 완료 경제성이 없으며 9/28 bootstrap의 compact auxiliary receipt도 invalid다. 오프라인 제공자 응답은 자연 호출·실현손익 증거가 아니다. 다음 적격 자연일의 source·후단 결과·stage terminal 및 실제 메인 PID 소비를 확인하기 전에는 신규 AI 임계치 승격이나 실현 수익 개선을 주장하지 않는다.
  - 구현 완료 기준: 실제 machine `ENTER_NOW`의 `entry_execution_sizing_plan_sha256` writer→AI trace `entry_economic_plan_sha256`→owner replay seed와 exact input/응답·근거·판정 전 수치/유형·비용 label producer를 연결한다. 기존 근거 개수 두 축, 세 bounded-risk materiality 수치, 가격·tick/시가총액·유동성·변동성·구조 상태 selector, compact prompt 변형 **네 조정축 전부**의 후보·동일 basis 평가·독립 holdout·단일 AI component CAS·v1/신규 loader·parent fallback·rollback·stage/PREOPEN/장중 경로를 코드와 fixture로 닫는다. 같은 frozen source의 분모·행동·EV 동등성과 stage wall/CPU/RSS/I/O·provider budget·후속 handoff 성능을 대조한다. source gap은 해당 leaf의 승격만 carry하며 구현 누락을 완료 처리하지 않는다.
  - 운영 수용 기준: 자연일에서 네 축의 후보·선정/미선정·비용 EV와 stage terminal, 실제 PID의 AI 정책 hash·판정 변화·후단 주문 및 `COMPLETED + valid profit_rate`를 순서대로 대사한다. 적격 자연 근거가 없으면 원인별 `source_gap` 또는 `insufficient_independent_evidence`와 incumbent carry를 기록하고 운영·경제성 수용은 OPEN으로 남긴다.
  - 권한 경계: 이 항목은 계획·증거 owner이며 현재 문서 변경만으로 AI threshold, prompt/provider, 주문, hard guard 또는 봇 PID를 변경하지 않는다. 기계 BLOCK/RECHECK 및 타 family의 표본을 AI 승격 근거로 전용하지 않는다.

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
