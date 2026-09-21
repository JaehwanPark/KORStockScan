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
  - 즉시 적용 구현: [전략 임계치/runtime 리뷰](../audit-reports/2026-09-21-main-entry-strategy-runtime-review.md). 사용자 승인으로 장후 적격 generation을 다음 장전 대기 없이 current CAS/reload로 적용한다. 코드·정책 생성·배포/PID·비용 경제성은 별도 판정하며 미지원 raw/auxiliary/owner replay는 이 OPEN owner에 보존한다.
  - 18:08 재평가/배포: runtime `77b6beb51`·PID `346701` 기동 검증. KRX 1,712건 중 raw 지원 1,708건/실행·비용 연결 0건으로 `incumbent_carry`; 새 임계치 미생성. candidate auxiliary+owner replay 연결 구현과 동일 기회 비용 검증이 남아 이 owner는 OPEN이며 경제성 완료가 아니다.
  - 최신 18:41 배포: `ea21e9dcc`·PID `367246` 실제 release cwd/PID 영수증 확인. 18:39 재생성은 연구 후보 판정 변화까지 확인했으며 비용·실행 연결 결손으로 새 정책 승격 없이 incumbent를 유지한다. 작업본/배포본 소스 통합과 미사용 중간 작업트리 정리는 [통합 정리 기록](../audit-reports/2026-09-21-main-entry-strategy-runtime-review.md#작업본배포본-통합-정리)에 남긴다. 아래 계획 단계 문구와 이전 PID는 당시 이력이며 이 OPEN의 경제성 완료를 뜻하지 않는다.
  - 9/21 신규 계획: [메인 BLOCK/RECHECK 전환 임계치 장후 학습·런타임 구현](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md). 기존 3축 제한과 별개로 전략적 과열·매도벽·분산·돌파·확인 조건을 raw 기반으로 재판정하는 후보→전체 기회비용→dated policy→실제 runtime 연결 P0–P6을 이 owner에 추가한다. 계획 수립만 완료하며 구현·정책 변경·배포·재기동은 미실행이다. 기존 source/경제성 acceptance와 아래 역사 증거를 보존한다.
  - 추가 구현 Acceptance: 동일 당시 입력의 전략 BLOCK→ENTER_NOW·RECHECK→ENTER_NOW 및 위험 진입 억제 fixture, source/주문 안전 불변, 후보별 실제 action 전환·paired 비용 후 EV/일별 순익·holdout, publisher/PREOPEN/runtime의 동일 정책 hash 소비. `no_action_change_in_search_space`와 `evaluated_no_edge`를 구분한다. 기존 루프 복구 완료 owner는 재개방하지 않는다. Due/TimeWindow는 기존 일정의 인계 창이며 신규 전체 구현의 당일 완료를 의미하지 않는다.
  - 후속 사용자 지시/계획 보완: 설정 가능한 모든 main 전략 임계치의 joint search와 3축 이상 동시변경 fixture를 포함한다. [§6.4 최소 갱신·§7 장중 승계 계약](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md#64-승격-및-종료-상태)에 따라 구현·검증 후 평가를 실행하고 적격 결과를 장중 새 기본 정책으로 적용, 다음 적격 정책 또는 명시적 safety rollback까지 승계한다. 이번 범위의 검증된 복수좌표 bundle 교체는 사용자 명시 지시이므로 일반 단일축 override/다음 PREOPEN 대기/후보별 재승인을 추가하지 않는다. source·broker·order·qty·provider·custody·hard safety 및 별도 operator lock은 유지한다.
  - 추가 검증: 전체 탐색의 완료와 적격 best-so-far를 분리하고 0.10%/5종목/5일/실체결 등의 옛 gate가 신규 계약을 다시 막지 않는지 모든 consumer에서 검사한다. 장중 atomic activation/current generation→actual PID→자정/PREOPEN/재시작 승계, 신규 후보 실패 시 incumbent 유지가 필수다. 이번 turn은 문서 점검·수정이며 실제 구현·평가 실행·정책 적용은 아직 미실행이다.
  - 유형·상태 계획 보완: 같은 계획 §4.1–§4.3/§6.5의 `분류 feature/경계+유형별 전체 전략 임계치+선택 순서+상위 기본값`을 단일 정책으로 장후 공동 학습·발행하고 runtime이 동일 selector로 소비한다. 가격/tick·유동성·변동성·시총/유통규모·세션/시간·현재 흐름을 검토하며 정상 metadata 결손은 검증된 parent를 사용한다. 시총 latest 소급·leaf별 과도한 표본 gate·분류/임계치 세대 혼합을 금지한다. shared selector/effective vector parity·분류+다축 조합 oracle·장중 전환/승계가 추가 Acceptance이며 코드/운영 변경은 미실행이다.
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
  - P3 follow-up review: background widget fact admission now follows the same priority scope while retaining episode evidence; forked checkpoint readers reset inherited cache locks. Deployment evidence is owned by the linked I/O review. Natural next-session acceptance stays with this existing OPEN item.
  - P3 I/O repair (415255eb0 deployed; 447 source + 447 release tests PASS; 55 paused/3 priority closed; next-session natural evidence remains OPEN): [policy-source cache and observation scope review](../audit-reports/2026-09-21-widget-io-policy-cache-and-observation-scope-review.md). Preserve original source hashes and current authority checks; prioritize 006800/010140/080220 research, keep execution and active episodes, defer wider WS registration. Code/release and natural next-session acceptance remain separate.
  - P3 전환 후 재리뷰: 제외 봉 metadata 재혼입·dead PID의 REST 대체 허용·원천 실패 사유 덮어쓰기 회귀를 재현·수리한다. 기존 observed_valid_rows 전환을 유지하며 원천 guard·주문 freshness는 그대로 둔다. [수리/배포 증거](../audit-reports/2026-09-21-widget-ws-completed-bars-implementation-review.md#observed-history-follow-up-review-and-repair).
  - P3 관측구간 전환 승인: 현재 수준의 결손은 행 제외로 허용한다. `observed_valid_rows`에서 검증된 이전 PID 완료봉을 유지하고 세션 prefix 강제·최대 lookback 과잉 최소값을 제거한다. 기존 P3 줄의 세션 전체/사전3창 조건은 이 승인으로 대체하며, 실제 consumer WS 분봉 선택·분봉 요청0·원천/주문 guard 보존이 이번 종료검사다. 자연3창/주문성과는 전환 후 관찰로 분리한다. [전환 기록](../audit-reports/2026-09-21-widget-ws-completed-bars-implementation-review.md#operator-approved-observed-history-cutover). 전환검증 PASS(19:02:59): f6e7bf2a5 푸시·630 PASS·수집기4 새 PID. 활성4종목 WS 완료봉 실제 선택/분봉 REST0/최종source-quality PASS, AL6 원천검사 PASS. main367246·auto33200 유지; 비운영시간 자연기동/3창/성과는 후속 관찰이며 이번 전환 blocker가 아니다.
  - P3 잔여 실행: native AL 세션 시작 coverage·이전 세션 원장 bounded tail·무거래 개장/경계 처리와 `ws_when_ready` 자동 선택을 연결한다. 기존 REST cadence·수량/guard를 유지하고 충분한 native history만 WS로 소비한다. 최신 main 전략 배포를 보존하며 main/collector4 실제 PID와 종료 episode/auto-expansion의 다음 정상 기동 정의를 구분한다. [상세 리뷰](../audit-reports/2026-09-21-widget-ws-completed-bars-implementation-review.md#native-session-history-and-readiness-driven-consumption-follow-up). 잔여 Acceptance는 실제 native 선택·동일 세대 자연3창·primary bar REST0이며 과거 결손을 임의 합성하지 않는다. 실행 receipt: fbe11c5f9 푸시·1,241 PASS·메인361275/collector4 배포, episode5 다음 기동 정의 반영.18:35 신규 AL6 원장/봉 일치; 실제 selector는 ws_when_ready이나 session/rolling 이력 부족으로 REST 유지, 자연 수용은 OPEN.
  - P3 재리뷰 보완: 결손구간 간 REST cooldown 우회·손상 seed 캐시 예외·최소 이력 우회를 수리했다. 승인된 커밋/푸시·배포 및 PID 확인은 기존 구현 리뷰의 후속 receipt가 소유하며, 세션 초기 이력/가격기준과 실제 WS bar 소비 acceptance는 OPEN 유지한다. 배포코드 `d6b26e455` 및 `codex/widget-p3-review-20260921` 푸시 완료, 1,138 PASS, 메인 PID343737·수집기4개 actual cwd/commit 일치.
  - P3 구현/반복 리뷰 후속: [완료 분봉 구현·검증·배포 receipt](../audit-reports/2026-09-21-widget-ws-completed-bars-implementation-review.md). durable AL writer→공통 reader→widget5/episode4 연결, quiet 복구 억제·종목별 손실격리·교차 process seed/gap lease·출처/세대/minimum-history 보존. 최신 메인 인계의 병행 수리를 보존하며 publisher와 consumer 선택을 분리한다. 다음 acceptance는 동일 producer/세션의 완전한3×15분과 consumer 원천/분봉 REST0·정당 차단 receipt다. ended episode 재생·연구 universe 확대·주문/threshold/quantity 변경 없이 기존 단일 owner를 유지한다. publisher49e4448ac/PID329859·reader c2ea0d267/4collector배포, 최종1,129 PASS;17:43 원장→완료봉6종목일치/손실0. 실제bar선택은REST유지: 세션시작VWAP/anchor를재기동시점으로바꾸는결함을차단했으며, 같은가격기준의초기세션seed 계약·정책별전체lookback→실제consumer전환→자연3창이잔여종료검사다. 시간경과만으로세션prefix가복구되었다고처리하지않는다.
  - P2 실제 입력·episode 시한 후속 실행: [수리/배포 기록](../audit-reports/2026-09-21-widget-p2-source-and-episode-deadline-review.md). 메인4914977fd/PID259944·consumer bd448943e. 기본3종목의 해당 현재가/호가 REST를 WS로 대체하고 삼성 최근체결 negative veto·당일 저가/등락률·원 시각/route를 보존한다. 시한 지난 마지막봉/PLANNED leg는 시장자료 조회·주문 예약 전에 차단하며 최종 사유는SKIP_OWNER_DEADLINE이다. 기존 P2E·정책/수량/주문/custody 보존. 최종 producer release849 PASS, consumer receipt 후속291 PASS(중복 포함). 분봉·보조지표 REST와58/198종목 확대·P3는 미완료. 15:16 producer/후속 consumer 세대 변경으로 아래15:00–15:45 연속3창 계획을 종결 증거로 재사용하지 않는다. 다음 acceptance는 새 cohort/세션 내 완전한 연속3×15분(당일 잔여 세션이 부족하면 다음 활성 세션), primary-symbol REST0·명시적 WS 소비·결손률, 이후 자연 제출/정당 차단 receipt다. 종료된 episode를 조기 기동/과거 신호 재생하지 않으며 기존 owner1개를 유지한다.
  - 원천차단/P3 확정 후속: [원인 분석](../audit-reports/2026-09-21-widget-source-block-and-p3-connection-review.md), [연결계획 §3.3.1](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md#331-p3-연결-확정-원천-상태분리와-단일-완료-분봉-발행). quiet-only 갱신/재연결 금지;16:36 명시적단절→epoch2 뒤 이전epoch receipt와복합오류·다른symbol REST귀속·반복demotion REG를먼저분리/수리한다. 기존canonical writer 분봉투영/공통reader/단일seed lease 후 현재AL cohort→widget/episode를연결하고 source/bar namespace·causal availability를검증한다. 현메인5e3f48bd9/PID297783; 아래4c5/PID285831은과거다. 이번은분석·문서확정이며구현·재기동은없다. 기존Acceptance와Due/Slot/TimeWindow/Track을유지하고새OPEN owner를추가하지않는다.
  - WS 후속 코드리뷰·수정·배포16:33: 기본3/확장 observer consumer `d8bb46367`, PID299807/299806/299798/299905. 기본 시각 오판·최종 세션 경계·필수0B/0D시각 누락·실패 census 창 귀속 수리, 배포본370 PASS. 삼성 장후AL 원천PASS; 두산·한화는 정규전용closed; 확장3종목은AL 선택 후 분봉 REST 예산대기. 메인4c5dc8a06/PID285831·정책·구독·수량 불변. [재리뷰/배포/rollback/자연 증거](../audit-reports/2026-09-21-widget-p2-source-and-episode-deadline-review.md#approved-second-review-and-collector-deployment). 아래2b1a76a48/기본bd448943e는 이전 인계다. P3·완전한3창·주문/비용 후 성과는 이 owner에 남는다.
  - AL 원천 기준 정정·후속 인계: 유효_AL를 신뢰하고 개별 REST 수치 차이를 gate로 사용하지 않는 사용자 지시를 반영했다. 이전 cross-scope 연구 차단 제거, quote/bar 개별 출처·원시각 검증 보존. P3 원장에 원본item/FID13·15 보존을 구현해 누적량/체결량·시각/세대의 자체 검증을 준비했다. 15,000콜백 p95≤0.026041ms/p99≤0.037895ms·유실0, 운영1ms/2ms guard 불변. [최종기록/rollback 경계](../audit-reports/2026-09-21-widget-p2-source-and-episode-deadline-review.md#operator-correction-integrated-al-ws-is-the-authoritative-source). 병행 메인 수리를 보존한4c5dc8a06(PID285831) 원천수집과2b1a76a48(PID291143) 기존58종목 observer 중006800/010140/080220 WS 선택을 배포했다. 오래된 cycle 시각이 새 snapshot을 미래로 오판하던 결함은 atomic read 시각으로 수정하고 원0B/0D 시각·20초 guard를 보존했다(158 PASS). 구독/정책/수량은 불변이다. 16:16:48 세 종목 모두AL WS 실제 선택 확인; 080220 분봉 REST 예산 대기는 남았다. 4건 KRX→KRX 거래량 진단은 AL 채택 blocker에서 제외하며 P3 완료 분봉 소비는AL 내부 연속성/원시각·원량 계약 증거 후 검증한다.
  - P2/P3 추가 실행: 확장 수집기2개 WS 입력·시각/출처·실패 분모 보존을 구현,425 회귀 PASS 후 `2bef246e1` immutable 후보를 준비했으며 운영에는 미선택이다. 현재 후보355/통합등록22, 전체 필요378 item>로컬 cap56이므로 기존 메인/보유 구독 보존하에 한정 cohort만 다음 대상으로 삼는다. `_AL` 수신 유효와 KRX 분봉 결합 연구 적합성은 별개다. 기존 canonical stream을 재사용해 공식 KRX27봉을 대조했으나 거래량4건 불일치(OHLCV23/27)로 P3는 미종결이다. [구현·용량·실제 분봉 증거/다음 closure](../audit-reports/2026-09-21-widget-p2-source-and-episode-deadline-review.md#continued-work-after-the-operators-1520-close-clarification). 사용자 정정대로15:20 이후는 정규 종료 경계로 해석하며15:40 기본3수집기는closed다. 연속3창은 다음 유효 정규 세션에서 확인한다. P3 누적거래량/ingress 유실 증거 연결·불일치 구간 격리·same-scope OHLCV/신호 검증이 다음 구현 선행조건이며 별도 collector/owner를 만들지 않는다.
  - P2 최신15:27 관측: 15:19에는3종목 필수 입력 PASS였으나15:20 이후0B 체결은 갱신되지 않고0D 호가만 계속 수신된다. 원20초 신선도 검사로 현재3종목 입력 unavailable이며 REST 예산 대기와 구분한다. [원 시각 증거](../../tmp/widget-p2-20260921/closing-auction-observation.json). 세션 경계와 일치하는 차단으로 기록하고 유효 세션의 자연 체결 재수신·연속 창·제출 검증은 OPEN으로 유지한다.
  - 이전 P2E 구현/배포 이력(현재 인계는 위 P2 항목): [리뷰·PID·rollback](../audit-reports/2026-09-21-widget-p2e-entry-ws-review.md). WS adapter5개 consumer·원 시각/route/누적 거래량·체결10개 계약·비종결 WAIT 보존 구현, final consumer release376 PASS. consumer0148cff58/위젯 PID247031, 메인은 병행 수리를 보존한12bb51c49/PID248631·exact-date bootstrap PASS. 삼성 이월0·수량/정책/주문 guard 보존. 종료된 episode는 재실행하지 않고 다음 자연 기동에 소비한다. 유효 WS 검사별 ka10004/ka10003 요청0; 전체 시간 예산을 보장하지 못하는 REST 복구는 시작하지 않는다. 14:00–14:45 P1은 raw/집계 분모 불일치로 미통과. 당시 다음 검증 계획은 **15:45 이후**15:00–15:15/15:15–15:30/15:30–15:45의 동일 producer/consumer 세대3창이며, 현재는 위 P2의 새 세대 일정으로 대체한다. 자연 검증은 해당 P2E cohort의 완전한 동일 세대 원천 창과 이후 자연 submit-path receipt이며, 세대 변경 시 다음 완전한 창으로 이동한다. 미시도는 pending, 종료 episode PID는 미소비로 남긴다. 현재 기본3종목 P2 입력 전환은 위 항목이 소유한다. 전종목 확대·P3 분봉·경제성은 OPEN이며 별도 owner를 만들지 않는다.
  - 삼성 custody 최신 증거: [25주 수동매도 원장 반영](../../data/runtime/manual_close_reconciliation/samsung_widget_sale_20260921_0027855/receipt.json). 주문0027855 수동매도25주, 원장/이월0주, 위젯 PID223297의14:14 자연 소비 확인. 아래10:05/13:51의25주·PID75952는 당시 이력이며 현재 보유/기동 증거로 재사용하지 않는다. P2E 수리는 이 원장이나 과거9건 신호를 초기화/재실행하지 않는다.
  - WS 후속 코드리뷰/보완: [집계·시각·등록/접미사 계약 수리](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md#integrated-source-follow-up-code-review-and-repairs).8개 실패 사례 재현 후 동일 회차 실패 재발행 중복집계·교차 scope 시각검사 누락·잘못된 등록 증거·item/suffix 충돌을 보완, 직접 영향346 PASS. `_AL` 유효 수신 인정·기존 거래 guard 유지. 작업본 미배포이며 현재 수집기를 재기동하지 않았다. 기존 v3 분모는 raw 성공/실패 재발행 중복을 대사한 뒤 평가하고, 새 count-basis 소비 여부를 다음 인계에서 확인한다. main compact 시각 fixture2건은 변경 전 배포본에서도 동일 실패로 별도 보존한다.
  - 이전 WS 배포 이력(현재 인계는 위 P2E 항목): `6c1bfa172` 기본3종목 collector13:51 재기동, PID209903/209901/209907의_AL 유효 수신·source_bound_v3 소비 확인, 배포본272 PASS. 메인174887·trader75952·삼성 이월25 보존. [실제 인계/롤백/P2 필드 의존성](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md#integrated-source-deployment-and-continuation). 다음 검증은 **14:45 이후**14:00–14:15/14:15–14:30/14:30–14:45의 완전한3창이며 아래13:45 기준은 이전 consumer 이력으로 대체한다. P2는 low_pric/삼성 flu_rt 보존 및 WS provenance 연결 후 입력 전환, P3는 연속 체결 원천 입증 후 완료 분봉 연결이 남는다. 현재 selected_input=existing_rest이며 확대/P3 완료로 처리하지 않는다.
  - WS 원천 인정 정정: 사용자 지시대로 모든 종목의 같은 종목 `_AL` 유효 수신을 전환 원천 검증에 인정한다. 원 요청 KRX/NXT 등록 부재·거래장소가 다른 REST 값 차이만으로 탈락시키지 않는다. [공통 reader 수리/공식 참조/검증](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md#integrated-symbol-source-acceptance-correction).13:45:42 작업본 reader로 삼성·두산·한화_AL 모두 유효 확인; source item별 분모·필드 시각·epoch/route/producer 검증 유지. 아직 배포/PID 소비·P2 실제 입력 전환 완료가 아니며 기존 구형 집계를 소급 PASS로 바꾸지 않는다. 다음 인계는 수정 reader의 consumer 소비와 원천별 자연 coverage 확인이며 기존 단일 owner가 소유한다.
  - 당일 개선 후속 코드리뷰: [배포 없는 재리뷰/보완](../audit-reports/2026-09-21-integrated-code-review.md#후속-전체-개선-재리뷰--배포-없는-작업본-보완). fork 후 부모 WS 비교 분모가 자식 PID로 표시되는 결함을 consumer PID key로 격리했다. 원천 결손/경제성·매매 guard는 그대로이며 이번 작업본 보완은 배포·재기동하지 않는다. 다음 승인 인계 때 실제 collector source/PID 소비를 확인해야 하고 기존 P2/P3 gate를 대체하지 않는다.
  - 후속 검증 완료:30파일 통합2,707 PASS, compile/Bash/diff/print-only parser PASS. 가격 guard fixture의 시계/선행 cooldown을 정합화했으며 주문 미제출·337bps/80bps 검증은 유지한다. 기존 정적 경고6건·pandas/fork 경고4건과 자금/AI timeout/종료 summary 운영 잔여를 보존한다. 운영4b3b4080c/PID174887은 변경하지 않았다.
  - P2/P3 진행 요청 반영: [선행 검증/세대 혼합 집계 수리](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md#p2p3-requested-prerequisite-review-and-bounded-census-repair). 12:44 현재 P1 비교 미완료·잔량/가격 차이 미해명으로 P2 실제 입력 전환/확대는 보류한다. 기존 census에 창별 producer 세대·혼합/결손 표시를 보완했으며 실패 분모를 지우지 않는다. 작업본 수리와 배포 소비는 별개이고 수집을 끊는 재기동은 하지 않는다.13:30 이후 기존 bound 원시 관측으로 producer/epoch를 대사하거나 새 census 배포 이후의 완전한 창으로 검증해야 하며, 구형 집계만으로 PASS 처리하지 않는다. P3는 coalesced tick/checkpoint를 연속 원장으로 사용할 수 없으므로 기존 REST 완료 분봉 유지; 연속성/동일 봉·신호 검증 후 연결하며 구현 완료로 처리하지 않는다.
  - 이전 WS 비교 창(위13:51 인계로 대체): 자금 관측/경보 분리 승인 배포의12:57:40 메인 재기동으로 WS producer가 PID174887로 바뀌었다. 기본 collector153602·153619·153620은 재기동하지 않았고 기존 process-local census를 유지한다. 혼합 producer 창12:45–13:00는 제외하고 **13:45 이후**에13:00–13:15/13:15–13:30/13:30–13:45 연속3×15분 창을 검증한다. 앞선13:30 점검시각은 대체하며 다른 producer/PID 분모를 합산하지 않는다. collector는 아직 구형 census pin이므로 exact 원시 관측의 세대 대사가 필요하고 새 main 배포만으로 v2 census 소비를 주장하지 않는다. [최신 배포/자연 소비 receipt](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md#authorized-non-entry-capital-coverage-and-execution-gap-separation), [통합 리뷰 이력](../audit-reports/2026-09-21-integrated-code-review.md). REST 중복조회 감축은 WS 전환/P2 승인이나 자동 gate 통과가 아니다.
  - WS 계획 첫 인계: 사용자 승인으로 P0/P1 코드87742bd0b 커밋·푸시·immutable 배포,11:43 메인PID131444 및 삼성/두산/한화 collector PID131725/131734/131735 재기동. 기존 writer와3종목 collector에 공통 exact-route/epoch/clock reader 및 비교 census를 연결했고 세 consumer의 자연 수신과 raw 기록을 확인했다. 실제 REST 입력·구독·주문·분봉은 유지한다. [코드/공식 근거/검증/운영 인계](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md). 다음 검증은12:30 이후11:45–12:30의 연속3×15분 창·잔량 차이·REST 실패 포함 분모이며, P2 전환/확대와 P3 episode 분봉은 기존 gate를 통과하기 전 완료로 처리하지 않는다.
  - Widget/episode WS 개선 계획: [공통 시세 수집 개선안](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md). 10:30의 공통 read budget 대기·유효 입력 결손을 P0 계약/구독 용량→P1 기존 WS 공유·3종목 비교→P2 관측 확대, 별도 후속 P3 분봉/episode로 해소한다. 각 운영 인계는 P4 검토/배포/PID gate를 먼저 거쳐 P5 자연 소비를 검증한다. 계획 작성 당시에는 구현·구독·배포 완료가 아니었으며 후속 승인 범위는 위 구현 항목이 소유한다. 실제 실행은 각 단계 gate와 해당 작업 권한 충족 후 진행하며 기존 수량/정책/주문 guard와 최신 exact custody receipt를 보존한다. 주문 직전 검사는 위 P2E 보완이 소유하며 별도 OPEN을 복제하지 않는다.
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
  - 9/21 후속 요청: [돌파 원천/고정 저항선·stale 계획 §4.5–§4.6 및 비진입5초 §6.1](../proposals/main-submit-bottleneck-causal-repair-plan-2026-09-21.md#45-921-후속--공식-원천과-국소-돌파-실패-보완계획). 공식0B 고가/고가시간은 있으나 국소 저항/돌파시각 직접 필드는 확인되지 않았다. 돌파/stale는 계획이며 비진입 cache-only만5초 작업본 변경; ENTER_NOW/사전준비2초·실제 sizing fresh조회 유지. 두 임계치의 기존 장후 자동 튜너 없음. 과거 임계치 불변 설명의 예외는 이 명시 승인 범위만이며 배포/재기동·자연 소비는 미실행, 기존 OPEN owner로 인계한다.
  - 후속 구현 정정: 사용자 계획 구현 승인으로 entry-only 고정 돌파선/RECHECK, 분석 내부 최종 WS 재검증·단일 as_of·동일 경제성 입력, 장후 구형/신형 의미 격리까지 작업본 구현·반복 리뷰했다. 위 “돌파/stale는 계획”은 이전 단계 기록이다. 비진입5초 유지, holding·주문 guard/ENTER_NOW2초 불변. 새 변경의 배포/PID 소비·자연 stale/결손 개선·비용/holdout은 아직 OPEN이며 기존 배포 receipt로 대신하지 않는다. [후속 구현 검증](../audit-reports/2026-09-21-main-submit-causal-repair-review.md#후속-작업본--국소-돌파stale-연결-및-장후-의미-분리).
  - 최신 후속 승인 배포: 손상 snapshot 안전 차단과 최종 입력 timing의 실제 payload 저장 누락을 추가 보완했다. 최신 WS/P2 기반 보존, 최종 배포 `9e998bddd`/메인 PID280948(15:55:30), 물리 release865 PASS·당일 정책 인계 PASS·15:55:38 health7/7 PASS. 위 미배포 문구는 구현 turn 이력이다. 독립 widget/episode unit·PID·정책은 변경하지 않았다. 이후 natural machine capture/재확인·실제 제출·비용 경제성은 기존 OPEN에 보존한다. [최종 receipt](../audit-reports/2026-09-21-main-submit-causal-repair-review.md#후속-승인--국소-돌파stale-최종-배포와-재기동).
  - 후속 승인 배포: [main 인과 수리·통합 배포](../audit-reports/2026-09-21-main-submit-causal-repair-review.md#후속-승인--반복-리뷰통합-배포메인-재기동). 분리 release727/통합493 PASS 후 동시 배포된 WS81eb16c09를 보존한9e828ab85로 main PID242503→244168 graceful 전환,14:48:38 정책 인계 PASS.14:50 기준 main/수집기 liveness와 별개로 구형 widget startup receipt 및 I/O wait42.13% health fail을 보존한다. 신규 revision/정기 report 소비·정상 제출/경제성은 이 OPEN, 별도 widget unit 인계는 WS owner가 담당한다. 최초 미배포 설명은 이전 구현 turn 이력이며 후속 배포 승인/실행은 이 receipt가 우선한다.
  - 후속 소비:14:50 정기 Sentinel 새 이력 필드112row 생성/14:51:32 정상 종료.14:52:57–14:53:00 bounded 신규 표본2attempt에서 동일 snapshot hash 관측→terminal 전달·single_revision/충돌0 확인(BLOCK2, 관측 자금 결손1·DANGER guard 제외1). 전체 신규 분모/재평가 chain/실제 제출 검증과 혼용하지 않는다.14:53:08 I/O 경보 해제, health6 PASS/widget receipt1 FAIL로 별도 인계 결손은 남긴다.
  - 후속 구현 승인/작업본 수리: [인과 복원 리뷰](../audit-reports/2026-09-21-main-submit-causal-repair-review.md). 명시적 same-attempt revision·경제성 이력, large-sell 단독 조건의 main RECHECK, 최종 입력 로그 및 동일 scanner 세대의 admission 사유 연결을 구현·검증한다. 과거 085910의 최초 결손은 DANGER가 아니라 kt00011_empty로 정정한다. 구형 충돌과 자금 결손·경제성 null은 보존하고, 임계치/추가 계좌조회·배포/재기동은 실행하지 않는다. 아래 “계획 수립만/문서 반영만”은 이전 요청의 이력이며 이번 구현 승인은 배포 승인으로 확대하지 않는다. 새 OPEN 없이 기존 자연 수용 owner를 유지한다.
  - 위험 차단/상승 미진입 경로검증 계획 보완: [상세계획 §4.1–§4.4](../proposals/main-submit-bottleneck-causal-repair-plan-2026-09-21.md). 오후4건의 large-sell WAIT_CONFIRMATION→main BLOCK을 actual core/policy→재확인 소비→terminal까지 검증하며 legacy compose WAIT 테스트로 대체하지 않는다. 오전 census의 상승 모형35구간 중 미승격20·늦은발견9는 반환 성공과 실제 admission disposition을 구분한다(미승격20의 candidate_evaluated 첫 사유는 모두 returned). exact payload/로그 불일치와 failed_breakout의 단일 원인·비용/역행·차단 이후 경로를 대조하며 하락/비상승 대조군을 포함한다. 과거 완료봉 결손 수리와 조건부 자금 검증을 재개방하지 않고, 이번은 문서 반영만이며 threshold/안전장치·runtime 변경 권한은 추가하지 않는다.
  - 신규 상세계획(계획 수립만): [메인 제출병목 인과 복원·정상 제출 경로 검증](../proposals/main-submit-bottleneck-causal-repair-plan-2026-09-21.md).13:50 기준95평가의 BLOCK37/RECHECK42/source-invalid14/충돌2를 보존한다. 원천 ENTER_NOW2가 동일 ID 후속 BLOCK으로 UNKNOWN이 된 전이를 먼저 복원하고, 관측 DANGER·AI caution/invalid·실제 terminal을 분리한 뒤 확인된 지연/WS I/O 원인만 최소 보완한다. 기존 자금 연결 재구현은 기본 수리 범위에서 제외한다. S4는 자연 진입이 제출 직전 경로에 도달했을 때의 조건부 검증이며 새 결함 재현 때만 해당 부분을 추가 수리한다. 자금 표본 부재는 S1–S3 수리 완료·승인된 배포를 막지 않는다. nonentry 자금 관측62건의100% 수집은 목표가 아니며 주문 허용에 필요한 증거 결손은 허용하지 않는다. 이 요청은 신규 구현·커밋푸시·배포·재기동·주문을 실행하지 않으며 기존 개별 승인 범위를 확대하지 않는다. 수정 후 자연 정상 제출/정당한 안전 차단의 동일 시도 end-to-end 증거는 이 owner, WS 성능/P2/P3는 기존 공통 자연 수용 owner, 비용 경제성은 기존 direct-family owner가 소유한다.
  - 비진입 자금 관측/실행 결손 분리 승인: [원천 보존·경보 분리 보완](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md#authorized-non-entry-capital-coverage-and-execution-gap-separation). 명시적인 BLOCK/RECHECK cache-only miss만 관측 coverage로 분리하며 source_gap/경제성 미검증·분모는 보존한다. ENTER_NOW/실제 제출·충돌·원인 불명·운영/증거금 계약 결손은 기존 경보 유지. 과거 사건은 exact ID 전수 일치 때만 observation_only_unresolved로 재분류하고 복구로 표시하지 않는다. 배포 후 정기 Sentinel의 상세 원인·행동별 분모·경보 소비를 확인한다. 계좌 조회 한도/만료·주문 guard/P2/P3 전환은 변경하지 않는다.
  - 분리 보완 소비 확인:4b3b4080c 배포·PID17488712:57:40, 정책 PASS·초기 health7/7 PASS.13:00 정기 Sentinel/monitor에서 명시적 비진입 관측 결손36(최근30분)과 구조적 결손31(기존45분 보존/유예)을 분리하고 원본 결손·기존 active 경보를 보존했다. 새 PID5건: RECHECK3/BLOCK2/ENTER_NOW0, 자금·계획 연결1/관측 결손3/unsupported1. 자금 결손 전체 해소가 아니며12:59:34 AI timeout1도 별도 보존한다. 다음 정상 ENTER_NOW 집단의 실제 자금 검증/제출 영향과 장후 비교 표본 coverage가 잔여 acceptance다.
  - 완료봉 연결 수리 승인: [원천·기계판정·관측 조회 보완](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md#authorized-machine-completed-bar-handoff-and-observation-read-reduction). optional AI context OFF가 메인 필수 완료봉까지 숨긴 결함을 base candle 전용 전달로 수리하고 MTF OFF/원 시각·route·preflight를 보존한다. BLOCK/RECHECK 관측은 기존 exact 자금 증거만 재사용하고 추가 동기 계좌조회는 생략하며 미수집/경제성 null을 그대로 기록한다. 실제 주문 조회·한도·수량·임계치는 유지한다. 신규 자연 평가의 완료봉/판정과 자금 증거를 분리 검증하며 과거74건 scarcity 경보를 임의 복구하지 않는다.
  - 최신 소비 receipt: fee046b21 배포·메인 PID164792 재기동12:39:38, 정책 인계 PASS. 첫 자연7건12:40:30–12:41:20 완료봉130–220/결손0, BLOCK4·RECHECK3·ENTER_NOW0. 추가 동기 계좌조회 없는 nonentry cache miss가12:42:41 자연 기록됐지만 자금 결손은 미해소다. 초기 health7/7 PASS 뒤12:41:55는6 PASS/AI timeout log warning1(12:40:53 네패스, 기존5초 제한)로 보존한다. 완료봉 연결만 소비 확인이며 scarcity·자금·실주문·경제성 전체 완료가 아니다. 다음 정기 Sentinel의 신규 PID 집단과 별도 provider timeout 재발 여부를 기존 owner에서 구분 확인한다.
  - 당일 통합 리뷰 승인: [60파일 영향 경로 리뷰·추가 보완·운영 절차](../audit-reports/2026-09-21-integrated-code-review.md). 감독 세션 종료 경합은 child/session 부재 확인 후 최대3회만 재시도하고, 손상 선택 캐시 예외 및 WS 종목 epoch 타입을 보완한다. 기존 테스트 계약2건을 현행 retired/handoff 계약에 맞춘다. 검증 후 immutable 배포·메인 및 read-only 수집기5개 재기동 범위이며 한도·수량·주문/custody 불변, 자연 자금 증거와 경제성 OPEN은 유지한다.
  - 통합 배포 receipt: d06b39ca2/PID153806,12:20:38 bootstrap PASS, 통합2,622/추가122/배포본122 PASS(중복 포함, 합산 금지). 수집기5개 동일 release active,3종목 새 WS 비교 원천 정상 소비, symbol-runtime 자연 재사용11건에도 data_wait 보존.12:20:33 이전 PID 종료의 기존 summary-close 경합6건은 raw 보존 후 경고했고12:22:01 health7/7 PASS; 종료 경합 자체는 미수리이며 로그 억제 없이 producer 종료→admitted drain·후행 raw 보존을 확인할 잔여로 남긴다. 새 메인 자금 결손은 다음 정상 Sentinel cohort로 별도 확인한다.
  - 추가 수리 승인: 현 PID104424의 신규11평가에서 자금 결손7 및 날짜형 운영계약 결손2를 확인했다. 기존 비동기 preparation worker의 bounded source-only 수집→최종 시세 갱신→동일 조건/2초 증거 재사용 경로와 date 원형 직렬화를 보완한다. 한도·주문 우선권·fresh 주문 조회·deadline은 유지하며 과거 결손은 보존한다. 검증/배포/PID/새 자연 증거는 [당일 수리 근거](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md)에 분리 기록한다.
  - active-path 재검토: 첫 후속 PID113775/2227e76b2는 bootstrap PASS이나 실제 스캐너가 legacy라 async 준비가 미소비였다(11:10 자연 평가7건 모두 자금 결손). legacy bridge→기존 detached worker의 비차단 준비 전달을 추가한다. 모드/한도/주문 경계는 그대로이며 새 PID의 자연 exact receipt 재사용을 확인하기 전 완료로 처리하지 않는다.
  - 보완 배포: 0d7fed630/PID117559, 11:15:32 bootstrap 및 11:15:41 health7/7 PASS. 보완 회귀360·worker 추가6 PASS. 초기 자연9평가에는 자금 결손8·자금 이후 슬리피지 안전 차단1이 남아 있어 원천 해소를 닫지 않는다. 백그라운드 준비의 실제 실행은 확인했으나 공유 시장자료 조회 포화로 bounded 요청도 실패한다. 기존 main source owner가 시장조회 중복 감축 및 동일 attempt 자금/정책/운영계획 자연 연결을 소유하며 과거 결손·별도 widget 작업은 보존한다.
  - 11:20 정기 소비 확인: cron이0d7fed630을 소비했고11:20:08 종료했다. 새 PID17평가 중 자금 결손11, required-feature guard3, source-invalid1, probe unsupported1, slippage guard1. 전체 자금/정책/계획 자연 연결0·증명된 cache hit0이므로 배포/PID/정기 소비만 완료이며 실제 병목 해소와 날짜형 자연 acceptance는 OPEN이다.
  - 중복조회 감축 확대 승인: 메인 ka10080 원응답의 서로 다른 출력 봉 수 간 재사용과 위젯 exact REST 성공 응답 공유를 기존 모듈에 보완,34e77146c 배포·PID141501 인계·기본3수집기 및 기존 symbol-runtime/research-watch 수집기 기동 확인.385회귀 PASS. 최대3초·원 수신시각/만료·token/route/body/분 경계를 보존하고 계좌·주문·execution-critical 경로는 제외한다. [리뷰·공식 근거·배포/감독세션 복구](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md#authorized-duplicate-market-read-reduction).12:05 자연 수집기 재사용2건 확인; 새 메인8평가 중 자금 결손4·source-only 자금/계획 연결1·나머지 guard/unsupported3이다. WS 입력 전환/P2·P3와 별개이며 기존 한도·우선권·custody 불변, 전체 자연 조회 절감과 자금 증거 해소는 미완료로 유지한다.
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
