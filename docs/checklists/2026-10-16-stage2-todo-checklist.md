# 2026-10-16 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-15", "sources": {"entry_cancel_wait_policy": {"sha256": "15f81d9b8a37802ca2acf02f9a9e3cf07eeaf448d55ccb0f43ff50f8163b6948"}, "entry_cancel_wait_tuning": {"sha256": "34642d91df551b625536d20d843720492e5f0602913b85c2441d014675fede1d"}, "holding_path_vote_policy": {"sha256": "18046d934e68ef5399ea5da70a05d85ecf506ef7f21ce394dd739b664fafa364"}, "initial_quantity_refresh_stage": {"sha256": "e77ce2dcbe3514efb7858c42ffd47ac09bb0bac9b27237c6a790ef3ea77ee996"}, "runtime_approval_summary": {"sha256": "df8d5d533c5c9d374bbd9152b2b7b5d636c7d487291464a4b0130937bc5cf19d"}, "stage_legacy_machine_report": {"sha256": "e01d25807936044402cd31ef1591dde850af775083e0c843d16706f9b59c57d5"}, "stage_main_auxiliary_policy": {"sha256": "47bab59daa174cb61ea0cdfa3512a501d99667f64f9c176fe3af8d78c2595c1e"}, "stage_main_machine_policy": {"sha256": "0f159fe256daeaec7fdc597190693ea97a9c3f3552a369adc40eabdea6d71a96"}, "stage_main_stop_confirmation": {"sha256": "ead9bdc4112d120a854b654fa75b855473d6efc53ef99811a51fedf81b3875e3"}, "stage_outcome_labels": {"sha256": "e6e6942543a583a003ebb7a488cf6972b81bdd2cd67841bc9bebf2bf4818eae5"}, "stage_pre_submit_delay": {"sha256": "0a46a1667e53ea2654fefd3966c0187ba972e4287254e9ffe340c11c0815d26d"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-16", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "c7a85d7db1c77cc882e167b1c227a768f08e5055f60a1da57b61829d271dcb33", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-16.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-15", "source_report_sha256": "4641f73710ee5a7307fe31b5bb9ee67d4286a3d600ef63ed228a94af5570891d", "status": "verified_incumbent_carried", "target_date": "2026-10-16"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-16.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "b1d9518d416ff623687daad4ceafed3534970e7a805c3644d591c5a38192bf46", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "15f81d9b8a37802ca2acf02f9a9e3cf07eeaf448d55ccb0f43ff50f8163b6948", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "a1da51594cdbd9fc9fa204b0b6222ca2259bed616a1e82cb7cfa8773f0199d0b", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "b1d9518d416ff623687daad4ceafed3534970e7a805c3644d591c5a38192bf46", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "75735c8dfc25af4bbc8ae1d12a839933a22a9712cb7302436440bbe4ac738f41", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "e09b65d145d38c0ac585b2899ea5415ebf6fd3fa567a9285b274dac0ccf31d3c", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "a39b58ba143f61bff59f219db17d76ba5c1f5f05b5b87acb9ee369e197fe4c80", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-15", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-16.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-15`; next apply date: `2026-10-16`.
- 아래 상태는 summary `df8d5d533c5c9d374bbd9152b2b7b5d636c7d487291464a4b0130937bc5cf19d` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
- direct source: `9/9`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `initial_quote_timing_policy_published` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `cumulative_winrate_selected` | `verified` | `preopen_policy_handoff` |
| `compact_auxiliary` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-16`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-15.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-15.json)
  - 판정 기준: source_date=`2026-10-15`, apply_date=`2026-10-16`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=verified); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=09d592da2dc7c980401cd4999ecfaad2d306d85d89a5c8f7c6fa5cdc0fd0993d, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-16`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-15.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-15.json)
  - 증거: runtime_summary_sha256=`df8d5d533c5c9d374bbd9152b2b7b5d636c7d487291464a4b0130937bc5cf19d`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-15/auxiliary.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-15`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-16`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-15.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-15.json)
  - 증거: runtime_summary_sha256=`df8d5d533c5c9d374bbd9152b2b7b5d636c7d487291464a4b0130937bc5cf19d`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-15.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`bounded_reconciliation_metadata_required`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-15`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-16`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-15.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-15.json)
  - 증거: runtime_summary_sha256=`df8d5d533c5c9d374bbd9152b2b7b5d636c7d487291464a4b0130937bc5cf19d`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-15.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-15`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:b259d8ff72490cd8ff4293422d15c19e6a8834c8cf024f30f3619522fffab2e6 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-15; 발행 2026-10-15; 적용 2026-10-16. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": "since_checkpoint_dispatch_continuity_missing", "known_open_count": null, "status": "unknown"}, "daily_state": "source_gap", "daily_submitted_parent_count": null, "daily_zero_is_verified": false, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "8b488745b882ae770c74920c1511ae4c2d20b96ea7b848cc394a478b90a8a3a8", "research_evaluation_status": "model_unvalidated", "runtime_effect": false, "source_date": "2026-10-15", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->

## 전일 미종결 owner 인계

원 Acceptance·이력을 보존한 운영 인계다. Due만 다음 거래일16로 이관하며 source15의 관측·정책 날짜를 바꾸지 않는다. 같은 ID의 자동 OPEN은 중복 생성하지 않는다.

- [ ] `[MainStopLossRetirementRuntimeTuning1010] holding_vote 정책 생성 코드·원천 세대 계약 검증` (`Due: 2026-10-16`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`holding_vote`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_date=`2026-10-14`, artifact=`/home/ubuntu/KORStockScan/data/report/monitor_snapshots/holding_exit_observation_2026-10-14.json`, report_sha256=`5eb9158585c4f460d8f2c4c873a1600bd1e805e5a8495a2b51eb636dca5efb39`.
  - 세대 결속: source_generation=`1609973c820643368a9465903fcf1b5f0c284c28eb98c744b4ae6360265921a5`, code_sha256=`b2087e97e70fc145620d3440c4fddafd633ab8e45d3aa492fffec17a7b04bcab`, contract_sha256=`753ea75c3470866f6e56fad1a50b3fa5cc3c46bac5e114061fd8e176905004ff`.
  - 완료 기준: repair_owner=`MainStopLossRetirementRuntimeTuning1010`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.

  - 10/15 검증 경고 보완: native 원 보고서·정책 봉인을 유지하고 현재 코드의 실제 fixture 시험/영수증을 별도 검증한다. 코드 capability의 보충 소비와 source/sample/경제성 수용은 분리하며 이 OPEN owner는 원 수용 기준을 유지한다. [통합 수리·실제 영수증](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.

- [ ] `[PostcloseStructuralPolicyCompletion1011] rising_missed 정책 생성 코드·원천 세대 계약 검증` (`Due: 2026-10-16`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`rising_missed`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_date=`2026-10-14`, artifact=`/home/ubuntu/KORStockScan/data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_2026-10-14.json`, report_sha256=`246826488e17a7e4a7f2972e4eac79f84fd329b0eafad515301d028ca0bb48c8`.
  - 세대 결속: source_generation=`2fabb9f84793363a4c81b3b584a9aa4878c86208db13a69ebc4f036d8e21d1b4`, code_sha256=`dfe2d56deef10ebaf4f2aa6e3edd6215f769d08ba8ac123808459c2cc8fb720f`, contract_sha256=`2f50be1eb4ba77d48330b4d4ae3356bcb04fb4cfe2904cdaf1ab0557d45f4912`.
  - 완료 기준: repair_owner=`PostcloseStructuralPolicyCompletion1011`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.

- [ ] `[MainMarketWeaknessPostcloseObservation1008] 압축 원천·native 판정 연결·누적·약세 조정 후보 보완` (`Due: 2026-10-16`, `Slot: POSTCLOSE`, `TimeWindow: 검증된 수리의 후속 배치·자연 수용; 실제 연구는 21:40~익일 05:40 허용 슬롯`, `Track: RuntimeStability`)
  - Source: [10/14 구현 리뷰](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md), [10/13 결함보완계획 WR0–WR5](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md), [원 MW0–MW6·구현/배포 이력](../proposals/main-market-weakness-observer-repair-and-postclose-research-implementation-plan-2026-10-08.md), [기존 stable ID·Acceptance](2026-10-09-stage2-todo-checklist.md).
  - 범위: 10/14 사용자 승인으로 WR1~WR4 작업본 구현·반복 코드리뷰/수정을 수행했다. gzip-only reader/native 연결·확인 latch/누적/phase/typed 후보/안내와 설정 재결속을 구현했다. 실제 배치·예약 재결속·원천 재계산·실발송은 후속 수용이다. 추가 장중 hook·로깅·metadata·파일 조회/계산·queue/thread·API/AI 호출은 0, 기존 보조 패턴연구·정책/주문·Main/manual custody·퇴역 경계는 보존한다. joint/지연 개선 작업의 구현·배포 승인을 전용하지 않는다.
  - Acceptance: 기존 MW1 회귀·선택 observer 자연 소비 경계를 보존한다. 실제 schema/선별 전 census·gzip/원본 alias·bounded decode·effective listing 검증, 원 event/attempt/hash/ask/feature/label binding·결손 U, A/B/C/U·미래 join/TTL300·지연60/180·W/F/U 공통 분모·origin/중복 분리를 검증한다. 같은 관련 정의만 날짜 간 누적하고 실제 변경은 분리한다. 기계 지원 수치 축/미지원 사유와 보조 PASS 이후 CF를 구분하며 후보 합계 최대6·고정1,000회 안정성/U 민감도를 유지한다. 최대9회·야간 총 예약600초/worker1/512MiB·자식 회수·crash/delta0, optional code/calendar rebind와 terminal→누적→후보→관리자 Telegram 의미 ID/receipt·정정/uncertain→night summary를 검증한다. 연구는 strict/PREOPEN·기동 비차단이며 95% 보장·정책 자동 적용·주문 권한은 없다.
  - 리뷰 보완 수용: gzip-only 날짜 discovery→pending→실제 reader까지, 잔여 budget/CRC·hard kill 뒤 prefix 반복 억제·daily/cumulative/notification phase 재개를 검증한다. 2회 활성/3회 회복 확인 latch를 primary로 두고 raw 진단·실제/재구성 근거를 분리한다. 기계/보조 kind별 K/R/A/N 공통 분모·추가만 있는 후보·U 민감도·parent/preview/winner_group, key 이행 중 오정정0·원 sent 보존을 검증한다. optional rebind는 기존 notify/설치 이력/source 경계를 보존하고 자정 active/staged를 구분한다. outside_night_window의 신규 연구 상태 쓰기는0이며 최신 야간 시도와 원 계산 receipt를 별도 보존한다.
  - History: 10/9 MW1 수리·MW2–MW5 구현/반복 검증·selected release/optional 설치는 [배포 리뷰](../audits/main-market-weakness-review-deployment-2026-10-09.md)의 역사다. 10/13 점검 누적16,722개·자연1,534개·시장 연결0·후보0은 입력 연결 결함이며 no-edge가 아니다. 새 결함만 열고 과거 완료 구현을 전면 재실행하지 않는다. 이 stable ID를 미래 날짜에 Acceptance와 함께 이전하며 중복 OPEN을 만들지 않는다.
  - 인계: 원 AUTO 봉인 bytes와 다른 OPEN owner를 보존한다. 최종 checklist 문서 바이트의 기존 strict/PREOPEN 영향은 `DirectFamilyPreopenPolicyHandoff`가 기존 승인 범위에서 검증하고 과거 PASS를 현행으로 주장하지 않는다. 현재 작업본 코드 수리·표적 회귀는 완료했으며 배치·연구 재계산·실발송은 미실행이다. 원 기계 숫자 역할 미확인은 role_unverified, 완전 확인점 재생 producer 부재는 confirmation_replay_unavailable이며 지원 축/실제 수치로 보고하지 않는다.

  - 구현 검증: [구현 리뷰](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md)의 회귀/compile/정적 검사·문서 parser 결과를 수용한다. 실제 예약의 원천 연결/A·B/U·phase·notification disposition·최신 시도/원 계산은 검토 release 배치와 자기 code rebind 후 확인한다. 기계 수치 후보 부재·새 자연 표본 부족은 경제성 null/연구 capability이며 source 수리 실패나 no-edge로 전용하지 않는다.
  - 후속 재리뷰: [8종 수정 근거](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md#후속-코드-재리뷰와-수정보완), 표적 263개 통과. 재생 producer 부재는 selection/안내 거부, 두 지원 필터의 추가 모집단은0이다. pending 날짜 중 outbox 보존·cursor 변경 시 발송 보류·conflict 캐시 무효화·오래된 철회/정정 억제·comparison→manifest 중단 복구·저장 오류 defer·probe BLOCK 분리·실제 capability 사유를 후속 배치 수용에 포함한다. 원 K/R/A/N 통계 수용은 미지원 재생 producer의 완료를 뜻하지 않는다. 배포·예약 변경·운영 원천 재계산·실발송 미실행 경계를 유지한다.

  - 배포 승인 수용: 후속 사용자 “배포승인”으로 [검증한 불변 배포본](../../data/report/main_market_weakness_deployment/2026-10-14/build.json)의 선택·자기 optional 예약 code rebind를 실행한다. 최종 결과는 [배포 결과](../../data/report/main_market_weakness_deployment/2026-10-14/deployment-result.json)가 소유한다. 기존 enabled/notify·설치 이력·source 경계와 정지된 Main 상태를 보존하며 기동·정책 발행·장중 연구/실발송은 포함하지 않는다. 263개 release 회귀 통과와 실제 다음 야간의 terminal→누적→알림 disposition 수용을 구분하고 자연 수용 전 이 OPEN owner를 유지한다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.
  - 10/15 후속 수리: [야간 처리 정체·근거 고정 리뷰](../audits/main-market-weakness-night-progress-and-evidence-review-2026-10-15.md), [운영 계약 §11](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md#11-2026-10-15-처리-정체근거-보존-보완-운영-계약). 원천 갱신 우선·밤 사이 날짜 순환·다음 날짜 유입 차단, 원천 소실/빈 replay의 결손 사유, 장후 observer 원 bytes 고정을 구현·재리뷰했고 278개 표적 검증을 통과했다. 10/14 미검증 epoch의 종료 영수증 부재는 U로 보존한다. 검토본 배포/rebind와 실제 중간 날짜 진전→migration 종료→누적/알림 disposition은 별도 자연 수용이며 장중 계측·원천 재작성·기계 역할 부여·매매 변경으로 결손을 대체하지 않는다.
  - 10/16 날짜·보고 보완: [완전성·최신 원천·보류 보고 리뷰](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md), [운영 계약 §12](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md#12-2026-10-16-날짜-완전성최신-원천-처리보고-보완-운영-계약). 발견된 미시작 날짜도 pending에 포함하고 원천 소실/목록 변경을 대사한다. 최신 마감일 야간 우선 기회와 기존 backlog 순환, 초기 calendar/EOD/budget/deadline 보류의 최신 시도 기록, native 입력·projection·연결 건수 구분을 구현·반복 리뷰했으며 289개 회귀를 통과했다. 작업본 메타데이터 검사는 미시작10/15를 식별했지만 운영 재집계·배포/rebind·실발송은 미실행이다. 배포 전용 세션의 통합·자기 code binding 재조회와 다음 허용 야간의 실제 진전→migration/누적→알림 disposition 수용 전 이 OPEN을 유지한다. 기존 보조평가·장중 추가 부하0·매매 권한 경계를 보존한다.
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.

- [ ] `[AuxiliaryCircuitRecoveryRepair1012] 보조판정 회로·제출 증빙의 다음 정상 신호 수용` (`Due: 2026-10-16`, `Slot: INTRADAY`, `TimeWindow: 승인된 적용 후 다음 정상 attempt`, `Track: RuntimeStability`)
  - 10/16 우선순위 보완: [원천·보조 계약 리뷰](../audits/main-submit-priority-source-and-auxiliary-contract-review-2026-10-16.md)의 삼성2건 원 budget/capture clock trace 누락과 HPSP4건 CAUTION→INSUFFICIENT 분류 결함을 격리 작업본에서 수리한다. 원 deadline·AI 입력/응답/연구와 PASS 조건을 유지하며 다음 실제 PID의 capture 전후·잔여 budget·canonical CAUTION을 확인한다. 코드 검증은 실제 지연 감소·제출·경제성 수용을 대체하지 않는다. 기존 Acceptance/History와 OPEN을 유지한다.
  - 19:40 세션 경계 추가 결함: 이전PID가 완료 결과 회수 전에 fixed-watch route conflict를 던져 스나이퍼 스레드가 종료됐다. 원 queue로 결과를 소비·거절·정리하고 pending 물리 작업을 유지하도록 수리했다. 원 구현 실패8개/새 구현 통과 및 관련151개·계약1,808개 PASS. 첫847607658 배포는19:42:59 완료됐으나 이 추가 수리는 새 rising/holding fixture와 ordered 재배포 후 현재 PID/정규 탐지로 닫는다. 19:44 자동 수동 이관으로 append된 삼성전자 제외 행과 기존 prefix를 보존한다. [추가 수리](../audits/main-entry-price-progress-deployment-review-2026-10-15.md#1940-세션-경계-치명적-예외-추가-수리).
  - 후속 사용자 승인 수리: 조기 source/non-entry 결과·trace의 원 async6필드 누락과 정책893개 경로 객체 재생성 비용을 보완했다. 원 구현의 ID 유실2개 재현, 전체 file/symlink/inode/ctime 검증 유지, 동일 입력50회 검증 p95 10.867→5.488ms를 확인했다. 7b2e421e3은 기존 운영05b78a401의 ancestor로 이미 포함되며 후속 통합에도 보존한다. 코드리뷰·회귀 후 ordered 배포/새 PID·정규 detector 수용은 DirectFamilyPreopenPolicyHandoff와 연결한다. 전체 자연 지연·AI/PASS→주문 수용은 별도이며 원5초·priority·동시성·정책·안전장치는 유지한다. [후속 수리](../audits/main-entry-price-progress-deployment-review-2026-10-15.md#후속-승인에-따른-요청-결속검증-비용-수리).
  - 19:06 새 API/artifact 경보 재발: 19:05:49 현재 PID의 provider12/timeout7/응답5(CAUTION4·VETO1·PASS0), native→claim p95 4.880초/준비 queue max23.45ms를 확인했다. 원5초 안 Main 인수·로컬 검증 비용 축소와 미연결 관측1건/완료봉 원천 대사가 다음 작업이며 새 runtime 수리는 미실행이다. 19:04 비실패는 역사적 결과로 보존하고 현재 수용은 미완료다. [재발 진단](../audits/main-entry-price-progress-deployment-review-2026-10-15.md#1906-api-및-artifact-경보-재발--현재-수용-미완료).
  - 14:28:02 지정06deaab345를 통합451b6c1ec에 포함해 배포·재기동했고 PID2276473의 코드·정책 소비를 확인했다. 이전 코드 검증 당시의 미배포 상태와 구분한다. source 실패→fresh source/완료봉→새 claim/평가/Main disposition은 다음 자연 신호에서 원 Acceptance로 수용하며 검증용 provider/주문을 만들지 않는다. [통합 적용 영수증](../audits/main-hpsp-trailing-event-replay-and-sell-outbox-repair-review-2026-10-15.md#통합-리뷰배포시작-복구-영수증).
  - 10/15 완료봉 후 원천 복구 연결: [재현·수리 리뷰](../audits/main-completed-candle-source-recovery-handoff-review-2026-10-15.md). 상시 감시의 fresh-source 반환이 새 native claim 선택을 건너뛰는 결함과 검증한 exact item 대신 과거 집계 item을 조회하는 결함을 수리하고 parent 증거를 보존했다. 최초250개 이후 후속 리뷰의 확장256개 회귀를 통과했다. 비상시 경로·원 lease/재시도·native5초·cooldown·안전 guard를 보존한다. VI 원천 결속은 사용자 범위에서 제외한다. 코드 검증이며 배포·재기동·새 PID 소비/자연 재평가·제출은 미실행이다. 별도 적용 후 source 실패→fresh source/완료봉→새 claim/요청→새 기계 평가/Main disposition을 이 owner에서 확인하며 신호 무효화·원천 대기를 성공으로 합성하지 않는다.
  - 10/15 사용자 구현 지시: 실제 차단/참고 문맥/분류 불명 이력을 분리하고, 동일 Main ENTER_NOW·유효 AI PASS·현재 trace/hash/revision이 확인된 두 약세 alpha veto만 참고 문맥으로 전환한다. micro source 결손·DANGER·stale·가격·계좌·주문·수량 보호와 기존 lock 원본을 보존한다. [적용 범위](../proposals/main-postrestart-submission-bottleneck-review-and-remediation-plan-2026-10-14.md#14-2026-10-15-사용자-지시--main-승인-타점의-약세-veto-범위-정정). [구현 리뷰](../audits/main-long-probe-and-weak-veto-scope-review-2026-10-15.md).
  - 10:53 timeout 코드 수리: 주문 없이 종료된 원 native 평가의 arm을 정리하고 첫 후속 신호 재방문으로 연결한다. 종료 PASS 재사용·재기동 PID/문맥 불일치를 차단하며 원 마감·예약·지연/주문 custody·정책/원천을 보존한다. [구현·재기동 인계 계약](../audits/main-native-entry-arm-handoff-repair-2026-10-15.md). 11:37 후속 사용자 승인으로86f789693 재리뷰·잠금 경합 보완·기존 통합본 병합 후 ordered 배포/재기동을 수행한다. 다음 자연 신호의 큐 방문→확보→provider/submit 영수증은 이 OPEN owner에서 확인한다. 공용 handler 변경으로 달라진 rising_missed/holding_vote capability 코드 세대도 정확한 후속 해시·네트워크 차단 fixture로 검증한 뒤 재배포한다. 원 정책/보고서 봉인과 과거 unverified는 보존한다.
  - 10:33 시작 경합 후속: PID 확인 전 새 관측이 frozen predecessor를 덮어쓴 원 경보를 보존한다. ordered 시작 중 게시/알림/계산을 보류하고 기존 첫 정규 slot 기한을 유지한다. 다음 정규 관측의 새 PID/generation과 detector 소비로 수용하며 원 미완전 관측/경제성 OPEN은 유지한다.
  - 추가 승인 통합: e6326b0b1의 재기동 source epoch/예약 충돌 분류와87fda9479의 optional 야간 순환·증거 고정을10:01 capture/관측 수리와 함께 배포한다. 원 signal 예약·정책·미확정 자료는 보존하며 새 PID/source epoch/요청 원장·탐지기와 optional code rebind를 실제 영수증으로 확인한다. 야간 자연 수용은 기존 MainMarketWeaknessPostcloseObservation1008가 소유한다.
  - 오류 수리 인계: 10/15 08:12 사용자 지시로 08:20 병목 감시를 중단하고 오류 수정·배포·재기동으로 전환했다. PRE 이름 alias만 동등 비교하며 원 receipt/revision·venue·route·수량/안전 guard를 유지한다. 표적 1,973개 통과; 새 PID 소비와 자연 제출은 별도 수용이다. [구현·배포 검토](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - 08:32 후속 경보 수리: native 장전 fixed-watch 대기와 active observing 상태·재사용 reader의 30분/10분 coverage 계약을 보완한다. 실제 원 보고서의 현재 PID·AI 진행 기록·원 결손은 유지하고 artifact 실패와 bounded pending을 구분한다. 완료 기준은 새 불변 release의 ordered 재기동·동일 정책 소비·새 관측 generation의 detector 재계산 일치다. 원본 경보/재현 및 배포 이력은 위 audit가 소유한다.
  - 08:51 후속: exact_route_item_missing 초기 대기·quiet old scanner 행·완전 native index의 raw0·kernel birth 이전 historical incident를 보완한다. 원 경보를 보존하고 새 current generation의 순수 재계산/daemon 수용으로 종료한다.
  - 정규장 재발 방지·통합: native 전체 wait/전환10초와 평가 전 취소 원 영수증을 재검증하고 사용자 지정92785b7da를 별도 작업 트리에 병합한다. 새 family code fixture·source exact handoff·ordered 재기동 후 실제 PID/관측/detector 수용으로 확인하며 기존 경제성 OPEN 기준은 유지한다.
  - 09:25 실제 게시 실패 후속: 기존3.7MB full state와 notifier2MiB reader의 계약 충돌을 observer 전용 reader/compact continuation으로 수리한다. 원 상태와 보고서·incident/cursor는 보존하며 새 generation의 정상 게시 및 detector 소비 확인 전에는 완료로 보지 않는다.
  - 게시 경합 재발 방지:50fd의 새 report 게시 전에 읽은 이전 generation 실패가 늦게 반환되는 경합을 확인했다. 긴 검사 뒤 최신 report/selector를 검증하고 교체 시 동일 계약으로1회 재검증한다. 기존 실패/진단은 보존하며 배포·새 PID·자연 보고서·탐지기 최종 소비를 별도 대사한다.
  - 10:01 후속 원인:09:58 HPSP 요청 capture의 nonblocking generation lock 경합으로 reference/async/request 증빙이 누락됐다. 사전 중복 조회를 기존 exclusive append 검증으로 일원화하고 원 실패를 보존한다. 다음 native 요청→응답→pending 증빙 및 새 detector 소비로 확인하며 이전 provider timeout·경제성 수용은 별도다. 10:03 native feature_window_incomplete의 consumer 분류 누락도 같은 원 영수증과 생산자 사유·count로 수리하며 UNKNOWN과 미소비 확인을 보존한다.
  - Source: [보조 회로·제출 보완계획](../proposals/main-auxiliary-circuit-recovery-and-submit-receipt-remediation-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md), [10/14 제출 병목 개선계획 B0/B2/B3](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md).
  - Acceptance: 실제 새 PID/cwd/start ticks·bundle/registry 소비, 같은 시장명 비교의 receipt→revision→sizing 연결, 원 native5초·단일 recovery lease·공통 인증/unknown fail-closed·보호 exit 독립성을 확인한다. 회로가 자연히 열리지 않으면 HALF_OPEN 성공을 주장하지 않고 pending으로 남긴다. PASS와 intent/send/fill/terminal을 분리한다.
  - History: 10/12 계획의 P0-A/B/P1 새 결함만 구현 범위다. 기존 완료 native/readiness/auth owner 전체를 다시 열지 않는다. 기동 준비·배포 수용은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.

- [ ] `[NonfixedDispatchReadinessReview1012] 혼합 관측·0D 이력·probe 편입 및 신규 등록의 자연 수용` (`Due: 2026-10-16`, `Slot: INTRADAY`, `TimeWindow: 승인된 적용 후 정규5분 연속3회`, `Track: RuntimeStability`)
  - 10/16 우선순위 보완: [원천·보조 계약 리뷰](../audits/main-submit-priority-source-and-auxiliary-contract-review-2026-10-16.md)의 PID3083694 probe36건 중 stale14·source-censored3·feature UNKNOWN1을 원 결손으로 보존한다. 별도 native 호가 누락/역전/stale 회귀에서 readiness의 호가 부적격 표시 누락을 재현해 진단을 수리하며 detector/ready/pending와 슬롯·TTL·freshness는 유지한다. 셀트리온 원 UNKNOWN의 당시 native quote는 결손으로 남기고 배포 후 exact item/epoch/sequence의 자연 receipt로 기존 Acceptance를 확인한다.
  - 다음 보완:17:57:01 라온시큐어 no-match 원본의 raw_ready_count1(다른 scope 포함)과 selected_ready_count0을 observer가 혼동해 미분류 처리했다. `_probe_verified_no_match`에서 전체/선택 scope 카운트를 분리하고 선택 TRUE·pending·stale·다른 PID는 계속 거부한다. 이번 최종화 수리와 별도로 미적용이며 원본 재생·거부 회귀가 closure다. [근거와 범위](../audits/main-finalization-live-vote-read-race-repair-2026-10-15.md).
  - 10/15 비상시 원천7건 추적: [등록·첫 수신·exact 원천 리뷰](../audits/main-nonfixed-registration-source-gap-review-2026-10-15.md). 기한 내 REG 후 future 완료 지연의 연결 결함1건을 재현해 수리했고 표적342개 검증을 통과했다. 같은 lease/item/epoch·원3초 전송 예산·원 residence/native 마감과 cleanup을 보존한다. 늦은 전송2건은 timeout, 등록 후 exact 쌍 미확인4건은 원천 대기로 유지한다. 격리 작업 트리 코드 검증이며 배포·재기동·자연 복구/제출은 미실행이다. 별도 적용 후 동일 lease의 timely local REG→원천 검사→원 마감/cleanup과 Main disposition을 확인한다. VI 결속·슬롯 추가 증설·TTL 변경은 포함하지 않는다.
  - 10/15 사용자 확정: 전체5 내 장기 슬롯2→3개 및 두 cycle의 적격 대기/장기 대기 진단값 연결. 별도 적용 전 용량 비교·부하실험·추가 확인은 생략하며 코드 리뷰·보완·기능 회귀는 수행한다. 이전 long2 보존 조건은 이번 지정 변경에 한해 대체한다. [변경 계약](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md#13-2026-10-15-사용자-확정--장기-슬롯3-및-대기-계측-연결). [구현 리뷰](../audits/main-long-probe-and-weak-veto-scope-review-2026-10-15.md).
  - 오류 수리 인계: 10/15 관측 수리: NXT/KRX/SOR exact item·route의 native 만료 영수증, selected pending/최신 truth/누적 lifecycle의 서로 다른 모수를 검증한다. 과거 source gap·로컬 deadline·0B 누락은 보존한다. 08:19 forward index는 현재 10분 window complete이며 과거 backfill은 없다. [구현·배포 검토](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - Source: [잔여 병목·패턴 보완계획](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md), [10/14 비고정 관측 개선계획 B0/B4](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md).
  - Acceptance: 사용자10/15 확정 슬롯5/long3·60/150초·원 lease deadline 보존, mixed branch 긴 관측 순환, exact item/route/epoch/sequence의 0D count·중복/신원 결손 분리, Main 편입 첫 실패와 capture/lease/record/PID/start 연결을 확인한다. 등록6정의/4scope의 registry·native root·OR 한 기회 소비를 실제 대상에서 확인하며 신호 미발생은 pending이다. PRE NXT와 AFTER SOR 범위를 REGULAR로 복사하지 않는다.
  - History: 10/12 완료 owner의 R1/R2/R4 새 결함 범위와 지정 등록의 자연 수용만 전달한다. 과거 원천의 route/count·미확정 손익을 소급 보충하지 않고 새 경제성/미래 날짜 gate를 추가하지 않는다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.

- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-16`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - 13:55 배포 수용: 48968ade9/PID3646205/start18963364의 기동 후 native6.56초·정규 full exact SHA/FAIL0, KRX/NXT 잔고·미체결0·새 epoch fixed5 실수신을 확인했다. 정규13:50 첫 stable 통지 후13:55 새 보고서 세대도 동일 key/duplicate_incident·추가 통지0이다. [최종 검증](/home/ubuntu/KORStockScan/tmp/holding-sentinel-performance-20261016/incident-final-verification.json). 원 과거5건 복원·mandatory TP 자연 양성·비용/경제성 OPEN 및 원 Acceptance는 그대로 유지한다.
  - 13:30 반복 경보 보완: [성능 배포·동일 결손 식별 리뷰](../audits/main-holding-sentinel-performance-review-and-deployment-2026-10-16.md). 59c/PID3600286 기동 후 native6.42초·full exact SHA/FAIL0을 확인했으나 과거5개 source_gap은 보존한다. report 해시·릴리스 경로에 따른 재통지는 native full gap census의 position/BUY/signal/reason으로 제한 식별한다. 원 발송 기록은 같은 보고서 SHA에 한해 이행하며 새 결손/부분 검증은 계속 경보한다. 기존 OPEN·경제성·자연 TP 수용과 수동/retired custody는 유지한다.
  - 10/16 성능 개선 승인: [holding 읽기·계산 및 배포 리뷰](../audits/main-holding-sentinel-performance-review-and-deployment-2026-10-16.md). scope 후보 전수 검색·전일 cache 전량 읽기·중복 hash를 줄이고 원 native 전체 보고서 parity를 확인한다. 기존 정책·원 source-gap·현재 일자 원 fields를 보존하며 코드리뷰/회귀 후 정규 ordered 배포·새 PID·기동 이후 보고서/탐지기 SHA 수용으로 확인한다. 원 Acceptance/기한은 유지한다.
  - 10/16 추가 승인: 최종4c65523b2 기반 source-gap 수리를 통합하고 필수 최초 TP 전이를 상세256행 cap과 분리한다. 과거5건은 원 source-gap/비용 null을 보존하고 원 cap 소진 시각을 설명한다. [통합·전이 수리 및 배포 수용](../audits/main-postclose-source-gap-final-release-review-2026-10-16.md)의 코드 리뷰·fresh fixture·원 정책 보존 검증 후 정규 ordered 배포/재기동과 새 PID 소비를 확인한다. 원 Acceptance/기한·수동/retired custody·hard safety는 유지한다.
  - 20:00 후속 결함: live naive KST→마감 판단/HOLD 시각 결속과 명시적 수동 보유 분모를 수리한다. 미결 주문·exit token·대사·unknown custody·과거/미래/비유한 HOLD는 계속 미확인이다. 관련253개·배포/세대1,853개 회귀 통과, 원 구현8개 실패 재현. 알테오젠49300의 오늘 원 terminal HOLD 부재는 그대로 OPEN이며 원천/대사 및 다음 자연 terminal 영수증을 확인한다. 배포/현재 observer 세대는 DirectFamilyPreopenPolicyHandoff로 연결한다. [수리 리뷰](../audits/main-entry-price-progress-deployment-review-2026-10-15.md#2000-종료-검사-실패--시각과-수동-custody-계약-수리).
  - 10/15 추가 수리: [preset·비용 시각·수동 이관 계약 리뷰](../audits/main-holding-preset-cost-clock-and-manual-handoff-contract-repair-2026-10-15.md). 연구 +0.4/-3/1800/0.0023·공통 pin·실효 preset·등록 대기/완료를 병렬로 결속하고 원 ISO 비용 시각을 불변 소비한다. 기존 비상시 등록 완료 연결 수리와 선택본451b6c1ec 기준 격리 커밋으로 준비한다. 과거 partial-fill/preset 원천 결손·실현 비용 null을 보존하며 배포·PID 소비·자연 receipt·경제성은 미수용으로 남긴다. 재기동·정책/제외 파일·주문 변경 없이 기존 Acceptance/History와 OPEN을 유지한다.
  - 10/15 주성49294 추가 연구: [하드스톱 전체 흐름 연구](../audits/main-jusung-hard-stop-pattern-and-full-flow-research-2026-10-15.md), [동결 검증](../../tmp/jusung-pattern-flow-research-20261015/verification.json). 당시bb480/PID2039852에서 보유 path63행 전부 입력 결손·provider0, trailing256개 한도 소진, stop 원천 비용시각 문자열↔재생 epoch 불일치를 확인했다. 별도 preset -1.4%와 공통 stop 원천의 분리·수동 이관 종료도 재생에 결속해야 한다. 기존 scope의 source/consumer 수리 대상으로 인계하며 구현·배포 완료로 닫지 않는다. 수동관리 이관은14:41:28 증거 기준 유지, 제외 해제·매도·재기동·provider/정책 변경 권한 없음. 기계 패턴 후보는 기존 누적 정책 반영 연구로 분리하고 원 보조 연구를 보존한다.
  - 14:28:02 통합451b6c1ec/PID2276473 적용 완료. 시작 복구가14:28:00에 원 HPSP49293/0043525/61455의 native receipt1건을 ACK해 journal을 정상 종결했다. 원 동결본/hash·broker provenance/실제 비용 결손을 유지하며 drain 이후 HPSP 주문 registry 추가0·receipt/sync 오류 증가0이다. 다른 종목196170의14:33 정상 매수와 분리한다. 통합1,664개·배포216개·독립 fixture177개 검증 통과. [적용 후 검증](../../tmp/hpsp-integrated-deploy-20261015/postdeploy-verification.json). 14:31:43 및14:33 정규 log_scanner PASS·새 오류0을 확인했다. 새 포지션의 peak/복구 자연 수용은 별도이며, 이전 선택본부터 있던 holding_exit_sentinel 시간대 혼용 정렬 실패는 원 source/as-of 보존 검토→mixed-timezone 회귀→정규 게시로 수용한다. 실제 비용/경제성 OPEN과 원 Acceptance를 유지한다.
  - 보유 계약 수리의 통합 배포·재기동이 후속 승인됐다. 코드/PID 반영은 [통합 배포 리뷰](../audits/main-cumulative-holding-integration-deployment-2026-10-15.md)에서 확인하며, 실제 preset·수동 이관 자연 receipt와 비용 성과는 별도 수용한다.
  - 후속 사용자 승인: HPSP 수리의 재리뷰·보완 후 배포·재기동 및 `06deaab3453edcb66e493098f9128651f53b928f`의 완료봉 원천 복구를 통합한다. 실제 선택본bb4808c77의 기존 수리·정책을 보존하며 원 PREOPEN source/code 계약과 현재 세대 fixture 검증 뒤 ordered 전환을 수행한다. 배포 수용은 `DirectFamilyPreopenPolicyHandoff`, 각 자연 수용은 이 owner와 `AuxiliaryCircuitRecoveryRepair1012`에서 기존 Acceptance로 확인한다.
  - 10/15 HPSP 후속 결함 수리: [고점 재생·SELL outbox 리뷰](../audits/main-hpsp-trailing-event-replay-and-sell-outbox-repair-review-2026-10-15.md). 실제 0B 묶음 고점 반영·실패 상태 분리·복구 표시, fast/normal 및 장후 consumer 계약과 고정 감시의 native receipt ACK를 보완했다. 원 journal/hash·broker provenance 결손을 보존하고 관련377개 회귀·compile·diff 검증을 통과했다. workspace 코드 리뷰 범위 finding 0이며 기존 PID2039852 경보·outbox pending의 live 해소는 미확인이다. 배포·재기동·live journal 변경은 미실행; 별도 승인된 적용 후 같은 leg의 ACK/종결·중복 주문0·새 고점 재생/복구와 탐지기 소비를 확인하며 원 Acceptance/경제성 OPEN은 유지한다.
  - 오류 수리 인계: 10/15 08:05:17 missing 경보는 08:05:01 START→08:05:24 DONE 사이 첫 게시 경합이었다. 최초 missing에 한 cadence 300초 유예를 적용하되 existing malformed/date mismatch/markdown-only는 즉시 검출한다. 대상 회귀 포함 1,973개 통과. [구현·배포 검토](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 식별 결함: ["policy_binding_gap"]
  - 완료 기준: 기간·정산 세대·first crossing/유예·signal별 lifecycle/as-of의 producer→consumer 회귀 검증.
  - 비용 원천 부재·자연 표본 0은 코드 결함과 분리하며 신규 EV gate·SELL/retry·재기동 권한을 만들지 않는다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.

- [ ] `[CumulativePolicyAdoptionDeployment1015] 누적 기계 후보 등록안 배포 대기` (`Due: 2026-10-16`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - 10/15 장후 복구: EOD20:56:31(당일DB2,622행·원천 부족4종목) 뒤 원 machine stage가 origin reader displacement로 실패했다. [부모 custody 복구 검토](../audits/main-postclose-origin-parent-custody-repair-review-2026-10-15.md)의310개 검사·동일128 scope/76,800행/607신호·원천847/코드37개 검증 후 `430bb7659`를 분석용으로 선택하고21:25 기존 recovery reuse 경로를 재실행했다. Main 정지·원 pending c15491190e72·현재 부모1f069c6894b5·기존 정책/수동 통제를 보존했다. 이는 매매 재기동/PID 소비가 아니며 장후 terminal·10/16 prepared/PREOPEN/PID 수용은 실제 후속 영수증까지 OPEN이다.
  - 추가12가설 구현 인계: 별도 작업본 `entry-progress-cumulative-20261015`에서 214개 회귀·27 partition native/35,558대안 일치 검증과 private 준비(content82796bfeee27)를 완료했다. [추가 구현 검토](../audits/main-entry-price-progress-implementation-review-2026-10-15.md). 기존38가설 운영 pending c15491190e72와 구분하며, 새12가설의 등록/배포/PID 수용은 이번 구현으로 승인되지 않는다. 기존 parent/pending 충돌은 원 등록을 보존하고 현재 parent·날짜·후속 권한을 재확인한다.
  - 통합cfa070c1e로 코드 배포·재기동 완료. publication10/15·target10/16 누적 등록 receipt c15491190e72의 durable intake 완료, 현재 policy pointer 불변. 정상 장후 stage와 적용일 PREOPEN/PID 소비는 OPEN이며 오늘의 코드 소비와 혼합하지 않는다.
  - 10/15 후속 지시로 통합 배포·재기동이 승인됐다. 기존 배포대기 상태는 이 승인으로 대체하며, publication10/15·target10/16 및 원 parent CAS를 유지해 durable intake와 정상 장후 stage→PREOPEN 인계를 수행한다. [통합 배포 리뷰](../audits/main-cumulative-holding-integration-deployment-2026-10-15.md).
  - Source: [구현·리뷰·격리 검증](../audits/main-cumulative-policy-adoption-implementation-review-2026-10-15.md), [정책 반영 계획 §11](../proposals/main-cumulative-research-policy-adoption-plan-2026-10-14.md#11-1015-별도-작업본-구현과-배포-대기-인계).
  - 사용자 지시는 별도 작업본의 구현·반복 보완·배포대기다. 이 항목의 일정은 자동 배포/등록/재기동 권한이 아니다. source 수리의 과거 OPEN을 재개하지 않는다.
  - 작업본 `/home/ubuntu/KORStockScan-worktrees/cumulative-policy-adoption-20261015`, branch `codex/cumulative-policy-adoption-20261015`; private data/tmp와 immutable prepared archive를 보존한다. 원 작업본의 동시 작업은 그대로 둔다.
  - Acceptance: 코드·원천/variant/native-reader 검증 PASS와 prepare authority false를 확인한 뒤 배포 지시를 기다린다. 승인 후 새 selected release/코드·현재 parent CAS·날짜·원천 해시를 대조하고 durable intake→동일 세대 stage→적용일 준비/정상 PID 소비를 기존 `DirectFamilyPreopenPolicyHandoff`와 연결한다. target이 지나면 publication/target을 새로 준비한다.
  - History: 10/14 계획, 10/15 누적 연구 38개 가설·19,892개 관측 대안과 reviewed 15개 scope 변경/7개 승계를 계승한다. 성공 보존율/표본/EV/새 날짜 gate는 추가하지 않는다. 코드·준비와 실제 등록/활성/PID/자연 거래/실현 성과는 별도 상태다.
  - 인계 원본: [10/15 동일 ID의 Acceptance·이력](2026-10-15-stage2-todo-checklist.md). 원 관측/정책 날짜는 유지하며 미완료를 완료로 바꾸지 않는다.


## 장후 반복 읽기 개선의 격리 구현 인계

사용자10/16 추가 승인으로 SOR 미식별 체결의 KRX 소비값·원본 분리, 정책 발행/기동의 pipeline raw 재해시 제외, full detector digest 세션과 frozen 매도 후 metadata를 보완한다. `35beec0f`도 통합하며 리뷰·검증 후 배포/재기동한다. 기존 `DirectFamilyPreopenPolicyHandoff`/`HoldingProfitExitSourceContractRepair`가 native PID·실제 읽기량·다음 자연 체결/관측 수용을 소유하고 원 OPEN/경제성 결손을 유지한다. [수리·배포 리뷰](../audits/main-sor-krx-and-pipeline-validation-deployment-review-2026-10-16.md).

기존 `DirectFamilyPreopenPolicyHandoff`가 반복 검증으로 실패한 장후 인계 경로의 적용·현재성 수용을 계속 소유한다. OPEN stable ID·기한·원 Acceptance는 바꾸지 않는다. 사용자10/16 지시로 controller/prepare CLI의 실행 내 digest 공유와 delay 단일 패스 검증을 별도 작업본에 구현했다. [구현·반복 리뷰](../audits/main-postclose-read-reduction-implementation-review-2026-10-16.md), [운영 계약](../proposals/main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md#장후-cli-실행-내-재사용-보완--2026-10-16)을 따른다.

이 체크리스트는 구현 작업본의 인계 초안이다. 원 작업공간의 봉인된10/16 checklist·선택본·정책·controller/prepared는 변경하지 않았다. 구현 검증은 배포·PREOPEN/PID 소비·정규 장후 성능 수용과 별개다. 적용할 때 기존 source/code/date/native handoff 검증을 수행하며 원 정책 코드 계약 차이를 무시하거나 기존 준비본을 새 코드로 재라벨링하지 않는다. 세대 전체 게시의 원자성과 프로세스 사이 재사용은 이번 구현 대상이 아니다.

사용자 후속 배포·07:55 확인 지시를 수용했다. 기존 `DirectFamilyPreopenPolicyHandoff`의 원 수용 기준으로 정규 PREOPEN/첫 기동과 후속 ordered 배포를 검증한다. [배포 리뷰](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md). 원 운영 체크리스트와 이미 봉인된 정책/PREOPEN bytes는 별도 보호한다.

580d5865b의 selected-phase 실패와 정지 복구는 같은 `DirectFamilyPreopenPolicyHandoff`가 소유한다. 원 native PID 증거·정책·봉인 체크리스트와 실패 attempt/hold를 보존하고, 검토 source-pair 및 새 attempt에서 native 소비를 확인한다. 상세는 위 배포 리뷰를 따른다.

추가 승인된6cf45b5c 통합·optional code/calendar 재결속은 기존 `MainMarketWeaknessPostcloseObservation1008`와 `DirectFamilyPreopenPolicyHandoff`가 각자의 설치/선택·PID 수용을 소유한다. 원 enabled/notify/source floor/설치 역사·후보/outbox와 야간 예산을 유지하고 다음 자연 야간 수용은 OPEN이다. [통합·배포 리뷰](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md#6cf45b5c-통합과-optional-codecalendar-인계).

현재 승인 배포는 세 overnight SELL 완료 outbox의 엄격한 broker/BUY 결속 ACK 수리를 포함한다. 원 record49300/49328/49267과 leg hash를 보존하고 native PID·세 key ACK·terminal 및 다음 detector로 운영 수용한다. 비용 미상/기존 연구 OPEN은 유지한다. 동일 배포 owner와 위 감사 근거를 사용하며 수동 주문/journal 편집은 하지 않는다.

08:36:58 b4d23f658 native 배포/PID 수용과08:37 세 SELL key ACK 및 optional code/calendar verify를 확인했다. 후속08:42 observer의 lazy auxiliary 부재와 sentinel clock 혼용은 동일 배포 owner에서 보완·새 PID/자연 cron/detector 수용한다. 원 FAIL·partial/source gap·비용 미상 및 다음 optional 자연 야간 OPEN은 유지한다. 위 배포 리뷰의 원인/시험/종결 증거를 따른다.

3c814c05c의08:57:51 native PID와09:00:35 holding 정규 DONE을 확인했다.09:01:47 의미 영수증 누락은 후속 native_validated/observation_complete 소비로 닫고 기존 source/policy/economics 공백은 HoldingProfitExitSourceContractRepair에 유지한다. 시도0·strict pending 부재만 남은 observer 경계는 같은 배포 owner에서 추가 수리·native 수용한다. 원 운영 checklist bytes와 OPEN stable ID는 유지한다.

09:06:39 추가 policy_binding_gap은 HoldingProfitExitSourceContractRepair가 소유한다. legacy BASE 원 target pin/hash와 native record/symbol을 보존·결속하는 보고서 수리를 같은 배포 owner에 인계한다.75d preflight 중단과 원 실패를 보존하며 새 natural 보고서/의미 detector로 닫는다. 원 first-crossing/비용 미상 OPEN은 별도다.

036930 SOR venue UNKNOWN terminal ACK와 revive49342의 실제 편입을 기존 HoldingProfitExitSourceContractRepair/DirectFamilyPreopenPolicyHandoff에서 확인한다. 원 거래소/비용 미상·수동456010 제외·원4개 key를 보존하고 duplicate watch/guard 완화 없이 자연5개 편입으로 닫는다. 상세 배포 리뷰를 따른다.

현재 PID의 bare/typed receipt 비교 결함도 같은 source-only owner에서 수리했다. 원 manifest/env/archive와 native0c461429 fixture를 유지하고 최종 PID/036930 ACK/고정5개·정규 detector로 확인한다. 상세 원인/시험은 위 감사 근거를 따른다.

predecessor native preflight 반복 읽기/120초 timeout도 같은 DirectFamilyPreopenPolicyHandoff가 소유한다. 정확히 같은 CLI/cache에 session을 전달하고 원 deadline/의미 검증을 유지한다. 실제 native validation_io·새 PID·036930 ACK·5개 편입·최종 detector로 수용하며 원 timeout을 보존한다.

11:35 후속 관측에서 delay source ledger 내부의 과거 pipeline 재해시와 observer role 공통 잠금 경합을 확인했다. 기존 owner의 잔여 결함으로 지연·수량 정책 소비의 봉인 참조 검증과 generation별 잠금을 보완한다. [SOR/pipeline 재리뷰](../audits/main-sor-krx-and-pipeline-validation-deployment-review-2026-10-16.md)의 추가 배포·현재 PID·실측 I/O 수용을 따르며 원 실패와 자연 관측/경제성 OPEN은 유지한다.

selected 단계의 영수증 ABI 불일치와 PREOPEN 전용 중단 복구 한계를 같은 owner에서 보완한다. 원 실패·기동 hold·당일 intraday 실제 소비 증거를 보존하고 exact frozen generation 검증 후 정식 중단 복구를 수행한다. 정책 재선정·임계치 변경·native 소비 합성은 하지 않는다.

09:49 cold timeout의 실패 이력을 보존하고 같은 배포 owner에서 기존 transition TTL120초/의미 검증을 유지한다. 단일 역사파일 content-hash 준비와 native phase 비용을 구분해 실제 PID/ACK/고정5개 수용을 확인한다. 원 운영 checklist bytes는 유지한다.

10:13:11 같은-PID native 복구/PID3083694와 원4개 SELL ACK·고정5개를 확인했다.10:20 자연 full observer 회복과10:22:17 전체 FAIL0(경고1/PASS6)을 대조했다. 원150초 timeout·I/O/원천 결손·다음 optional 야간 OPEN은 유지하며 상세 감사 근거를 따른다. canonical 당일 checklist는 SHA394a2f6e… 그대로다.
