# 2026-10-08 Stage2 To-Do Checklist

## 오늘 목적

- 승인된 10/7 원천의 EOD 제외 장후 재개를 완료하고, 10/8 exact-date 정책·최종화·PREOPEN 준비와 정상 예약기동을 확인한다.
- 독립 운용 정책 구현/배포, 실제 AI 비교 완료, 신규/기존 정책 승계, 실제 PID 소비를 각각 확인한다.

## 오늘 강제 규칙

- 사용자 승인 Main 판정 계약은 실제 ask, 30분, 비용률 .0023, 비용 후 +.4% 목표와 soft -3% 선도달의 누적 raw 승률이다. EV·손익비·최소 표본/일수·holdout·기존 제출 보존 gate를 추가하지 않는다.
- 운영 AI 횟수 계약은 유지하되, 후속 사용자 지시에 따라 장후 보조비교 신규 호출은 원천일당 누적 100회로 제한한다. 이미 초과한 10/7 재개는 추가 호출 0회이며 저장 응답을 재집계한다. provider 간격·외부 rate limit·중복/불확실 예약·timeout과 broker/account/order/수량/자본/custody/manual veto/hard safety는 보존한다.
- clean tuning baseline은 `2026-06-05T00:00:00+09:00`이다. 식별 가능한 결손 row/window를 제외하고 UNKNOWN·U·valid-empty·미완료 실제 비교를 구분한다. 과거 archive를 현행 원천으로 복원하지 않는다.
- EOD와 독립 owner를 중복 재실행하지 않는다. Main-only/OFF·퇴역 정책과 기존 보유 청산 소유권을 보존한다. 코드 검증/선택 release/준비 정책/PID/자연 주문·실현 손익을 같은 완료로 표시하지 않는다.
- Project/Calendar 동기화는 사용자 표준 명령으로 수행한다. 자동 생성된 원 strict의 checklist 바이트를 보존하고, 후속 구현은 동일 stable ID에 인계한다. 중복 OPEN이나 이전 준비를 대체하는 허위 PASS를 만들지 않는다.

## 전일 OPEN 인계

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] 독립 정책 후속 보조 튜닝·장중 적용 인계` (`Due: 2026-10-08`, `Slot: INTRADAY`, `TimeWindow: 검증 완료 후 승인된 배포·재기동 및 보조 교체`, `Track: RuntimeStability`)
  - Source: [독립 탐지·기여도 계획](../proposals/main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md), [구현·운영 인계](../audits/main-operating-policy-implementation-and-postclose-review-2026-10-07.md), [10/7 원 Acceptance·검증 이력](2026-10-07-stage2-todo-checklist.md).
  - 승인: 사용자가 구현→반복 리뷰/보완→배포 후 중단한 EOD 제외 장후를 재개·모니터링하고 다음 기동을 준비하도록 명시했다. 20:41 보류를 새 코드 gate/배포 후 해제한다. 원천일 10/7, 정책/기동 대상 10/8을 보존한다.
  - Acceptance: 기존 실제 목록+8개 정확 정의/적용 범위, 독립 탐지/typed union, scope 실행 hash, live outbox와 offline 공유 원장 분리, full expected membership, 실제 AI 증분 호출·원 응답 보존, 후속 개선 incomplete scope의 native pair carry(사용자 지정 초기 목록은 비교와 독립), 48셀/128route loader와 report/감시 소비를 검증한다.
  - 10/8 장중 후속 실행 승인: 사용자 승인에 따라 보조 튜닝 registry·사전 쌍 비교·장중 보조 binding reader를 구현하고 반복 검증 후 배포·재기동한다. 기존 기계 목록과 code pin은 유지한다. 미완료 AI 비교는 초기 등록/현재 기동을 막지 않으며, 후속 보조 변경은 유효 공통 쌍의 누적 PASS 승률로 별도 결정한다. [후속 구현 기록](../audits/main-auxiliary-paired-tuning-intraday-implementation-review-2026-10-08.md).
  - 현 상태 정정: 10/7 장후 finalization은 10/8 07:26 완료, 07:35 PREOPEN 및 07:55 Main PID 기동을 확인했다. 아래의 장후 진행/기동 hold 문구는 과거 이력이다. 후속 작업은 기존 bootstrap을 보존하는 장중 인계이며 10/7 EOD/장후를 중복 재생성하지 않는다.
  - 초기 등록 정정: 지정된 기존+8개 목록은 비교 완료·PASS/승리 수와 독립하여 적용한다. 정확 승인/부모/정의와 복합 입출력 형식은 검증하고 기존 REGULAR 보조 arm을 이관한다. PRE/AFTER는 같은 유형 REGULAR arm을 승계한다. 미완료 비교는 사후 개선 자료로 유지하며 초기 운용을 native carry로 되돌리지 않는다. 최종 준비는 이 보완 뒤 재봉인한다.
  - 10/8 후속 승인: 과도한 보조비교를 중단하고 신규 호출 원천일당 100회로 축소한다. 재실행/세대 변경으로 reset하지 않고 failed/uncertain도 차감한다. 장후 완료 및 exact-date 준비 검증 전까지 07:35/07:55 예약과 start/restart/preopen·직접 봇 시작을 hold한다. 원천/기존 응답/EOD는 보존한다.
  - 운영 종료 조건: 원래 cron 5개와 final-refresh timer만 복원하고 장후 체인을 한 번 재개한다. 실제 최신 terminal→summary/tower→오늘 checklist→strict `--require-summary-handoff`→controller DONE→finalization→exact-date PREOPEN prepared를 재봉인한다. EOD를 재실행하지 않는다.
  - 상태: 최초 확장 회귀 699 PASS 이후 indirect consumer/보유 재현/호출 서명 결함을 보완했다(통합 395·장중 62·immutable 188 PASS). 정확 입력 투영은 실제 120개 확인점 bytes 일치(확장 135·immutable 53 PASS), 대형 native 보고서 reader는 244 PASS, final audit 순서 barrier는 작업본/immutable 각각 149 PASS다. `66fce0a9` / `operating-union-20261008-v7` 배포 및 63 owner 검증 완료. 01:46 기계 누적 확인점 117,763건(확정 77,903/U 39,860)의 native 검증 succeeded, 01:47 전체 wrapper 재개. 실제 AI 비교·최종화/PREOPEN은 진행 중이며 아직 완료 아님. 자연 주문/실현 성과는 기동 준비의 코드 종료 조건으로 요구하지 않는다.

  - 재개 보완: 분할수량 553 MiB 원천의 bounded streaming·exact census, archive 원천일 전달, episode OFF 시 미사용 capacity 승계, 실행 중 machine preflight 보존을 검증하고 보완 릴리스로 인계한다.
  - 실제 AI 후속 보완: v7 입력 전수 234,389건 결손 0을 확인했으나 실호출에서 CAUTION 위험 인용 필드 혼동을 발견했다. union v2 전송 문구/schema 설명을 명확히 하고 validator는 유지했다. 같은 실패 입력 12건 실호출 12/12 유효(PASS 3·CAUTION 8·VETO 1), 확장 98 PASS. 원 응답/불확실 예약을 보존한 새 세대 배포·장후 재개 및 최종 준비는 계속 진행 중이다.
  - 스케줄 보완: 명시 ADD scope와 현행 대조군을 우선 호출하고 전수 eligible 큐를 유지한다. 신규 8개 scope 확정 확인점 849건이 기존 대규모 모집단 뒤에서 발행창을 소진하는 문제를 보완한다. 순서만 변경하며 승률/대상 제외/요청 key/불확실 예약/호출 quota/운영 보호조건은 바꾸지 않는다. 스케줄·공유 원장·운용 계약 회귀 68 PASS 후 배포 검증 중이다.
  - 소비자 보완: 기계 계산은 02:39 succeeded. semantic detector의 operating schema 누락과 128 route 신규 준비/기존 쌍 carry 표시를 보완했다(semantic 170·인계/PREOPEN 175 PASS). 기존 AI deadline 06:39:18 KST을 유지하여 후속 배포/복구가 종료 시각을 뒤로 미루지 않도록 인계한다. 최종 실제 비교·전수 terminal·strict/controller/finalization·10/8 PREOPEN 준비는 아직 진행 중이다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-07", "sources": {"entry_cancel_wait_policy": {"sha256": "b9562c7326a79d6c0b318c1c00077d8fc5a149debdf4a251028fd1577becab59"}, "entry_cancel_wait_tuning": {"sha256": "aa06f039aedc160202a74d528569dd509599a99474ac8f55a9cdbafdb645c173"}, "holding_path_vote_policy": {"sha256": "71221a9f65775d0fceee43ce47ff08acf5d830b136e1b9774a90739fcb8b07bc"}, "initial_quantity_refresh_stage": {"sha256": "35e190825f27181f5c25dda5102ef1d85c966e4e1709a21d2ae12897a1ce6f9d"}, "runtime_approval_summary": {"sha256": "90e1c7fc6b0d6c72b87e4529f4cfc430d8694224aa4fd942df5a60139d390511"}, "stage_episode_policy": {"sha256": "2434c5be3ffb1753586791e768ce4144b4577e2a3376d9425d9e7c728dbb4d1c"}, "stage_legacy_machine_report": {"sha256": "567d095a2bfe5f2a3aeb2b33341eb07fb3a22440a635b6cd5efc7e59b4e09df9"}, "stage_legacy_policy_approval": {"sha256": "feb7c2bc826a75ac7fef6da0e8120dfcc3dff4dad91cb7c41a6796fe10f78236"}, "stage_machine_attribution": {"sha256": "5834f3dfa9b69e942533f48926383038de828922b55e9a764d50869d7009e3dd"}, "stage_machine_timing": {"sha256": "57d14be4d5a48d95558202617a8ba3614b35a2dd65e86685a53258e5f3cdee3c"}, "stage_main_auxiliary_policy": {"sha256": "b733df79a04ba6a196beac399287867c4901d916e080dd85384578971e792303"}, "stage_main_machine_policy": {"sha256": "54dcbd0f051cfa80bf63334615f6b01874e268eeef4575cc5bc2a84e39226660"}, "stage_market_weakness": {"sha256": "a9ee032d3c6f4488e2f565bf4498f54d95de971f962a4059b8942f50a4d92082"}, "stage_outcome_labels": {"sha256": "a76dc2f67e3067b13e339b98a5d3d13eefdd5cb5a9e231b8367da7463239e9f5"}, "stage_pre_submit_delay": {"sha256": "fa96cc0292cefabc47abfdd9e7c849f8257afc8f57a6899077606633cb729881"}, "stage_research_allocation": {"sha256": "d9a44771aa5e76fcfb10cd8f7a30cf377ed0e1bea1eb7efda9e2be48b8ce0d18"}, "stage_research_capacity": {"sha256": "f7d4a6b7233045721f53e9ae29e526f000d21285b21134982daed4eaf1978f6b"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-08", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "528556fca5e67676b6e1125e560e76051574bfaf167c54225b422dfa45bab442", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-08.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-10-07", "source_report_sha256": "4ca812fae292e94bc8b9caa4baabfb11454fe8ab6b7d3846faff5efe04da007c", "status": "estimated_provisional_published", "target_date": "2026-10-08"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-08.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "1ac6274f39022fcb33a038cc4dec69cd85bbbe35cf7de20b39b6fc776a153a19", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "b9562c7326a79d6c0b318c1c00077d8fc5a149debdf4a251028fd1577becab59", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "e03307e5ac633d9ea33c24ebb5a07e2ceb3ab9ae7f414c4bec5e4f3a556e86c9", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "d311f8ce8f276c342a2b95889529ff9ba5474e5ef01513422f52cd0700174261", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "1ac6274f39022fcb33a038cc4dec69cd85bbbe35cf7de20b39b6fc776a153a19", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "9f74c8f5abb7a610e8379dbc169cd2d8b9dd290409956a889b365e63aeb51de0", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "bd0c0624826b6f9c5845da1e79ecf5ffec247fd140d19c8c25c99ef8da240023", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "5df07fe61d092dc8efe38f26c8aa5c65d0d3e541974e763efd09450fd06f0cc8", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-07", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-08.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-07`; next apply date: `2026-10-08`.
- direct source: `10/10`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `source_gap` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `cumulative_winrate_selected` | `verified` | `preopen_policy_handoff` |
| `compact_auxiliary` | `cumulative_winrate_selected` | `verified` | `preopen_policy_handoff` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-08`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 판정 기준: source_date=`2026-10-07`, apply_date=`2026-10-08`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=verified); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); low_price_two_leg(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=verified); pre_submit_delay(valid=True, handoff=not_applicable); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`90e1c7fc6b0d6c72b87e4529f4cfc430d8694224aa4fd942df5a60139d390511`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-07.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`90e1c7fc6b0d6c72b87e4529f4cfc430d8694224aa4fd942df5a60139d390511`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-07.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-07`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-07.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json)
  - 증거: runtime_summary_sha256=`90e1c7fc6b0d6c72b87e4529f4cfc430d8694224aa4fd942df5a60139d390511`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-10-07.json`.
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
