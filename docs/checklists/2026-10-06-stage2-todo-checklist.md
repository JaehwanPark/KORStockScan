# 2026-10-06 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-02", "sources": {"entry_cancel_wait_policy": {"sha256": "f069e0758b9f9374157ebf53b2fe16f8b06f133306f971d0f422e7636ffb8c58"}, "entry_cancel_wait_tuning": {"sha256": "4732284c5d4131d2cfa28f18ece093d559c699110b55426a2fcba88202ab845c"}, "holding_path_vote_policy": {"sha256": "95e5caf57a53e25a932b135335c40cbd4e17dd5084c7a889b2880b7d22dc1717"}, "initial_quantity_refresh_stage": {"sha256": "4148079cd14bf2d513c1a1accd4a0da4988bc634ca3f9fa46e5512e8d2835d47"}, "runtime_approval_summary": {"sha256": "1a94a59a4b26620724e82a96872053f795f5c17cce37863ce07a761451e731f3"}, "stage_collector_recommendation": {"sha256": "35a090dd88aa69e3ca0fdcbe5d119f7e44e4a8453cf039f53cba465ac13b87fc"}, "stage_episode_policy": {"sha256": "e43dea07979e94f732e02c3618db81806fc33551e77eaada0b17f1497b957339"}, "stage_legacy_machine_report": {"sha256": "cf1d0718d2b112391d8c9aa950584f54dc63432e4aae8e806b573e73326e91d7"}, "stage_legacy_policy_approval": {"sha256": "b2611a8f4af6f641639118859b8dd1a7849246a358536df8d50b33d3122695c0"}, "stage_machine_attribution": {"sha256": "2d084c8ec82a71e75153bf9cc9562306e6ed0048b4726847eb814773396a2ea2"}, "stage_machine_timing": {"sha256": "759ef5307f5574980e2376245b0cc553ec696c6a4e699fb5adfa87d52e0b5fb5"}, "stage_main_auxiliary_policy": {"sha256": "ec3be09e09cdef7a8e8c6d01dce07e78411254b336c5c26001ce96f151366bd7"}, "stage_main_machine_policy": {"sha256": "977f9caa114a8cc3152031b91ae7e5a70d647504383936548bb686f8428e30b7"}, "stage_market_weakness": {"sha256": "fb0b4418b91630a850a08b8b33ac1f4bc00468c5dd5dabe8dc3b67dbea7c6bb6"}, "stage_outcome_labels": {"sha256": "c34d293b89d804a268ba5399e595c325eb705c46dae725a1081504834036a8ac"}, "stage_pre_submit_delay": {"sha256": "28c820701e1d91c36c63beba5c2acd42ea726847dce6baea15705e37f0c02f5f"}, "stage_research_allocation": {"sha256": "316eb7f0e4e542ae9a8594e391d7023fe5eb2bb3615a987d74202aeeb800ec28"}, "stage_research_capacity": {"sha256": "566481b0cf9c82810a8b5bc47d7793daa82848ebc994e8b4cae121003101edf2"}, "stage_widget_policy": {"sha256": "6751eed6783c61bef8fa5e60129a94d4852c6937bcdff895e78074190eb4bc8f"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-06", "expected_state": "verified", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "43fcaac44792cb55fced0883b12216f2423468703bea2aee2765d01f01daa926", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-06.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-10-02", "source_report_sha256": "48bcc0e27ae62a0afaaeb85a943453b00915c28fee9c536c0df8827d3a23c3e9", "status": "estimated_provisional_published", "target_date": "2026-10-06"}, "manifest_content_sha256": "4399f577fb7245f69df9a381312b689d042b8fecafed7d9222b66b13313d11da", "manifest_env_sha256": "694a97763bbc121f2ed4284b15f5e877b94696542d65ad2f461a7bb6ad629d9a", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-06.json", "manifest_sha256": "0582ef3e33be0b9aae4223d63d015d90a7828f4c76d330f3b956d188fb26cc61", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "a9b67327196d5097727dd3a4d52d25aa2f8a7b3218d7bab8ad0d009318ee50f4", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "f069e0758b9f9374157ebf53b2fe16f8b06f133306f971d0f422e7636ffb8c58", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "3312caedf6c59cb32c016879b87f6bc2c7d866e456b308ad49f04c0c69e1c57a", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "1a6101bf1be3871299407ff0570d57178693efb382bf2825c1503de4ab10e4a3", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "a9b67327196d5097727dd3a4d52d25aa2f8a7b3218d7bab8ad0d009318ee50f4", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "05d2f165fca6733ba454f53b652cae4b50c3cc83bb6f17bd8b1d93a525758f05", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "cf3ee1f743708fb0643b02eb41072457309b74ad3782b205a34171475f258976", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "b8a10cf7d91509378c33f8d5d0fa840cdc822f53bb39257ec49557546ca9f82f", "valid": true}], "release_selection_sha256": "3fbf97f5dcf66c201b96cbf2969446c797bdea0213311a0630c69d7ed7b561cc", "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": "e16ac48b8d6486adaf9e179a125d2aa6b76d8723", "source_date": "2026-10-02", "source_preopen_state": "verified", "source_reported_pid_receipt": true, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-06.json", "verification_sha256": "bd7995edcd37609d13f9a28ea615effe9a933987d116aed7cbbd9f2eacb28202"} -->

## Family 직접 증거 상태

- source date: `2026-10-02`; next apply date: `2026-10-06`.
- direct source: `10/10`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `verified`; natural acceptance: `pending`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `mixed` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `source_gap` | `blocked` | `producer_contract_repair` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`1a94a59a4b26620724e82a96872053f795f5c17cce37863ce07a761451e731f3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-10-02.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`exact_stop_distance_missing_or_invalid`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`1a94a59a4b26620724e82a96872053f795f5c17cce37863ce07a761451e731f3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-02.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`1a94a59a4b26620724e82a96872053f795f5c17cce37863ce07a761451e731f3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-02.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 후속 상세계획: [probe 체결 조건부 잔여 주문 경제성 재생 보완](../proposals/entry-probe-conditional-owner-replay-remediation-plan-2026-10-06.md). 사전 관측의 미확정 가격을 유지하고, 동결 context와 실제/CF 후속 원천을 결속해 typed 재생을 지원한다. 계획 작성 완료·구현 미실행이며 기존 완료 기준과 OPEN owner를 유지한다.
  - 실행 순서: 전수 source census → 조건부 계획·context 계약 → 순수 native 계산 parity → 실제 실행 복원 → causal CF·운영 경제성 → consumer·리뷰·회귀. 표본/원본 결손은 해당 scope의 `not_observed`/`source_gap`으로 남기며 성공 보존율 veto나 주문·예약·API/provider 권한을 추가하지 않는다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`1a94a59a4b26620724e82a96872053f795f5c17cce37863ce07a761451e731f3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-10-02.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`1a94a59a4b26620724e82a96872053f795f5c17cce37863ce07a761451e731f3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-10-02.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_operating_population_unbound`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`future_exact_changed_decision_owner_replay_and_completed_profit_rate`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 장중 원천 복구: [058610 preflight 계약 삭제·복구 점검](../audits/main-machine-preflight-source-gap-058610-recovery-2026-10-06.md). 현재 PID pin의 7/23 보호 계약이 11:59 정리 때 삭제돼 계산 전 trace 83건을 차단했다. 12:22:57 archive 동일 bytes/SHA/원래 mtime 복원 뒤 같은 PID의 자연 assessed 13건을 확인했다. 이는 과거 가격 재학습이나 주문 실패 수가 아니다. current dependency receipt를 기존 정리 보호 참조에 연결했다.
  - 계측 인계: 사용자 승인 후 287 PASS 및 자연 수용에서 발견한 빈 ID 문자열 처리 후속 162 PASS를 거쳐 `abb71f8d`를 배포했다. 12:51:20 graceful restart 뒤 Main singleton PID `4100807`의 새 root/commit·bootstrap·intraday consumption PASS. 당일 정책/PREOPEN 5개 SHA 불변, 새 자연 probe 22개 중 assessed 3개·WS first-data 44개 및 heartbeat·broker/custody gate 확인. 삭제된 context OFF marker도 archive 동일 SHA로 복원해 기존 PID/새 PID 19-key overlay 일치와 정리 보호 참조를 검증했다. 별도 source age/필수값 결손·coverage 경보, 058610 새 assessed 미관측 및 기존 장후 cleanup failure는 유지한다. 기존 장후 경제성 완료 기준을 source 복구·배포만으로 체크하지 않는다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Main 원천·판정 계약 보완 배포

- [x] `[MainMachineSourceRepairDeploy1006] Main 기계 원천 갱신·증거 해시·probe 관측 시각 수정 배포 및 재기동` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 사용자 승인 후 당일`, `Track: RuntimeStability`)
  - Source: [원천 갱신·증거 해시 보완](../audits/main-machine-source-refresh-and-admission-hash-remediation-2026-10-06.md), [018880 관측 시각·제출 경로 점검](../audits/main-entry-pre-ai-probe-clock-and-018880-lineage-audit-2026-10-06.md), [배포·기동 수용 기록](../audits/main-machine-source-remediation-deployment-review-2026-10-06.md).
  - 권한: 사용자가 반복 코드리뷰·보완 및 배포·재기동을 명시 승인했다. 기존 기계/보조 정책, hard safety, 원천 freshness/conflict, broker·수량·cap·custody·operator lock을 보존한다.
  - 코드 gate: 관련 12개 module 1,143 PASS, 실제 WATCHING handler source wait 3 PASS. 재기동 fresh gate에서 과거 holding vote v2 summary의 소비 호환성 결함을 발견해 보완, 추가 181 PASS 및 실제 기존 PID/bootstrap 재검증 통과. compile·Ruff·shell·diff 확인. 미확정 probe 체결가격의 경제성 재생은 미지원으로 유지한다.
  - Acceptance: fresh KRX/NXT broker inventory·미체결 및 로컬 custody, immutable release·rollback, 당일 정책 보존 handoff, singleton 새 Main PID/root·policy/bootstrap receipt, WS first-data·heartbeat와 시작 후 오류/중복 주문 확인. 자연 source·submit·fill·비용 수익은 별도 증거다.
  - 완료: 통합 코드 `c5297da9`와 보유 정책 소비 호환성 보완 `1667abb9`를 배포했다. 11:47:53 graceful restart 뒤 Main singleton PID `4071430`, 새 root·bootstrap·intraday consumption PASS, 정책/PREOPEN 5개 hash 불변. KRX/NXT 잔고·미체결 및 로컬 활성 custody 0. WS first-data·heartbeat·process health PASS. 설치 Episode 122개 route·366개 policy pin과 cron 8개 경로 검증, 웹·체결 통보 active PID 새 root 확인. 격리/비활성 Episode 상태는 유지했다.
  - 별도 상태: 자연 원천 복구 retry·실제 제출/체결·비용 수익은 이 기동 확인으로 입증하지 않는다. 시작 중 `cron_completion`은 05:03 저장소 정리의 `micro_reversion_storage_status=partial_failure` 및 그에 따른 `postclose_finalization cleanup_failed`를 그대로 보고했다. Main process health PASS와 전체 장후 DONE을 구분하며 원 실패 receipt를 보존했다.

## 위젯 전체 제거 인계

- [ ] `[WidgetFullRetirement1006] 위젯 런타임·장후·관측·연구·화면/API 전체 제거` (`Due: 2026-10-06`, `Slot: MANUAL`, `TimeWindow: 실행 중; 외부 제거·자연 장후/기동 후 종결`, `Track: RuntimeStability`)
  - Source: [위젯 전체 제거계획](../proposals/widget-full-runtime-postclose-retirement-plan-2026-10-06.md), [정적 의존성·설치 현황](../../tmp/widget-full-retirement-planning-20261006/inventory.json).
  - 상태: 서버 코드·배포·정리 검증 완료. 커밋 `b53a3835`, 대상 3,382 PASS/skip 1, 전용 unit 11개 mask, API 404, 설치 Widget dispatch 0, 정책 pin 366개 검증. 전용 데이터 2,668개와 임시 릴리스 삭제 후 약 639MiB 확보. [최종 감사](../audits/widget-full-retirement-execution-review-2026-10-06.md). Main/에피소드 새 코드·episode fact producer의 실제 소비, 10/7 dated 정책 생성은 자연 장후/기동 receipt로 확인한다.
  - 외부/자연 acceptance: Windows는 운영자가 직접 제거 예정. 실제 제거 확인과 새 장후·다음 기동 receipt 전까지 G4/G5를 완료하지 않는다.
  - 범위: 자동/수동 위젯 주문, 가격 API·Windows client, collector/Telegram, 종목·보조 연구와 정책 발행, unit/timer/installer, 장후/PREOPEN/감시·배분, 전용 cache/data 정리.
  - 선행조건: 신규 widget BUY/ADD·수동 진입 차단 뒤 fresh broker/custody 대사; 잔여 노출 종결 또는 승인된 정확한 인계. 당시 로컬 수량 0은 broker flat 증거가 아니다.
  - 완료 기준: 계획 G0~G5. active 위젯 실행·필수 의존성 0, 공통 계산 이관과 Main/에피소드 회귀 통과, archive/삭제 manifest, 외부 Windows 확인, 자연 장후·다음 기동 증거를 구분한다.
  - 권한 경계: 이번 제거 실행은 승인되었다. 청산 주문·소유권 재분류를 추정 승인하지 않으며 Main 삼성 고정 감시·에피소드·공통 토큰/WS·order registry와 hard safety를 보존한다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```



## Episode 원천 전이 인계

- [ ] `[EpisodeCaptureSequence1006] Episode 동일 시각 상태 전이의 원천 sequence 소비 인계` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 09:00~20:00`, `Track: SourceQuality`)
  - Source: [10/2 원천·의미 복구 감사](../audits/postclose-semantic-source-monitoring-2026-10-02.md). 기존 active custody 원천 보완이며 OFF 신규 연구 복원은 아니다.
  - Acceptance: producer의 profile/day/instance sequence·이전 observation SHA와 소비자의 정확 predecessor 검증, same-clock 전이·append 유실·다른 PID/generation·날짜 reset 회귀를 유지한다. 기존 raw106건 conflict는 재라벨링하지 않는다. source-only 코드378 PASS와 Episode 실제 service pin/PID 소비를 구분하며, 별도 배포 권한 전에는 해당 매매 service pin/기동을 변경하지 않는다. 자연 해당 source가 없으면 not_observed로 인계한다.



## Cancel wait 실행 세대 인계

- [x] `[EntryCancelWaitSourceReconciliation1002] cancel wait 새 계약 실행 세대·직접 소비 수용` (`Due: 2026-10-06`, `Slot: PREOPEN`, `TimeWindow: 00:10~07:35`, `Track: MainEntry`)
  - Source: [취소 대기 원천 대사·승계·의미감시 보완구현 계획](../proposals/entry-cancel-wait-source-reconciliation-remediation-plan-2026-10-02.md). 사용자 추가 구현·반복 리뷰 지시를 반영했다. [구현 리뷰](../audits/entry-cancel-wait-source-reconciliation-implementation-review-2026-10-02.md)는 작업본 코드와 격리 시험의 근거이며 실제 새 장후 세대·배포/PID 수용은 별도다.
  - Acceptance: 당일 verified empty와 9/30 실제 제출 2건의 대사 미완료를 분리한다. 승계 이벤트만 남은 날짜까지 원 source/hash를 검증하고 미분류·registry 미등록·terminal/cost 결손을 durable ledger에 보존한다. 미검증 과거의 확정 미해결 count는 null이며 EV/후보를 합성하지 않는다. 공통 semantic projection→summary→실제 tower 전용 필드→다음 checklist→strict 및 artifact freshness→기존 notification filter/mock 도달을 대조한다. 정상 carry·미도래·세대 전환 오탐과 중복 알림을 막고 현행 대기시간/scope·별도 순차 timeout owner·hard safety·정책/매매 권한을 보존한다. 반복 리뷰·표적 검증 후 코드와 자연 세대 수용을 구분한다. 복구 불가 항목은 artifact/owner/closure test와 함께 blocked로 남기고 같은 입력을 반복 재생하지 않는다.
  - 계획 수용: 현재 배포본 관련 60 PASS와 별도로 과거 미분류 승계 누락·원천 검증 호출 0회를 격리 재현했다. 장후 감시 전용 검사/알림 stage 허용 및 실제 tower 발행 누락까지 계획에 포함했다. 계획은 link·단일 owner·authority·diff·print-only parser로 검증하며 진행 중 장후 recovery/source 세대·불변 실행 코드·selector를 교체하지 않는다.
  - 구현 검증: event-only 원천 재검증·부분 cohort quarantine·forward 거래일 봉인 대사·source-only custody·null/0·정확 terminal/cost·64MB metadata 예산/세대 cache를 보완했다. 실제 direct tower/checklist 발행 누락을 추가 발견해 report/policy receipt와 단일 block을 연결했다. 공통 validator/summary/scoped strict·artifact freshness/장중 표시·알림 mock·자정 분석일 전파를 반복 리뷰·보완했고 최종 영향 11 suite 565 PASS·compile PASS다. 검토 범위 미해결 코드 finding 0.
  - 추가 리뷰(10/3): 완료 run의 원 날짜 감시 누락, 완료 소비 불일치의 영구 pending, pending 소비의 잘못된 알림 회복을 재현·수정했다. 읽기 중 파일/원천/native 교체와 오류, 알려진 reuse 결함의 보존도 보완했고 30개 회귀를 추가했다. 최종 11 suite 595 PASS·compile PASS, 검토 범위 미해결 코드 finding 0. 초기 565 PASS 이력 및 운영 수용 경계는 유지한다.
  - 이전 미수용: 10/3 01:30:24 KST에는 선택본63936cf1과 작업본8개 파일이 달랐고10/2 보고서에 새 계약이 없어 not_observed였다. 해당 snapshot과565/595 PASS 이력을 보존한다.
  - 운영 세대 수용(10/3): 승인된 통합 배포 뒤 고정10/2 원천으로 새 report/policy를 발행했다. report4732284c·policyf069e075, 발행10/3·적용10/6, 대기시간90/120/600/1200초 유지다. controller의 tower 생성 누락을 보완한 선택본a17bd6d2에서 summary→실제 tower→checklist→strict와 의미감시 소비가 모두 verified·finding0이다. 관련322 PASS 및 재생성83 PASS, 실제 receipt는 `tmp/postclose-outcome-readiness-closure-20261003/cancel-native-consumer-verified.json`과 [전체 리뷰](../audits/postclose-outcome-readiness-closure-review-2026-10-03.md)에 보존한다.
  - 인계 범위: 새 계약/native last consumer 수용을 완료했다.9/29·9/30·10/1의 원 producer census 부재와 과거 확정 미해결 null은 `DirectFamilySourceRepairEntryCancelWait`로,10/6 당일 bootstrap/PID는 `DirectFamilyPreopenPolicyHandoff`로 유지한다. 현재 완료는 미래 PREOPEN/PID·경제성 승인을 뜻하지 않는다.

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:34de120a64b3d704c1c2ce26beabb215f943af293946c91701f778e14e581b97 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-10-02; 발행 2026-10-03; 적용 2026-10-06. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `53ad2ba5afd959005a3f7dc6684b9174be36e8d2459f8c8bfcfc6b72fb4dd8d0`; 정책 bundle `3c500f6ae2222ecb607048213b6ae4fda27f60cbb703af1eb9f76789b0026b99`; consumer `0a82074b01c78b3af7e8e4f6432902ee542d9f3ffc494433fa9d186aa54bde7d`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:d5de01e3aeda7a31dc1f8cd01b0c0f50323c01126f06ea8c34aa8147cd8edbaa -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-02; 발행 2026-10-03; 적용 2026-10-06. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "d1534bc0784f7a1f0a0e580d48eea0d63282a6cdf40d97d00c46fb717d04ef0b", "runtime_effect": false, "source_date": "2026-10-02", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->


## 두산 Main 고정감시 전환

- [ ] `[DoosanEpisodeToMainFixedWatch] 두산 에피소드 제거·Main 초기 정책 지정의 PREOPEN 전환` (`Due: 2026-10-07`, `Slot: PREOPEN`, `TimeWindow: 07:00~08:00`, `Track: Runtime`)
  - Source: [전환 계획](../proposals/doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md), [구현·검토 증빙](../audits/doosan-main-fixed-watch-implementation-review-2026-10-06.md).
  - 사용자 기준: 초기 정책 적격성 입증 불필요. 두산 초기값은 현재 Main 비삼성 정책 지정; 연구 source_gap/표본 부족은 지정 보류 사유가 아니다. 실제 원천·owner·broker·수량·주문·수동 veto guard 유지.
  - 구현 상태: workspace 3 profile/6 timer 및 override·dispatch 제거, symbol/owner 재등록 차단, Main 두 종목 고정감시와 WS exact item 승계, all-date intent 확인, 원래 policy hash 유지한 archive projection과 공용 원천 기록기 수리. 연구 25건 중 native lineage 결손 24·다른 scope 1, native 고정감시 0; 신규 수익성 증거 아님.
  - Acceptance: G0 fresh broker/원장 flat·미확정 intent 0; G1 installed 전용 timer/drop-in 제거·퇴역 instance mask; G2 새 코드와 rollback에 episode BUY 0; G3 종목별 고정 target/slot/상태 분리; G4 exact 0B/0D→quote→판정 source gate; G5 초기 지정과 후속 연구 구분; G6 exact-date owner/PREOPEN·release·PID·자연 기동 receipt. 코드 PASS를 설치 삭제/PID/실제 수익으로 대체하지 않는다.
  - 당일 전환: 14:23 native broker/원장/미확정 intent 0 재확인 후 timer 6개 삭제·instance 6개 mask 및 terminal 퇴역 receipt 발행. 14:24 Main 새 release/PID bootstrap PASS, 삼성·두산 독립 고정 target와 exact 신규 0B/0D 확인. 후속 mask 해석·installer priority·control receipt 권한 수리를 반영한 최종 d0a539ab/PID 4146183에서 14:33 bootstrap·실제 소비 PASS. 116 route/348 policy pin과 cron 8개 확인, 최종 139 PASS. 58-profile 소비 호환성을 위해 다음 template 시작 code를 맞추되 다른 종목의 현재 active PID·정책 값은 유지했다.
  - 후속 권한/리뷰: 사용자가 배포·재기동 승인. 122 PASS 추가 리뷰로 retiring/unknown order process만 차단하며 검증된 다른 종목 에피소드·Main 소유자는 유지한다. 당일 기존 owner/PREOPEN/bootstrap을 보존하고 episode BUY guard만 영구 제외한다. 다음 PREOPEN에서 Main·수동 owner만 발행한다.
  - Next: 당일 설치·Main code handoff/PID/자연 source는 완료. 10/6 native 장후 source→strict/controller→10/7 준비·10/7 owner 활성화는 예약 chain의 후속 수용이며 미래 완료를 추정하지 않는다. 기존 log_rotation_cleanup/postclose_finalization 실패·episode failed 3개의 별도 원천 상태는 성공으로 덮지 않는다. 기존 custody 자동 이관·청산 주문·다른 에피소드 재기동 없음.

## 고정감시 원천·정리 후속 보완

- [ ] `[FixedWatchSourceAndCleanupRepair1006] 삼성·두산 기계정책 연결과 WS 원천 지연 보완의 자연 수용` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 15:10~20:00`, `Track: Runtime`)
  - Source: [결함·수정·정리 복구 증빙](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md).
  - 사용자 권한: 확인 결함 수정/리뷰 및 기존 cleanup_failed 복구. 두산 배포·재기동의 기존 승인 범위에서 정책 보존 후속 handoff; 새로운 정책·주문·원천 age/cap/read budget 변경 없음.
  - 코드: fixed symbol별 기계 owner 연결, dashboard 출력 window만 lock 안 동결, 단일 episode fact worker 분리, capture clock 보존, 예약/정산과 같은 lock 안 Provider summary 발행. 관련 642 고유 pytest PASS, compile/diff/parser 확인.
  - 정리 완료: 원장 36개 기록·manifest 원본 유지, 요약 복구 Provider 0; 15:09:46 target 10/2 네이티브 cleanup DONE, storage·compression·data failures 0. 과거 FAIL을 보존했다.
  - Acceptance: A1 reviewed immutable release/PID와 당일 원 정책 해시 동일; A2 삼성·두산 exact 0B/0D freshness/epoch와 snapshot lock/publication; A3 두산 자연 기계판정 trace와 BLOCK/RECHECK의 Provider 호출 전 종료; A4 다음 native 장후의 새 예산 원장 companion 결속. 짧은 관찰을 종일 결손 0/수익 증거로 대체하지 않는다.
  - 별도 상태: 10/2 전체 finalization 복구는 v3 소비 계약에 대해 v2 선행 terminal인 `predecessor_terminal_failure`; cleanup PASS와 혼동하지 않는다. 퇴역 Widget 복원·과거 성공 합성·다른 episode 재기동 없이 10/6 native v3 장후 chain에서 확인한다.
  - 당일 반영: af780d9b immutable/PID 13210, 15:13:54 bootstrap 소비 PASS, 원 정책·PREOPEN 5개 해시 동일. 두 actual target/current PID env resolver 모두 기계 primary. 15:15~15:17 121 frame 연결 정상, snapshot 최대 1.471초, 두 종목 0B/0D 3초 초과 0. capture lock 중앙값 201.732ms 및 CPU 한 core 100.53%는 그대로 공개한다. A1/A2 해당 창 PASS, A3 새 자연 machine 이벤트 미관측/A4 다음 장후 예산 companion 수용은 OPEN.
