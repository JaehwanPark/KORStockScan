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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-02", "sources": {"entry_cancel_wait_policy": {"sha256": "f069e0758b9f9374157ebf53b2fe16f8b06f133306f971d0f422e7636ffb8c58"}, "entry_cancel_wait_tuning": {"sha256": "4732284c5d4131d2cfa28f18ece093d559c699110b55426a2fcba88202ab845c"}, "holding_path_vote_policy": {"sha256": "95e5caf57a53e25a932b135335c40cbd4e17dd5084c7a889b2880b7d22dc1717"}, "initial_quantity_refresh_stage": {"sha256": "4148079cd14bf2d513c1a1accd4a0da4988bc634ca3f9fa46e5512e8d2835d47"}, "runtime_approval_summary": {"sha256": "36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92"}, "stage_episode_policy": {"sha256": "e43dea07979e94f732e02c3618db81806fc33551e77eaada0b17f1497b957339"}, "stage_legacy_machine_report": {"sha256": "cf1d0718d2b112391d8c9aa950584f54dc63432e4aae8e806b573e73326e91d7"}, "stage_legacy_policy_approval": {"sha256": "b2611a8f4af6f641639118859b8dd1a7849246a358536df8d50b33d3122695c0"}, "stage_machine_attribution": {"sha256": "2d084c8ec82a71e75153bf9cc9562306e6ed0048b4726847eb814773396a2ea2"}, "stage_machine_timing": {"sha256": "759ef5307f5574980e2376245b0cc553ec696c6a4e699fb5adfa87d52e0b5fb5"}, "stage_main_auxiliary_policy": {"sha256": "ec3be09e09cdef7a8e8c6d01dce07e78411254b336c5c26001ce96f151366bd7"}, "stage_main_machine_policy": {"sha256": "977f9caa114a8cc3152031b91ae7e5a70d647504383936548bb686f8428e30b7"}, "stage_market_weakness": {"sha256": "fb0b4418b91630a850a08b8b33ac1f4bc00468c5dd5dabe8dc3b67dbea7c6bb6"}, "stage_outcome_labels": {"sha256": "c34d293b89d804a268ba5399e595c325eb705c46dae725a1081504834036a8ac"}, "stage_pre_submit_delay": {"sha256": "28c820701e1d91c36c63beba5c2acd42ea726847dce6baea15705e37f0c02f5f"}, "stage_research_allocation": {"sha256": "316eb7f0e4e542ae9a8594e391d7023fe5eb2bb3615a987d74202aeeb800ec28"}, "stage_research_capacity": {"sha256": "566481b0cf9c82810a8b5bc47d7793daa82848ebc994e8b4cae121003101edf2"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-06", "expected_state": "verified", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "43fcaac44792cb55fced0883b12216f2423468703bea2aee2765d01f01daa926", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-06.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-10-02", "source_report_sha256": "48bcc0e27ae62a0afaaeb85a943453b00915c28fee9c536c0df8827d3a23c3e9", "status": "estimated_provisional_published", "target_date": "2026-10-06"}, "manifest_content_sha256": "4399f577fb7245f69df9a381312b689d042b8fecafed7d9222b66b13313d11da", "manifest_env_sha256": "694a97763bbc121f2ed4284b15f5e877b94696542d65ad2f461a7bb6ad629d9a", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-06.json", "manifest_sha256": "0582ef3e33be0b9aae4223d63d015d90a7828f4c76d330f3b956d188fb26cc61", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "a9b67327196d5097727dd3a4d52d25aa2f8a7b3218d7bab8ad0d009318ee50f4", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "f069e0758b9f9374157ebf53b2fe16f8b06f133306f971d0f422e7636ffb8c58", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "3312caedf6c59cb32c016879b87f6bc2c7d866e456b308ad49f04c0c69e1c57a", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "1a6101bf1be3871299407ff0570d57178693efb382bf2825c1503de4ab10e4a3", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "a9b67327196d5097727dd3a4d52d25aa2f8a7b3218d7bab8ad0d009318ee50f4", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "05d2f165fca6733ba454f53b652cae4b50c3cc83bb6f17bd8b1d93a525758f05", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "cf3ee1f743708fb0643b02eb41072457309b74ad3782b205a34171475f258976", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "b8a10cf7d91509378c33f8d5d0fa840cdc822f53bb39257ec49557546ca9f82f", "valid": true}], "release_selection_sha256": "ef942eb2a5839c42fc88f6f51cc1255adb4852f944b931b6c8f10868be09e684", "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": "fbfc9dd6432e337b61ab63744216f32b80875bc6", "source_date": "2026-10-02", "source_preopen_state": "verified", "source_reported_pid_receipt": true, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-06.json", "verification_sha256": "3501ab9dd5f2cd6eba5163c75971f5bcfdb4cb8e805d3bef1314317a2aed3c11"} -->

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

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] 연속 반전 보조 입력·실제 AI 누적 승률·정규장 승계의 장후 통합` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 10/6 보완 연구 후~10/7 01:30 정책 확정 및 06:50 최종 인계`, `Track: RuntimeStability`)
  - Source: [통합 계획 §6](../proposals/continuous-reversal-machine-policy-nextday-plan-2026-10-06.md#6-보조판정-정책-확정과-장후-학습-전환), [보조 보완 연구·코드 검토](../audits/auxiliary-reversal-phase-repair-and-call-quota-review-2026-10-06.md).
  - 현재 완료: 372개 반전·추가 1,742회 실제 AI, as-of phase/진입가격/인용/schema 보완 및 대상 검증. 미완료: 정기 compact producer/최종 운영 prompt/12셀 dated publisher와 runtime 직접 연결. 기계 ENTER+provider_called trace 모집단은 새 family에서 사용하지 않는다.
  - 완료 기준: 전수 반전 원천·분리 라벨→같은 기계 부모의 실제 AI raw PASS 누적 승률→12셀 선택·무표본 동일 유형 정규장 payload/hash 승계→단일 writer/loader·새 machine/label dependency·summary 직접 소비. EV·손익비·최소 표본/일수·구 독립 holdout/기존 제출 보존을 새 채택 문턱으로 요구하지 않는다. 문구가 바뀌면 실제 해당 prompt/input/schema hash로 재비교한다.
  - 역할 경계: 이 ID는 보조 producer/consumer 통합을 소유한다. 최종 release·EOD 제외 장후 전체 재생성·strict/controller/PREOPEN/PID의 통합 종결은 `DirectFamilySourceRepairMainMechanisticEntry`에 결과를 인계하며 별도 전체 실행을 중복 시작하지 않는다. 무제한 호출 승인은 계수/영속 예약/실제 응답 보존을 없애지 않는다. 주문·수량·자본 cap·custody·operator veto·hard safety는 유지한다.
  - 이전 원천 기록 보존: source 10/2의 `exact_stop_distance_missing_or_invalid`, runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, [원 summary](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json), 원 `compact_auxiliary_paired_economic_2026-10-02.json`은 source_gap 감사 이력으로 보존한다. 옛 `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`를 새 반전 family의 채택/인계 조건으로 되살리지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-02.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-02.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-10-02.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] 연속 반전 기계·보조 12셀 전환·최종 배포·EOD 제외 장후 전체 재생성·10/7 정상기동 준비` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 10/6 22:03~10/7 06:50 및 07:32~08:05 소비 확인`, `Track: RuntimeStability`)
  - Source: [통합 전환·전체 재생성 계획](../proposals/continuous-reversal-machine-policy-nextday-plan-2026-10-06.md), [보조 보완 실제 호출·운영 quota 코드 검토](../audits/auxiliary-reversal-phase-repair-and-call-quota-review-2026-10-06.md), [전수 가격 반전 연구](../audits/continuous-price-reversal-zero-base-research-2026-10-06.md), [장후 중단 영수증](../../data/report/postclose_operator_stop/2026-10-06/operator-stop-receipt.json).
  - 현재 완료: 10/6 22:03:45 KST 장후 controller/tuning 그룹 중단·잔여 0 당시 확인. 원 wrapper 20:59:55 실패 및 기계 21:29:59 구 carry 보존. 보조 입력·프롬프트/schema 보완 후 372점에 추가 1,742회 실제 호출, 운영 AI 횟수 quota 영구 제거 코드와 대상 회귀 64 PASS. 현재 배포·새 정책 발행·전체 장후 재생성·10/7 prepared/PID 소비는 미완료다.
  - 권한/범위: 사용자가 보조 보완을 먼저 실행하고 계획 수정을 이어가도록 지시했으며 오프라인 연구 무제한 호출과 운영 AI 호출한도 영구 해제를 명시 승인했다. 운영 total/group cap=None, 예전 횟수 env의 자동 복원 금지. 계수·중복/오류 재시도/외부 provider rate limit과 broker/order/custody/manual/retirement guard는 유지한다. 최종 통합 배포·장후 전체 실행·기동 준비는 이번 보완 계획의 후속 실행이며 완료로 표시하지 않는다.
  - Acceptance: 기존 판정 행을 모집단으로 쓰지 않는 연속 반전 kernel→30분/+0.4%/soft -3% 라벨→삼성 시장 3셀·비삼성 시장×가격대 9셀의 기계 누적 승률 및 보조 실제 원 PASS 누적 승률→동일 runtime consumer. 보조 문구/input/schema가 달라지면 실제 해당 hash로 재비교하며 EV·보정 승률·최소 표본/일수·기존 제출 통과 보존 문턱은 추가하지 않는다. 프리/애프터 무표본은 같은 종목군·가격대의 정규장 payload/hash를 그대로 승계하고 로컬 승률은 null로 남긴다.
  - 배포/재생성 Acceptance: 계획 P1~P7. 전환 machine+aux code 최종 immutable release→source/publication 기준 10/6/effective 10/7 단일 generation으로 **EOD 제외 활성 장후 전체** 재생성. main embedded/등록 stage·machine refresh·tuning·archive·summary/tower/checklist·strict/controller/finalization·cleanup/final detector·bootstrap 포함. EOD updater는 재실행하지 않고 원 terminal/hash를 검증한다. OFF/퇴역 family 복원·구 성공 표지만 변경하는 재사용 금지.
  - 종료/소비: 06:30 목표·06:50 상한까지 전체 장후 complete와 exact-date prepared를 각각 확인, 07:32 owner/07:35 Main PREOPEN 및 07:55 정상 PID에서 code·기계/보조 hash·quota=None 소비 확인. 문서 최종 hash 고정 뒤 strict→controller→prepared. 미완료는 원 실패/미준비를 유지하고 검증된 정규장/기존 정책 carry 가능 여부만 따로 기록한다. 실제 주문·체결·손익은 별도 관측이다.
  - 이전 원천 기록 보존: source 10/2 `machine_operating_population_unbound`, runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, [원 summary](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json). 기존 completed-profit/EV 완료 문구는 새 기계정책 채택 기준으로 재사용하지 않는다. stable ID는 유지하며 `MainSubmitDroughtPathAcceptance1006`의 기존 경로 수리 자연 수용은 별도 보존한다.

- [ ] `[JejuEpisodeRetirementHpspAlteogenMainFixedWatch] 에피소드 8종목 퇴역·Main 고정감시 5종목 다음 기동 자연 확인` (`Due: 2026-10-07`, `Slot: PREOPEN`, `TimeWindow: 07:32~08:05 및 적격 정규장 자연 판정`, `Track: RuntimeStability`)
  - Source: [실행 계획](../proposals/jeju-episode-retirement-hpsp-alteogen-main-fixed-watch-initial-policy-plan-2026-10-06.md).
  - 범위: 제주·TYM·CJ CGV·영원무역·SK텔레콤·한세실업·NHN·카카오 27개 profile와 timer 54개 및 service instance 54개 퇴역; HPSP·알테오젠·주성엔지니어링을 기존 삼성·두산 Main spec/정책/주문 경로에 추가한다.
  - 권한: 사용자 계획 실행·반복 리뷰·배포·재기동 승인. 신규 3종목 초기 정책은 기존 비삼성 Main 부모로 지정하며 성과/표본 적격성 증명을 선행 조건으로 요구하지 않는다. 원천·세션·주문·수량·custody·operator veto·hard safety는 보존한다.
  - Acceptance: 종목별 fresh broker/custody/전체 날짜 intent flat, 27개 전용 profile·54개 timer 제거 및 54개 instance mask, 재등록/auto expansion 차단, 남은 31개 profile 원 정책 값 보존, 5종목 실제 metadata→기계 resolver 및 compact AI 역할, WS publication/연구 저장 독립 검증, 신규 3종목별 10개 후보 연구, reviewed release/정상 Main singleton 및 policy/hash 소비. 자연 source/판정/제출/체결/수익은 각각 별도 receipt; 해당 session 미관측은 `not_observed`로 인계한다.
  - 기존 `DoosanEpisodeToMainFixedWatch`, `FixedWatchSourceAndCleanupRepair1006`, `FixedWatchBudgetSummaryPostcloseAcceptance1006`의 별도 자연 수용과 원 장후 실패/원천 결손은 보존한다.
  - 10/6 실행 완료: 코드 `511664f3`/Main PID `169115` bootstrap·프로세스 건강 PASS, native 퇴역 timer 54개 제거·instance 54개 mask, 현재 31개 profile·186개 policy pin·cron 8개 PASS, 원 자료 34개 SHA 보존. 1,304개 통합·추가 router 90개 회귀 PASS; 신규 3종목별 10개 후보 연구는 source_gap 처분. [최종 실행 검토](../audits/episode-eight-retirement-main-five-execution-review-2026-10-06.md).
  - 잔여 자연 확인: 현재 신규 3종목은 `fixed_watch_nxt_eligibility_unproven` WAIT이며 기존 listing/eligibility 원천으로 확인한다. 10/7 owner PREOPEN의 현재 15종목 scope, 31개 episode 실 기동, 5종목 정확 admission→기계 hash/compact 역할·WS/원천을 확인한다. KRX 정규장은 NXT 대기를 적용하지 않는다. 해당 session 미관측은 `not_observed`이며 성과 사전 입증 또는 주문/threshold/guard 우회 조건을 새로 만들지 않는다.

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
  - Acceptance: A1 reviewed immutable release/PID와 당일 원 정책 해시 동일; A2 삼성·두산 exact 0B/0D freshness/epoch와 snapshot lock/publication; A3 두산 자연 기계판정 trace와 BLOCK/RECHECK의 Provider 호출 전 종료. 예산 원장 장후 수용은 아래 별도 owner로 연결한다. 짧은 관찰을 종일 결손 0/수익 증거로 대체하지 않는다.
  - A5 과거 완료 복구: [v2 증거 소비·최종화 복구 계획](../proposals/postclose-v2-evidence-finalization-recovery-plan-2026-10-06.md). 10/2 v2 선행 12개 원 code/output/input/prerequisite를 읽기 검증하고 summary만 현재 v3로 재계산한 뒤 strict/controller→native cleanup/detector→최종화 DONE을 확인한다. 15:05 predecessor 실패와 15:09 cleanup PASS는 보존한다. 15:40 재시도의 `future_preopen_generation_stale`는 기존 당일 정책 보존 handoff의 frozen 파일/권한/소비/current PID 검증을 장후 소비자에 연결해 보완한다. 적용일이 지난 과거 복구는 다음 날짜 PREOPEN을 생성하지 않는다. A5 결과는 원 finalization DONE 및 후속 detector `recovered_late` 영수증으로 확인하며 10/6 자연 장후/10/7 기동 수용을 대체하지 않는다.
  - A5 연결 수리: 독립 읽기 owner `eeccb1f4`에서 요약을 재생성했다. 삭제된 원 `designated-machine-policy-20261005-3d0e5106` 코드 root는 Git 원본으로 복원하여 기존 기계 단계 해시와 대조했고, 12개 선행 원 정책/입력은 유지했다. 16:04 native summary 완료와 정책 bootstrap 검증 PASS. 이후 당일 정책 보존 재기동 및 원 날짜 최종화 결과는 위 A5의 native receipt로 판정한다. 복원한 원 코드 root는 선행 정책 증명에 필요하므로 보존한다.
  - 당일 반영: af780d9b immutable/PID 13210, 15:13:54 bootstrap 소비 PASS, 원 정책·PREOPEN 5개 해시 동일. 두 actual target/current PID env resolver 모두 기계 primary. 15:15~15:17 121 frame 연결 정상, snapshot 최대 1.471초, 두 종목 0B/0D 3초 초과 0. capture lock 중앙값 201.732ms 및 CPU 한 core 100.53%는 그대로 공개한다. A1/A2 해당 창 PASS, A3 새 자연 machine 이벤트 미관측은 OPEN. 장후 companion 수용은 별도 owner에서 확인한다.

- [ ] `[FixedWatchBudgetSummaryPostcloseAcceptance1006] 장후 Provider 원장 요약의 자연 발행 결속 확인` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~06:50`, `Track: Postclose`)
  - Source: [수정·검증 증빙](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md), 위 `FixedWatchSourceAndCleanupRepair1006`의 A4 후속 수용을 이관했다. 코드·10/3 원장 복구·10/2 cleanup DONE 증거는 그대로 보존한다.
  - Acceptance: 10/6 native 장후에 Provider 예약/정산을 실제 발행하면 execution-date ledger/manifest/summary의 head/bytes·예산·가격·authority 결속을 확인한다. 미호출/OFF는 not_applicable이며 입증을 위한 Provider 재호출을 하지 않는다. 새 v3 stage→summary→strict/controller/finalization을 원 source/publication/effective date로 확인하고 과거 10/2 v2 성공을 새 producer 성공으로 합성하지 않는다.

- [ ] `[MainSubmitDroughtPathAcceptance1006] Main 제출 경로 수리의 다음 기동·자연 평가 확인` (`Due: 2026-10-07`, `Slot: PREOPEN`, `TimeWindow: 07:32~08:05 및 적격 session 자연 판정`, `Track: RuntimeStability`)
  - Source: [실행·리뷰](../audits/main-submit-drought-remediation-execution-review-2026-10-06.md), [계획](../proposals/main-submit-drought-priority-remediation-plan-2026-10-06.md).
  - 권한: 사용자 구현·반복 리뷰·배포·재기동 승인. 공통 WATCHING 평가 가격 gate 분리 및 등록 recipe 증거 계약 수리. A/B/C/D/E 비교 우위 없음으로 추가 전략 완화·정책값 변경 없음.
  - Acceptance: reviewed release/당일 bootstrap PID 소비, source-valid WATCHING의 목표가 위 평가→exact 기계 캡처, BLOCK/RECHECK provider 0, recipe ENTER_NOW→새 확인 fact/provider 원응답→동일 policy/source validator→기존 WAIT/probe 또는 BUY guard 경로. 정상 미통과와 원천 결손을 분리하며 적격 기회 없음은 `not_observed`; 실제 주문·체결·비용 수익을 코드 수리 조건으로 만들지 않는다.
  - 기존 `FixedWatchSourceAndCleanupRepair1006`, `DirectFamilySourceRepairMainMechanisticEntry`, `DirectFamilySourceRepairCompactAuxiliary`, `DirectFamilySourceRepairEntrySplit`, `JejuEpisodeRetirementHpspAlteogenMainFixedWatch`의 원천·장후·자연 수용 소유와 hard/source/account/order/quantity/cooldown/custody/veto guard를 보존한다.
  - 10/6 코드 수리·반복 리뷰 및 가격 manifest 소비 보완 완료: `fbfc9dd6`, Main PID `338586`/20:03 bootstrap PASS, 원 정책·PREOPEN 34개 SHA 보존, 에피소드 31개 profile·186개 pin 보존. 회귀 실행 1,877건 PASS(중복 포함); 454종목 가격 재계산 후 비삼성 현재 7/36승 대 D 16/102승, A/B/C/D/E 추가 완화 미선정. 현재 자연 KRX 정규장 recipe 수용은 `not_observed`, 다음 적격 session에서 해당 exact trace를 확인한다.
