# 2026-10-08 Stage2 To-Do Checklist

## 오늘 목적

- 승인된 10/7 원천의 EOD 제외 장후 재개를 완료하고, 10/8 exact-date 정책·최종화·PREOPEN 준비와 정상 예약기동을 확인한다.
- 독립 운용 정책 구현/배포, 실제 AI 비교 완료, 신규/기존 정책 승계, 실제 PID 소비를 각각 확인한다.

## 오늘 강제 규칙

- 사용자 승인 Main 판정 계약은 실제 ask, 30분, 비용률 .0023, 비용 후 +.4% 목표와 soft -3% 선도달의 누적 raw 승률이다. EV·손익비·최소 표본/일수·holdout·기존 제출 보존 gate를 추가하지 않는다.
- 운영/오프라인 AI 횟수 quota=None을 유지한다. provider 간격·외부 rate limit·중복/불확실 예약·timeout과 broker/account/order/수량/자본/custody/manual veto/hard safety는 보존한다.
- clean tuning baseline은 `2026-06-05T00:00:00+09:00`이다. 식별 가능한 결손 row/window를 제외하고 UNKNOWN·U·valid-empty·미완료 실제 비교를 구분한다. 과거 archive를 현행 원천으로 복원하지 않는다.
- EOD와 독립 owner를 중복 재실행하지 않는다. Main-only/OFF·퇴역 정책과 기존 보유 청산 소유권을 보존한다. 코드 검증/선택 release/준비 정책/PID/자연 주문·실현 손익을 같은 완료로 표시하지 않는다.
- Project/Calendar 동기화는 사용자 표준 명령으로 수행한다. 현재 summary 미생성으로 자동 checklist builder는 아직 실패 상태이며, 생성 후 동일 stable ID에 인계하고 중복 OPEN을 만들지 않는다.

## 전일 OPEN 인계

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] 독립 운용 정책 통합 배포·10/7 장후 재개·10/8 정상 기동 준비` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 승인 코드 배포 후 장후 최종화 및 07:55 예약기동 준비`, `Track: RuntimeStability`)
  - Source: [독립 탐지·기여도 계획](../proposals/main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md), [구현·운영 인계](../audits/main-operating-policy-implementation-and-postclose-review-2026-10-07.md), [10/7 원 Acceptance·검증 이력](2026-10-07-stage2-todo-checklist.md).
  - 승인: 사용자가 구현→반복 리뷰/보완→배포 후 중단한 EOD 제외 장후를 재개·모니터링하고 다음 기동을 준비하도록 명시했다. 20:41 보류를 새 코드 gate/배포 후 해제한다. 원천일 10/7, 정책/기동 대상 10/8을 보존한다.
  - Acceptance: 기존 실제 목록+8개 정확 정의/적용 범위, 독립 탐지/typed union, scope 실행 hash, live outbox와 offline 공유 원장 분리, full expected membership, 실제 AI 증분 호출·원 응답 보존, incomplete scope의 native pair carry, 48셀/128route loader와 report/감시 소비를 검증한다.
  - 운영 종료 조건: 원래 cron 5개와 final-refresh timer만 복원하고 장후 체인을 한 번 재개한다. 실제 최신 terminal→summary/tower→오늘 checklist→strict `--require-summary-handoff`→controller DONE→finalization→exact-date PREOPEN prepared를 재봉인한다. EOD를 재실행하지 않는다.
  - 상태: 최초 확장 회귀 699 PASS 이후 indirect consumer/보유 재현/호출 서명 결함을 보완했다(통합 395·장중 62·immutable 188 PASS). 정확 입력 투영은 실제 120개 확인점 bytes 일치(확장 135·immutable 53 PASS), 대형 native 보고서 reader는 244 PASS, final audit 순서 barrier는 작업본/immutable 각각 149 PASS다. `66fce0a9` / `operating-union-20261008-v7` 배포 및 63 owner 검증 완료. 01:46 기계 누적 확인점 117,763건(확정 77,903/U 39,860)의 native 검증 succeeded, 01:47 전체 wrapper 재개. 실제 AI 비교·최종화/PREOPEN은 진행 중이며 아직 완료 아님. 자연 주문/실현 성과는 기동 준비의 코드 종료 조건으로 요구하지 않는다.

  - 재개 보완: 분할수량 553 MiB 원천의 bounded streaming·exact census, archive 원천일 전달, episode OFF 시 미사용 capacity 승계, 실행 중 machine preflight 보존을 검증하고 보완 릴리스로 인계한다.
  - 실제 AI 후속 보완: v7 입력 전수 234,389건 결손 0을 확인했으나 실호출에서 CAUTION 위험 인용 필드 혼동을 발견했다. union v2 전송 문구/schema 설명을 명확히 하고 validator는 유지했다. 같은 실패 입력 12건 실호출 12/12 유효(PASS 3·CAUTION 8·VETO 1), 확장 98 PASS. 원 응답/불확실 예약을 보존한 새 세대 배포·장후 재개 및 최종 준비는 계속 진행 중이다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-07", "sources": {"entry_cancel_wait_policy": {"sha256": "b9562c7326a79d6c0b318c1c00077d8fc5a149debdf4a251028fd1577becab59"}, "entry_cancel_wait_tuning": {"sha256": "aa06f039aedc160202a74d528569dd509599a99474ac8f55a9cdbafdb645c173"}, "holding_path_vote_policy": {"sha256": "71221a9f65775d0fceee43ce47ff08acf5d830b136e1b9774a90739fcb8b07bc"}, "initial_quantity_refresh_stage": {"sha256": "35e190825f27181f5c25dda5102ef1d85c966e4e1709a21d2ae12897a1ce6f9d"}, "runtime_approval_summary": {"sha256": "9b875822310d460c031a892eab37ca5a47061415b6bd57d6bf69cf184c7e7340"}, "stage_episode_policy": {"sha256": "a402715ecdda8b9f9f59e50e6754b5155831715456d554470a2a89fafff199de"}, "stage_legacy_machine_report": {"sha256": "baaff72692a85ec56dbc8bd56a3b3d5ecef8908b9b8c61baccb2314ac1b8391b"}, "stage_legacy_policy_approval": {"sha256": "7de0c478a4d1edc867ba2b1b1a24e5fb165a28a15856e3f63716259789072683"}, "stage_machine_attribution": {"sha256": "7a11c1d3eb60a601da58027cfc135973eed990328bdf9e727b2da3f03e523710"}, "stage_machine_timing": {"sha256": "fba312455d70f351d8670a3a1a341201841123010ac7cba4a9fbce085d2b496d"}, "stage_main_auxiliary_policy": {"sha256": "cac63befc78b6f701c732f75f559ddfd90b453ad1b9b8088a100f0326c6e28c6"}, "stage_main_machine_policy": {"sha256": "d8bebe6ac68dc13a42084164c03c521ed3c9e19a4da4a999436220385dc81811"}, "stage_market_weakness": {"sha256": "4233aad6e69a090fc024c3d08f2f2049087f69f222c85c4526c8933c42f0896e"}, "stage_outcome_labels": {"sha256": "2afda6ba249a88fd3def05efc409389781e10fccb50a847d5c23e6f0c43a0a8a"}, "stage_pre_submit_delay": {"sha256": "80be5f0af1c6179d35ea46886bda1cc17a3bb54272332e4cd708f9d46472e51b"}, "stage_research_allocation": {"sha256": "1d3315612ff2a04a8e46502ba2ef617a68abbf85899066734ca663264a23da8c"}, "stage_research_capacity": {"sha256": "3871739e4ad5f075e60064808744776a33792e001a60aed439c1ebede5595b94"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-08", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "528556fca5e67676b6e1125e560e76051574bfaf167c54225b422dfa45bab442", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-08.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-10-07", "source_report_sha256": "4ca812fae292e94bc8b9caa4baabfb11454fe8ab6b7d3846faff5efe04da007c", "status": "estimated_provisional_published", "target_date": "2026-10-08"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-08.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": null, "valid": false}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "b9562c7326a79d6c0b318c1c00077d8fc5a149debdf4a251028fd1577becab59", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "c57b7a427994e875ffabd3c95bf1020b9a66aeace17bd11cd284713716c0b342", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "006804460a5478dc1ee19b9516f33295e3506c94c89e4c917326c859994355bd", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": null, "valid": false}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "c4c6588beea04a339254db95f79f292c95e0d3f478d49aeb07479101bb7c6bcc", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "b069eccaf4523f443346731f841bbe38d678e0586b907c7a177fbbff00ee58f4", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "f4372933b291ed965b24aaf50ee94966115004e300ee385069dded34876c5669", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-07", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-08.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-07`; next apply date: `2026-10-08`.
- direct source: `8/10`; direct state: `incomplete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `not_applicable` | `not_applicable` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `source_gap` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `unsupported_scope` | `blocked` | `scope_contract_decision` |
| `compact_auxiliary` | `not_applicable` | `not_applicable` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-08`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 판정 기준: source_date=`2026-10-07`, apply_date=`2026-10-08`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=False, handoff=not_applicable); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=not_applicable); low_price_two_leg(valid=True, handoff=blocked); main_mechanistic_entry(valid=False, handoff=blocked); pre_submit_delay(valid=True, handoff=not_applicable); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilyScopeDecisionMainMechanisticEntry] main_mechanistic_entry 직접 family 지원 범위 계약 확정` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`9b875822310d460c031a892eab37ca5a47061415b6bd57d6bf69cf184c7e7340`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-10-07.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`scope_contract_decision`, comparison_status=`unsupported_scope`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_policy_selected_portfolio_economics_separate`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`natural_machine_policy_outcomes`. policy_receipt_valid=`False`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`9b875822310d460c031a892eab37ca5a47061415b6bd57d6bf69cf184c7e7340`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-10-07.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`not_applicable`, resolution_mode=`retired_or_not_applicable`, prospective_resolution_mode=`-`, first_blocker=`missing`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`missing`. policy_receipt_valid=`False`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`9b875822310d460c031a892eab37ca5a47061415b6bd57d6bf69cf184c7e7340`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-07.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`9b875822310d460c031a892eab37ca5a47061415b6bd57d6bf69cf184c7e7340`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-07.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`not_applicable`, resolution_mode=`retired_or_not_applicable`, prospective_resolution_mode=`-`, first_blocker=`semantic_unverified_large_source`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`submitted_order_frozen_plan_model_holdout_paired_candidate_and_loader`. policy_receipt_valid=`True`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`9b875822310d460c031a892eab37ca5a47061415b6bd57d6bf69cf184c7e7340`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-10-07.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:12be24a4a75391740ab53c40568fd040cfcce61ebcc99462325cd093340ffaf4 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-07; 발행 2026-10-07; 적용 2026-10-08. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "ecfb49ce9e1a4a18b72971f1ad069e70b04c6909f722a61442365c4b3e53db5f", "runtime_effect": false, "source_date": "2026-10-07", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->
