# 2026-09-30 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-29", "sources": {"holding_path_vote_policy": {"sha256": "797692f1b4be0eb19f3d06de30700b38b3efae20e9626e26468a86e2e151a3e0"}, "initial_quantity_refresh_stage": {"sha256": "45eadad08fdfd97e128c5a8cb9d82e1f652dceb7fc43ba9b716fb49cb18ceff0"}, "runtime_approval_summary": {"sha256": "d66470f26fbfc27c0bf6c2a9c8650c0309d3197e46a7e1e21afff20949a8f5e3"}, "stage_collector_recommendation": {"sha256": "5aba0991470d6f66906e2e4342d78a57aea19a4ae89295530de1bfe4dceff351"}, "stage_episode_policy": {"sha256": "12eea3df0b2b062ac6b9c0965f775729a27fa2593682e2ddd9c5c1abf23645b2"}, "stage_legacy_machine_report": {"sha256": "324f0bbce228d7d7de8151eb88e50187e4064d08d94f880a6f3c9b53b811a62f"}, "stage_legacy_policy_approval": {"sha256": "7241c7405f3408693f985a84e94ea79b13732e322b7e8617cc7c7c5f368a7745"}, "stage_machine_attribution": {"sha256": "95d9e88688e042d4861cabb2de548f8b62f729557aff0d0a484d991bd8582b3a"}, "stage_machine_timing": {"sha256": "d173e1964275fe3b4640515b86c16aea764a39026376a015a72bb52847a80ba1"}, "stage_main_auxiliary_policy": {"sha256": "07ee490ed700e0708b4c3a1bf2c98f23bf01aa0e3bc26fae76f80d5a2efc2021"}, "stage_main_machine_policy": {"sha256": "bce473dfe70128b3c9922d3418dfa5bd4b92e2da9c14a005d40fc451a0d43385"}, "stage_market_weakness": {"sha256": "d4fd18efc6d5ef72b87830a6f1f3b15cc37da23b115555c3686cc564221e8c7c"}, "stage_outcome_labels": {"sha256": "c185e7f5808af16348444a20f6ef5e1b1352d5d1e61d8c22ba8c52dcd041d299"}, "stage_pre_submit_delay": {"sha256": "eea0d9f1c4577dd8769e48df047d2eb7b42611131d218666aa376e5288b8ee87"}, "stage_research_allocation": {"sha256": "9d529634997877115b145aa1392517cfb6dd34399d4e30c92836f56524871192"}, "stage_research_capacity": {"sha256": "ef7a0c258fc72d9eb93eb4ae53f1ca74283f8082771dc61e66219fc24b0fc889"}, "stage_widget_policy": {"sha256": "0bd763e235cabb404e6861a246940ed7947f71ed69f66edf01ab958c12cd7e1e"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-09-30", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "1cd1442a5f15a6dc89e35123af24347291e9e462cc6e86a9b80af0b3b8fcbfaa", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-09-30.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-09-29", "source_report_sha256": "9b7648f95b4e63a66d0a4658ec99e07bd05d7a6b3756a277f4fc29157af86d72", "status": "estimated_provisional_published", "target_date": "2026-09-30"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-30.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "505ffff1817b81d848bb4d7efe0852e4ce90c2cb4325efadfdb545342d67d174", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "beec77e61cd8938b1df5b72ad5883a3e21116bdd6504a6c8c1de27e0d43c52bd", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "77f88904f5b113b7a1e299a04cecc03aea2324e7615f290697d9656294491968", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "365d850390d61d5588ec4ec9df78256885ef9345935e8fe9af214bd312116d3e", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": null, "valid": false}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "505ffff1817b81d848bb4d7efe0852e4ce90c2cb4325efadfdb545342d67d174", "valid": false}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "1d77030b9d581c62306918b78355fdd22bf5e1e730d97ea436520b67124b3069", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "aea601071ac5c4665ee91a603d68bc525ea9567d32d846c117788952c21ed409", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "63ac90fecfc34e32001ae26857ef4cf8d50d620660ec4aae43dff2fe3e163c5c", "valid": true}], "release_selection_sha256": "33e19ee7de37dafab262db7a5de44a914d05b22791f44df0c23963bebc4f23dc", "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": "5b0bfbb10c7b74f98ecbb30e6ca051ef945b7042", "source_date": "2026-09-29", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-30.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-09-29`; next apply date: `2026-09-30`.
- direct source: `10/10`; direct state: `complete`.
- economic state: `source_gap`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `source_gap` | `blocked` | `producer_contract_repair` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `source_gap` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `source_gap` | `blocked` | `producer_contract_repair` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-09-30`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-29.json)
  - 판정 기준: source_date=`2026-09-29`, apply_date=`2026-09-30`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=blocked); entry_cancel_wait(valid=True, handoff=not_applicable); entry_split(valid=True, handoff=blocked); low_price_two_leg(valid=True, handoff=blocked); main_mechanistic_entry(valid=False, handoff=blocked); pre_submit_delay(valid=True, handoff=blocked); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-29.json)
  - 증거: runtime_summary_sha256=`d66470f26fbfc27c0bf6c2a9c8650c0309d3197e46a7e1e21afff20949a8f5e3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-29.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`terminal_path_not_evaluable`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-09-29`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-29.json)
  - 증거: runtime_summary_sha256=`d66470f26fbfc27c0bf6c2a9c8650c0309d3197e46a7e1e21afff20949a8f5e3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-29.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-09-29`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-29.json)
  - 증거: runtime_summary_sha256=`d66470f26fbfc27c0bf6c2a9c8650c0309d3197e46a7e1e21afff20949a8f5e3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-29.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-09-29`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-29.json)
  - 증거: runtime_summary_sha256=`d66470f26fbfc27c0bf6c2a9c8650c0309d3197e46a7e1e21afff20949a8f5e3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-29.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_operating_population_unbound`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`future_exact_changed_decision_owner_replay_and_completed_profit_rate`. policy_receipt_valid=`False`, source_date=`2026-09-29`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairPreSubmitDelay] pre_submit_delay 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-29.json)
  - 증거: runtime_summary_sha256=`d66470f26fbfc27c0bf6c2a9c8650c0309d3197e46a7e1e21afff20949a8f5e3`, source_artifact=`/home/ubuntu/KORStockScan/data/report/pre_submit_delay_tuning/pre_submit_delay_tuning_2026-09-29.json`.
  - 상태: family=`pre_submit_delay`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`pre_submit_delay_tuning`, closure_test=`exact_attempt_submit_clock_quote_cost_terminal_and_independent_holdout`. policy_receipt_valid=`True`, source_date=`2026-09-29`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

- [ ] `[MainAuxiliaryIntradaySourceSemanticAcceptance0930] 기계·보조 AI 장중 원천 의미감시 자연 수용` (`Due: 2026-09-30`, `Slot: INTRADAY`, `TimeWindow: 08:00~20:00`, `Track: RuntimeStability`)
  - Source: [원천결손 재발 방지 계획](../proposals/machine-auxiliary-source-gap-prevention-plan-2026-09-29.md), [운영 절차](../time-based-operations-runbook.md).
  - 완료 기준: 선택 릴리스와 실제 5분 Sentinel 소비를 먼저 확인한 뒤, `submission_bottleneck_monitor_latest.json`의 프리·정규·통합 애프터 경로별 probe/trace/pending 최근 10분 원천 커버리지와 원인별 분해를 대사한다. 희소 체결 진단과 경로·선택 틱·캡처·보조 AI 비용/pending 결손의 알림을 구분하고, 원천 부재·부분 tail은 정상으로 닫지 않는다. 같은 단계의 새 정상 영수증 없이 recovery를 주장하지 않으며 후행 1/3/5/10분 가격·경제성은 별도 장후 수용으로 남긴다.
  - 권한 경계: source-quality/report-only 알림이다. 자동 조회·주문·threshold·provider·bot·수량·hard safety 변경이나 과거 원천 복구 권한이 없다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:d7be407fb450a2c18b2deb11817f30375a88ee0a9dc6c7ee3e6d75b1eb81d7ce -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-29; 발행 2026-09-29; 적용 2026-09-30. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `3c5954322e6e0d721b846c169569c005a05a40be5e9036509233207a450f986b`; 정책 bundle `4e8e7f90ca1b9bf3717d99ab4a1f8b5b37f3c7fe679a54fea85f163e91cd456b`; consumer `f2428b77fc00a064e47c2ef9ee549f03a8422751d52931de4b9ba4ac19c9b81c`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
