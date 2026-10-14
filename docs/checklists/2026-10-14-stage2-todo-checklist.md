# 2026-10-14 Stage2 To-Do Checklist

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

10/13 장후 실패 지점 수리·재실행의 다음날 수용은 기존 `DirectFamilyPreopenPolicyHandoff`와 family source owner가 [복구 근거](../audits/postclose-failed-stage-recovery-implementation-review-2026-10-13.md)로 수행한다. Source/publication 10/13·적용 10/14, native 실패/재개 ID와 완료 계산을 보존한다. 직접 복구의 승인된 custody 설정 전달과 entry-split의 값·정책 불변 서식 압축을 검증한 뒤 summary/checklist/strict/controller를 닫는다. 준비와 실제 PREOPEN/PID·비용 후 성과를 구분하며 새 OPEN ID·매매/수동 env/lock/provider/threshold 권한을 만들지 않는다.

## 약세 장후 연구 결함보완 인계

- [ ] `[MainMarketWeaknessPostcloseObservation1008] 압축 원천·native 판정 연결·누적·약세 조정 후보 보완` (`Due: 2026-10-14`, `Slot: POSTCLOSE`, `TimeWindow: 검증된 수리의 후속 배치·자연 수용; 실제 연구는 21:40~익일 05:40 허용 슬롯`, `Track: RuntimeStability`)
  - Source: [10/14 구현 리뷰](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md), [10/13 결함보완계획 WR0–WR5](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md), [원 MW0–MW6·구현/배포 이력](../proposals/main-market-weakness-observer-repair-and-postclose-research-implementation-plan-2026-10-08.md), [기존 stable ID·Acceptance](2026-10-09-stage2-todo-checklist.md).
  - 범위: 10/14 사용자 승인으로 WR1~WR4 작업본 구현·반복 코드리뷰/수정을 수행했다. gzip-only reader/native 연결·확인 latch/누적/phase/typed 후보/안내와 설정 재결속을 구현했다. 실제 배치·예약 재결속·원천 재계산·실발송은 후속 수용이다. 추가 장중 hook·로깅·metadata·파일 조회/계산·queue/thread·API/AI 호출은 0, 기존 보조 패턴연구·정책/주문·Main/manual custody·퇴역 경계는 보존한다. joint/지연 개선 작업의 구현·배포 승인을 전용하지 않는다.
  - Acceptance: 기존 MW1 회귀·선택 observer 자연 소비 경계를 보존한다. 실제 schema/선별 전 census·gzip/원본 alias·bounded decode·effective listing 검증, 원 event/attempt/hash/ask/feature/label binding·결손 U, A/B/C/U·미래 join/TTL300·지연60/180·W/F/U 공통 분모·origin/중복 분리를 검증한다. 같은 관련 정의만 날짜 간 누적하고 실제 변경은 분리한다. 기계 지원 수치 축/미지원 사유와 보조 PASS 이후 CF를 구분하며 후보 합계 최대6·고정1,000회 안정성/U 민감도를 유지한다. 최대9회·야간 총 예약600초/worker1/512MiB·자식 회수·crash/delta0, optional code/calendar rebind와 terminal→누적→후보→관리자 Telegram 의미 ID/receipt·정정/uncertain→night summary를 검증한다. 연구는 strict/PREOPEN·기동 비차단이며 95% 보장·정책 자동 적용·주문 권한은 없다.
  - 리뷰 보완 수용: gzip-only 날짜 discovery→pending→실제 reader까지, 잔여 budget/CRC·hard kill 뒤 prefix 반복 억제·daily/cumulative/notification phase 재개를 검증한다. 2회 활성/3회 회복 확인 latch를 primary로 두고 raw 진단·실제/재구성 근거를 분리한다. 기계/보조 kind별 K/R/A/N 공통 분모·추가만 있는 후보·U 민감도·parent/preview/winner_group, key 이행 중 오정정0·원 sent 보존을 검증한다. optional rebind는 기존 notify/설치 이력/source 경계를 보존하고 자정 active/staged를 구분한다. outside_night_window의 신규 연구 상태 쓰기는0이며 최신 야간 시도와 원 계산 receipt를 별도 보존한다.
  - History: 10/9 MW1 수리·MW2–MW5 구현/반복 검증·selected release/optional 설치는 [배포 리뷰](../audits/main-market-weakness-review-deployment-2026-10-09.md)의 역사다. 10/13 점검 누적16,722개·자연1,534개·시장 연결0·후보0은 입력 연결 결함이며 no-edge가 아니다. 새 결함만 열고 과거 완료 구현을 전면 재실행하지 않는다. 이 stable ID를 미래 날짜에 Acceptance와 함께 이전하며 중복 OPEN을 만들지 않는다.
  - 인계: 원 AUTO 봉인 bytes와 다른 OPEN owner를 보존한다. 최종 checklist 문서 바이트의 기존 strict/PREOPEN 영향은 `DirectFamilyPreopenPolicyHandoff`가 기존 승인 범위에서 검증하고 과거 PASS를 현행으로 주장하지 않는다. 현재 작업본 코드 수리·표적 회귀는 완료했으며 배치·연구 재계산·실발송은 미실행이다. 원 기계 숫자 역할 미확인은 role_unverified, 완전 확인점 재생 producer 부재는 confirmation_replay_unavailable이며 지원 축/실제 수치로 보고하지 않는다.

  - 구현 검증: [구현 리뷰](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md)의 회귀/compile/정적 검사·문서 parser 결과를 수용한다. 실제 예약의 원천 연결/A·B/U·phase·notification disposition·최신 시도/원 계산은 검토 release 배치와 자기 code rebind 후 확인한다. 기계 수치 후보 부재·새 자연 표본 부족은 경제성 null/연구 capability이며 source 수리 실패나 no-edge로 전용하지 않는다.
  - 후속 재리뷰: [8종 수정 근거](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md#후속-코드-재리뷰와-수정보완), 표적 263개 통과. 재생 producer 부재는 selection/안내 거부, 두 지원 필터의 추가 모집단은0이다. pending 날짜 중 outbox 보존·cursor 변경 시 발송 보류·conflict 캐시 무효화·오래된 철회/정정 억제·comparison→manifest 중단 복구·저장 오류 defer·probe BLOCK 분리·실제 capability 사유를 후속 배치 수용에 포함한다. 원 K/R/A/N 통계 수용은 미지원 재생 producer의 완료를 뜻하지 않는다. 배포·예약 변경·운영 원천 재계산·실발송 미실행 경계를 유지한다.

  - 배포 승인 수용: 후속 사용자 “배포승인”으로 [검증한 불변 배포본](../../data/report/main_market_weakness_deployment/2026-10-14/build.json)의 선택·자기 optional 예약 code rebind를 실행한다. 최종 결과는 [배포 결과](../../data/report/main_market_weakness_deployment/2026-10-14/deployment-result.json)가 소유한다. 기존 enabled/notify·설치 이력·source 경계와 정지된 Main 상태를 보존하며 기동·정책 발행·장중 연구/실발송은 포함하지 않는다. 263개 release 회귀 통과와 실제 다음 야간의 terminal→누적→알림 disposition 수용을 구분하고 자연 수용 전 이 OPEN owner를 유지한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-13", "sources": {"entry_cancel_wait_policy": {"sha256": "05c6e58c448d49a125423be5a8d2a971991b8ebfd78460f094c74f8465fcef84"}, "entry_cancel_wait_tuning": {"sha256": "5dac925e60640179237cf2064ef917be65baea75a131567e876aafdff514b178"}, "holding_path_vote_policy": {"sha256": "6174f941e52aff50a45afeacce70718e74ac785d82780ab3fbbe47998f526c6c"}, "initial_quantity_refresh_stage": {"sha256": "e638ee74c917dd3801a762567227b8e1439e0ad7f237d86761e43adbbbb1b070"}, "runtime_approval_summary": {"sha256": "7c2ba65d165c6fe4e1584ab3df486c41eaf59f1d7acc6ce009812732e606570a"}, "stage_legacy_machine_report": {"sha256": "e9ab06a6a0057e160343a44ca6a50e48b8484979a10e26b1df5fff09fb07e27f"}, "stage_main_auxiliary_policy": {"sha256": "0cbaaa3a22241b7024c923d3169ae37562cf3bd0c5e7c296ee26bee59e9c0c1d"}, "stage_main_machine_policy": {"sha256": "5650282d7bbdc92c45841e087b98d9c7652570503db5ad830313630b500cdb8d"}, "stage_main_stop_confirmation": {"sha256": "d583b0b9289f18b6f3b21bb89c378908784834374290ab5deb0f6702be51618b"}, "stage_outcome_labels": {"sha256": "824175ca361e7ad29ea4acf3681cf9c6d93cd08abd08b293627f1c57a0f4a894"}, "stage_pre_submit_delay": {"sha256": "206da07f312bf0423f00d9cc270bb05edfb5a5ba082006de252aed4e010257b7"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-14", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "a83b57e2c55ec178aa7a50c1bfb7841cbb1a60acadf30e4df7deca38a15eb105", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-14.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-13", "source_report_sha256": "0cfa241344048dd5d704d4478f682734cfa9607c83bde36565eeed4524b6b56e", "status": "verified_incumbent_carried", "target_date": "2026-10-14"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-14.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "7524031752b1dd4f165a7e189ca0c4820396e5f10eacc6e078d83a8e2e0340c0", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "05c6e58c448d49a125423be5a8d2a971991b8ebfd78460f094c74f8465fcef84", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "fae051dcb3cce32d2496070481b92c31cb84a6d460a6d8e473d41f9a4c477d4d", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "7524031752b1dd4f165a7e189ca0c4820396e5f10eacc6e078d83a8e2e0340c0", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "741e4c7dfb805006a9ecbe3ed91cdbe1d057573a328b594c16c6d2f43e324b82", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "ad0cf8e387706397b81bb96499a485ba84e76faa1d5e09b36b4e161aa3b0e635", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "1c231b8d6ba2661e874409fe604e3de34fc9f8cc1ff907a29e6f1c503ebc31af", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-13", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-14.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-13`; next apply date: `2026-10-14`.
- 아래 상태는 summary `7c2ba65d165c6fe4e1584ab3df486c41eaf59f1d7acc6ce009812732e606570a` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
- direct source: `9/9`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `initial_quote_timing_policy_published` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `compact_auxiliary` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-14`, `Slot: PREOPEN`, `TimeWindow: 다음 승인된 적용·기동 시점`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 판정 기준: source_date=`2026-10-13`, apply_date=`2026-10-14`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=incumbent_preserved); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=df061c25b6f68a6979ebbdb5f3b2093666589240ce6e100cd04ca3bb94467ac0, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 증거: runtime_summary_sha256=`7c2ba65d165c6fe4e1584ab3df486c41eaf59f1d7acc6ce009812732e606570a`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-13/auxiliary.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-13`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 증거: runtime_summary_sha256=`7c2ba65d165c6fe4e1584ab3df486c41eaf59f1d7acc6ce009812732e606570a`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-13.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-13`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 증거: runtime_summary_sha256=`7c2ba65d165c6fe4e1584ab3df486c41eaf59f1d7acc6ce009812732e606570a`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-13.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-13`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 증거: runtime_summary_sha256=`7c2ba65d165c6fe4e1584ab3df486c41eaf59f1d7acc6ce009812732e606570a`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-13/machine.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-13`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-14`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 식별 결함: ["policy_binding_gap"]
  - 완료 기준: 기간·정산 세대·first crossing/유예·signal별 lifecycle/as-of의 producer→consumer 회귀 검증.
  - 비용 원천 부재·자연 표본 0은 코드 결함과 분리하며 신규 EV gate·SELL/retry·재기동 권한을 만들지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 10/14 Main stop 압축 binding 수리 인계

- Source: [Main stop 압축 binding 수리](../audits/main-stop-compression-binding-repair-2026-10-14.md).
- 기존 `DirectFamilyPreopenPolicyHandoff`가 10/13 원 source/publication·10/14 적용일의 손절 binding 수용을 맡는다. 압축 전후 원본 내용 SHA·크기 및 동일 logical source 집합의 native binding, 손절 값·cell disposition 보존, summary/strict/controller·최종화·full prepared 검증을 확인한다. 과거 `MainStopLossRetirementRuntimeTuning1010` 완료 ID를 현재 owner로 복원하지 않으며 원 Acceptance·실제 PREOPEN/PID 경계를 유지한다.
- 별도 `HoldingProfitExitSourceContractRepair`의 전일 Sentinel 경고·자연 표본·비용 결손은 이 수리의 완료와 구분한다. 매매 재기동·주문·threshold/provider·수동 env/lock·외부 sync 권한을 만들지 않는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:34c742a788c1415fd2d3dbca24cd035f04ead9269f2e954345dc6abf783d94c2 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-13; 발행 2026-10-13; 적용 2026-10-14. `no_submitted_orders` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": null, "checkpoint_sha256": "60b1961951ac3fdc82c8bb7ec9b628e1eceb3540884f6e4a457211420281b222", "historical_terminal_or_profit_inferred": false, "known_open_count": 0, "registry_tail_hash": "b03d9a806ec95f8eebbf83e87900f4957b46d90312e721c1d10f10d7f2912d83", "status": "verified_empty"}, "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "no_submitted_orders", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "baabff708b4f0ab1911421993ff9349ccb3688165f610260470c617d724291b4", "research_evaluation_status": "no_submitted_orders", "runtime_effect": false, "source_date": "2026-10-13", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->

## 10/14 승인 구현의 자연 수용 인계

- [ ] `[AuxiliaryCircuitRecoveryRepair1012] 보조판정 회로·제출 증빙의 다음 정상 신호 수용` (`Due: 2026-10-14`, `Slot: INTRADAY`, `TimeWindow: 승인된 적용 후 다음 정상 attempt`, `Track: RuntimeStability`)
  - Source: [보조 회로·제출 보완계획](../proposals/main-auxiliary-circuit-recovery-and-submit-receipt-remediation-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md), [10/14 제출 병목 개선계획 B0/B2/B3](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md).
  - Acceptance: 실제 새 PID/cwd/start ticks·bundle/registry 소비, 같은 시장명 비교의 receipt→revision→sizing 연결, 원 native5초·단일 recovery lease·공통 인증/unknown fail-closed·보호 exit 독립성을 확인한다. 회로가 자연히 열리지 않으면 HALF_OPEN 성공을 주장하지 않고 pending으로 남긴다. PASS와 intent/send/fill/terminal을 분리한다.
  - History: 10/12 계획의 P0-A/B/P1 새 결함만 구현 범위다. 기존 완료 native/readiness/auth owner 전체를 다시 열지 않는다. 기동 준비·배포 수용은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다.

- [ ] `[NonfixedDispatchReadinessReview1012] 혼합 관측·0D 이력·probe 편입 및 신규 등록의 자연 수용` (`Due: 2026-10-14`, `Slot: INTRADAY`, `TimeWindow: 승인된 적용 후 정규5분 연속3회`, `Track: RuntimeStability`)
  - Source: [잔여 병목·패턴 보완계획](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md), [10/14 비고정 관측 개선계획 B0/B4](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md).
  - Acceptance: 슬롯5/long2·60/150초·원 lease deadline 보존, mixed branch 긴 관측 순환, exact item/route/epoch/sequence의 0D count·중복/신원 결손 분리, Main 편입 첫 실패와 capture/lease/record/PID/start 연결을 확인한다. 등록6정의/4scope의 registry·native root·OR 한 기회 소비를 실제 대상에서 확인하며 신호 미발생은 pending이다. PRE NXT와 AFTER SOR 범위를 REGULAR로 복사하지 않는다.
  - History: 10/12 완료 owner의 R1/R2/R4 새 결함 범위와 지정 등록의 자연 수용만 전달한다. 과거 원천의 route/count·미확정 손익을 소급 보충하지 않고 새 경제성/미래 날짜 gate를 추가하지 않는다.

### I/O 개선의 추가 수용과 승인 경계

- Source: [장후 배포·기동 준비 검증](../audits/main-io-postclose-deployment-and-next-session-readiness-2026-10-13.md), [I/O 구현 리뷰](../audits/main-io-contention-and-repeated-validation-implementation-review-2026-10-13.md), [10/13 원 Acceptance·추가 인계 이력](2026-10-13-stage2-todo-checklist.md).
- `DirectFamilyPreopenPolicyHandoff`는 사용자가 승인한 장후 완료 후 배포와 10/14 07:35 PREOPEN→07:55 정규 기동을 수용한다. 원 10/13 source/publication과 10/14 effective date, selected commit, policy/registry/bootstrap 및 실제 PID/start ticks/cwd가 일치해야 한다. Prepared PASS는 실제 기동/주문/성과가 아니다. 기존 AUTO 항목을 실행 owner로 사용한다.
- `NonfixedDispatchReadinessReview1012`는 기존 Acceptance를 유지하며 정규 08:00/08:05/08:10 Sentinel 연속 3회 DONE/exit 0, 전체 report population·source freshness≤600초, cold/warm 구분과 RSS/wall/논리·물리 I/O를 확인한다. 최초 색인 약1.12GiB의 저장·cold 비용을 포함하며 frozen 읽기79.3% 감소를 자연 성능이나80% 목표 달성으로 표시하지 않는다. 현재 정책의 실제 registry/정의/scope 소비를 검증하며 과거 등록 수치를 새 membership으로 합성하지 않는다.
- `AuxiliaryCircuitRecoveryRepair1012`는 같은 정상 attempt의 stage clocks·local p95/p99·offered/timeout/censored 분모와 원 native5초·필수 저장/guard를 확인한다. 초기 구간에 자연 신호나 HALF_OPEN 표본이 없으면 pending을 유지하고 실제 표본에 연결한다. 새 실주문/provider replay를 검증용으로 만들지 않는다.
- History: 10/13 I/O 코드/격리 parity·비용 검증은 완료 기록이며, 최신 장후 수리와 결합한 코드 검증·선택 릴리스·준비·실제 PID·자연 성능을 분리한다. 기존 주문/수량/가격/계좌/custody/퇴역/운영자 가드 및 separately approved policy를 보존한다.


### 10/14 최종 릴리스 기준 I/O 추가 구현 인계

- Source: [구현 리뷰](../audits/main-io-residual-implementation-review-2026-10-14.md), [보완 계획](../proposals/main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md).
- 기존 `NonfixedDispatchReadinessReview1012`는 정상/source-only의 priority·단일 예산·보류 이력 보존·native cold/warm parity와 적용 후 정규3슬롯 source age/분모/worker I/O를 수용한다. bytes 감소와 전체 host p95는 별도이며 synthetic8MiB 실험을 실운영 개선으로 승격하지 않는다.
- 기존 `DirectFamilyPreopenPolicyHandoff`는 명시적 transition digest session의 기본 full 경로·원 정책/selector/PID 독립 검사를 유지한다. 후속 사용자 “코드리뷰 후 수정보완을 반복하고 배포 및 메인봇 기동하라” 승인으로 검증된 릴리스 배포와 Main 기동을 수행한다. 선택5fb4c0a33은 미기동 배치이며 마지막 실제 소비 릴리스01d9fefa4/PID3854164의 native 정지 인계 증거를 검증한다. 기존07:35~08:15 및08:00/08:05/08:10 창은 새 구현의 수용 일정이 아니다. 새 기동·배포가 수행될 때 native source/code handoff와 실제 successor receipt를 따로 검증한다.
- 기존 `AuxiliaryCircuitRecoveryRepair1012`는 실제 정상 attempt가 생긴 뒤 원5초 deadline·local 지연·offered/timeout/censored·필수 guard를 비교한다. Main 정지/자연 표본 부재는 pending이며 구현·단위시험 통과로 닫지 않는다.
- 이 인계는 격리 candidate의 checklist 변경이며 승인된 배포의 snapshot/CAS 절차가 공유 문서 publication을 소유한다. 현재 공유 checklist의 약세 연구 배포 이력을 함께 보존한다. 원 Acceptance/History와 stable ID를 유지한다.

### 10/14 비고정 관측·제출 병목 개선계획 인계

- Source: [개선계획 B0–B4](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md). 10:33:50~11:17:00의 ff32b99b3/PID53125 근거로 작성한 계획이며 구현·배포·자연 수용 완료를 뜻하지 않는다. 기존 OPEN ID·Due/Slot/TimeWindow·Acceptance/History와 AUTO 봉인 영역을 유지한다.
- `AuxiliaryCircuitRecoveryRepair1012`의 추가 수용: B0의 exact request/raw response/validated PASS/Main terminal 대사, B2의 공통·분기 fact 계약 및 원 응답 보존, B3의 원5초·기존 NS5/R2b 지연 목표를 확인한다. 원12시도·4호출·3응답·1timeout은 고정 창의 회귀 기준이며 미래 자연 분모로 재사용하지 않는다.
- `NonfixedDispatchReadinessReview1012`의 추가 수용: B4의 기존 target 중복 defer·해제 후 복귀, fresh 적격 대기와 PID carry-over 분리,5/long2·60/150초·mixed branch/market/source 순환·단일 lease/ACK를 확인한다. 원32관측의 no-pattern22와 source gap10을 보존하고 conflict40을 물리 관측40으로 계산하지 않는다. 비고정 편입 표본 부재는 pending이다.
- `DirectFamilySourceRepairMainMechanisticEntry`는 B1 완성봉 시작/종료·원천 시각·reduced/strict 소비 계약 수리를 기존 source owner로 받는다. 현재 POSTCLOSE 창은 장중 수동 실행 권한이 아니다. 실제 stale/quote·holding/custody guard와 기존 CR7 입력 감축을 보존하며, 새로운 수리의 코드 검증·발행·자연 수용을 별도 기록한다.
- `DirectFamilyPreopenPolicyHandoff`는 후속 허용된 적용 시 affected code/registry/prompt/schema pin·원 policy 날짜·준비·PID 소비 및 최종 checklist generation 영향을 검증한다. 이 문서 수정으로 기존 prepared/strict receipt를 다시 PASS라고 주장하거나 보고 재생성·재기동을 실행하지 않는다. 실제 검증 슬롯은 승인된 적용 이후로 잡고, 문서 계획은 runtime 권한을 추가하지 않는다.

### 10/14 B0–B4 승인 구현·배포 인계

- 사용자 후속 “계획을 구현하고 코드리뷰 후 수정보완 완료시 배포 및 재기동 승인”은 이 B0–B4 구현과 기존 owner의 sealed contract-repair 발행·ordered Main 재기동에 적용한다. [구현 리뷰](../audits/main-nonfixed-submit-bottleneck-implementation-review-2026-10-14.md)가 코드·독립 리뷰·표적 검증을 기록하며, 배포 결과는 `data/report/main_nonfixed_submit_deployment/2026-10-14/deployment-result.json`과 native transition receipt로 구분한다.
- 기존 `DirectFamilyPreopenPolicyHandoff`는 selected commit/PID/start/cwd·원10/13 source/publication 및10/14 effective date·원 policy/PREOPEN/env/manifest hash·native code handoff·별도 auxiliary manifest/registry generation을 대사한다. shared checklist만 과거 frozen bytes와 다르면 두 버전을 보존하고 exact sealed incumbent 문서만 기존 release-set/detector/Sentinel lock 안에서 predecessor 검증에 사용한다. 다른 frozen mismatch는 중단한다. graceful drain 후 candidate 문서를 발행하며 선택 이전 실패에는 byte CAS로 편집본을 복구한다.
- 기존 `AuxiliaryCircuitRecoveryRepair1012`는 원 request/PID/hash·raw/contract-valid/executable response를 분리하고 worker 완료→coordinator ready→Main guard를 함께 관측한다. 고정5/비고정5·보호 위치의 구조 fixture 통과와 helper 추가 비용은 실제 Main 성능 개선으로 보고하지 않는다. 원5초와 필수 guard는 유지한다.
- 기존 `NonfixedDispatchReadinessReview1012`는 실제 배포 이후 정규5분 연속3슬롯의 source/단일 lease/중복 defer·해제 후 복귀·전체 cohort/long2·eligible wait·cold/warm I/O를 확인한다. snapshot 결손 시 기존 callback으로 판단하며 자연 비고정 신호·편입·경제 표본 부재는 pending이다. 기존 AUTO 봉인 영역·stable ID·원 Acceptance와 다른 owner는 유지한다.

### 10/14 Entry-split 검증 projection·Main 신호 전달 보완 인계

- Source: [검증·timeout 보완계획 E0–E4/T0–T5](../proposals/entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md), [구현 리뷰](../audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md). 후속 사용자 지시로 반복 리뷰/수정·검증 완료 후 배포·Main 재기동을 수행한다. 다른 세션의 작업본과 기존 AUTO 봉인 원 bytes를 보존하며 새 OPEN ID를 만들지 않는다.
- 기존 `DirectFamilySourceRepairEntrySplit`가 native full 검증→원 bytes/semantic generation 결속→작은 projection/receipt/manifest→모니터의 exact 상태를 수용한다. 크기 오류의 수리는 source_gap/비활성 후보/기존 설치를 성공으로 변경하지 않으며 원 정책·보고서 전체 연구 재생성은 별도다. 누락/invalid metadata에서 hot full parse0, 새 프로세스 warm full read0와 source변경시 무효화를 확인한다.
- 기존 `AuxiliaryCircuitRecoveryRepair1012`가 원5초·같은 PID/attempt의 eligible→claim·budget/SDK/실제 settlement·Main terminal을 수용한다. 실제 방문 ACK와 hint token 비교, 이미 방문한 WATCHING의 pass당 bounded 재편입과 선택적 중복 schema 구성을 검증한다. 3.105초의 특정 내부 phase와 전체 p95 개선은 자연 자료 없이는 미입증이다.
- 기존 `NonfixedDispatchReadinessReview1012`는 고정/비고정 순환 fairness·단일 claim/lease·COMMIT/HOLDING/EXIT 보호 위치를 확인한다. 기존 `DirectFamilyPreopenPolicyHandoff`는 selected기반 immutable후보·정확한 code pair/정책 인계·graceful drain→publish→준비→singleton PID/start/cwd 실제 소비를 수용한다. Main/manual custody·보조 overlay·128scope·모델/프롬프트·원 기한·매매 가드는 보존한다.

- Entry-split 추가 자연 수용: 첫4e21 코드의 실제 cold 검증·PID 소비는 PASS이나14:25 예약 결과의 routed data mount 오류는 실패로 보존한다. 기존 `DirectFamilySourceRepairEntrySplit`/`DirectFamilyPreopenPolicyHandoff`는 trusted root 정규화 반례와 exact source pair 재검증·동일 승인 재배포 후 PID 및 후속 예약 보고서의 verification=verified를 수용한다. source_gap·후보 비활성·기존 incumbent은 바꾸지 않는다. 첫 배포의 frozen logs/code handoff는 수정하지 않는다.

재기동 진단 순서 보완 acceptance(기존 `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`, `DirectFamilyPreopenPolicyHandoff` 소유): 최초 full sweep의 자기 PID/start/manifest/consume/final record-pid 장벽·기존150초 한도/heartbeat/실패 노출, 정확한 old observer bytes에 한정한 예약 대기와 current partial/stale/오류 보존을 리뷰·반례·실제 첫 진단/예약으로 검증한다. 원 source gap·정책 및 기존 OPEN/자연 수용은 보존한다. [구현 계획 §13](../proposals/entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md#13-재기동-직후-진단-순서의-근본-보완) 및 `data/report/startup_observer_order_deployment/2026-10-14`에서 증거를 확인한다.

위 재기동 진단 acceptance의 ordered 첫 PID는 final record-pid→동일 transition complete/pass·successor identity 순서까지 확인한다. 과거 완료 transition과 이후 같은 릴리스/다음 날짜 native 기동을 분리하고, 오래된 workorder Markdown coverage 선언은 현행 runner JSON·performance 감시를 유지한 채 정리한다.

동일 재기동 acceptance에는 실제 selected router parser의 record-only `--workspace` subprocess 검증과 실패 owned hold의 검증된 원자 인계를 포함한다. 40357 실패 시도는 보존하고 새 commit/transition으로 수용하며 원 정책·OPEN·원천 결손은 유지한다. [실패 보존·복구 계약](../proposals/entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md#14-실제-cli-계약-누락과-실패-기동의-보존복구)을 따른다.

기존 `NonfixedDispatchReadinessReview1012`/`DirectFamilyPreopenPolicyHandoff`의 동일 진단 수용에는 [15:37 경보 원인 분리](../proposals/entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md#15-1537-이후-경보의-독립-원인-표시-보완)를 포함한다. 같은 작은 snapshot의 freshness·generation·semantic·원 blocker를 각각 확인하고 일반600초/실제 결손 partial FAIL·원 정책/OPEN/AUTO를 보존하고 아래 승인된 pending 예외를 구분한다. upstream 생성 시각과 관련 latest_event, 이전 수용 source_as_of 승계를 구분하며 stage 제외 대기를 정상 평가/valid_empty로 합성하지 않는다. 새 배포·첫 health·정상 예약은 `data/report/observer_alert_dimensions_deployment/2026-10-14`에 별도로 기록한다.

15:40 사용자 후속 지시의 동일 owner 수용: fresh-at-complete exact predecessor의 첫 예약+180초 한정 WARNING 대기, 현행 fresh/complete-read의 빈 cohort·정확한 보호 판정·정상 CAUTION/VETO·정확한 Main 종료/거절 PASS에 한정한 observation_pending WARNING을 별도 검증한다. 현재600초/PID/start 분모를 일치시키고 기존30분/allPID 이력은 보존한다. 미확인 PASS·실패/모순 제출·실제 계약 오류는 FAIL이다. 원 partial·미검증·과거 실패를 유지하며 정상/PASS/경제·매매 권한으로 전용하지 않는다. 이미 stale/현행 stale·production 실패·기한 초과·실제 원천/검증 모순은 FAIL이고 generic grace는 금지한다.

기존 `AuxiliaryCircuitRecoveryRepair1012`/`NonfixedDispatchReadinessReview1012`/`DirectFamilyPreopenPolicyHandoff`의 후속 수용에 [주성 조합 입력 원천 수리](../proposals/entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md#16-애프터마켓-주성-조합-입력의-실제-생산-결함-수리)를 포함한다. composed 원 확인 DD/volume와 rolling refinement를 구분하고 원 top/base 변조 거부·noncomposed bytes 보존·기준/후보128scope fresh parity·모듈1개 exact old/new source를 검증한다. 과거 원 trace·failure·정의/정책/pointer·OPEN/AUTO를 보존하며 새 PID의 자연 conflict 비재발과 observer 결과를 별도로 수용한다.

기존 NonfixedDispatchReadinessReview1012/DirectFamilyPreopenPolicyHandoff의 동일 기동 수용은 b0d795c1c 첫 진단 CAS 실패 이력을 보존하고, 정확한 영수증 읽기 경합의 원150초 내 재확인·지속 경합 timeout·실제 invalid FAIL을 추가한다. 새 OPEN/AUTO/정책/원천 완전성·경제 gate를 만들지 않는다. 최초 full sweep의 ordered complete 이후 시각과 현재 PID/start/영수증, 첫 정규 observer/후속 daemon을 data/report/startup_receipt_race_deployment/2026-10-14에서 확인한다.

같은 기존 기동 owner는 현재 PID의 검증된 birth 하한·실제 유효600초/수명 읽기 범위·기동 전 historical 분리를 수용하고, 원10분/allPID의 실패/partial은 보존한다. exact 초기 수신 guard/native confirmation pending은 원 UNKNOWN/censored를 유지한 WARNING이며 성공 판정으로 전용하지 않는다. current unknown·증빙 손상·읽기 미완전·실제 계약 오류는 FAIL이다.

같은 owner의 최종 보고서 건강 수용은 엄격한 완전 관측 검증과 별도로 bounded_source_quality_observation WARNING을 검증한다. fresh/current/정상 발행·정확한 actor/native/정책/schema/count·clean bounded reader·현재 issues0이 필수다. 원 source quality/AI invalid·timeout·미확인 PASS/소비·partial/uncovered를 보존하며 full validation/복구/매매 권한으로 전용하지 않는다. malformed/IO·변조·실제 계약 issues는 FAIL이다.

기존 동일 기동/observer owner는 f25 첫 진단 PASS와 정규 semantic 실패를 보존하고, 최종 notify/세대 봉인 이후 건강 계산→실제 main 발행 dict의 재계산 equality를 추가 수용한다. 세대 교체 시 미발행, 정식 fixed_watch_post_receipt_warmup 대기의 원 typed/native/주문금지 계약도 검증한다. 정책/권한/OPEN/AUTO는 보존하며 data/report/observer_publication_order_deployment/2026-10-14의 실제 정규 보고서와 후속 daemon에서 닫는다.
