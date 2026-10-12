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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-08", "sources": {"entry_cancel_wait_policy": {"sha256": "a6c11256631df36fea57f530cfc547fb1819747b8b95931af0ff760e779ddfdd"}, "entry_cancel_wait_tuning": {"sha256": "3b990ba3ba607b8f69ee8061a5f0aedc7f9a52c569aa14d2ad41958ebad69e3b"}, "holding_path_vote_policy": {"sha256": "7df6d8469a571e971cbca13ee57e10c28e6c52008a00d217fb4b36dc4364e24a"}, "initial_quantity_refresh_stage": {"sha256": "cd1e12ac85875c46f79fd064b8533a14732afe7068d06e0900f23d92fa8ac706"}, "runtime_approval_summary": {"sha256": "a86c25c2ef87cbab3d98c2bae0470e78000eba80b738934f19916f2ef8028c0e"}, "stage_legacy_machine_report": {"sha256": "409ab98c9181523041ce133bf3661b357b9d6951fcc29840b8b71b36a4d1a654"}, "stage_main_auxiliary_policy": {"sha256": "3ff42274508b06c216a138caf08e758f189da6734f2f918bcc4c2f25d2786c9a"}, "stage_main_machine_policy": {"sha256": "c017902624abac4a409dc23eaae6bbfa44d1cd7f081b87c6f790750ebe4ded62"}, "stage_outcome_labels": {"sha256": "e492a62963215b085e23c985d62336a6a936be510603582ece5417fa863f72d5"}, "stage_pre_submit_delay": {"sha256": "032782eb40b0e9adba97e49f5468f39c2c29894902283f3523a8473a9ea08bcd"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-12", "expected_state": "verified", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "4af72a38194cec2f59a70191111153add4de6797b35f7030aa622ba4a59d4b8e", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-12.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-08", "source_report_sha256": "a79b5f1cf6581631da863f82f78595825e3a8c27ec84c47a12b83bbb0d1f3a6d", "status": "verified_incumbent_carried", "target_date": "2026-10-12"}, "manifest_content_sha256": "0d2e2203731654ea97a58e68933b24fe63c61aff0fdc33de4868c39186a99cad", "manifest_env_sha256": "60edeac844de9355e8f9d13a2d679d78d3ea0fb683e755288483ff88a9ee064a", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-12.json", "manifest_sha256": "844abfa247dea3ac59e3bbfe04b397f5da7259000e33b003f0d486ac07934289", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "955b8551c06ad8f308dc3d0e4e0bf8cd214348dde0c18d51a4cd0427f1d38bfa", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "a6c11256631df36fea57f530cfc547fb1819747b8b95931af0ff760e779ddfdd", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "3f493607ae2210cd23dbcc49a4c287fc469e10750392a4ddea4b91d20c021425", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "955b8551c06ad8f308dc3d0e4e0bf8cd214348dde0c18d51a4cd0427f1d38bfa", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "5d6965735038034fb12be1b6af3823a813b815856182d04736c88fa91255d5aa", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "31fbaa57a009260d5d784868d58eab7b8df44a45e2aedd996a401cb797d465f1", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "fbc59cf51391554121bc02fec4a35cda3df91ccca8bb6b166149e4f8d56e4163", "valid": true}], "release_selection_sha256": "d6fd15cac876d5b5d295a4038244a504e7dc291149687f41d70d1dcb08678862", "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": "29118f4754e05c5672e6caaa48d736771cf27d6a", "source_date": "2026-10-08", "source_preopen_state": "verified", "source_reported_pid_receipt": true, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-12.json", "verification_sha256": "929fcb0df0f4ceb2500f92f9cc899213bf6c33cde9663aaf593585b85c8776d2"} -->

## Family 직접 증거 상태

- source date: `2026-10-08`; next apply date: `2026-10-12`.
- 아래 상태는 summary `a86c25c2ef87cbab3d98c2bae0470e78000eba80b738934f19916f2ef8028c0e` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
- direct source: `9/9`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `verified`; natural acceptance: `pending`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `initial_quote_timing_policy_published` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `compact_auxiliary` | `insufficient_sample` | `incumbent_preserved` | `producer_contract_repair` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] compact_auxiliary 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 증거: runtime_summary_sha256=`a86c25c2ef87cbab3d98c2bae0470e78000eba80b738934f19916f2ef8028c0e`, source_artifact=`/home/ubuntu/KORStockScan/data/report/continuous_reversal/2026-10-08/auxiliary.json`.
  - 상태: family=`compact_auxiliary`, task_role=`producer_contract_repair`, comparison_status=`insufficient_sample`, resolution_mode=`verified_policy_carry_comparison_incomplete`, prospective_resolution_mode=`-`, first_blocker=`contract_state_requires_followup`.
  - 완료 기준: closure_owner=`continuous_reversal_postclose`, closure_test=`exact_date_native_policy_and_normal_consumer_receipts`. policy_receipt_valid=`True`, source_date=`2026-10-08`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 증거: runtime_summary_sha256=`a86c25c2ef87cbab3d98c2bae0470e78000eba80b738934f19916f2ef8028c0e`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-08.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-08`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json)
  - 증거: runtime_summary_sha256=`a86c25c2ef87cbab3d98c2bae0470e78000eba80b738934f19916f2ef8028c0e`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-08.json`.
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
<!-- entry_cancel_wait_handoff_sha256:ed1537c059a6fa6161f27e6e0ae0fe096abc2f798acd441446b399e38ed61b61 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-08; 발행 2026-10-08; 적용 2026-10-12. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": null, "daily_state": "no_submitted_orders", "daily_submitted_parent_count": 0, "daily_zero_is_verified": true, "economic_population_status": "legacy_coupled", "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 0, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 0, "missing_dates": ["2026-09-29", "2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "8f97e95ada920a3adcce8f1526cee4e58d00fca9124f673c1bf4bb4b4f671dbe", "research_evaluation_status": null, "runtime_effect": false, "source_date": "2026-10-08", "status": "incumbent_carry", "terminal_unverified_count": 0, "unclassified_submission_count": 0, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->

<!-- initial_quantity_repair_natural_acceptance_20261011 -->

## 최초 수량 Q8 자연 수용

기존 OPEN owner `DirectFamilyPreopenPolicyHandoff`가 [10/11 초기수량 구현·배포](../audits/initial-quantity-producer-consumer-implementation-review-2026-10-11.md)의 다음 영업일 소비를 함께 확인한다. 별도 중복 owner를 생성하지 않는다.

- 07:35 PREOPEN에서 새 선택 릴리스·당일 bootstrap·현재 수량 정책의 파일/내용 SHA와 실제 env가 일치하는지 확인한다. 07:55 이후 실제 Main PID·start ticks·cwd 및 같은 정책 영수증을 대조한다.
- 현재 수량은 부모 정책 유지다. 코드 배포·준비 PASS를 실제 PID 소비·경제성 개선으로 대체하지 않는다.
- 자연 주문이 있을 때 첫 주문 시작+1200초의 quote route/item/epoch·probe 포함 순차 leg·큐 거부/종료·체결/취소 terminal을 확인한다. 주문이 없으면 관측 대기이며 실제 0원 경제 성과로 추가하지 않는다.
- 과거 비용/큰 native projection 결손은 제외 상태를 보존하며 새 비용 NULL/실제0·누적 세대 및 결속 원천은 정규 장후 생산자로 대사한다.

<!-- main_stop_semantic_natural_acceptance_20261011 -->

## Main 손절·의미적 감시기 배포 후 자연 수용

기존 OPEN owner `DirectFamilyPreopenPolicyHandoff`가 [10/11 손절·의미적 감시기 배포](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)의 새 릴리스 소비를 함께 확인한다.

- 07:35 PREOPEN은 `main-stop-semantic-20261011-v1`의 bootstrap·당일 세대·실효값을 대조하고 07:55 Main PID의 cwd/start ticks와 loader/pin 영수증을 대조한다. 준비 PASS는 실제 PID 소비가 아니다.
- source10/8의 새 stop stage 부재는 `not_installed`이다. 10/12 장중에는 현행 실효값을 position pin으로 유지하며 새 stop 원천을 기존 bounded 큐로 수집한다. source10/12 장후부터 native stop stage가 실행되어 다음 영업일9cell 부모 계승/변경 계약을 발행한다.
- holding path vote는 v11의 생존4경로×3시장만 신규 요청한다. 과거 v10 원장/현재 수탁을 보존하며 퇴역 score/bad-entry/whipsaw·episode/widget actuator는 복구하지 않는다.
- 원천 큐 거부·수집 결손은 source-gap이며 실제 SELL/비용후 성과를 만들어내지 않는다. 신규 보호선 생성·vote 경제 변경 selector·전체 Main/host 성능·자연 청산은 각각 잔여 수용이다.

<!-- postclose_structural_natural_acceptance_20261011 -->

## 장후 원천·정책 생성 구조 배포 후 자연 수용

기존 OPEN `DirectFamilyPreopenPolicyHandoff`가 [10/11 구조 보완 배포](../audits/postclose-structural-policy-completion-implementation-review-2026-10-11.md)의 새 릴리스 소비를 확인한다.

- 07:35 PREOPEN 및 07:55 Main은 `main-postclose-structural-20261011-v2` / `5106ddaefb8fdaff8b06d92f8064a66f3256eaaa`를 소비하며, cwd/start ticks·loader 정책 hash를 대조한다. 오늘의 봉인 준비는 실제 PID 소비가 아니다.
- 기계/보조 정책과 수량 parent, 기존 손절·trailing·제출지연 실효값을 유지한다. 숫자 EXIT 실험은 승인된 frozen 계약과 전체 성능 receipt가 없으면 unarmed이며 신규 정책값을 합성하지 않는다.
- 기존 account-sync의 custody checkpoint, TP1 차단 시점의 cache/depth 원천, bounded queue의 complete/drop 상태를 기존 원천에서 확인한다. 정규장·애프터장의 판단 scope는 통합시장으로 유지하고 물리 venue와 분리한다.
- 퇴역 episode/widget/PYRAMID/Opening actuator는 복원하지 않는다. 자연 주문·청산·비용후 성과와 전체 연구 성능은 별도 잔여 수용이다.

<!-- cron_0535_night_repair_20261012 -->

## 최종화 예약·야간 연구 계약 보완

- [x] `[AuxiliaryReaderCompatibilityPreflight1012] 보조판정 호환성 증빙 준비·기동 사전검증 코드 보완` (`Due: 2026-10-12`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:25~10:00`, `Track: RuntimeStability`)
  - Source: [코드 리뷰·현재 후보 검증](../../tmp/auxiliary-reader-preflight-20261012/review.json). PREOPEN 후보·장중 인계·Main spawn 이전에 native compatibility/registry 검증을 수행한다. 누락·변조·검증 중 변경·미래 후보에 현재 증빙 대입을 거부하며 provider/broker 호출과 정책값 변경은0이다.
  - 코드 수용: 관련199회귀·compile·bash 문법·diff 검증 PASS. 실제 새 릴리스 배포/PID 소비는 [별도 운영 영수증](../../tmp/auxiliary-reader-preflight-20261012/completion.json)으로 확인하며 이 완료 표시는 코드 검증만 뜻한다. 기존 DirectFamilyPreopenPolicyHandoff와 원 PREOPEN/정책/기한은 보존한다.

- [x] `[CronFinalizationScheduleRepair1012] 최종화05:35 예약·야간 연구 검증/로그 보완` (`Due: 2026-10-12`, `Slot: IMPLEMENTATION`, `TimeWindow: 06:55~07:35`, `Track: RuntimeStability`)
  - Source: [리뷰·적용 근거](../audits/cron-finalization-0535-and-night-research-repair-2026-10-12.md). 사용자 실제 예약 변경·결함 보완·배포 승인에 따라 cron/installer/router/감시 창을05:35로 일치시키고06:00·06:50 마감은 유지했다. owner 행 위치 오인과 MTA 부재 로그 유실을 보완하며 기존 연구 예산·알림·매매 경계를 유지한다.
  - 종료: workspace/불변 release282 passed·원천/정책값 보존·실제 설치 readback·native strict/controller/PREOPEN 재봉인으로 수용한다. 실제05:35 예약/야간 연구 실행은 아직 미관측이며 별도 자연 수용이다.
  - 기존 OPEN `DirectFamilyPreopenPolicyHandoff`는 새 `cron-0535-night-repair-20261012-v1` / `5ca5f585b104bb4c441f949d4051ff090a9c0e9a`의07:35/07:55 예약 소비를 함께 대사한다. 이 코드 교체가 정책값이나 새 실주문 권한을 만들지 않는다.

<!-- auth_historical_replay_repair_20261012 -->

## 인증8005 역사 로그 재탐지 보완

- [x] `[Auth8005HistoricalReplayRepair1012] 역사8005 오탐·false restart 요청 보완` (`Due: 2026-10-12`, `Slot: IMPLEMENTATION`, `TimeWindow: 07:15~07:35`, `Track: RuntimeStability`)
  - Source: [리뷰·원상 영향 근거](../audits/auth-8005-historical-log-replay-repair-2026-10-12.md). 원09일22:36:36 오류를12일07:00 새 장애로 처리한 결함을 수리했다. 역사 시각 행은 원 evidence로 분리하며 현재 오류·시각 미상·retry/handoff·cooldown/cap 계약을 보존한다. 원 false flag/count1은 정확 actor 근거로 철회·정정했고 token을 복원/수동 발급하지 않았다.
  - 종료: workspace/불변 release174회귀, 새 코드 CAS·strict/controller/PREOPEN 재봉인으로 수용한다. 실제 당일 인증·07:35/07:55 새 릴리스/정책 PID 소비는 기존 OPEN `DirectFamilyPreopenPolicyHandoff`가 대사한다.
  - 현재 선택 릴리스는 `auth-history-guard-20261012-v1` / `5f9309222d837baf7227edcc8b4b60ff85bdfef1`이며 이전05:35 예약 및 정책값은 유지한다.

<!-- preopen_activation_binding_repair_20261012 -->

## 실패 PREOPEN 실제 활성화 연결 복구

- [x] `[PreopenActivationBindingRepair1012] prepared PASS 이후 기계정책 릴리스 불일치 보완` (`Due: 2026-10-12`, `Slot: IMPLEMENTATION`, `TimeWindow: 07:35~08:40`, `Track: RuntimeStability`)
  - Source: [원인·리뷰·복구 근거](../audits/preopen-activation-release-binding-repair-2026-10-12.md). 원07:35:33 failure는 보존하며 exact target12 후보를 신규 release에 동일정책 code refresh로 결속한다. 등록·threshold·AI·provider·주문 정책은 재선정하지 않는다.
  - 종료: 관련 회귀·wrapper 검증와 불변 release 검증, source8/publication11/effective12 CAS·strict/controller·prepared 재봉인으로 수용한다. native PREOPEN 실제 성공과07:55 Main/PID 소비는 기존 OPEN DirectFamilyPreopenPolicyHandoff에서 확인한다.
  - 선택 릴리스: `preopen-candidate-binding-20261012-v4` / `29118f4754e05c5672e6caaa48d736771cf27d6a`;05:35 최종화 예약은 유지한다.

## Buy Funnel 보고서 직렬화·복구 판정 코드리뷰

- [x] Buy Funnel 판정 증빙 시각의 JSON 내보내기와 반복 크론 복구 판정 보완 (`ID: BuyFunnelSerializationRecovery1012`; Priority: P0; Track: report; Slot: intraday-code-review; TimeWindow: current-session). 사용자 구현·배포·재기동 승인 범위다. 시각 ISO 정밀도/시간대 보존, 전체/소형 보고서 원자 교체와 기존 reader 권한 보존, 최신 동일 owner DONE의 과거 FAIL 회복 및 재실패 검증을 완료했다. 이 체크는 코드리뷰 종료이며 배포·자연 크론 DONE·소비 보고서 경고 해소는 `tmp/buy-funnel-serialization-repair-20261012/completion.json`의 별도 현재 증빙으로 확인한다. 기존 trading policy·PREOPEN 원본·원천/증빙 해시·5초 기한·주문/provider 권한을 보존한다. Source: [운영 계약](../runtime-release-routing.md#buy-funnel-report-recovery).
