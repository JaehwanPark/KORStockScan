# 2026-10-12 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-08", "sources": {"entry_cancel_wait_policy": {"sha256": "a6c11256631df36fea57f530cfc547fb1819747b8b95931af0ff760e779ddfdd"}, "entry_cancel_wait_tuning": {"sha256": "3b990ba3ba607b8f69ee8061a5f0aedc7f9a52c569aa14d2ad41958ebad69e3b"}, "holding_path_vote_policy": {"sha256": "022f33ad44ac3c56ad03f8f5eaff2b4d9ddc5b5d6f23a65d4ed0aa0c8a9716cc"}, "initial_quantity_refresh_stage": {"sha256": "88c01b8feea596f7c423671f1b0cbb94c7c7e569382eee9af98e94c6c8bf53ba"}, "runtime_approval_summary": {"sha256": "e4d8f5fea759996514ed1404e23a12399db35aa6f8da0661b8c142aa293b3f50"}, "stage_legacy_machine_report": {"sha256": "409ab98c9181523041ce133bf3661b357b9d6951fcc29840b8b71b36a4d1a654"}, "stage_main_auxiliary_policy": {"sha256": "3ff42274508b06c216a138caf08e758f189da6734f2f918bcc4c2f25d2786c9a"}, "stage_main_machine_policy": {"sha256": "c017902624abac4a409dc23eaae6bbfa44d1cd7f081b87c6f790750ebe4ded62"}, "stage_outcome_labels": {"sha256": "e492a62963215b085e23c985d62336a6a936be510603582ece5417fa863f72d5"}, "stage_pre_submit_delay": {"sha256": "b80f4e49938460e818412671deb13aeadc2ccee56243a92c3cc39cf41864b348"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-12", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "21d652d6cdca1419f261451b0e7767ece6d1e4d92c2c039883049fbc1256e40d", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-12.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-10-08", "source_report_sha256": "6813718b0a1e2aba81f945d354ad6680f61687250a0d536eab626da34971c561", "status": "estimated_provisional_published", "target_date": "2026-10-12"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-12.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "04f13c0bbc438e28f8f97de86f0fa4d52e6ea73a35fc355123daa5b7b2ce5a27", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "a6c11256631df36fea57f530cfc547fb1819747b8b95931af0ff760e779ddfdd", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "3f493607ae2210cd23dbcc49a4c287fc469e10750392a4ddea4b91d20c021425", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "04f13c0bbc438e28f8f97de86f0fa4d52e6ea73a35fc355123daa5b7b2ce5a27", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "a791667ab1188b50681fa6edd8d336f16a6a17edab4571349b76a8265cfb01e1", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "31fbaa57a009260d5d784868d58eab7b8df44a45e2aedd996a401cb797d465f1", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "fbc59cf51391554121bc02fec4a35cda3df91ccca8bb6b166149e4f8d56e4163", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-08", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-12.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-08`; next apply date: `2026-10-12`.
- 아래 상태는 summary `e4d8f5fea759996514ed1404e23a12399db35aa6f8da0661b8c142aa293b3f50` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
- direct source: `9/9`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `compact_auxiliary` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-12`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 판정 기준: source_date=`2026-10-08`, apply_date=`2026-10-12`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=not_applicable); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 증거: runtime_summary_sha256=`e4d8f5fea759996514ed1404e23a12399db35aa6f8da0661b8c142aa293b3f50`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-08/auxiliary.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-08`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 증거: runtime_summary_sha256=`e4d8f5fea759996514ed1404e23a12399db35aa6f8da0661b8c142aa293b3f50`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-08.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-08`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 증거: runtime_summary_sha256=`e4d8f5fea759996514ed1404e23a12399db35aa6f8da0661b8c142aa293b3f50`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-08.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-08`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:93ebc4cc933d4e8716163c30c2f498c32bb5fab6cb922e796a2eec029ca90c64 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-08; 발행 2026-10-08; 적용 2026-10-12. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "8f97e95ada920a3adcce8f1526cee4e58d00fca9124f673c1bf4bb4b4f671dbe", "runtime_effect": false, "source_date": "2026-10-08", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->
