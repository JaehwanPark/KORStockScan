# 2026-09-29 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-28", "sources": {"holding_path_vote_policy": {"sha256": "189f12af64c15270bc5a9a6708a4b9f60ef066066ead1c1849efd881ecee6bda"}, "initial_quantity_refresh_stage": {"sha256": "9326c38114626abafb59a9a6a0e8d9a61cb580c30d0d6827f63b0574d5405279"}, "runtime_approval_summary": {"sha256": "f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8"}, "stage_collector_recommendation": {"sha256": "b67f142bece7d4c111c1f48d325c9f149995af78008a22aae793d11633b0fed7"}, "stage_episode_policy": {"sha256": "e404384aa18f1adac7b792c86db0a38ce92e25d14e6e3dfdd480382d919aefb5"}, "stage_legacy_machine_report": {"sha256": "64d1cde8061abead665151ff2b41673358593a7fd98e99b9f185450b076d2fa4"}, "stage_legacy_policy_approval": {"sha256": "18d3307aa1e7cd9c2c704d0a65eb2548d4157071c7c2d79305e264dd32480193"}, "stage_machine_attribution": {"sha256": "6e09df99de4961e9ea10063dcef4e4a85f712540a31b8a5ca71fa7a3ac2d9046"}, "stage_machine_timing": {"sha256": "a58a5d43acfcfa52834af13657656800d4cfe0c23a92e7f27b13ed6146d5b780"}, "stage_main_auxiliary_policy": {"sha256": "b877ef5d09dc1ffb9d2d660c13ca84aef6bc96edd1173ac0134e732586fd7ad9"}, "stage_main_machine_policy": {"sha256": "523e8fafafd3c1d523496f5cc9b2e9dc30dcd46cb1290c7727e80916cd0278b1"}, "stage_market_weakness": {"sha256": "4076ce4c48a2bdd24554711fd54d53f4859681284cfe3dfe274d13fe8c4abcf2"}, "stage_outcome_labels": {"sha256": "664a9bc6ad1c4fb9f8f5126c9c024f2e02c25284fa54193d2771d1ef42d7b921"}, "stage_pre_submit_delay": {"sha256": "894d228abf1fb1f79e57f2ada38777893527c07d30258f690dbfcac53cd2f2dc"}, "stage_research_allocation": {"sha256": "4a265d9693f9b7a437c2f66ac1dd65546210565189cf52a8ca3d0ae6ff27119c"}, "stage_research_capacity": {"sha256": "72c664ec3f20f960b517c7f710c04caab741f58b59a64e38f87ebf9a125ac0c1"}, "stage_widget_policy": {"sha256": "a7d54df02abff8b39b3128f0823e29214c07410acf0068e3786d783b51c302a7"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-09-29", "expected_state": "verified", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "636b8818db0e1d1c647198622afdfb91b6bdba8b1d6b96f4e492fc67a26df010", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-09-29.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-09-28", "source_report_sha256": "2dfd68133d8dd27739baf53ff6ad0a17bd596f5cfaf4244710de3a9c2db518d6", "status": "estimated_provisional_published", "target_date": "2026-09-29"}, "manifest_content_sha256": "9e7f4008127c2bc439916204e266c722654bd4f28ca9c4a29ab541068b674c63", "manifest_env_sha256": "736fa7bc1c5a91350a68c4e23c36c5c84ef57ca0b8737a18cc08ba44be2fc775", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-29.json", "manifest_sha256": "ae62b779c28a3a20060a2841b24073bd6978d7caff9ba23934772a7ef99d458b", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "d7635723b46faa1edd06ab1f733bda7866a773f60dfcb644d4545d9573b0f8eb", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "5ea6ab6de45963ead91f7612b14433456c9316600d1a675bd6fbfd76b2e4895d", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "1d52bf1e53a5ef041840a024b927db839c7ab580397da52485f462c6074b3152", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": "e3f29300efffc62185fd5238ea8f18154ee819ec001ab728dea561db14ae5b33", "valid": true}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "082a5001ef9b0669e853b5941d751cc80c81988e6e612343b4c56f1cca3b6b52", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": "56897f1bacb40b5c406a05ba9719b0b965b31496c84d1b84f4b27386ad2d9b14", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "d7635723b46faa1edd06ab1f733bda7866a773f60dfcb644d4545d9573b0f8eb", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "fd657c922c193a8952283dac7821dd59df49b765cc1e48cb79fc05ff5913436a", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "66099f70ce31bbb4e836f1807bbc5fe6916ae197105f2afbfea0af1677fb4a9f", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "3214ae3a6fe90573482f5efa75d773517f5f3f4f7286c6406dda8b02fab53791", "valid": true}], "release_selection_sha256": "237fa888508fa99eb7dc535fab53f49db628952ad98f5ad3aab3bd9ca00182b5", "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": "e4117982fe34fe8bfc74a7468c6f049f25e7c149", "source_date": "2026-09-28", "source_preopen_state": "verified", "source_reported_pid_receipt": true, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-29.json", "verification_sha256": "a5be5799405901ed1acb112480b7639cc89b00f41eaf4ecc9326ac9f2971f171"} -->

## Family 직접 증거 상태

- source date: `2026-09-28`; next apply date: `2026-09-29`.
- direct source: `12/12`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `verified`; natural acceptance: `pending`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `source_gap` | `blocked` | `producer_contract_repair` |
| `scale_in_split` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `machine_entry` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `source_gap` | `blocked` | `producer_contract_repair` |
| `low_price_expansion` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `unsupported_scope` | `blocked` | `scope_contract_decision` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyScopeDecisionMainMechanisticEntry] main_mechanistic_entry 직접 family 지원 범위 계약 확정` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-28.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`scope_contract_decision`, comparison_status=`unsupported_scope`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_policy_selected_portfolio_economics_separate`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`natural_machine_policy_outcomes`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-28.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`terminal_path_not_evaluable`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-28.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_dispatch_or_parent_lineage_unclassified`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-28.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-28.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairPreSubmitDelay] pre_submit_delay 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/pre_submit_delay_tuning/pre_submit_delay_tuning_2026-09-28.json`.
  - 상태: family=`pre_submit_delay`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`pre_submit_delay_tuning`, closure_test=`exact_attempt_submit_clock_quote_cost_terminal_and_independent_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairScaleInSplit] scale_in_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-28.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-28.json)
  - 증거: runtime_summary_sha256=`f21c522c148290b45c43d2b145b4421c14618f7244d7976f723c3b10d8cda4f8`, source_artifact=`/home/ubuntu/KORStockScan/data/report/scale_in_split_order_plan/scale_in_split_order_plan_2026-09-28.json`.
  - 상태: family=`scale_in_split`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`scale_in_split_order_plan`, closure_test=`eligible_add_fill_terminal_clock_cost_and_independent_paired_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-28`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

- [ ] `[MachineNonentryOutcomeLineageNaturalAcceptance0929] 기계 비진입 후행가격·캡처 결속 자연 수용` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~21:40`, `Track: RuntimeStability`)
  - Source: [기계 비진입 후행경로 보완안](../proposals/machine-nonentry-outcome-lineage-remediation-plan-2026-09-29.md).
  - 완료 기준: 배포된 producer의 probe 결과 digest와 해시 검증 캡처를 attempt별로 대사하고, 프리마켓 `_NX`·정규장/통합 애프터마켓 `_AL` 완료봉 캐시의 source date·route·세션·생성 해시를 장후 `main_machine_policy` 영수증까지 확인한다. 동일 `BLOCK/RECHECK` 모집단에서 10/30/60분 커버리지·비용 결속·첫 도달과 source gap을 재측정한다.
  - 권한 경계: 코드·테스트 통과와 실제 릴리스/PID 소비, 자연 장후 수집, 날짜·표본 허들, direct family 운영 경제성 결속을 각각 구분한다. 결손을 0수익으로 대체하거나 정책 기준·주문 가드를 변경하지 않는다.

- [ ] `[EntryAiScoreAuthorityRemoval0929] 진입 AI Score 의 실시간 판단·장후 튜닝 권한 제거` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [기계 비진입 후행경로 보완안의 추가 범위](../proposals/machine-nonentry-outcome-lineage-remediation-plan-2026-09-29.md#추가-범위-보정되지-않은-진입-ai-score-의-판단장후-튜닝-권한-제거-open).
  - 변경 범위: 진입 `confidence` 유래 호환 `score`의 BUY/WAIT 경계·조건부 재평가·점수대 해제 권한과 장후 `score_recovery_observation` → `wait6579_ev_cohort` → `score_recovery_economics` → `operator_policy_succession`의 점수 기반 모집단·후보·승계 권한을 함께 제거한다. score가 없는 입력은 결손으로 남기고 역사적 영수증은 진단용으로 보존한다.
  - 코드 상태: 점수 독립 행동 표시, 원천·verdict 기반 재호출·사전제출 신뢰, 점수대 복구/브리지 퇴역, 장후 관찰·경제성·승계·백테스트 후보 차단을 구현했다. 리뷰에서 원주문 재조정 영수증·출처 결손·통합시장 매도 세션·보유 AI 입력 중복과, 점수 유래 목표가격·WAIT=50의 과거 호환 확률 잔류를 보완했다. 통합 영향 회귀 2,205건과 추가 표적 회귀 620건, Python compile·셸 문법·diff 검사·체크리스트 print-only parser가 통과했다. 불변 릴리스·PID·자연 장후 소비는 별도 확인한다.
  - 완료 기준: 동일 기계·compact verdict와 동일 신선 원천에서 AI Score만 달리해도 행동, 재판정 선택, 장후 정책 후보 및 PREOPEN 승계가 달라지지 않는지 생산자부터 소비자까지 확인한다. 새 점수 독립 경로는 기계 재판정 또는 기존 compact 보조판정, 정확 비용·holdout과 소유 정책 계약을 별도로 검증한다. 코드 리뷰와 표적 검증, 릴리스 선택, 실제 PID 소비, 자연 결과를 구분한다.
  - 권한 경계: 현재 선택 릴리스·운영자 lock·주문·provider·threshold·hard safety를 문서 변경만으로 수정하지 않는다. VETO/CAUTION, source gap, DANGER, broker/account/order/quantity/cooldown 가드는 유지한다.

- [x] `[PostcloseEodGatedScheduleAndMorningFinalization] EOD 이후 장후 계산 및 다음 KRX 영업일 아침 finalization으로 일정 조정` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~06:50`, `Track: RuntimeStability`)
  - Source: [운영 runbook](../time-based-operations-runbook.md), [장후 결과 검토 지침](../postclose-tuning-result-review-task-instructions.md), [runtime release routing](../runtime-release-routing.md)
  - 변경 범위: main/widget/machine-refresh/archive 모두 exact-date EOD terminal 이후 heavy work를 시작한다. Finalization은 effective date의 직전 KRX source date를 선택해 05:00 예약, 06:00 predecessor deadline, 06:50 종료 상한을 적용한다.
  - 완료 기준: EOD `completed|completed_with_warnings` + exact target/latest quote date + positive row count gate, wrapper/test 리뷰 통과, immutable selected release의 cron route 및 두 비활성 systemd consumer pin, active timer 보존, finalizer 06:50 상한과 07:20 PREOPEN scanner 전 30분 margin을 검증한다. actual main PID/order authority는 변경하지 않는다.
  - 배포 증거: selected release `db62ac287f783c8eed72344f5134680b3c118ed6`; cron `POSTCLOSE_FINALIZATION_0500` 및 `--resolve-effective-today` 검증, widget/machine systemd pin 및 timer active. 254개 표적 테스트 통과.
  - authority 경계: main PID `1252310`은 기존 `4263bc0c`에서 계속 실행 중이며 재기동하지 않았다. 새 schedule release PID 소비는 미확인이다. 첫 자연 EOD terminal·아침 finalizer 결과는 다음 운영 영수증으로 확인한다.
  - 권한 경계: resource guard를 약화하거나 source population/holdout/quality를 줄이지 않는다. 봇 재기동, 주문, policy/provider/threshold/safety 변경은 없다.

- [x] `[PostcloseCronEffectiveDateReceiptRepair0929] 05:00 finalizer·cleanup detector 날짜 결속 및 누락 모듈 반영` (`Due: 2026-09-29`, `Slot: INTRADAY`, `TimeWindow: 12:15~20:05`, `Track: RuntimeStability`)
  - Source: [9/29 error detection 영수증](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-09-29.json), [runtime release routing](../runtime-release-routing.md).
  - 원인: 9/29 effective date의 직전 KRX source date는 9/28인데 detector가 `target_date=2026-09-29` marker를 찾았다. 선택된 통합 릴리스에는 generation 검증 import의 소유 모듈과 finalizer 생산 경로도 빠져 있었다.
  - 코드 영수증: immutable 후보 `bbde9aa790ccc111444cce962bab8f6a892eadf6`에서 날짜·마감시각·9/28 사전선택 영수증 경계를 수리하고 generation 모듈·wrapper를 결속했다. 표적 75개 테스트, compile, `bash -n`, diff 검증을 통과했다.
  - 완료 기준: 승인된 전환 뒤 selector와 실제 bot PID가 같은 후보를 소비하고 새 error detection 영수증에서 `cron_completion`의 `no today marker` ERROR가 사라져야 한다. 9/28의 07:11 finalizer·08:28 cleanup은 `recovered_late`와 `historical_gap` 경고로 보존한다. 이후 source date의 marker·06:50 상한·generation 결속 결손은 계속 FAIL이다.
  - 적용 영수증: 사용자가 즉시 릴리스 선택·재기동을 승인했다. selector와 실제 PID `1299512`(12:32:59 KST 시작)는 모두 `bbde9aa790ccc111444cce962bab8f6a892eadf6`을 가리키며 release-set/cron routing, runtime policy bootstrap 검증을 통과했다. 12:33:12 KST 새 error detection 영수증의 `cron_completion`은 `warning`이며 두 `no today marker` ERROR가 사라졌다. 늦은 완료와 9/28 generation 미결속, 별도 `panic_sell_defense` 경고는 유지된다.
  - 권한 경계: 이 승인 범위는 수정 릴리스 선택과 main bot 재기동이다. 주문·provider·threshold·hard safety 변경 권한은 포함하지 않는다.

- [ ] `[AvgDownSharedReboundReceiptClosure0928] 물타기 공통 반등·정확 체결 복원·불타기 퇴역 수용` (`Due: 2026-09-29`, `Slot: INTRADAY`, `TimeWindow: 08:00~20:00`, `Track: RuntimeStability`)
  - Source: [구현계획](../proposals/avg-down-shared-rebound-receipt-and-pyramid-retirement-implementation-plan-2026-09-28.md), [9/29 코드 리뷰](../audit-reports/2026-09-29-avg-down-rebound-receipt-and-pyramid-retirement-implementation-review.md). 9/28 동일 ID owner의 후속 건이다.
  - 코드 완료 기준: 대우건설 `047040`/보유 `48376`의 사전검사 세부 blocker와 원천 시계, 최초 BUY 주문·체결의 재기동 후 검증 복원, ADD 차단·주문·체결·청산의 동일 보유 결속, PYRAMID 신규 판단·주문 불가와 과거 pending·SELL 정산 유지, 표적 회귀·리뷰를 확인한다. S15·VCP 신규 진입은 퇴역 상태를 유지하고 옛 custody만 복구·정산한다.
  - 운영 수용 기준: 선택 release·실제 PID 소비, 첫 자연 원천·투표·주문 또는 미주문·체결, `COMPLETED + valid profit_rate`와 정확 비용의 충분한 동일 보유 표본을 별도 영수증으로 확인한다. 코드 통과를 실주문 또는 증분 순익으로 간주하지 않는다.

- [ ] `[S5FIN05FinalDetectorGeneration0929] 최종 detector의 장후 원천 세대 수용` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [S5 결손](../audit-reports/2026-09-27-intraday-postclose-handoff-S5.md) `S5-FIN-05`, [9/29 S6 수리 보고서](../audit-reports/2026-09-29-intraday-postclose-handoff-S6-S5-FIN-05.md). 9/28 finalizer 07:11 DONE 뒤 strict·controller 세대가 08:25·08:26에 변경된 건을 별도 역사적 결손으로 보존한다.
  - 완료 기준: 새 자연 source date에서 `postclose_exit` 세 snapshot 논리 SHA·archive 선택, fresh controller/strict 세대, cleanup, 최종 detector의 결속된 DONE marker와 이후 detector PASS를 동일 세대로 검증한다. fixture 통과·선택 릴리스·실제 PID 소비·경제성은 각각 별도로 기록한다. 정규 장후·PREOPEN을 수리 검증 목적으로 다시 실행하지 않는다.

- [ ] `[ScalpSimRuntimeRetirement0929] 기본 scalp simulator 신규 런타임·장후 기본 실행 퇴역` (`Due: 2026-09-29`, `Slot: INTRADAY`, `TimeWindow: 10:00~20:00`, `Track: RuntimeStability`)
  - Source: 9/29 실제 `scalp_sim` 가상 보유와 `sim_post_sell` 최근 출력, [현행 기준](../plan-korStockScanPerformanceOptimization.rebase.md) §1/§5/§8.
  - 완료 기준: 신규 sim 진입·재기동 복원·sim 전용 WS 등록이 중단되고 장후 `--evaluate-sim` 기본 실행이 OFF인 코드를 리뷰·회귀 검증한다. 과거 sim 원천과 real post-sell/holding/exit custody를 보존한다. 선택 릴리스와 실제 PID 소비, 자연 `scalp_sim=0`, 다음 장후 단계의 skip 영수증은 별도로 확인한다.

- [ ] `[SamsungMainFixedWatchRetirement0929] 삼성전자 Main 고정감시 이관 및 시간대별 독립 기계 퇴역` (`Due: 2026-09-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [구현계획](../proposals/samsung-main-fixed-watch-and-time-machine-retirement-plan-2026-09-29.md).
  - 변경 범위: `005930`을 스캐너 없이 Main의 고정 WATCHING 기계판정 경로에 편입하고 총 감시 상한 안의 1칸·세션별 정확 WS route·출처/장후 결속을 보장한다. 오전·점심·오후 독립 기계의 신규 BUY, 기동 timer/preflight, 삼성 전용 장후/PREOPEN 후보 생산을 퇴역한다. widget 및 다른 episode의 독립 소유권과 과거 custody를 보존한다.
  - 코드 완료 기준: 재기동·세션전환·동일 종목/owner 충돌에서 중복 감시/주문 없이 Main 기계판정에 도달하고, `BLOCK/RECHECK` 후행 데이터와 `source_gap`을 구분하며, scanner 분모에 고정감시를 혼합하지 않는다. 독립 세 서비스의 신규 BUY와 재활성화 경로 0건, 기존 미결·보유 SELL/복원 경로 보존, 표적 회귀·코드 리뷰를 확인한다.
  - 운영 수용 기준: 적용 직전 broker/owner custody, 선택 release와 실제 Main PID·systemd/timer·WS 등록, 프리/정규/통합 애프터 세션별 자연 판정·주문/미주문·체결/terminal·비용 후 성과를 각각 대사한다. 기존 세 기계를 자동 롤백으로 재가동하지 않는다.
  - 권한 경계: 이 계획/체크리스트는 서비스 중단·재기동·실주문 승인이 아니다. 수동 veto, source freshness, broker/account/order/quantity/cooldown, provider, cap 및 hard safety를 우회하지 않는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:2775f343e6f7366231d5dc47531ef214841f1b1deb2fe07454da85b661983a27 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-28; 발행 2026-09-28; 적용 2026-09-29. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `1604b2662edf27ca68b91b6b13e3180cf6e8faf13ceb4bbaf0c2cea91b6a7819`; 정책 bundle `13e0a269e2f557cbb84f64ab3f9dba0cdf4ae7d4bdf747d6ab2bb9ada06b84ca`; consumer `beed5aa660f4ca1c77f2cfd6ea33171d3ce4229ac05a5e44b07d3f04536c15e1`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
