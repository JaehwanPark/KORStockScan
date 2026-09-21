# 2026-09-21 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 메인 기계 진입판정 장후 튜닝 루프 복구

- [x] `[MainMechanisticEntryPostcloseLoopRestore0920] 메인 기계 진입판정 full calibration·다음 거래일 정책 발행 복구` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: ScalpingLogic`)
  - Source/Receipt: [상세 복구 계획](../proposals/main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md), [현재 정책](../../data/runtime/mechanistic_entry_policy/policy_2026-09-21.json). release `df2931b19`; report `83a088cd...`; bundle `c6a7253c...`; main·compact receipt와 strict chain PASS.
  - 완료: exact source→full paired calibration→family별 source 보존→incumbent carry 발행→summary/checklist 연결을 복구했다. 과거 8건의 exact 원화 replay는 `historical_unrecoverable`, 미래 자연 owner replay는 `prospective_resolution_mode=natural_maturity`로 분리했다. 정상 PREOPEN·실제 PID·적용 버전별 `COMPLETED + valid profit_rate` 성과는 아래 direct-family OPEN 작업이 소유한다.
  - 권한 경계: 기존 비용·holdout·promotion floor, provider·주문·수량·cap·custody·operator lock·hard safety를 완화하지 않는다. 구현·배포·정책 파일·PID 소비·자연 EV 개선을 별도 상태로 보고한다.

## 장후 통합 복구·최종 인계·정상 기동 준비

- [ ] `[PostcloseLateSourceFinalHandoffAudit0920] 장후 25–29 검증·전체 복구·다음 PREOPEN 기동 준비` (`Due: 2026-09-21`, `Slot: PREOPEN`, `TimeWindow: 07:00~07:20`, `Track: RuntimeStability`)
  - Source: [통합 보완·전체 재생성 상세계획](../proposals/postclose-integrated-verification-recovery-and-next-preopen-readiness-plan-2026-09-20.md), [장후작업 현행 활성 목록](../audit-reports/2026-09-05-postclose-work-inventory.md).
  - Preparation evidence: [통합 복구 최종 리뷰](../audit-reports/2026-09-20-postclose-integrated-recovery-review.md). 9/20 15:26:54 main/widget/machine 및 finalization DONE, 직접 원천11/11. code5bd73a8d2 배포, 서비스9개 정의/129개 인스턴스 시작 없는 source binding. 9/21 carry/fallback actual reader 검증 완료; 신규 승격0. 기존 main 운영 경제성 구조적 OPEN과 자연 PREOPEN/PID·완료 손익은 별개다.
  - 일정: 9/20 통합 수리·A–H 복구와 준비 검증을 마쳤다. 이 OPEN은9/21 07:00~07:20 준비 정책/source release/서비스 변경 여부 재확인만 소유한다. 정상07:35 PREOPEN 및 예정 기동/PID 소비는 기존 `DirectFamilyPreopenPolicyHandoff`가 소유하며 오늘 조기 실행하지 않는다.
  - 현황: source9/17 실패분의 통합 복구를 완료했고9/18 관측 미적재는 보존했다. 25–29 날짜/scoped/terminal/attempt, finalizer 설치·선행 의존, widget root, 과거 복구 날짜 결함의 수리 증거를 최종 리뷰에 남겼다. 기존 main 운영 경제성 미지원 계약은 원 owner의 구조적 OPEN이다.
  - Acceptance: 기존 경제성 구현은 재사용 검증하고 main ME8–ME13 병행 owner의 수리/회귀를 인계받는다. 서비스별 검증된 immutable source에서 source9/17→실제 publication→effective9/21을 고정한다. 전체 활성 main/widget/machine 결과와 직접 소비·단계별 rc·최종 summary/checklist/verifier·terminal을 대사한다. 과거 실패 이력은 보존한다.
  - 준비 정책: 검증된 candidate/유효 incumbent·기존 fallback을 구분한다. 필수 기동 계약 미충족은 정확한 blocked로 남기며 source gap을 no-edge로 바꾸지 않는다. 자동 생성 family 분류와 closure도 producer 증거 기준으로 재생성해야 한다.
  - 권한 경계: 9/20 통합 보완·검증·커밋/푸시·immutable 배포·전체 장후 복구 및 필요한 schedule/service source binding 수리는 사용자 승인 범위다. 봇 재시작/수동 기동·주문·조기 PREOPEN·외부 sync는 금지하며 기존 거래 시각·수량·guard를 보존한다.

**9/20 최종 정정:** 아래 AUTO 블록은 재생성된 직접 원천11/11의 최신 투영이다. main terminal proxy는 운영 비용 EV와 분리됐으며 미래 계약 증거 없는 natural maturity 추론을 제거했다. cancel/split의 역사 source gap은 지원 producer 회귀 실패를 뜻하지 않는다. 기존 메인 ME8/ME9/ME10 경제성 구조적 OPEN은 해당 owner에 남고, 장전 시간창은 실제07:35 PREOPEN/07:55~07:58 기동에 맞췄다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-17", "sources": {"independent_machine_terminal": {"sha256": "9e4f4300396e265b946ebe4dac435b856cc0d9e253bd31c15ab4d35c38cd8149"}, "independent_widget_terminal": {"sha256": "7ddb5a614204a1bcc4554a2bac1b7d4e4966c335b07dcdb82402300a930b0a8d"}, "runtime_approval_summary": {"sha256": "aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"allowed_runtime_apply": false, "apply_date": "2026-09-21", "expected_state": "future_due", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-21.json", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "746d8386d02a7f1736d14b3ef6b3a4f37e84aee9958fed56ce041371f24dd7fc", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "ab2aebb66b496b82c842e71948f1d621359160c9552bc0105753ea6232baac6c", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "878cd9c0e58f002b3e73de1d7ef88f1482e0878f1bf7279fcb601de0e8fdd484", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": "e6eb934aa5c94ef0dc13768a03201101f17770e39440700acdc77c1453cd3c96", "valid": true}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "d8c1ddd7788bd10c5421e6c0baa5857b279779697b0f64b49f39f45d6c47af2c", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": "afe0de10123f3a50b52cdccc3b65f3037f3ef96f80bb07221f08db13897fec66", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "746d8386d02a7f1736d14b3ef6b3a4f37e84aee9958fed56ce041371f24dd7fc", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "08aeca97da9b50e906812284b40afab3e5506cb4f220ae45ecf51c6d71b09c84", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "78455dc26512a907571b62df1c11320d62c66e5d8bec7068df0422d241de33af", "valid": true}], "runtime_effect": false, "schema": "direct_family_future_handoff_v1", "source_date": "2026-09-17", "source_preopen_state": "pending", "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-21.json"} -->

## Family 직접 증거 상태

- source date: `2026-09-17`; next apply date: `2026-09-21`.
- direct source: `11/11`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `scale_in_split` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `machine_entry` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `mixed` | `blocked` | `producer_contract_repair` |
| `low_price_expansion` | `source_gap` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `source_gap` | `blocked` | `producer_contract_repair` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `measured_no_edge` | `incumbent_preserved` | `terminal_incumbent` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-09-21`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - 9/21 Rising-missed 결함 수리: 늦은 source9/17 재생성이 effective9/18만 갱신하여9/21 정책 해시를 고립시킨 원인을 수리한다. [원인·발행/검증 계약·배포 증거](../audit-reports/2026-09-21-rising-missed-tp1-handoff-repair.md). 사용자 배포·재기동 승인 범위에서 기존 보고서 보존 재발행→당일 receipt 수용→새 PID 검증을 닫으며 `incumbent_preserved`, runtime override0을 유지한다. 다른 family와 전체 경제성 acceptance는 이 수정으로 완료하지 않는다.
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 판정 기준: source_date=`2026-09-17`, apply_date=`2026-09-21`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=blocked); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); low_price_expansion(valid=True, handoff=blocked); low_price_two_leg(valid=True, handoff=blocked); machine_entry(valid=True, handoff=not_applicable); main_mechanistic_entry(valid=True, handoff=blocked); rising_missed(valid=True, handoff=incumbent_preserved); scale_in_split(valid=True, handoff=incumbent_preserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 기동 계약: exact-date bootstrap이 apply enabled/date를 당일로 갱신하되 후순위 operator override/lock을 보존한다. pre-cutover context promotion의 두 commit 파일이 함께 보존 종료된 경우에만 context-only rollback을 적용하고, 부분 소실·hash/권한 불일치는 기동을 차단한다. 런처·관리형 restart·authority preflight의 PID 검증은 먼저 read-only로 확인하고 현행 bootstrap의 `--write-verify-artifact` 호출만 현재 receipt를 갱신한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`exact_stop_distance_missing_or_invalid`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-17.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`execution_compact_coverage_unproven`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-17.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceExpansion] low_price_expansion 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-09-17.json`.
  - 상태: family=`low_price_expansion`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`allocator_snapshot_contract_invalid`.
  - 완료 기준: closure_owner=`low_price_two_leg_expanded_candidate_research`, closure_test=`retained_source_isolation_frozen_allocator_independent_holdout_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-17.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_sample_floor`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-17.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_operating_population_unbound`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`future_exact_changed_decision_owner_replay_and_completed_profit_rate`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairScaleInSplit] scale_in_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`aa06d205e5e79f3b9921cc0a69cd8d5184e39e211fb62d840fddb607f2113332`, source_artifact=`/home/ubuntu/KORStockScan/data/report/scale_in_split_order_plan/scale_in_split_order_plan_2026-09-17.json`.
  - 상태: family=`scale_in_split`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`scale_in_split_order_plan`, closure_test=`eligible_add_fill_terminal_clock_cost_and_independent_paired_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```



## R0–R3 독립 AI 연구 폐기

사용자 지시로 `scalping.micro_reversion.ai_quality_cycle` 장후 실행기·R2/R3 인계·legacy/current-axis 전용 런타임 및 파생 산출물을 제거한다. 별도 OPEN 복구 작업을 만들지 않는다. 현행 compact·AI 원천/라벨·주문/체결·공유 경제성 owner는 보존한다. 구현·검증·삭제 증거는 [폐기 리뷰](../audit-reports/2026-09-18-ai-quality-cycle-retirement-review.md)를 따른다. 코드 선택·실제 PID 소비와 장후 전체 DONE은 별도다.

<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-17`; status: `waiting_sources`
- native rows SHA256: `775387a554d9781595ac71637571d270f0714437d297e4a467b2d4271a9926f0`
- counts: `{"already_implemented_verified_eligible": 0, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 0, "blocked_missing_evidence_nonrequest": 2, "deferred": 9, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 0, "implement_now_unaccounted_count": 0, "implementation_requested_total": 0, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 26, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 26, "observed_no_patch": 15, "rejected": 0, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"blocked_missing_evidence": 2, "deferred": 9, "observed_no_patch": 15}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 2}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"deferred": 9, "observed_no_patch": 14}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->


<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:fc0d94352f151b719e972fff253dc9f4921b5ebf936ac6cd6d30cc5a9d673c0c -->

## Entry cancel-wait 장후 handoff

- 평가 2026-09-17; 발행 2026-09-18; 적용 2026-09-21. `source_gap` / `incumbent_preserved`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->

## Low-price actual 정책 자연 적용·경제성 Acceptance

- [ ] `[LowPriceExpandedResearchRepair0918] 저가주 연구 입출력·해시·추천 handoff 보완과 배포·실소비 확인` (`Due: 2026-09-21`, `Slot: PREOPEN`, `TimeWindow: 07:35~09:35`, `Track: RuntimeStability`)
  - Source: [LP-A0–A7 구현 종결](../audit-reports/2026-09-19-low-price-actual-paired-implementation-closure.md), [원래 Acceptance·History](2026-09-18-stage2-todo-checklist.md#저가주-확장-연구-보완자연-경제성-검증), [상세 계획](../proposals/low-price-two-leg-actual-conditioned-paired-economic-search-and-preopen-runtime-consumer-improvement-plan-2026-09-18.md). [LP-B0–B6·수동 청산 정정 종결](../audit-reports/2026-09-19-low-price-exploration-manual-close-implementation-review.md), [후속계획](../proposals/low-price-two-leg-exploration-promotion-gate-separation-and-economic-evidence-completion-plan-2026-09-19.md).
  - 승인/History: 기존 사용자 구현·리뷰·commit/push·future immutable 배포 승인과 source9/17/pub9/18/effective9/21 incumbent_preserved/mutation0 증거를 유지한다. 완료된 LP0–LP6/Q0–Q5 또는 unchanged 전체 grid/raw를 재실행하지 않는다.
  - Acceptance: 정상7:35 공통 PREOPEN의 exact-date applied/hash, native preflight/service/machine의 selected source·실제PID 소비를 확인한다. Writer/reader/hash·기존accepted profile·등록된 미래seed/BBO/수량·same-date peer/비용 후 비교경제성의 기존 잔여조건을 보존한다. 자연 actual entry/fill·COMPLETED 비용 후 EV/관측일당 순익은 적용 버전에 귀속하고 미발생/null/sample/source/custody를 분리한다. Implementation closure는 자연 경제 개선 acceptance가 아니다.
  - 권한 경계: 조기 PREOPEN/수동 trading service restart·주문·새profile enrollment·quantity/target/cost/grid/floor·operator veto/custody/provider/Main restart/guard 변경 없음. 기존quarantine3·동일날짜 freeze·same-stage·rollback·hard safety를 유지한다. 전체chain 외부 FAIL을 본 family PASS로 바꾸지 않는다.
  - 다음 조치: 정상기동 receipt가 없으면 future_due/source_gap, 표본이 부족하면 hold_sample, 실제 source/경제조건을 닫으면 기존 unused paired window의 단일profile/axis 승격 경로로 넘긴다. 별도 신규 실행owner 없이 본ID를 유지한다.

  - LP-B 구현 Closure: source9/17/pub9/19/effective9/21 research2profile·distinct3개, 보조 carry CF3개 모두 순익/day 개선 없음. Applied manual13행/20leg의 역사 보정, actual/model custody 분리, v10/v9·v4 검증 및 verified incumbent carry/mutation0. Receipt: `tmp/low-price-exploration-manual-close-20260919/`. 자연 적용/PID/경제 개선과 whole-chain 외부 FAIL은 미완료로 유지.

## 삼성 native 경제성 및 기존 pipeline 자연 acceptance

- [ ] `[CodeImprovementWorkorderReview0918] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-21`, `Slot: ALL`, `TimeWindow: 07:45~20:35`, `Track: ScalpingLogic`)
  - PR 최종 재리뷰: `f7d4c468d`/`ae1b5df66`은 다일 자본 의존성, opening 원천 해시 재사용, 2차 phase 캐시 우회를 수리. 운영 producer·다일 지원 입력·정책 발행·실패 회귀50 통과. selected immutable `postclose-producer-repair-reviewed-20260920-ae1b5df66`, 9개 서비스 정의/129개 인스턴스 inactive/PID0 유지. 후행 결과·strict·9/21 reader 증거는 `tmp/postclose-producer-final-review-20260920/`; 자연 생성·PID 소비·EV 개선과 별개이다.
  - 생산자 역추적 PR0–PR5 구현·리뷰·배포: `11253429a` → 최종 `5532fce36`. 사전 자본 생성/날짜별 소비·장후 snapshot 거부, rising/census immutable binding, scanner 미호출 AI/원천 결손 및 SOR 정합성 보완. [통합 계획 §12.8](../proposals/postclose-integrated-verification-recovery-and-next-preopen-readiness-plan-2026-09-20.md#128-pr-실행-보완검증-기록-2026-09-20). source9/17 제한 재생성·9/21 reader·strict(main_terminal) PASS; 신규 양수 승격0. 자연 opening receipt/독립 표본/정상 PREOPEN·PID/완료 손익 확인 및 외부 cash-flow·미호출 AI 운영 범위는 별도 OPEN. 증거 `tmp/postclose-producer-repair-20260920/`.
  - Workorder 구조 구현: [W0–W6 계획·결과](../proposals/code-improvement-workorder-structural-closure-and-ev-evidence-prioritization-plan-2026-09-19.md). 수동 direct-family generation `2026-09-17-5aa459cacc82`, source/semantic `dcb36465f419973150280e44146de970374f578ec8f60e94aaf4955ea86d4039`(`logical_source_content_v2`), contract issue0·intake conservation PASS·implementation request0. source23/selected12/non-selected11은 implement0·attach14·defer9다. 과거 submit terminal gap51은 현행 call-local finish receipt가 구현되어 P3 자연 receipt 대기, WS repair receipt도 P3, tuning 허용 unknown warning은 P4 evidence다. Scanner opportunity는 비용 후 `-2.38954987%`/3pair/3일 `measured_no_edge`라 policy `254d5ab28a6b2089c4d6d036222aedb45dbc353dcd0d5429abd04c755bc9e010` incumbent 보존이다. Actual paired EV·원화 일별 순익은 과거 미선정 arm recipe/quantity/guard 결손으로 null이며 미래 사전 배정 arm 자연 owner를 유지한다.
  - Pipeline 재리뷰/정리 및 다음 삼성 분석: [owning review](../audit-reports/2026-09-18-pipeline-rereview-cleanup-and-samsung-machine-entry-analysis.md), `tmp/pipeline-rereview-samsung-analysis-20260918/`. 중첩 schema 손상 fallback/strict OPEN을 수리·회귀 검증하고 불필요 과거 진단125개만 제거, 원 불일치/현재/rollback 보호. 삼성 source/정책/독립 service는 read-only이며 완료 pair0/source gap을 natural wait나 no-edge로 바꾸지 않음. 배포·후행 재인계 receipt와 자연 PID/parity OPEN을 분리한다.
  - Pipeline verbosity Source/Closure: [PV0–PV6 계획](../proposals/pipeline-event-verbosity-incremental-parity-and-consumer-cost-optimization-plan-2026-09-18.md), [owning review](../audit-reports/2026-09-18-pipeline-event-verbosity-incremental-review.md), `tmp/pipeline-verbosity-incremental-20260918/` receipts. 운영 producer/종료·handover·publication/증분·정정·missing/resource 및 실제 후행 소비 계약을 검증한다. 동일 `order_pipeline_event_compaction_v2_shadow`의 source/resource/자연 OPEN을 `defer_evidence`로 보존하고 반복 신규 구현/provider/full-wrapper recovery 또는 전체 chain/PREOPEN GREEN으로 바꾸지 않는다. raw·주문·정책·threshold/quantity/budget/custody/override·resource floor 및 실행 중 release는 보존한다.
  - Pipeline 자연 Acceptance: 다음 유효 source-day의 전체/완료창 parity·정상 종료/restart coverage·실제 Sentinel/execution census 소비 및 제한 비용을 확인한다. 과거9/15/16 손실의 raw fallback/원인 미확정과9/17 bootstrap을 자연 표본 대기로 숨기지 않는다. 실제 PID/주문/EV는 이 진단으로 승인하지 않는다. 해당 native owner는 이 기존 code-workorder 실행 ID를 재사용하며 별도 중복 작업/cron을 만들지 않는다.

  - 삼성 implementation Source: [S0–S6 계획](../proposals/samsung-owner-quantity-native-economic-timing-plan-2026-09-18.md), [owning review](../audit-reports/2026-09-18-samsung-owner-native-economic-timing-implementation-review.md), `tmp/samsung-owner-economic-timing-20260918/`. 비교는 owner별 승인 수량 독립이며 shared capital authority 없음. 현재 9/19 checklist 부재 및 source-day9/18을 보존한다.
  - 삼성 Acceptance: 다음 eligible/blocked/recheck native root 및 SOR deferred opening의 최초 실행시점 source→cost/code/quantity/selected exit/admission/stage guard→원 order/fill terminal projection을 대사. 자연 independent model/candidate holdout floor·coverage를 충족하기 전 승격 금지. selector/unit config와 실제 PID 소비·실제 행동을 구분하고, actual root/version별 dedup rolling/cumulative 비용 모델 순익·tail·노출·오차를 확인. settled cash net/인과적 개선은 별도 근거 없으면 null. partial/취소 race/carry CF unsupported를 natural maturity로 숨기지 않는다.
  - 금지: 새 서비스/collector/DB·전수 raw 재실행·bot restart/주문/조기 PREOPEN 확정·hard guard/quantity/budget/custody/override/holdout 완화. 자연 입력이 selected exit pin이라는 이유만으로 전수 unsupported이면 source/code defect로 재개.

## Limit-down 전용 축 폐기

- 사용자 지시로 전용 장후 보고/경제성/정책·관찰 슬롯·스캐너/PREOPEN 소비·verifier 요구를 작업본에서 제거하고 누적 전용 산출물을 삭제했다. 활성 OPEN 복구 owner를 만들지 않는다. 공유 원천과 과거 custody 안전은 보존한다.
- [폐기 리뷰](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md)에서 검증·삭제 증거와 선택 배포본 구분을 확인한다. 이 기록은 봇 재시작·주문·조기 PREOPEN 승인이 아니다.


## 공통 자연 수용 인계

- [ ] `[KiwoomCommonHealthOpportunityCostAcceptance0917] 공통 health·실행 모델·compact 정책 자연 소비 및 실제 성과 검증` (`Due: 2026-09-21`, `Slot: ALL`, `TimeWindow: 07:00~20:35`, `Track: RuntimeStability`)
  - Widget/episode WS 개선 계획: [공통 시세 수집 개선안](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md). 10:30의 공통 read budget 대기·유효 입력 결손을 P0 계약/구독 용량→P1 기존 WS 공유·3종목 비교→P2 관측 확대, 별도 후속 P3 분봉/episode로 해소한다. 각 운영 인계는 P4 검토/배포/PID gate를 먼저 거쳐 P5 자연 소비를 검증한다. 현재는 계획 수립이며 구현·구독·배포 완료가 아니다. 실제 실행은 각 단계 gate와 해당 작업 권한 충족 후 진행하며 기존 수량/정책/주문 guard·삼성25주 custody를 보존한다. 별도 OPEN을 복제하지 않는다.
  - Widget custody repair: 사용자 과거 사건 전부 종결·삼성 25주 보유 확인에 따른 [사건/정책/이월 보존 수리](../audit-reports/2026-09-21-widget-policy-custody-repair.md). commit51417126f 배포·10:05 위젯 PID75952 재기동, 13건 종결·삼성 동일 설정 인계·이월25 보존. 작업검사238/배포본219 PASS, 기존 wrapper fixture 실패1은 변경 전 재현. 실제 PID/config/policy hash 검증 통과·허용종목 삼성1·주문0; 두산·한화 연구 축적/다른 에피소드 제외·OFF는 유지하며 미래 자연 체결·경제성 완료와 분리한다.
  - 9/21 승인된 장중 결함 수리: [위젯 fleet 리뷰](../audit-reports/2026-09-21-widget-fleet-runtime-repair.md). symbol collector 조건검사 중복 해시·달력 계산과 health 감시 누락을 수리하고 immutable 배포/PID·자연 수집을 확인한다. 삭제 release 경로 및 변경 incumbent은 당일 consumer 재검증으로 해소하되 KRX safety veto와 CJ CGV preflight 격리는 유지한다. 사용자 명시 승인 범위의 배포·재기동이며 주문/guard 변경·경제성 완료 권한은 아니다.
  - Source/History: [9/18 기존 stable ID 원 기록](2026-09-18-stage2-todo-checklist.md), [통합 계획 CI5](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md). 기존 CW/ADQ/Samsung/AVG_DOWN·공통 health·PREOPEN 외부 blocker와 별도 custody·override acceptance를 승계하며 완료된 구현 재검토를 새 owner로 복제하지 않는다.
  - Acceptance: 기존 정상 producer→lossless census/원자 plan→운영 CF→선행 실제 모델 검증→scope/route별 prompt holdout→dated policy→정규 PREOPEN/실제 PID·issued prompt→joint applied-version COMPLETED valid cost/profit의 rolling/cumulative 성과. source/model/pending/unsupported/no-edge·actual/partial/CF를 분리한다. source gap0·배포·scoped PASS는 자연EV 또는 전체 native DONE이 아니다. 모델·표본·일별 순익·tail·비용·hard guards를 유지한다.
  - Next: 다음 자연 입력의 plan/stop/route/coverage 생성과 모델 proof부터 확인한다. irrecoverable9/17 입력은 제외 유지; 같은 자료의 반복 실행·추정 복원 금지. 계획된 장전 밖 수동 apply/기동/주문 권한을 만들지 않는다.
  - WS Acceptance: [구현 리뷰](../audit-reports/2026-09-19-ws-freshness-conditional-economics-implementation-review.md)의 새 integrated v2 source/policy hash, 정상 PREOPEN immutable receipt, 실제 PID의 same-tier bonus/order 변화, exact selection-version COMPLETED full-cost EV·일별 순익·tail·capital을 확인한다. source9/17 비교0/null은 구현 실패나 경제 개선으로 바꾸지 않는다.
  - WS Handoff: source section `02afcf30577e8fa290e00fe9d62e1e624adcb8ce2217dbfaec418a010ece49d2`, policy `5cb82631ef6674c80a5154737ccdca70b6d6ac75fad0194d2cc883e5ef45bf51`, effective `2026-09-21`. 현재 `source_contract_blocked`/bonus0이므로 정상 PREOPEN의 inactive 보존 receipt와 새 자연 source의 원 plan·quantity·guard·양측 terminal 보강 여부부터 확인한다.

- Limit-down 후속 리뷰·관련 커밋/푸시·immutable 배포: `fcfd7b8e5`. 검토 범위 결함0·통합1,531 passed(기존 wrapper 실패5/제외1은 baseline 재현)·물리 release6 passed·전용 산출물 잔여0. [최종 증거](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md). main 정기 cron target 부재는 기존 상태이며 선택/route 검증과 분리한다. 독립 unit pin·공유 원천/guard 보존; 기동/주문/조기 PREOPEN 미실행·PID 소비 미확인.

<!-- scanner_lookup_attention_handoff_sha256:c37a4406d71da14478ef113d145684caae7faa5437634763c816ea0cfcea3621 -->
- Scanner lookup source 2026-09-17; policy 2026-09-18; publication 2026-09-19; effective 2026-09-21: `hold_no_edge`. Opportunity EV `-2.38954987%`/3pair/3일, primary actual paired EV `None`; source gaps `['complete_partition_or_actual_selection_missing', 'original_unselected_entry_recipe_quantity_guard_missing']`. Baseline bonus0을 유지하며 자연 pair/PREOPEN/PID/full-cost outcomes는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`에서 계속 확인한다.



## 제출병목 지속 감시

- [ ] `[SubmissionBottleneckMonitorNatural0921] 기존 Sentinel의 제출병목 지속 감시·통보 자연 소비 확인` (`Due: 2026-09-21`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:55`, `Track: RuntimeStability`)
  - 추가 수리 승인: 현 PID104424의 신규11평가에서 자금 결손7 및 날짜형 운영계약 결손2를 확인했다. 기존 비동기 preparation worker의 bounded source-only 수집→최종 시세 갱신→동일 조건/2초 증거 재사용 경로와 date 원형 직렬화를 보완한다. 한도·주문 우선권·fresh 주문 조회·deadline은 유지하며 과거 결손은 보존한다. 검증/배포/PID/새 자연 증거는 [당일 수리 근거](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md)에 분리 기록한다.
  - active-path 재검토: 첫 후속 PID113775/2227e76b2는 bootstrap PASS이나 실제 스캐너가 legacy라 async 준비가 미소비였다(11:10 자연 평가7건 모두 자금 결손). legacy bridge→기존 detached worker의 비차단 준비 전달을 추가한다. 모드/한도/주문 경계는 그대로이며 새 PID의 자연 exact receipt 재사용을 확인하기 전 완료로 처리하지 않는다.
  - 지연 identity 경보 표시 수리 승인: 과거 미복구 사건을 `historical_unresolved`로 보존하고 최근10분 신규 결손/재발 없음/관측 불가를 분리한다. 해시 일치 시 발생시각·종목·누락 필드를 보충하고 실제 재발은 이전 history 보존 후 유예·지속 조건으로 재통보한다. 감시기의 매매 권한은 그대로 없으며 사용자 승인 배포·graceful 재기동과 다음 정기 소비만 확인한다. [리뷰](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md#authorized-delayed-identity-alert-separation), 관련 회귀233 PASS; 기존 자금/경제성 결손과 전체 submit drought는 별도다.
  - 지연 경보 수리 자연 소비 완료: `a58e65411`, PID `104424`,10:52:53 bootstrap·health7/7 PASS.10:55 cron이 새 release를 선택해10:56:01 완료하고 최근 식별139 event/결손0, 구형 사건=`historical_unresolved`, 상세 시각·003160·evaluation_attempt_id 및 기존39 proof/count 보존을 확인했다. 정기 통보=`sent`; 과거 복구 또는 경제성 완료로 승격하지 않는다. rollback·원본 상태는 위 리뷰의 별도 deployment receipt에 보존했다.
  - 9/21 승인 수리: [preflight·제출병목 보완 리뷰](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md). baseline 복귀 원본 날짜·해시 연결, 실제 source blocker 알림, 장전 세션 alias 동일 시도 집계를 수리한다. 사용자 명시 승인으로 해당 코드 배포·메인 graceful 재기동을 수행하며 감시기 자체의 자동 변경 권한은 추가하지 않는다. 신규 평가의 baseline ready·기계판정 도달을 확인하고 과거 실패/체결·경제성은 별도 보존한다.
  - 수리 완료 증거: `20432a6e2`, 관련 회귀297 PASS, PID `55596` release/cwd·bootstrap PASS. 09:37:29 신규 평가부터 `ready_baseline_v1 -> assessed/BLOCK` 자연 도달 확인. 오래된 가격/체결은 기존 RECHECK 유지. 과거 실패·통보 이력과 독립 자연 거래/비용 경제성은 이 OPEN에 보존한다.
  - 자연 소비 후속 보완: 09:40 Sentinel에서 드러난 정상 평가 ID 누락과 필수 특징 부족 RECHECK 오분류를 보완했다. producer→capture→경제성 관측의 동일 attempt/명시 route 연결 및 guard 제외 계약 회귀413 PASS. 같은 사용자 승인 범위로 후속 immutable 배포·graceful 재기동 후 신규 원천 ID 소비를 확인한다. 과거 원천은 재작성하지 않는다.
  - 최종 배포 증거: `9a638d68c`, PID `66129`(09:52:46 bootstrap PASS), 통합 회귀556 PASS. null alias의 실제 machine hash 가림까지 수리했다. 09:53:34 신규34 event/4 exact BLOCK에서 identity 결손0·충돌0, health7/7 PASS. `exact_broker_capacity_missing`(공유 요청 제한)·`frozen_operating_contract_missing`은 실제 경제성 source gap으로 남기며 제한/guard 완화 또는 수익 완료로 바꾸지 않는다. 상세·rollback은 위 리뷰의 최종 receipt에 보존했다.
  - 정기 소비: 09:55 cron이 최종 release를 선택해09:55:52 발행했다. 최종 PID 신규9 attempt의 충돌/경제성 이벤트 누락0. 최근 창 안의 수리 전 identity 결손143 event·기존 incident/자연 통보 이력은 보존하며 신규 재발 또는 임의 recovered로 바꾸지 않는다.
  - 경제성 원천 후속 승인: 기존 백그라운드 관측 worker의 실제 정책 캐시 공급을 연결하고 실패 원인을 보존했다. 동일 계좌·종목·가격·주문/잔고 세대·시각의 성공 kt00011 증거만 관측용으로 재사용하며 주문 직전 조회/공유 한도/우선권은 유지한다. 반복 초기화 안내도 제거했다. 통합 회귀1,279 및 추가 증거 검사4 PASS; 사용자 승인 배포·graceful 재기동 후 동일 신규 attempt의 자금·정책·운영계획 자연 연결을 별도 확인한다. 미연결 원천/비용 경제성은 기존 `DirectFamilySourceRepairMainMechanisticEntry` OPEN으로 보존한다.
  - 후속 배포·자연 확인: 실제 SCANNER 태그의 운영계약 연결 누락까지 보완한 `b6600b6a3`, PID `93897`, 10:34:28 bootstrap·health7/7 PASS, 추가 회귀169+316 PASS. 10:37:18 `067310/aims-41c7ef15145a0a871e84`의 실제 신규 조회→정책→운영계획→동일 기계 BLOCK 및 Sentinel projection/monitor join이 `recorded_source_only`로 검증됐다. 제한 내 나머지 조회 결손과 `000660`의 margin-capacity≠cash-flow 결손, 자연 cache-hit 효과 및 비용 EV는 미완료로 보존한다. 정기 monitor의 다음 자연 소비는 이 OPEN에서 이어가며 수동 발행/경보 삭제는 하지 않는다. 상세 해시/경계/rollback은 위 리뷰의 supplemental receipt 참조.
  - 10:40 정기 소비 확인: cron이 `b6600b6a3`를 선택해10:40:07 발행했고 같은 `067310` 시도/자금·seed·plan 해시를 `recorded_source_only`로 보존했다. identity 결손0, monitor=`observing/idle`; 상위 funnel=`SUBMIT_DROUGHT_CRITICAL` 및 나머지 원천/실제 거래·경제성 OPEN은 별도다.
  - Source: [제출병목 한정 감시 계획](../proposals/intraday-semantic-entry-monitoring-and-telegram-alert-feasibility-plan-2026-09-20.md), [배포·검증 리뷰](../audit-reports/2026-09-20-main-machine-operating-evidence-closure-review.md#11-제출병목-한정-감시와-후속-재리뷰-920).
  - Acceptance: 경제성 observation/gap stage가 cache에서 보존되고 signed plan/cost/capital source 결손 및 관측 부재가 economic_producer_gap으로 탐지됨. 정상 guard/unsupported/모델 검증 대기와 구분. 선택 release의 기존 Sentinel→작은 submission source→최근30분 exact 분모/지속 상태가 자연 갱신됨. 실제 지속 incident 발생 시 Telegram 발송 receipt, 미발생은 정상 관찰로 구분. mock 통과를 자연 통보/EV로 보고하지 않음.
  - Boundary: 메인 제출병목·원천/identity 결손만 알림. 위젯/에피소드·예외 에러 detector는 별도 owner. 자동 수정·주문·추가 AI/계좌 조회·재기동·조기 PREOPEN 금지. 정상 guard/분모0/창 이탈은 결함·복구로 단정하지 않음.

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:e04d550ada76bd04b67bf0b48d9853f9b816d38d29be8e234f7c35958947f3f5 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-17; 발행 2026-09-20; 적용 2026-09-21. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `f416784a75ce26cc6103516868b8f798fd823638c03cf2f1c5862bd5ff21d3d4`; 정책 bundle `15c063637359bd4cbd5a567760abecdf6229aee1f44d1e9d6a7cbc2dc7e97eb7`; consumer `1600fa6fc564fb0b2c923bb5ff28bea2c814280487189709ed12603b583051a9`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
