# 2026-09-21 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-17", "sources": {"runtime_approval_summary": {"sha256": "32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"allowed_runtime_apply": false, "apply_date": "2026-09-21", "expected_state": "future_due", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-21.json", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "1f9033799ee64a0546c0541c0229c2af4f13f176df00659d915ff8e29a9de5d7", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "e776e62ff76d701c8ebd5bae0319c93a215ad40e30b967e804d1a4ed13dd0624", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "607ee9b59e1fac947d22a615d9b0e70da287fed180b03e72004304f5e3084277", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": "81bae6390b287d0abe09bc3cd217160af55aacb694b69d346090b26669603336", "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "8ac3bd7615405581f1028dc97a4b4f54023ee7934f7092d66826c8eae5474348", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": "e4d8ac537ba72ef10714e955447b7b3560547ffa3f13dbb7f473e6a34dcae0b8", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "1f9033799ee64a0546c0541c0229c2af4f13f176df00659d915ff8e29a9de5d7", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "5358bf7816fb7a51261d1d8dfb21628b09b6565084693219218165f2061c9770", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "06ab68bc30662489abe83b172cf5012ee7004d22815f58331d13346256842a4b", "valid": true}], "runtime_effect": false, "schema": "direct_family_future_handoff_v1", "source_date": "2026-09-17", "source_preopen_state": "pending", "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-21.json"} -->

## Family 직접 증거 상태

- source date: `2026-09-17`; next apply date: `2026-09-21`.
- direct source: `11/11`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `scale_in_split` | `insufficient_sample` | `incumbent_preserved` | `natural_evidence_wait` |
| `machine_entry` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `mixed` | `blocked` | `producer_contract_repair` |
| `low_price_expansion` | `not_applicable` | `blocked` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `source_gap` | `blocked` | `producer_contract_repair` |
| `compact_auxiliary` | `source_gap` | `incumbent_preserved` | `natural_evidence_wait` |
| `rising_missed` | `measured_no_edge` | `incumbent_preserved` | `terminal_incumbent` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-09-21`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 판정 기준: source_date=`2026-09-17`, apply_date=`2026-09-21`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); low_price_expansion(valid=False, handoff=blocked); low_price_two_leg(valid=True, handoff=blocked); machine_entry(valid=True, handoff=not_applicable); main_mechanistic_entry(valid=True, handoff=blocked); rising_missed(valid=True, handoff=incumbent_preserved); scale_in_split(valid=True, handoff=incumbent_preserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilyNaturalEvidenceCompactAuxiliary] compact_auxiliary 직접 family 자연 표본·독립 검증 확인` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.json`.
  - 상태: family=`compact_auxiliary`, task_role=`natural_evidence_wait`, comparison_status=`source_gap`, resolution_mode=`historical_unrecoverable`, prospective_resolution_mode=`natural_maturity`, first_blocker=`exact_stop_distance_missing_or_invalid`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilyNaturalEvidenceScaleInSplit] scale_in_split 직접 family 자연 표본·독립 검증 확인` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317`, source_artifact=`/home/ubuntu/KORStockScan/data/report/scale_in_split_order_plan/scale_in_split_order_plan_2026-09-17.json`.
  - 상태: family=`scale_in_split`, task_role=`natural_evidence_wait`, comparison_status=`insufficient_sample`, resolution_mode=`natural_maturity`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`scale_in_split_order_plan`, closure_test=`missing`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-17.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`execution_compact_coverage_unproven`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`missing`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-17.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-17.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`actual_sample_floor`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`missing`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-17.json)
  - 증거: runtime_summary_sha256=`32bee665eac39f86800f806aac7061a85bc253a83c89fad14280da859af58317`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-17.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_operating_population_unbound`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`future_exact_changed_decision_owner_replay_and_completed_profit_rate`. policy_receipt_valid=`True`, source_date=`2026-09-17`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```



## R0–R3 독립 AI 연구 폐기

사용자 지시로 `scalping.micro_reversion.ai_quality_cycle` 장후 실행기·R2/R3 인계·legacy/current-axis 전용 런타임 및 파생 산출물을 제거한다. 별도 OPEN 복구 작업을 만들지 않는다. 현행 compact·AI 원천/라벨·주문/체결·공유 경제성 owner는 보존한다. 구현·검증·삭제 증거는 [폐기 리뷰](../audit-reports/2026-09-18-ai-quality-cycle-retirement-review.md)를 따른다. 코드 선택·실제 PID 소비와 장후 전체 DONE은 별도다.

## Low-price actual 정책 자연 적용·경제성 Acceptance

- [ ] `[LowPriceExpandedResearchRepair0918] 저가주 연구 입출력·해시·추천 handoff 보완과 배포·실소비 확인` (`Due: 2026-09-21`, `Slot: PREOPEN`, `TimeWindow: 07:35~09:35`, `Track: RuntimeStability`)
  - Source: [LP-A0–A7 구현 종결](../audit-reports/2026-09-19-low-price-actual-paired-implementation-closure.md), [원래 Acceptance·History](2026-09-18-stage2-todo-checklist.md#저가주-확장-연구-보완자연-경제성-검증), [상세 계획](../proposals/low-price-two-leg-actual-conditioned-paired-economic-search-and-preopen-runtime-consumer-improvement-plan-2026-09-18.md). [LP-B0–B6·수동 청산 정정 종결](../audit-reports/2026-09-19-low-price-exploration-manual-close-implementation-review.md), [후속계획](../proposals/low-price-two-leg-exploration-promotion-gate-separation-and-economic-evidence-completion-plan-2026-09-19.md).
  - 승인/History: 기존 사용자 구현·리뷰·commit/push·future immutable 배포 승인과 source9/17/pub9/18/effective9/21 incumbent_preserved/mutation0 증거를 유지한다. 완료된 LP0–LP6/Q0–Q5 또는 unchanged 전체 grid/raw를 재실행하지 않는다.
  - Acceptance: 정상7:35 공통 PREOPEN의 exact-date applied/hash, native preflight/service/machine의 selected source·실제PID 소비를 확인한다. Writer/reader/hash·기존accepted profile·등록된 미래seed/BBO/수량·same-date peer/비용 후 비교경제성의 기존 잔여조건을 보존한다. 자연 actual entry/fill·COMPLETED 비용 후 EV/관측일당 순익은 적용 버전에 귀속하고 미발생/null/sample/source/custody를 분리한다. Implementation closure는 자연 경제 개선 acceptance가 아니다.
  - 권한 경계: 조기 PREOPEN/수동 trading service restart·주문·새profile enrollment·quantity/target/cost/grid/floor·operator veto/custody/provider/Main restart/guard 변경 없음. 기존quarantine3·동일날짜 freeze·same-stage·rollback·hard safety를 유지한다. 전체chain 외부 FAIL을 본 family PASS로 바꾸지 않는다.
  - 다음 조치: 정상기동 receipt가 없으면 future_due/source_gap, 표본이 부족하면 hold_sample, 실제 source/경제조건을 닫으면 기존 unused paired window의 단일profile/axis 승격 경로로 넘긴다. 별도 신규 실행owner 없이 본ID를 유지한다.

  - LP-B 구현 Closure: source9/17/pub9/19/effective9/21 research2profile·distinct3개, 보조 carry CF3개 모두 순익/day 개선 없음. Applied manual13행/20leg의 역사 보정, actual/model custody 분리, v10/v9·v4 검증 및 verified incumbent carry/mutation0. Receipt: `tmp/low-price-exploration-manual-close-20260919/`. 자연 적용/PID/경제 개선과 whole-chain 외부 FAIL은 미완료로 유지.

## 삼성 native 경제성 및 기존 pipeline 자연 acceptance

- [ ] `[CodeImprovementWorkorderReview0918] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-21`, `Slot: ALL`, `TimeWindow: 07:45~20:35`, `Track: ScalpingLogic`)
  - Runtime summary 인계: [RA0–RA9 계획](../proposals/runtime-approval-summary-direct-evidence-handoff-optimization-plan-2026-09-19.md)에 따라 direct artifact 완결과 family 경제성·dated policy·다음 effective-date PREOPEN·자연 성과를 분리한다. 구조적 `source_gap/unsupported_scope/mixed`만 본 stable ID에 인계하고 maturity/no-edge로 신규 작업을 만들지 않는다. 정상 9/21 PREOPEN의 bootstrap hash·실제 PID 소비와 적용 버전별 `COMPLETED + valid profit_rate` 비용 후 성과는 자연 OPEN이며 구현·배포 PASS로 대체하지 않는다.
  - Workorder 구조 구현: [W0–W6 계획·결과](../proposals/code-improvement-workorder-structural-closure-and-ev-evidence-prioritization-plan-2026-09-19.md). 수동 direct-family generation `2026-09-17-5aa459cacc82`, source/semantic `dcb36465f419973150280e44146de970374f578ec8f60e94aaf4955ea86d4039`(`logical_source_content_v2`), contract issue0·intake conservation PASS·implementation request0. source23/selected12/non-selected11은 implement0·attach14·defer9다. 과거 submit terminal gap51은 현행 call-local finish receipt가 구현되어 P3 자연 receipt 대기, WS repair receipt도 P3, tuning 허용 unknown warning은 P4 evidence다. Scanner opportunity는 비용 후 `-2.38954987%`/3pair/3일 `measured_no_edge`라 policy `254d5ab28a6b2089c4d6d036222aedb45dbc353dcd0d5429abd04c755bc9e010` incumbent 보존이다. Actual paired EV·원화 일별 순익은 과거 미선정 arm recipe/quantity/guard 결손으로 null이며 미래 사전 배정 arm 자연 owner를 유지한다.
  - WS producer 재개방: [재점검된 WS 계획 §12](../proposals/ws-freshness-postclose-quality-consolidation-and-conditional-economic-policy-consumer-improvement-plan-2026-09-19.md), [정정된 WS 리뷰](../audit-reports/2026-09-19-ws-freshness-conditional-economics-implementation-review.md). source9/17 탈락 arm의 compact/plan/terminal은 `irrecoverable_historical_source_gap`으로 유지한다. 미래 simple-capacity changed selection은 promotion ID를 합성하지 않고 selection 직전 `scanner_selection_pair_id`로 양팔 rank/score/tier/slot/budget/source를 동결하며, 기존 prune BBO/market outcome에서 비용 후 opportunity book을 만든다. research gate 통과 뒤에만 기존 marginal slot 최대1개를 baseline/challenger에 사전 배정하고 선택된 한쪽이 기존 compact→plan→guard→order/terminal을 자연 생산하게 한다. 새 장중 provider 호출·shadow WATCHING·양쪽 동시 주문은 금지한다.
  - WS closure: pair seed→양팔 source outcome→non-null opportunity EV 또는 정확한 censored→dated hold/experiment policy→정규 PREOPEN 동일 hash 소비까지를 producer/consumer closure로 검증한다. 실제 경제성은 사전 배정 arm의 `COMPLETED + valid profit_rate` 비용 후 intention-to-treat EV·일별 순익·tail·자본이 기존 forward/sample gate를 충족한 뒤 별도로 닫는다. fixture·ID 추가·baseline hold 정책만으로 실제 EV 완료를 주장하지 않는다.
  - WS 구현 인계: WR0–WR5는 9/19 구현·회귀 검증됐다. 다음 자연 scan에서 general/simple-capacity pair 양쪽 event·BBO terminal이 같은 pair ID로 도달하는지, 9/21 정상 PREOPEN이 발행 정책 hash를 동결하는지, 선택된 arm만 기존 compact→guard→order 경로를 통과하는지 확인한다. pair 한쪽 결손·실제 completed 미성숙은 각각 censored/hold_sample이며0으로 계산하지 않는다.
  - Pipeline 재리뷰/정리 및 다음 삼성 분석: [owning review](../audit-reports/2026-09-18-pipeline-rereview-cleanup-and-samsung-machine-entry-analysis.md), `tmp/pipeline-rereview-samsung-analysis-20260918/`. 중첩 schema 손상 fallback/strict OPEN을 수리·회귀 검증하고 불필요 과거 진단125개만 제거, 원 불일치/현재/rollback 보호. 삼성 source/정책/독립 service는 read-only이며 완료 pair0/source gap을 natural wait나 no-edge로 바꾸지 않음. 배포·후행 재인계 receipt와 자연 PID/parity OPEN을 분리한다.
  - Pipeline verbosity Source/Closure: [PV0–PV6 계획](../proposals/pipeline-event-verbosity-incremental-parity-and-consumer-cost-optimization-plan-2026-09-18.md), [owning review](../audit-reports/2026-09-18-pipeline-event-verbosity-incremental-review.md), `tmp/pipeline-verbosity-incremental-20260918/` receipts. 운영 producer/종료·handover·publication/증분·정정·missing/resource 및 실제 후행 소비 계약을 검증한다. 동일 `order_pipeline_event_compaction_v2_shadow`의 source/resource/자연 OPEN을 `defer_evidence`로 보존하고 반복 신규 구현/provider/full-wrapper recovery 또는 전체 chain/PREOPEN GREEN으로 바꾸지 않는다. raw·주문·정책·threshold/quantity/budget/custody/override·resource floor 및 실행 중 release는 보존한다.
  - Pipeline 자연 Acceptance: 다음 유효 source-day의 전체/완료창 parity·정상 종료/restart coverage·실제 Sentinel/execution census 소비 및 제한 비용을 확인한다. 과거9/15/16 손실의 raw fallback/원인 미확정과9/17 bootstrap을 자연 표본 대기로 숨기지 않는다. 실제 PID/주문/EV는 이 진단으로 승인하지 않는다. 해당 native owner는 이 기존 code-workorder 실행 ID를 재사용하며 별도 중복 작업/cron을 만들지 않는다.

  - 삼성 implementation Source: [S0–S6 계획](../proposals/samsung-owner-quantity-native-economic-timing-plan-2026-09-18.md), [owning review](../audit-reports/2026-09-18-samsung-owner-native-economic-timing-implementation-review.md), `tmp/samsung-owner-economic-timing-20260918/`. 비교는 owner별 승인 수량 독립이며 shared capital authority 없음. 현재 9/19 checklist 부재 및 source-day9/18을 보존한다.
  - 삼성 Acceptance: 다음 eligible/blocked/recheck native root 및 SOR deferred opening의 최초 실행시점 source→cost/code/quantity/selected exit/admission/stage guard→원 order/fill terminal projection을 대사. 자연 independent model/candidate holdout floor·coverage를 충족하기 전 승격 금지. selector/unit config와 실제 PID 소비·실제 행동을 구분하고, actual root/version별 dedup rolling/cumulative 비용 모델 순익·tail·노출·오차를 확인. settled cash net/인과적 개선은 별도 근거 없으면 null. partial/취소 race/carry CF unsupported를 natural maturity로 숨기지 않는다.
  - 금지: 새 서비스/collector/DB·전수 raw 재실행·bot restart/주문/조기 PREOPEN 확정·hard guard/quantity/budget/custody/override/holdout 완화. 자연 입력이 selected exit pin이라는 이유만으로 전수 unsupported이면 source/code defect로 재개.


## 공통 자연 수용 인계

- [x] `[MainMechanisticEntryPostcloseLoopRestore0920] 메인 기계판정 장후 full 평가·미래 정책 발행 복구` (`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: ScalpingLogic`)
  - Source/Receipt: [복구 계획](../proposals/main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md). release `df2931b19`; report `83a088cd...`; 9/21 bundle `c6a7253c...`; main·compact receipt와 strict chain PASS.
  - 완료: full machine 평가→family별 source 보존→incumbent carry 발행→summary/checklist 연결을 복구했다. 과거 8건의 exact 원화 replay는 `historical_unrecoverable`, 미래 자연 owner replay는 `prospective_resolution_mode=natural_maturity`로 분리했다. 정상 PREOPEN·실제 PID·적용 버전별 `COMPLETED + valid profit_rate` 성과는 생성된 direct-family OPEN 작업이 소유한다.
  - 금지: compact-only 결과를 메인 평가 완료로 대체, 동일 정책 자기 비교를 개선으로 집계, 미청산·source-gap을 0으로 대입, 10bp·tail·holdout·hard guard 완화, 실행 중 봇 hot reload·주문.

- [ ] `[KiwoomCommonHealthOpportunityCostAcceptance0917] 공통 health·실행 모델·compact 정책 자연 소비 및 실제 성과 검증` (`Due: 2026-09-21`, `Slot: ALL`, `TimeWindow: 07:00~20:35`, `Track: RuntimeStability`)
  - Source/History: [9/18 기존 stable ID 원 기록](2026-09-18-stage2-todo-checklist.md), [통합 계획 CI5](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md). 기존 CW/ADQ/Samsung/AVG_DOWN·공통 health·PREOPEN 외부 blocker와 별도 custody·override acceptance를 승계하며 완료된 구현 재검토를 새 owner로 복제하지 않는다.
  - Acceptance: 기존 정상 producer→lossless census/원자 plan→운영 CF→선행 실제 모델 검증→scope/route별 prompt holdout→dated policy→정규 PREOPEN/실제 PID·issued prompt→joint applied-version COMPLETED valid cost/profit의 rolling/cumulative 성과. source/model/pending/unsupported/no-edge·actual/partial/CF를 분리한다. source gap0·배포·scoped PASS는 자연EV 또는 전체 native DONE이 아니다. 모델·표본·일별 순익·tail·비용·hard guards를 유지한다.
  - Next: 다음 자연 입력의 plan/stop/route/coverage 생성과 모델 proof부터 확인한다. irrecoverable9/17 입력은 제외 유지; 같은 자료의 반복 실행·추정 복원 금지. 계획된 장전 밖 수동 apply/기동/주문 권한을 만들지 않는다.
  - WS Acceptance: [구현 리뷰](../audit-reports/2026-09-19-ws-freshness-conditional-economics-implementation-review.md)의 새 integrated v2 source/policy hash, 정상 PREOPEN immutable receipt, 실제 PID의 same-tier bonus/order 변화, exact selection-version COMPLETED full-cost EV·일별 순익·tail·capital을 확인한다. source9/17 비교0/null은 경제 개선이 아니며, producer reachability가 닫히기 전에는 자연 acceptance 대기 상태로 바꾸지 않는다.
  - WS Handoff: source section `02afcf30577e8fa290e00fe9d62e1e624adcb8ce2217dbfaec418a010ece49d2`, policy `5cb82631ef6674c80a5154737ccdca70b6d6ac75fad0194d2cc883e5ef45bf51`, effective `2026-09-21`. 현재 `source_contract_blocked`/bonus0이므로 정상 PREOPEN의 inactive 보존 receipt와 새 자연 source의 원 plan·quantity·guard·양측 terminal 보강 여부부터 확인한다.

## Limit-down 전용 축 폐기

- 사용자 지시로 전용 장후 보고/경제성/정책·관찰 슬롯·스캐너/PREOPEN 소비·verifier 요구를 작업본에서 제거하고 누적 전용 산출물을 삭제했다. 활성 OPEN 복구 owner를 만들지 않는다. 공유 원천과 과거 custody 안전은 보존한다.
- [폐기 리뷰](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md)에서 검증·삭제 증거와 선택 배포본 구분을 확인한다. 이 기록은 봇 재시작·주문·조기 PREOPEN 승인이 아니다.

- Limit-down 후속 리뷰·관련 커밋/푸시·immutable 배포: `fcfd7b8e5`. 검토 범위 결함0·통합1,531 passed(기존 wrapper 실패5/제외1은 baseline 재현)·물리 release6 passed·전용 산출물 잔여0. [최종 증거](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md). main 정기 cron target 부재는 기존 상태이며 선택/route 검증과 분리한다. 독립 unit pin·공유 원천/guard 보존; 기동/주문/조기 PREOPEN 미실행·PID 소비 미확인.

<!-- scanner_lookup_attention_handoff_sha256:5d6ce1fd7f5626f666edffbab2cc71f83b3e16d2f3a3c4b81894ccc44037570a -->
- Scanner lookup source 2026-09-17; policy 2026-09-18; publication 2026-09-19; effective 2026-09-21: `hold_no_edge`. Opportunity EV `-2.38954987%`/3pair/3일, primary actual paired EV `None`; source gaps `['complete_partition_or_actual_selection_missing', 'original_unselected_entry_recipe_quantity_guard_missing']`. Baseline bonus0을 유지하며 자연 pair/PREOPEN/PID/full-cost outcomes는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`에서 계속 확인한다.

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:ff0412ac0bbf9c4be9ece10d3734469a2158cd2a139b6a2cba4c92d58dce5faa -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-17; 발행 2026-09-20; 적용 2026-09-21. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `178f0c5ed765889032ea3aa2bea82114ee21b7a837cb72366ea4ba4d18eaac86`; 정책 bundle `a805f9e0a3d84d4e92649c3c40a9b5fb5c045c8cc99a4e17ccf2a35412247416`; consumer `506a572c60c091d43dd7a8e7cdade5ef85f5598a8ef04656275d1cade1f8e5c4`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->
