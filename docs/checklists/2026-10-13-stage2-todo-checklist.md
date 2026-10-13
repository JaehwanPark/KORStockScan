# 2026-10-13 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-12", "sources": {"entry_cancel_wait_policy": {"sha256": "044a309e399df5499c75fc33ed6090e5c4c5d1cccf5b30ffd5db0069a72902ba"}, "entry_cancel_wait_tuning": {"sha256": "b6f790248a22afcc9525e86effac745e1536997d2e3fed61e51dd99b41f12f1f"}, "holding_path_vote_policy": {"sha256": "b19a1a4a38fa315fc5eed4100616201559c23c972777fc9f9e47329b8766328c"}, "initial_quantity_refresh_stage": {"sha256": "c75db66506a51e3ede6fcaa7b63128360306853e264148012b147e0556b15138"}, "runtime_approval_summary": {"sha256": "41ba57f7779a8930a7a4100eb66b00c4079b8adacf452726c33a82993c9e46bc"}, "stage_legacy_machine_report": {"sha256": "a8e5d8525e606b010c15c2d710eea71419ba76d5bbabc8a4d42b8fe3f7ba2edd"}, "stage_main_auxiliary_policy": {"sha256": "ac05eb708aa260f46d9a8051308115e61062927d2a89980054cf832f58d66efe"}, "stage_main_machine_policy": {"sha256": "c47c75b6e33c1813a152dd5738cc64a7eb738183bdeda9f67d6dcb923256e082"}, "stage_main_stop_confirmation": {"sha256": "8d3f3161307dee517a5d22455bb11d19b8e937f249419b07f2a0c042f98c096f"}, "stage_outcome_labels": {"sha256": "84edc5a692d35b18d9cf6a87e17f9dcf4672766a98e0765fae9d17d3709dbc18"}, "stage_pre_submit_delay": {"sha256": "09efcbdb838111c8729de848557c498e77d2fa0cc6a82945641d84e8fbafa2b1"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-13", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "63dea06eda175a0cf936bcce7729462aa1113a25e258782472794f9b26fb6dfb", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-13.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-12", "source_report_sha256": "3c82415bc99496a7cba8e32ca26f8ac72fdfc45d14b1e8750c9da5f3e7104fe0", "status": "verified_incumbent_carried", "target_date": "2026-10-13"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-13.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "28a0c6e19ebaedffc7c73af3f78173be471c8a6189014a6be7c2f380d0b1d188", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "044a309e399df5499c75fc33ed6090e5c4c5d1cccf5b30ffd5db0069a72902ba", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "954d58a2ca2408813251a6b87e848a013de6fe33ad59fbdeb34c987ca7e79ccf", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "28a0c6e19ebaedffc7c73af3f78173be471c8a6189014a6be7c2f380d0b1d188", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "90f82d89bb67187ab4669e580e8554db9863c25bb763f0e296eca58d193bac96", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "f476a4151d9db1f047cbc582c160e9aa649bb7c7a917caf1f48c0a5236a240c2", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "136ca8bfbe9acbc3e0e82f3f064b5e7d6846fbeaa37e701d85b4b3304c693280", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-12", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-13.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-12`; next apply date: `2026-10-13`.
- 아래 상태는 summary `41ba57f7779a8930a7a4100eb66b00c4079b8adacf452726c33a82993c9e46bc` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
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

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-13`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-12.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-12.json)
  - 판정 기준: source_date=`2026-10-12`, apply_date=`2026-10-13`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=incumbent_preserved); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=075daef9a31779ca80b1099635612c98ae039dc2d386d33a7adf80708a52d75e, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-12.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-12.json)
  - 증거: runtime_summary_sha256=`41ba57f7779a8930a7a4100eb66b00c4079b8adacf452726c33a82993c9e46bc`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-12/auxiliary.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-12`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-12.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-12.json)
  - 증거: runtime_summary_sha256=`41ba57f7779a8930a7a4100eb66b00c4079b8adacf452726c33a82993c9e46bc`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-12.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`producer_contract_review`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-12`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-12.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-12.json)
  - 증거: runtime_summary_sha256=`41ba57f7779a8930a7a4100eb66b00c4079b8adacf452726c33a82993c9e46bc`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-12.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-12`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-12.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-12.json)
  - 증거: runtime_summary_sha256=`41ba57f7779a8930a7a4100eb66b00c4079b8adacf452726c33a82993c9e46bc`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-12/machine.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-12`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:24b98d9d99b06187ad95c4f2089edfef591729ad168dd44a11e4ed617f8d49ca -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-12; 발행 2026-10-12; 적용 2026-10-13. `no_submitted_orders` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": null, "checkpoint_sha256": "3f5152b7a4e81d6b8257f5b7050f7cb61efc01482e1be833bd1ba459a38f0d81", "historical_terminal_or_profit_inferred": false, "known_open_count": 0, "registry_tail_hash": "b03d9a806ec95f8eebbf83e87900f4957b46d90312e721c1d10f10d7f2912d83", "status": "verified_empty"}, "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "no_submitted_orders", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "c16f32d8357515b60f927297a29f78a2332e3a5c9d455c6b585aa43211298d5c", "research_evaluation_status": "no_submitted_orders", "runtime_effect": false, "source_date": "2026-10-12", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->


<!-- postclose_source_recovery_20261012 -->

## 10/12 장후 원천 복구의 다음 기동 수용

기존 OPEN `DirectFamilyPreopenPolicyHandoff`가 [장후 복구 기록](../audits/postclose-monitoring-and-next-session-readiness-2026-10-12.md)의 다음날 기동 수용을 함께 수행한다. 별도 중복 실행 항목을 생성하지 않는다.

- 07:35 PREOPEN과 07:55 이후 Main의 실제 cwd·commit·PID/start ticks·정확 날짜 정책/env·인증/WS를 확인한다. 준비 성공은 실제 소비 증거가 아니다.
- 의미 감시는 실제 선택 릴리스의 코드 경로와 공유 data의 물리 경로를 구분해 검증한다. 복구 호출은 정규 라우터의 승인 수탁 환경 로더를 사용하고 계정/원장 값·guard를 변경하지 않는다.
- AI request 원천은 정규 원본이 있으면 원본을 소비하고 같은 논리 파일의 gzip 사본은 중복 소비하지 않는다. 원본 부재 시 압축본을 소비하며 원본 변경·삭제·새 원천은 guard와 기존 index의 세대 재검증을 요구한다. 이 계약을 source 감시기와 replay 독자에서 함께 검증한다.
- postclose_exit 재사용은 원천/window/비용/산출물 해시와 현행 holding-vote numeric 코드 세대를 확인하며 `incumbent_unverified`를 정상 snapshot으로 재사용하지 않는다. 과거 부모의 원 정책·원 산출물·strict 종료·동일 부모값 검증은 현재 PID 기동 검증과 분리한다. 런타임은 현행 코드/정책 검증을 유지한다.
- 미식별 대형 과거 행·미관측 label·확인되지 않은 actual cost는 결손/제외/null을 유지한다. source-gap carry·미승인 숫자 실험·전체 결합성능 미검증을 정책 개선 또는 실제 수익으로 보고하지 않는다.

<!-- main_residual_repair_20261013 -->

### 10/13 승인 구현의 자연 수용

- [ ] `[AuxiliaryCircuitRecoveryRepair1012] 보조판정 회로·제출 증빙의 다음 정상 신호 수용` (`Due: 2026-10-13`, `Slot: INTRADAY`, `TimeWindow: 07:55~08:15`, `Track: RuntimeStability`)
  - Source: [보조 회로·제출 보완계획](../proposals/main-auxiliary-circuit-recovery-and-submit-receipt-remediation-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md).
  - Acceptance: 실제 새 PID/cwd/start ticks·bundle/registry 소비, 같은 시장명 비교의 receipt→revision→sizing 연결, 원 native5초·단일 recovery lease·공통 인증/unknown fail-closed·보호 exit 독립성을 확인한다. 회로가 자연히 열리지 않으면 HALF_OPEN 성공을 주장하지 않고 pending으로 남긴다. PASS와 intent/send/fill/terminal을 분리한다.
  - History: 10/12 계획의 P0-A/B/P1 새 결함만 구현 범위다. 기존 완료 native/readiness/auth owner 전체를 다시 열지 않는다. 기동 준비·배포 수용은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다.

- [ ] `[NonfixedDispatchReadinessReview1012] 혼합 관측·0D 이력·probe 편입 및 신규 등록의 자연 수용` (`Due: 2026-10-13`, `Slot: INTRADAY`, `TimeWindow: 07:55~08:15`, `Track: RuntimeStability`)
  - Source: [잔여 병목·패턴 보완계획](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md), [구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md).
  - Acceptance: 슬롯5/long2·60/150초·원 lease deadline 보존, mixed branch 긴 관측 순환, exact item/route/epoch/sequence의 0D count·중복/신원 결손 분리, Main 편입 첫 실패와 capture/lease/record/PID/start 연결을 확인한다. 등록6정의/4scope의 registry·native root·OR 한 기회 소비를 실제 대상에서 확인하며 신호 미발생은 pending이다. PRE NXT와 AFTER SOR 범위를 REGULAR로 복사하지 않는다.
  - History: 10/12 완료 owner의 R1/R2/R4 새 결함 범위와 지정 등록의 자연 수용만 전달한다. 과거 원천의 route/count·미확정 손익을 소급 보충하지 않고 새 경제성/미래 날짜 gate를 추가하지 않는다.

## 10/13 shared-deadline 지연 보완 배포 수용

기존 `DirectFamilyPreopenPolicyHandoff`가 사용자 승인에 따른 지연 개선 코드의 ordered 배포·재기동을 소유한다. 원 10/12→10/13 정책·PREOPEN·bootstrap bytes를 유지하고 candidate code pin과 보조판정 128경로 호환성을 확인한 후 incumbent Main·supervisor 종료→selector/checklist 게시→native 인계→새 PID/start/cwd 소비를 검증한다. 원 strict checklist bytes는 native 역사 snapshot으로 보존하고 최종화 경고를 억제하지 않는다. [후속 구현 리뷰](../audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md)를 근거로 사용한다.

기존 `AuxiliaryCircuitRecoveryRepair1012`는 원 native5초·단일 lease·보호 exit·필수 저장을 유지한 상태에서 새로운 stage clock과 실제 caller timeout/SDK 종료·worker/Main 소비를 같은 attempt에서 검증한다. local p95 1.60초와 timeout 감소는 자연 표본이 없으면 미검증으로 남긴다. 기존 `NonfixedDispatchReadinessReview1012`는 WATCHING hint 재정렬의 전체 대상·HOLDING/주문/COMMIT 슬롯 보존과 fixed/nonfixed의 실제 경로 소비를 함께 확인한다. 코드·배포 PASS로 자연·경제성 수용을 완료하지 않는다.

첫 native PREOPEN 기동 이후의 배포는 실행 중인 원 PID의 실제 bootstrap 소비를 확인해 immutable native-predecessor 증빙으로 보존한다. 종료 후 원 정책·PID/start/cwd·준비 원천을 재검증하며 이전 장중 consumed 영수증을 만들어내지 않는다. 원 PID가 살아 있거나 증빙 결손/변조가 있으면 새 기동은 차단한다.

기동 인계는 변경 없는 손절 incumbent의 manifest·원 code digest·정확한 consumer source 쌍도 종료 전에 확인한다. 손절값과 report/bundle 원문은 보존하며 숫자 successor와 장후 연구/게시의 current-code 검증은 유지한다.

10/13 새 PID 시간초과 후속은 마지막 provider 전 fresh immutable view·동기 signature pass와 load/claim/auxiliary 자식 계측을 포함한다. 기존 native·registry/model·철회·pointer/원천·Main/submit guard는 모두 실행한다. static 부분 p95 비교164.21ms→129.95ms는 전체 local1.60초 또는 timeout 감소의 수용 근거가 아니다. 키움 kt00011 source-only150ms·원5초·계좌/가격/수량·정확 receipt2초·필수 저장은 유지하며 source TR/AI timeout을 실제 실패로 남긴다. 후속 코드 리뷰·776건 검증은 위 구현 리뷰가 소유하며 새 ID와 원장/정책 세대를 만들지 않는다.


기존 `DirectFamilyPreopenPolicyHandoff`가 저장·freshness 후속 보완의 ordered 배포도 소유한다. 검증된 canonical append의 반복 ADM body만 원본 attempt/hash로 참조하고, economic proof/전체 row population을 유지한 streaming cache projection을 포함한다. report wrapper는 5분 cron·flock/명시 override를 보존하며 기본 cooldown0, freshness600초를 사용한다. 원 policy/PREOPEN·수량·주문·custody와5초는 유지한다. 과거 미검증 원장·활성/rollback release는 보존한다.

기존 `AuxiliaryCircuitRecoveryRepair1012`는 verified immutable v6 view의 중복 static/configure 제거 후 source/PID/claim/ref/model/aux/end guard와 동일 attempt clocks를 수용한다. `NonfixedDispatchReadinessReview1012`는 자연 fixed/nonfixed 방문과 report DONE/freshness·row parity·저장 증가율을 확인한다. code/좁은 benchmark PASS는 전체 성능·provider 성공·경제성 완료가 아니다. [10:25 이후 리뷰](../audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md)에 원천·검증·실제 공간 회수를 기록한다.


report 메모리 후속 보완도 기존 위 owner들이 수용한다. read-local bounded string pool은 동일 row/field/JSON 값·독립 container와 raw/cache bytes를 보존한다. decoded prefix의 RSS 감소와 CPU 비용 증가를 분리하고 실제 정규 report의 전체 분모·RSS·DONE/freshness를 검증한다. 별도 owner/주문 권한 또는5초 갱신은 없다.
