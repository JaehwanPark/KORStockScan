# 2026-10-01 Stage2 To-Do Checklist

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



## 실행 항목

- [x] `[PostcloseSemanticMonitorPlan1001] 현재 릴리스 장후작업 연계 의미감시 수정보완계획 수립` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 22:20~23:59`, `Track: RuntimeStability`)
  - Source: [의미감시 연계 보완계획](../proposals/semantic-monitor-postclose-integration-repair-plan-2026-10-01.md), [통합 릴리스 인계](../audits/integrated-release-next-startup-handoff-2026-10-01.md).
  - Acceptance: selector/HEAD·감시 소스·실제 cron·새 장후 버전·기존 의미 report를 대사하고 same-day 검증 오탐, full-cost/동결 선정 검사 누락, 의미 warning 알림 누락, generation/준비/PID 경계를 계획에 반영한다. 문서 링크·소유자·print-only parser를 검증한다. 계획 수립 완료이며 구현·배포·재기동/보고서 재생성 영수증이 아니다. 후속 코드 owner는 `PostcloseSemanticMonitorContractRepair1002`다.

- [x] `[Postclose0930IndependentChainRecovery] 9월 30일 장후 독립 단계·최종 체인 복구` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 00:00~06:50`, `Track: RuntimeStability`)
  - Source: [장후 점검 운영 계약](../postclose-tuning-result-review-task-instructions.md), [단계 영수증](../../data/report/postclose_stage_terminal/2026-09-30/summary_handoff.json).
  - 이관: 9월 30일 23:39 모니터 스냅샷이 OOM 종료됐고, 정확일자 완료 포지션 축약본·네 산출물 해시 검증 및 퇴역 episode 공동 배분 OFF 수리를 적용했다. 수집기 원천 기간 및 자체 대상일 replay 재작성 계약을 보완해 재실행 성공했다. 원래 9월 30일 원천일과 수용 범위를 유지한다.
  - 10월 1일 압축 보관으로 바뀐 동일 원천은 해시 검증 후 필요한 보유 관측본을 복원하고 제출 지연 원천 영수증을 재봉인했다. 최종화가 전체 DONE controller를 단계 요약으로 우회하지 않도록 호출 경계를 수리했다.
  - 최종화 정리 실패 원인은 10월 1일 진행 중인 provider 예산 ledger의 미발행 요약 파일이다. 현재일 미완결 ledger는 압축 대상에서 제외하고 명시적으로 계수하며, 과거 닫힌 ledger의 검증은 유지한다.
  - 최종 오류 탐지는 다음 거래일 준비 예정일을 명시하지 않아 07:35 생산 전 bootstrap을 결손으로 오판했다. 원천일·준비 예정일을 함께 전달해 재실행한다.
  - 완료 기준: 기계정책의 동일 정책 후속 세대와 후행 원천 해시를 검증하고, 실패한 최초 단계부터 요약·strict verifier·controller·최종화까지 9월 30일 terminal을 다시 확인한다.
  - 종료 근거: 10월 1일 02:33:28 KST 재실행에서 9월 30일 main wrapper `succeeded`, 전체 strict `pass`, controller `done`, 최종화 정리·탐지 `done`; chain SHA `9f048316521e02d90b238a59ed2e2d23165e8190260158f9a3ea417fd76cf01b`.
  - 권한 경계: source-only 수리이며 Main bot 정지·재기동, 수동 env·lock 변경, 주문·provider·threshold·hard safety 변경을 포함하지 않는다.

- [ ] `[Postclose1001SelectedReleaseFinalizer] 05시 선택 릴리스 최종화 재실행 점검` (`Due: 2026-10-01`, `Slot: PREOPEN`, `TimeWindow: 05:00~06:50`, `Track: RuntimeStability`)
  - Source: [릴리스 라우팅 계약](../runtime-release-routing.md), [9월 30일 최종화 근거](../../data/report/postclose_done_controller/postclose_done_controller_2026-09-30.json).
  - 선택된 불변 릴리스 `1e355c3b`에는 이번 workspace 수리본이 아직 반영되지 않았다. 예약 실행이 최신 `done` 영수증을 덮어쓰거나 실패하지 않도록 릴리스 승계 또는 같은 세대의 05시 검증을 수행한다. 가변 workspace로 예약 경로를 우회하지 않는다.
  - 완료 기준: 선택 릴리스의 정확일자 controller `done`·strict `pass`·최종 탐지 영수증과 실제 05시 경로를 확인한다.
  - 16시 복구 재점검: 늦은 9/30 재계산의 최신 요약·strict `pass`, 전체 controller `done`을 확인했다. 준비일 결속, 과거 장전 릴리스 선택, 최종 controller 해시 재봉인 및 10/2 발행 정책 선택을 수리했다. [원천·정책 점검](../audit-reports/2026-10-01-postclose-0930-policy-readiness-review.md)에 따라 최종 릴리스의 정책 영수증·단계 영수증 재검증과 10/2 장전 bootstrap 검증을 확인한다. 오늘 메인 봇은 기동하지 않는다.

- [x] `[PostclosePreparedPreopenHandoff1001] 닫힌 장후 원천의 다음 기동일 장전 사전생성 검증` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~21:40`, `Track: RuntimeStability`)
  - Source: [릴리스 라우팅 계약](../runtime-release-routing.md), [9월 30일 닫힌 controller](../../data/report/postclose_done_controller/postclose_done_controller_2026-09-30.json).
  - 9/30 원천의 최신 strict DONE 및 10/2 기계·보조 AI 정책을 선택 릴리스에서 검사해 격리된 10/2 장전 env·manifest·검증 영수증을 만든다. 10/1 장후작업이나 메인 봇 기동을 선행조건으로 두지 않는다.
  - 완료 기준: 준비 영수증의 원천·정책·릴리스·직전 검증 장전 해시가 일치하고, 운영 장전 파일/정책 포인터/PID가 바뀌지 않는다. 다음 기동일에는 준비본 재검증 → 실제 장전 성공 영수증 → 실제 PID 소비를 별도로 확인한다.
  - 완료 근거: 최종 선택 릴리스 `459d718f`에서 9/30 전체 controller `done`·strict 결손 0, [10/2 준비 영수증](../../data/runtime/policy_bootstrap/prepared/2026-10-02/latest.json) 생성·재검증 `pass`. 운영 10/2 env/manifest는 미생성, 기존 정책 포인터 해시는 불변, 메인 PID는 없다. 10/2 실제 PREOPEN·기동 수용은 그날의 별도 영수증으로 확인한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-30", "sources": {"holding_path_vote_policy": {"sha256": "3c9622668e984dfd4d375bebd168e527e7e14cbacc428df9315894da9ae43251"}, "initial_quantity_refresh_stage": {"sha256": "86757f98d15651ad289cc2d8782b93cc20f2f58447dd082efda9f420e85d47bf"}, "runtime_approval_summary": {"sha256": "9a76de3ccbe57a8a09945803488c11b33fe5263fd3303a126aeff71a7b17b502"}, "stage_collector_recommendation": {"sha256": "fe6f4817a3a305ffe9240cffa52691be18dfa8be5323a000063771d2c458ced4"}, "stage_episode_policy": {"sha256": "837eee0b602ac42b845ec791eea9c1808d828dd278ac868dff21901e24a4ef2d"}, "stage_legacy_machine_report": {"sha256": "4e6b1f2a5f2f5d5730e0d7c7c903488bb982e29e2b21ff25964150d3ed3e446e"}, "stage_legacy_policy_approval": {"sha256": "b5bd1f57774c22733f9da1a80e74fb3e976fd4e7ac1cbd07bbe3fcd7aafa87e8"}, "stage_machine_attribution": {"sha256": "d9e8ac792134f3eb3ba2e7784dc935254e12f8cf4f98518cd1a9e2cead5f9eda"}, "stage_machine_timing": {"sha256": "6575cbeb38253e07edadf3bb8b2a9e944bdd5cd596ed293100409a64b6e573cc"}, "stage_main_auxiliary_policy": {"sha256": "f9b5c7de008fb26efd4c47e668035c9be8d5af4d01ec5e14b64221aad0515133"}, "stage_main_machine_policy": {"sha256": "4fa67bd9717c4503ee878b3df0a0a09a2534211b2203e2d460cd1246b4e4f002"}, "stage_market_weakness": {"sha256": "e172d4df2fae6af22b62eff56067fad328f699f28b4b3d0aa935048e6e367736"}, "stage_outcome_labels": {"sha256": "ca7cda975a440f9951a9cff20ad52f76686d7d7ce2bd1a57fb72061dfc7b7d62"}, "stage_pre_submit_delay": {"sha256": "c7ffac58ed7e57b5cdb3194f47b51598ff0dbd1bd3b9ae25b0128f3d819f00e8"}, "stage_research_allocation": {"sha256": "b8af29e16f33f78d8005cc562da3aa1079e1e6c4dfb4c795977c50992b206d64"}, "stage_research_capacity": {"sha256": "7a54ace6e769a0b45381d148217a264083d495578788de266df6de69869b3357"}, "stage_widget_policy": {"sha256": "72445b00fbf81c6e32bfcacd2202c7cf2c591e2f62731883f905484d65882522"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-01", "expected_state": "verified", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "a35785b93f0c848216b39bf07986b40407d4c8ed0d0a596ee357257887010a92", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-01.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-09-30", "source_report_sha256": "62325c2c19475c362344831122053d06848c6b8aa747c1d7f7815b1552244473", "status": "estimated_provisional_published", "target_date": "2026-10-01"}, "manifest_content_sha256": "f5db50db1f0fd844479c604145e4810c154ab342ce1b8749492b8ceeadf278cb", "manifest_env_sha256": "3e62cc7fc1dc91eaad340f978b1a4a6efd8379205300c48468c1e2c5521dcae5", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-01.json", "manifest_sha256": "4682b36e40b2fbb7e6e1bda2627ed70a3c5df863969a187ae2212fae9c38f086", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "aaabcdcfa6f061012f00b14b327407c127b5f603d5a573cdf8178c6fdefb5de9", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "9aea063cf7ee3b1bd2329664ca5759ea8f965bc535c09362f4d4d0851df99e1e", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "b83e8e2af73bef6c5fff20390d514d4c13d17c37127c6f2b2d0875e9b06f9efc", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "ae2cfaf4615d8f88be62c7b04e3736a8c77726b703df861155c2ed115629a26b", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "aaabcdcfa6f061012f00b14b327407c127b5f603d5a573cdf8178c6fdefb5de9", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "2d324c091ea8f1df1bc9c716cff3f35f5894fcaa43e246fa1df8d9121fe96166", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "030bfe3bfa0e4d9c0c7381802934d19232894fdc2eff714d385d369ae3463a21", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "672e224572c91f4a7ab0f755949132074a13d332416a9492d5a615bd6c980b68", "valid": true}], "release_selection_sha256": "fc57f940e4505b0140a28034c7bdee57b9832394860ffe8fd43bd3f41f723c9a", "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": "90c062985127294b61bc97084caab95f22e40a85", "source_date": "2026-09-30", "source_preopen_state": "verified", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-01.json", "verification_sha256": "a4691cddd495411382114682e07e40d78a134cc46d9f9a26af3e721324a22199"} -->

## Family 직접 증거 상태

- source date: `2026-09-30`; next apply date: `2026-10-01`.
- direct source: `10/10`; direct state: `complete`.
- economic state: `source_gap`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `verified`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `source_gap` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `source_gap` | `blocked` | `producer_contract_repair` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-30.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-30.json)
  - 증거: runtime_summary_sha256=`9a76de3ccbe57a8a09945803488c11b33fe5263fd3303a126aeff71a7b17b502`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-30.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`exact_stop_distance_missing_or_invalid`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-09-30`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-30.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-30.json)
  - 증거: runtime_summary_sha256=`9a76de3ccbe57a8a09945803488c11b33fe5263fd3303a126aeff71a7b17b502`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-30.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_dispatch_or_parent_lineage_unclassified`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-09-30`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-30.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-30.json)
  - 증거: runtime_summary_sha256=`9a76de3ccbe57a8a09945803488c11b33fe5263fd3303a126aeff71a7b17b502`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-30.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-09-30`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-30.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-30.json)
  - 증거: runtime_summary_sha256=`9a76de3ccbe57a8a09945803488c11b33fe5263fd3303a126aeff71a7b17b502`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-30.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-30`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-30.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-30.json)
  - 증거: runtime_summary_sha256=`9a76de3ccbe57a8a09945803488c11b33fe5263fd3303a126aeff71a7b17b502`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-30.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_operating_population_unbound`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`future_exact_changed_decision_owner_replay_and_completed_profit_rate`. policy_receipt_valid=`True`, source_date=`2026-09-30`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:542e12c648cbf009c8d816a6b3ee3587108771e136c6123ff16bcd1dd4f01610 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-30; 발행 2026-09-30; 적용 2026-10-01. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `3cdfe1c65e266c0e0849d4c42c415c81ddc9a44fa45b5395bed421396457fd42`; 정책 bundle `91b3ed34161172b4f2587e14069d05dbb0e023f58c9dc9eb38df46a7bbfd24d4`; consumer `f9c8fdc98da958e5ab80c0cda54ef0249d5dca9fb8823fa314d604bd490d77fb`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
