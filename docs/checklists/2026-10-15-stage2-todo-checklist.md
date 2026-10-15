# 2026-10-15 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-14", "sources": {"entry_cancel_wait_policy": {"sha256": "b5a8bc936880ede96b2d5c90f6d55af4b584c78194497b3e72f3a067c569682d"}, "entry_cancel_wait_tuning": {"sha256": "21c328a5c06e9da1c9fe8d75279bb7de02ba48ab10943073feae4eecf9b26d01"}, "holding_path_vote_policy": {"sha256": "dd5c323e134289ee726399be2a92f6c3ffea5b5150023e0ca2311ddf97d24d1e"}, "initial_quantity_refresh_stage": {"sha256": "784637e517144284c657148e5a92b078d4ee54be2521816bd42f933aea958d21"}, "runtime_approval_summary": {"sha256": "f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2"}, "stage_legacy_machine_report": {"sha256": "fe4a1273df0aabc233d93377dd79de890891e066b9fec5b47727703639b5c45b"}, "stage_main_auxiliary_policy": {"sha256": "52bdc560e266d6c8c3652cfdbd2885485c74fa82398ddd98d7e0bc6cb2c415b4"}, "stage_main_machine_policy": {"sha256": "d319a54df1711c377b3e85a9f6f291ba351f6ef3c7f0fbff5341a16de4c03a22"}, "stage_main_stop_confirmation": {"sha256": "01873957581ecc854845abef04b582033089623aa11a7f292ee2859761d2cdd3"}, "stage_outcome_labels": {"sha256": "aeb83dae569816cda06d60569dc3d355b2ea61495ab494e5addeb7949824c80c"}, "stage_pre_submit_delay": {"sha256": "9279f60d8ee23b57b9f9d2dc4d77df9cb6c2095245bf2e22f77c0e42896593cb"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-15", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "1bd995c85a8570a5f258deaf74fa2ca9122282cb504a3e4b51abebefffd8f78f", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-15.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-14", "source_report_sha256": "5eb9158585c4f460d8f2c4c873a1600bd1e805e5a8495a2b51eb636dca5efb39", "status": "verified_incumbent_carried", "target_date": "2026-10-15"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-15.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "31e574ad0c9b6654c498661cad5612ea85bf7054e9412c08632488148353b053", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "b5a8bc936880ede96b2d5c90f6d55af4b584c78194497b3e72f3a067c569682d", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "561bf3f8e3693c88f8136915df3853bdcb35cbbc8ced44a5f243d921b44fcb43", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "31e574ad0c9b6654c498661cad5612ea85bf7054e9412c08632488148353b053", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "ae0449f4bc974b3967d29adc214a7744d9c056b0534c8ffdb69e791d959fcd9e", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "49046de8cbf1004ca9f70945540c21576ca8413b5f95ea18cd07c78ec7c3d38d", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "07895418eb80241879600f4eafa555575ddcc35d20ab274f6702dfe514f048ba", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-14", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-15.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-14`; next apply date: `2026-10-15`.
- 아래 상태는 summary `f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
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
| `main_mechanistic_entry` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `compact_auxiliary` | `cumulative_winrate_selected` | `verified` | `preopen_policy_handoff` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-15`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - 판정 기준: source_date=`2026-10-14`, apply_date=`2026-10-15`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=verified); entry_cancel_wait(valid=True, handoff=incumbent_preserved); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=1070bb77bd3bccd712c238c3a82f5c24539f88e93d62643b851ba9a521b75f33, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-14.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-14`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`entry_cancel_wait`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_date=`2026-10-14`, artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-14.json`, report_sha256=`21c328a5c06e9da1c9fe8d75279bb7de02ba48ab10943073feae4eecf9b26d01`.
  - 세대 결속: source_generation=`be0e9778f30eb3ad84499b092dfd52705a93c9a390bea18992805f39a71ee17d`, code_sha256=`d8583947a62ffe15318b2819f6f4824b8835a7fc5865c5b00f85b8eb427620b0`, contract_sha256=`1b07937fc7fe1bb285c22119eb17cd82a004d310af2f326db07791f465013f03`.
  - 완료 기준: repair_owner=`DirectFamilySourceRepairEntryCancelWait`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.

  - 10/15 검증 경고 보완: native 원 보고서·정책 봉인을 유지하고 현재 코드의 실제 fixture 시험/영수증을 별도 검증한다. 코드 capability의 보충 소비와 source/sample/경제성 수용은 분리하며 이 OPEN owner는 원 수용 기준을 유지한다. [통합 수리·실제 영수증](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-14.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-14`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[MainStopLossRetirementRuntimeTuning1010] holding_vote 정책 생성 코드·원천 세대 계약 검증` (`Due: 2026-10-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`holding_vote`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_date=`2026-10-14`, artifact=`/home/ubuntu/KORStockScan/data/report/monitor_snapshots/holding_exit_observation_2026-10-14.json`, report_sha256=`5eb9158585c4f460d8f2c4c873a1600bd1e805e5a8495a2b51eb636dca5efb39`.
  - 세대 결속: source_generation=`1609973c820643368a9465903fcf1b5f0c284c28eb98c744b4ae6360265921a5`, code_sha256=`b2087e97e70fc145620d3440c4fddafd633ab8e45d3aa492fffec17a7b04bcab`, contract_sha256=`753ea75c3470866f6e56fad1a50b3fa5cc3c46bac5e114061fd8e176905004ff`.
  - 완료 기준: repair_owner=`MainStopLossRetirementRuntimeTuning1010`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.

  - 10/15 검증 경고 보완: native 원 보고서·정책 봉인을 유지하고 현재 코드의 실제 fixture 시험/영수증을 별도 검증한다. 코드 capability의 보충 소비와 source/sample/경제성 수용은 분리하며 이 OPEN owner는 원 수용 기준을 유지한다. [통합 수리·실제 영수증](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).

- [ ] `[PostcloseStructuralPolicyCompletion1011] rising_missed 정책 생성 코드·원천 세대 계약 검증` (`Due: 2026-10-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-14.json)
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`rising_missed`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`f45f42e4e86c2e7ab43dbfd5440279be8a34dcade9653b740ce3c5b66f65f2d2`, source_date=`2026-10-14`, artifact=`/home/ubuntu/KORStockScan/data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_2026-10-14.json`, report_sha256=`246826488e17a7e4a7f2972e4eac79f84fd329b0eafad515301d028ca0bb48c8`.
  - 세대 결속: source_generation=`2fabb9f84793363a4c81b3b584a9aa4878c86208db13a69ebc4f036d8e21d1b4`, code_sha256=`dfe2d56deef10ebaf4f2aa6e3edd6215f769d08ba8ac123808459c2cc8fb720f`, contract_sha256=`2f50be1eb4ba77d48330b4d4ae3356bcb04fb4cfe2904cdaf1ab0557d45f4912`.
  - 완료 기준: repair_owner=`PostcloseStructuralPolicyCompletion1011`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:9ac1db1c60c903b8f6e2566a1b4c0004d6d89079d3453d5b17735aca1c4efbbb -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-14; 발행 2026-10-14; 적용 2026-10-15. `no_submitted_orders` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": null, "checkpoint_sha256": "21ae9ffd7cb46f927c141bece5272469711bf958971693116285e805a880d2a5", "historical_terminal_or_profit_inferred": false, "known_open_count": 0, "registry_tail_hash": "b03d9a806ec95f8eebbf83e87900f4957b46d90312e721c1d10f10d7f2912d83", "status": "verified_empty"}, "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "no_submitted_orders", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "d102198527fa7ca05736770476780d3da0dc78ce8687ce1c67b13f942d48a9da", "research_evaluation_status": "no_submitted_orders", "runtime_effect": false, "source_date": "2026-10-14", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->

## 전일 미종결 수용 이관

  - 10/15 검증 경고 보완: native 원 보고서·정책 봉인을 유지하고 현재 코드의 실제 fixture 시험/영수증을 별도 검증한다. 코드 capability의 보충 소비와 source/sample/경제성 수용은 분리하며 이 OPEN owner는 원 수용 기준을 유지한다. [통합 수리·실제 영수증](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).

- [ ] `[MainMarketWeaknessPostcloseObservation1008] 압축 원천·native 판정 연결·누적·약세 조정 후보 보완` (`Due: 2026-10-15`, `Slot: POSTCLOSE`, `TimeWindow: 검증된 수리의 후속 배치·자연 수용; 실제 연구는 21:40~익일 05:40 허용 슬롯`, `Track: RuntimeStability`)
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

- [ ] `[AuxiliaryCircuitRecoveryRepair1012] 보조판정 회로·제출 증빙의 다음 정상 신호 수용` (`Due: 2026-10-15`, `Slot: INTRADAY`, `TimeWindow: 승인된 적용 후 다음 정상 attempt`, `Track: RuntimeStability`)
  - 오류 수리 인계: 10/15 08:12 사용자 지시로 08:20 병목 감시를 중단하고 오류 수정·배포·재기동으로 전환했다. PRE 이름 alias만 동등 비교하며 원 receipt/revision·venue·route·수량/안전 guard를 유지한다. 표적 1,973개 통과; 새 PID 소비와 자연 제출은 별도 수용이다. [구현·배포 검토](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - 08:32 후속 경보 수리: native 장전 fixed-watch 대기와 active observing 상태·재사용 reader의 30분/10분 coverage 계약을 보완한다. 실제 원 보고서의 현재 PID·AI 진행 기록·원 결손은 유지하고 artifact 실패와 bounded pending을 구분한다. 완료 기준은 새 불변 release의 ordered 재기동·동일 정책 소비·새 관측 generation의 detector 재계산 일치다. 원본 경보/재현 및 배포 이력은 위 audit가 소유한다.
  - 08:51 후속: exact_route_item_missing 초기 대기·quiet old scanner 행·완전 native index의 raw0·kernel birth 이전 historical incident를 보완한다. 원 경보를 보존하고 새 current generation의 순수 재계산/daemon 수용으로 종료한다.
  - 정규장 재발 방지·통합: native 전체 wait/전환10초와 평가 전 취소 원 영수증을 재검증하고 사용자 지정92785b7da를 별도 작업 트리에 병합한다. 새 family code fixture·source exact handoff·ordered 재기동 후 실제 PID/관측/detector 수용으로 확인하며 기존 경제성 OPEN 기준은 유지한다.
  - Source: [보조 회로·제출 보완계획](../proposals/main-auxiliary-circuit-recovery-and-submit-receipt-remediation-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md), [10/14 제출 병목 개선계획 B0/B2/B3](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md).
  - Acceptance: 실제 새 PID/cwd/start ticks·bundle/registry 소비, 같은 시장명 비교의 receipt→revision→sizing 연결, 원 native5초·단일 recovery lease·공통 인증/unknown fail-closed·보호 exit 독립성을 확인한다. 회로가 자연히 열리지 않으면 HALF_OPEN 성공을 주장하지 않고 pending으로 남긴다. PASS와 intent/send/fill/terminal을 분리한다.
  - History: 10/12 계획의 P0-A/B/P1 새 결함만 구현 범위다. 기존 완료 native/readiness/auth owner 전체를 다시 열지 않는다. 기동 준비·배포 수용은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.

- [ ] `[NonfixedDispatchReadinessReview1012] 혼합 관측·0D 이력·probe 편입 및 신규 등록의 자연 수용` (`Due: 2026-10-15`, `Slot: INTRADAY`, `TimeWindow: 승인된 적용 후 정규5분 연속3회`, `Track: RuntimeStability`)
  - 오류 수리 인계: 10/15 관측 수리: NXT/KRX/SOR exact item·route의 native 만료 영수증, selected pending/최신 truth/누적 lifecycle의 서로 다른 모수를 검증한다. 과거 source gap·로컬 deadline·0B 누락은 보존한다. 08:19 forward index는 현재 10분 window complete이며 과거 backfill은 없다. [구현·배포 검토](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - Source: [잔여 병목·패턴 보완계획](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md), [10/14 비고정 관측 개선계획 B0/B4](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md).
  - Acceptance: 슬롯5/long2·60/150초·원 lease deadline 보존, mixed branch 긴 관측 순환, exact item/route/epoch/sequence의 0D count·중복/신원 결손 분리, Main 편입 첫 실패와 capture/lease/record/PID/start 연결을 확인한다. 등록6정의/4scope의 registry·native root·OR 한 기회 소비를 실제 대상에서 확인하며 신호 미발생은 pending이다. PRE NXT와 AFTER SOR 범위를 REGULAR로 복사하지 않는다.
  - History: 10/12 완료 owner의 R1/R2/R4 새 결함 범위와 지정 등록의 자연 수용만 전달한다. 과거 원천의 route/count·미확정 손익을 소급 보충하지 않고 새 경제성/미래 날짜 gate를 추가하지 않는다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.

- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-15`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - 오류 수리 인계: 10/15 08:05:17 missing 경보는 08:05:01 START→08:05:24 DONE 사이 첫 게시 경합이었다. 최초 missing에 한 cadence 300초 유예를 적용하되 existing malformed/date mismatch/markdown-only는 즉시 검출한다. 대상 회귀 포함 1,973개 통과. [구현·배포 검토](../audits/main-premarket-error-repair-and-restart-2026-10-15.md).
  - Source: [runtime_approval_summary_2026-10-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-13.json)
  - 식별 결함: ["policy_binding_gap"]
  - 완료 기준: 기간·정산 세대·first crossing/유예·signal별 lifecycle/as-of의 producer→consumer 회귀 검증.
  - 비용 원천 부재·자연 표본 0은 코드 결함과 분리하며 신규 EV gate·SELL/retry·재기동 권한을 만들지 않는다.
  - 이관: 10/14 미종결 Acceptance/History를 보존해 10/15 동일 ID로 인계했다. 코드·장후 준비를 미래 자연 수용/비용 후 성과로 닫지 않는다.

기존 HoldingProfitExitSourceContractRepair는 10/13 policy_binding_gap 이력과 별도로 10/14 holding_exit snapshot의 source_gap_readiness_missing·COMPLETED 비용 원천 부재를 [전수 점검](../audits/postclose-monitoring-and-next-session-readiness-2026-10-14.md)로 수용한다. 12cell 검증 incumbent carry와 연구/PID/경제성 미확정을 분리한다.


<!-- SENTINEL_POSTCLOSE_INTEGRATION_HANDOFF_20261015_START -->
## 계산 수정 통합본과 다음 정상 기동의 수용 인계

- Source: [장후 통합·다음날 준비 리뷰](../audits/sentinel-postclose-integration-and-next-session-readiness-2026-10-14.md), [10/14 원 Acceptance/History](2026-10-14-stage2-todo-checklist.md).
- 기존 `DirectFamilyPreopenPolicyHandoff`는 다른 세션의 source/publication14 장후 전체 종료 후 승인된 계산 수정본 `a179bb42d`와 최신 장후 수리 통합배포, target15 준비·검증, 07:35 PREOPEN 및 07:55 정상 Main PID 소비를 각각 확인한다. 현재 정책·보조 판단값·operator custody를 보존한다. [01:31:55 실제 selector](../../tmp/sentinel-integrated-postclose-20261014/canonical-cli-bound-input-document-amendments-v2/selected-e74-observed.json)의 선택본은 `e74ec5c56`이며 Main 정지·`actual_pid_consumed=false`다. 후보 재결속과 target15 prepare/verify 완료는 이후 실제 영수증으로 별도 확인한다. 정지 배포 또는 prepared_verified를 실제 PID/주문/손익으로 표시하지 않는다.
- 자정 이후 코드 결속은 기존 준비 자동화의 `stopped_postclose_candidate_rebind`로만 수행한다. 실제 target15의07:35 이전, Main/supervisor 정지·정상 장후 격리·전체 controller/strict/producer 종료·미시도 PREOPEN과 canonical bootstrap env/manifest/verify 부재·선택/현재/원후보의 정확한 해시와 native 잠금이 필요하다. 원 native33·판단값·현재 pointer를 보존하고 source14 consumer→summary→controller→target15 prepare/verify를 재결속한다. 정상 PREOPEN/기동을 앞당기거나 실패 receipt·시간을 합성하지 않는다.

- 추가 Acceptance: `NonfixedDispatchReadinessReview1012`는 원천15행 제외로 교체된 source14 raw와 derived summary/cache의 세대를 별도 수리로 대사한다. 과거 source14 canonical CLI 발행은 [최종 감사의 SHA·파일 세대 결속](../../tmp/sentinel-integrated-postclose-20261014/cold-cli-policy-readiness-input-causal-review-v2.json) 확인 후 실행 전에 취소했으며 원 보고서·audit/final-contract를 보존한다. 필요시 별도 검토할 과거19:55:39.513196 cutoff의130초 native build-only 진단은 E에만 결과를 보존하는 계산 관찰로, 실제 CLI 발행 검증이나 자연 슬롯 수에 포함하지 않는다. 실제10/15 첫 CLI≤130초·observer40초 예약·전체≤180초와 정상08:00/08:05/08:10 연속3슬롯은 기존 owner/Acceptance에서 확인한다. source14 과거 계산과 실제 실행 시각15를 분리하고 과거 observer를 합성하지 않는다. 원생성물·실패/timeout·source-gap을 보존하며 캐시 준비를 자연 계산 성공이나 새 final-audit PASS로 보고하지 않는다. [digest와 인계 호출 경로](../../tmp/sentinel-integrated-postclose-20261014/audit-digest-deployment-callgraph-review.json)의 정적 검토는 실제 새 선택본의 native closure·target15 prepare/verify를 대체하지 않는다. `AuxiliaryCircuitRecoveryRepair1012`는 새 PID의 실제 정상 AI attempt 분모·stage clocks·timeout·회로와 PASS→intent/send/fill/terminal을 구분한다. 검증용 provider replay나 주문을 만들지 않는다.
- History: 다른 장후 세션이10/15로 이관한 위 두 OPEN stable ID와 원 Acceptance/History를 유지하며 이 추가 수용을 연결한다. 이전 날짜 구현·검증 완료 항목을 다시 열지 않으며 과거 로그·등록 membership·손익을 보충하지 않는다. 코드/배포/준비와 자연 성능·실제 거래·비용 후 경제성은 별도 수용이다.
<!-- SENTINEL_POSTCLOSE_INTEGRATION_HANDOFF_20261015_END -->

## 05:51 장전 최종화 경보 수리 인계

- 기존 `DirectFamilyPreopenPolicyHandoff`가 [준비 예산·코드 검증 경보 수리](../audits/morning-finalization-preparation-and-generation-warning-repair-2026-10-15.md)의 source14/target15 새 prepared·최종화·선택 commit·정규 PREOPEN/실제 PID 소비를 각각 확인한다. 준비 기본600초는 원06:50 마감 cap과 분리된 검증 예산이며 AI/매매 예산을 바꾸지 않는다. 원05:51 실패와 이전 준비 영수증을 보존한다.
