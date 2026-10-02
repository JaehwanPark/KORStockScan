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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-02", "sources": {"holding_path_vote_policy": {"sha256": "95e5caf57a53e25a932b135335c40cbd4e17dd5084c7a889b2880b7d22dc1717"}, "initial_quantity_refresh_stage": {"sha256": "4148079cd14bf2d513c1a1accd4a0da4988bc634ca3f9fa46e5512e8d2835d47"}, "runtime_approval_summary": {"sha256": "34829f81a39457a811cf8b8dd945ac1212d7b66367246b7f3cc4ec94bace330c"}, "stage_collector_recommendation": {"sha256": "6d31a225a02be815132b29383e9a0460f3044fac03888b4e484917aa66ea2225"}, "stage_episode_policy": {"sha256": "e43dea07979e94f732e02c3618db81806fc33551e77eaada0b17f1497b957339"}, "stage_legacy_machine_report": {"sha256": "f1650d6d1205d7ae52c314793cf73b7c47a1920182f03f01603324c35b3618aa"}, "stage_legacy_policy_approval": {"sha256": "b2611a8f4af6f641639118859b8dd1a7849246a358536df8d50b33d3122695c0"}, "stage_machine_attribution": {"sha256": "2d084c8ec82a71e75153bf9cc9562306e6ed0048b4726847eb814773396a2ea2"}, "stage_machine_timing": {"sha256": "759ef5307f5574980e2376245b0cc553ec696c6a4e699fb5adfa87d52e0b5fb5"}, "stage_main_auxiliary_policy": {"sha256": "316fb6afa9d69e9d9a8c61c586fbad32c48713ad09b6957361dc49f551aee29c"}, "stage_main_machine_policy": {"sha256": "b28940d9e5453988923aa047bc5e7d4a9897a6ef0b06096cb4f69e8b146f486e"}, "stage_market_weakness": {"sha256": "fb0b4418b91630a850a08b8b33ac1f4bc00468c5dd5dabe8dc3b67dbea7c6bb6"}, "stage_outcome_labels": {"sha256": "d8df7a20a1b6bb8d2c84d8ebd26ab97d87e401254e8d348a1ce3c4e56bb4805e"}, "stage_pre_submit_delay": {"sha256": "7aa3b0b64ad591a67c7e4cb12f99a1b65561ae75ee3fbdf5c8fc36918439142b"}, "stage_research_allocation": {"sha256": "316eb7f0e4e542ae9a8594e391d7023fe5eb2bb3615a987d74202aeeb800ec28"}, "stage_research_capacity": {"sha256": "566481b0cf9c82810a8b5bc47d7793daa82848ebc994e8b4cae121003101edf2"}, "stage_widget_policy": {"sha256": "83c92750b5dd13d8b88a345e0dab27eaa011589b3d6649f4447d043e7c136c13"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-06", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "43fcaac44792cb55fced0883b12216f2423468703bea2aee2765d01f01daa926", "cell_count": 15, "evidence_grade": "estimated_provisional", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-06.json", "policy_set_sha256": "707bb26b95488281f45fad130a45925b0d5ee087fb2ef4032f534a1fdf36ea63", "realized_paired_ev_krw": null, "source_date": "2026-10-02", "source_report_sha256": "48bcc0e27ae62a0afaaeb85a943453b00915c28fee9c536c0df8827d3a23c3e9", "status": "estimated_provisional_published", "target_date": "2026-10-06"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-06.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "58dcce5f8cfc4d945098fb774359625af657f0da35d7948da374fb311226c98c", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "38e329e131ad6c3828b8ee926fa917ab29f9625f17012784569bdcc014ddca8b", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "3312caedf6c59cb32c016879b87f6bc2c7d866e456b308ad49f04c0c69e1c57a", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": null, "valid": false}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "fa881104052ec52efd27258124b9760f658b4cb5441bcfe01fbff1f2eeff66a2", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "58dcce5f8cfc4d945098fb774359625af657f0da35d7948da374fb311226c98c", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "916cb379bd6837f0f8d8ef7a4761097c031f0036ba3dc1a4b59e77a210411d5a", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "cf3ee1f743708fb0643b02eb41072457309b74ad3782b205a34171475f258976", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "b8a10cf7d91509378c33f8d5d0fa840cdc822f53bb39257ec49557546ca9f82f", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-02", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-06.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-02`; next apply date: `2026-10-06`.
- direct source: `10/10`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `low_price_two_leg` | `mixed` | `blocked` | `producer_contract_repair` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `source_gap` | `blocked` | `producer_contract_repair` |
| `compact_auxiliary` | `source_gap` | `blocked` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-06`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 판정 기준: source_date=`2026-10-02`, apply_date=`2026-10-06`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=blocked); entry_cancel_wait(valid=True, handoff=not_applicable); entry_split(valid=True, handoff=blocked); low_price_two_leg(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=blocked); pre_submit_delay(valid=True, handoff=not_applicable); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`34829f81a39457a811cf8b8dd945ac1212d7b66367246b7f3cc4ec94bace330c`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-10-02.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`exact_stop_distance_missing_or_invalid`.
  - 완료 기준: closure_owner=`compact_auxiliary_paired_replay`, closure_test=`full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`34829f81a39457a811cf8b8dd945ac1212d7b66367246b7f3cc4ec94bace330c`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-02.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`34829f81a39457a811cf8b8dd945ac1212d7b66367246b7f3cc4ec94bace330c`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-10-02.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] main_mechanistic_entry 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`34829f81a39457a811cf8b8dd945ac1212d7b66367246b7f3cc4ec94bace330c`, source_artifact=`/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-10-02.json`.
  - 상태: family=`main_mechanistic_entry`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`machine_operating_population_unbound`.
  - 완료 기준: closure_owner=`ai_decision_action_outcome_calibration`, closure_test=`future_exact_changed_decision_owner_replay_and_completed_profit_rate`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```



## Episode 원천 전이 인계

- [ ] `[EpisodeCaptureSequence1006] Episode 동일 시각 상태 전이의 원천 sequence 소비 인계` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 09:00~20:00`, `Track: SourceQuality`)
  - Source: [10/2 원천·의미 복구 감사](../audits/postclose-semantic-source-monitoring-2026-10-02.md). 기존 active custody 원천 보완이며 OFF 신규 연구 복원은 아니다.
  - Acceptance: producer의 profile/day/instance sequence·이전 observation SHA와 소비자의 정확 predecessor 검증, same-clock 전이·append 유실·다른 PID/generation·날짜 reset 회귀를 유지한다. 기존 raw106건 conflict는 재라벨링하지 않는다. source-only 코드378 PASS와 Episode 실제 service pin/PID 소비를 구분하며, 별도 배포 권한 전에는 해당 매매 service pin/기동을 변경하지 않는다. 자연 해당 source가 없으면 not_observed로 인계한다.

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:024a1d943a8735fbc183ba1ead60c98aa65c9f1a157b467385c7e83da87e1099 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-10-02; 발행 2026-10-02; 적용 2026-10-06. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `23499dfdc9b00bbc445aafb8471e763a4dcf492ed60fa02303e953eee183de58`; 정책 bundle `f7198fbcc90b3d4a8044109210e41aaa62a106a2d98aeeda82dd5082f63c959e`; consumer `49c439548ff27853e2add5513bcf093b4c1bd54b50cd94077004378120484e59`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->

## Cancel wait 실행 세대 인계

- [ ] `[EntryCancelWaitSourceReconciliation1002] cancel wait 새 계약 실행 세대·직접 소비 수용` (`Due: 2026-10-06`, `Slot: PREOPEN`, `TimeWindow: 00:10~07:35`, `Track: MainEntry`)
  - Source: [취소 대기 원천 대사·승계·의미감시 보완구현 계획](../proposals/entry-cancel-wait-source-reconciliation-remediation-plan-2026-10-02.md). 사용자 추가 구현·반복 리뷰 지시를 반영했다. [구현 리뷰](../audits/entry-cancel-wait-source-reconciliation-implementation-review-2026-10-02.md)는 작업본 코드와 격리 시험의 근거이며 실제 새 장후 세대·배포/PID 수용은 별도다.
  - Acceptance: 당일 verified empty와 9/30 실제 제출 2건의 대사 미완료를 분리한다. 승계 이벤트만 남은 날짜까지 원 source/hash를 검증하고 미분류·registry 미등록·terminal/cost 결손을 durable ledger에 보존한다. 미검증 과거의 확정 미해결 count는 null이며 EV/후보를 합성하지 않는다. 공통 semantic projection→summary→실제 tower 전용 필드→다음 checklist→strict 및 artifact freshness→기존 notification filter/mock 도달을 대조한다. 정상 carry·미도래·세대 전환 오탐과 중복 알림을 막고 현행 대기시간/scope·별도 순차 timeout owner·hard safety·정책/매매 권한을 보존한다. 반복 리뷰·표적 검증 후 코드와 자연 세대 수용을 구분한다. 복구 불가 항목은 artifact/owner/closure test와 함께 blocked로 남기고 같은 입력을 반복 재생하지 않는다.
  - 계획 수용: 현재 배포본 관련 60 PASS와 별도로 과거 미분류 승계 누락·원천 검증 호출 0회를 격리 재현했다. 장후 감시 전용 검사/알림 stage 허용 및 실제 tower 발행 누락까지 계획에 포함했다. 계획은 link·단일 owner·authority·diff·print-only parser로 검증하며 진행 중 장후 recovery/source 세대·불변 실행 코드·selector를 교체하지 않는다.
  - 구현 검증: event-only 원천 재검증·부분 cohort quarantine·forward 거래일 봉인 대사·source-only custody·null/0·정확 terminal/cost·64MB metadata 예산/세대 cache를 보완했다. 실제 direct tower/checklist 발행 누락을 추가 발견해 report/policy receipt와 단일 block을 연결했다. 공통 validator/summary/scoped strict·artifact freshness/장중 표시·알림 mock·자정 분석일 전파를 반복 리뷰·보완했고 최종 영향 11 suite 565 PASS·compile PASS다. 검토 범위 미해결 코드 finding 0.
  - 추가 리뷰(10/3): 완료 run의 원 날짜 감시 누락, 완료 소비 불일치의 영구 pending, pending 소비의 잘못된 알림 회복을 재현·수정했다. 읽기 중 파일/원천/native 교체와 오류, 알려진 reuse 결함의 보존도 보완했고 30개 회귀를 추가했다. 최종 11 suite 595 PASS·compile PASS, 검토 범위 미해결 코드 finding 0. 초기 565 PASS 이력 및 운영 수용 경계는 유지한다.
  - 남은 수용: 10/3 01:30:24 KST read-only snapshot에서 이번 8개 producer/consumer는 별도 source 복구 선택본 63936cf1과 모두 SHA가 다르고 운영 10/2 report에는 새 reconciliation contract가 없어 자연 수용은 not_observed다. 작업본 통합·실행 세대 결정 후 고정 10/2 원천의 새 report/policy→동일 summary/tower→10/6 checklist→cancel-wait strict/의미감시를 한 번 대조한다. 결손은 source_gap/null·owner/closure test로 보존하고 양의 EV/실제 체결을 코드 수리 종료 조건으로 추가하지 않는다. 선택본·매매 프로세스·독립 pin은 이 작업에서 교체하지 않았다.
  - 인계 범위: 10/2 원 분석일의 코드 수리는 완료했고 이번 OPEN은 새 실행 세대의 계약·last consumer 확인이다. 실제 발행일/next trading date 및 기존 PREOPEN/PID owner 계약을 지키며, 인계 문서는 배포·재기동·원천 재생 실행 영수증이 아니다.
