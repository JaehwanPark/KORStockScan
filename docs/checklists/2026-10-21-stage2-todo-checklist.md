# 2026-10-21 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-20", "sources": {"entry_cancel_wait_policy": {"sha256": "ae39db733b8cdbdb6842b5da2a1d8c194856ce134878807b73d143b4c2049d11"}, "entry_cancel_wait_tuning": {"sha256": "5a990f09fdae96453a80e510f9c7d3444de767e94bfce2dc39efd233b9f9e97b"}, "holding_path_vote_policy": {"sha256": "ce5badd8996f00f4dc76008200decf3eeebc4c335969352b591820f70de89a26"}, "initial_quantity_refresh_stage": {"sha256": "9a0e57c7562010036d0601c1931c2a2634501340d7a7ce8297ccfb7a07929b27"}, "runtime_approval_summary": {"sha256": "8931bdad892e6fa2f34e23a6dde3449fdd20b52d5319a8ef5905f0eedf612790"}, "stage_legacy_machine_report": {"sha256": "eb59b0294ec0deadd307dd74c74592c3d6bed851dffbeb3e0adc6fdea34ad3b1"}, "stage_main_auxiliary_policy": {"sha256": "5cf08df0a4e3205e73577d2f4294c20bdc78551381557a6d0f50d558e4f9ec03"}, "stage_main_machine_policy": {"sha256": "61be4bb4e8dc4cd4d8a4c5370700432f824fba5dad91d0a5041d1745fc9dc236"}, "stage_main_stop_confirmation": {"sha256": "d4ac80eef5370f6beeee22dce9e8f1efd76461846bea729f6db4f4ad339f0405"}, "stage_outcome_labels": {"sha256": "0569174c2e406b5fd91af9cf4637cc9da8d7b3b9ddc5cb31fcade2a1ff4b5be0"}, "stage_pre_submit_delay": {"sha256": "780e011ff5fd3349067ef46e1fa8b9e1e7931fb28eb8d193483b02e63177668e"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-21", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "6b90d0f9aee20d10971eb9ea38b1c573a00850b81d834655794ee70e62201ac7", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-21.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-20", "source_report_sha256": "0c5753e5e3fc6451d8b75163298aa5c0c1115687b61723be4142334b758b475b", "status": "verified_incumbent_carried", "target_date": "2026-10-21"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-21.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "9193fdd82b56e4f8c24d09084af377edb311e5394a2ca9ac99c445f4d6dfcffe", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "ae39db733b8cdbdb6842b5da2a1d8c194856ce134878807b73d143b4c2049d11", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "aa23a8c82f8560dffdf2d11764ddc8287ee21da46d8541d902e0a0085e7f3f57", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "9193fdd82b56e4f8c24d09084af377edb311e5394a2ca9ac99c445f4d6dfcffe", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "ab345aba32377070b146bbed3b2ccc010e7f34b8b0eb5abdbb99ca878f5dbad9", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "4ca6bddab163d3827228588ad789e0fc3be3e4fe5e76a41bf68d6da6f5ba6d6c", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "e7679b6f37a6ce46feeabf2f53e1027732f35796e665055d4392dc9f9f212c58", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-20", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-21.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-20`; next apply date: `2026-10-21`.
- 아래 상태는 summary `8931bdad892e6fa2f34e23a6dde3449fdd20b52d5319a8ef5905f0eedf612790` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
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
| `main_mechanistic_entry` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `compact_auxiliary` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-21`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - 2026-10-21 08:22 실제 e427/PID960453/start18304028 native handoff·bootstrap 소비 PASS. 후속 finalization summary/checklist 세대 불일치와08:25 역사 사건의 발송 대기 오판을 기존 owner에서 수리·검증한다. 원 source/stage/snapshot/정책·실패 바이트 보존, 새 결손 탐지 유지. [원인·회귀·최종 소비](../audits/postclose-root-cause-recovery-review-2026-10-19.md#finalization-generation-and-pending-historical-notifications--2026-10-21). 09:00 selected6978/PID1139985/start18530727 native consumption PASS; original source20 finalization generation recovered with late-completion warning retained. 034020 native open-loss guard classification repair e0d07d4ab deployed09:18:50; PID1166767/start18643263 native consumption and current process_health PASS, active block0. Deferred artifact/resource/provider and late-finalization warnings remain recorded in the audit. Current08:31 native-root rejection cause still requires its next exact rejection receipt.
  - Source: [runtime_approval_summary_2026-10-20.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-20.json)
  - 판정 기준: source_date=`2026-10-20`, apply_date=`2026-10-21`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=9668356862bc7c2fda91e6daee541cbd35d560a9af8a988358906dd7b305089a, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] auxiliary 정책 생성 코드·원천 세대 계약 검증` (`Due: 2026-10-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-20.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-20.json)
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`auxiliary`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`8931bdad892e6fa2f34e23a6dde3449fdd20b52d5319a8ef5905f0eedf612790`, source_date=`2026-10-20`, artifact=`/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/2026-10-20/evaluation.json`, report_sha256=`78a003022686d8db123a092a695f9e490a401f4539f886ee48d9740a704c5a5c`.
  - 세대 결속: source_generation=`2dabd05c1e3b4655bde2395cd176742048aca2867f5bbac02006a08abd1d957c`, code_sha256=`4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac`, contract_sha256=`d721f7c80173371ade43197c338fa0ab2f67da39a6836380351ba22e6443fa73`.
  - 완료 기준: repair_owner=`DirectFamilySourceRepairCompactAuxiliary`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-20.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-20.json)
  - 증거: runtime_summary_sha256=`8931bdad892e6fa2f34e23a6dde3449fdd20b52d5319a8ef5905f0eedf612790`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-20.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-20`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.
  - <!-- POLICY_GENERATION_CAPABILITY_TASK -->
  - 정책 생성 코드 계약: family=`entry_cancel_wait`, status=`unverified`, findings=`['policy_generation_unverified']`.
  - 원본 증거: runtime_summary_sha256=`8931bdad892e6fa2f34e23a6dde3449fdd20b52d5319a8ef5905f0eedf612790`, source_date=`2026-10-20`, artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-20.json`, report_sha256=`5a990f09fdae96453a80e510f9c7d3444de767e94bfce2dc39efd233b9f9e97b`.
  - 세대 결속: source_generation=`7c684824788b9b894b4782f34f2fd2231c64a983e19bb76ba175587c46495752`, code_sha256=`47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff`, contract_sha256=`9648cbb507f56b70992a25d2312152adf2cf5dac44dc8f377c07d8c90bc5ef38`.
  - 완료 기준: repair_owner=`DirectFamilySourceRepairEntryCancelWait`, closure_test=`eligible_source_to_selection_publisher_native_reader`; 같은 원천·코드 세대의 fixture와 native reader 계약을 검증한다.
  - 권한 경계: report_only, runtime_effect=false, allowed_runtime_apply=false. 운영 정책의 경제성·PREOPEN handoff와 독립된 코드 검증이며 provider·주문·정책 적용·재기동 또는 비용 후 성과를 승인하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-20.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-20.json)
  - 증거: runtime_summary_sha256=`8931bdad892e6fa2f34e23a6dde3449fdd20b52d5319a8ef5905f0eedf612790`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-20.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-20`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:1fbd41bcb0e74e44f9ef018b0e162f6a3cbc92f46789e19185a8d04af011f219 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-20; 발행 2026-10-20; 적용 2026-10-21. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": "current_main_position_open", "known_open_count": 3, "status": "known_open"}, "daily_state": "submitted_orders_observed", "daily_submitted_parent_count": 4, "daily_zero_is_verified": false, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 25, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 33, "missing_dates": ["2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "recovered_source_dates": ["2026-09-30"], "report_proof_sha256": "1716ab6ee436fbd2cf2cc77adf30d5463b2eff6fc4fba64dcf27225b91b875bf", "research_evaluation_status": "model_unvalidated", "runtime_effect": false, "source_date": "2026-10-20", "status": "incumbent_carry", "terminal_unverified_count": 33, "unclassified_submission_count": 11, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->


## 미완료 원천 진단 인계

- [ ] `[InitialQuantityProducerConsumerRepair1010] 매수수량 원천·fact·시간창·장후 소비 결손 수리와 자연 수용` (`Due: 2026-10-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~23:59`, `Track: RuntimeStability`)
  - 08:20 source closure: e427676c4 reviewed; native four-archive enrollment51,898,161B preserved originals, trailing20,824scopes/currentness and quantity code-isolated proof PASS. Required live-policy/delay/stop/holding preflight PASS; ordered deployment/PID/detector remain pending.
  - Historical-source repair candidate 81c93baf9: three research-cost successors recovered; eight original exclusions retain exact IDs/hashes. Code-addressed native quantity proof preserves incumbent/candidate readers; 534 targeted tests pass. Ordered deployment and actual PID consumption are pending.
  - 22시 후속 보수: 원 수량 proof의 raw→native gzip 변환은 논리 SHA/size/원 inode identity로 대조하고, 비용·다른 원천 변경은 계속 거부한다. source19 proof는 기존 publisher의 전체 native 검증 후만 재발행하며 과거 비용/terminal 결손은 null로 보존한다.
  - 10/20 이관: 기능 수리·리뷰·native 재생·source19 strict/controller·20일 정책/PID 소비 완료. 수량 stage `4f3e04811174fa6fe7c8559c65994103d26d99116c572f16b159a9bd1577e82c`의 실제 마지막 소비를 확인했다. 6유형 기존 10/15/20/25/25% 부모 정책 유지; 실제 비용·terminal이 없는 과거 행은 null/제외로 보존한다. 아래 기존 Acceptance·실패·자연 수용 이력은 보존하며 다음 자연 완료 비용 표본만 대조한다. 코드 완료를 새 EV/실주문 성과로 해석하지 않는다.
  - 10/20 07:30: R19 native holding 18.623s와 최종 원천검사 결속 수량86c16e96을 확인. 손절은18 position 계산 후 indexed vote와 raw byte 세대의 비교 결함으로 최종 게시 실패. 원 실패 보존 후 기존 native typed verifier로 수리 중이며21 focused/48 handoff PASS. 전체 회귀·새 선택·재생성·20-date PREOPEN/PID는 미완료. [원인 수리 리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md)
  - 적용 수용: e7f4e2e8f/PID1495185/start3859414 ordered complete, 원 정책5파일 SHA 불변.16:18:50 자연 full에서 initial_quantity alert0·resource PASS, 과거 제외5/유효8/원 source_gap·null 보존. 새 결손·현재 수집 실패 경보 및 다음 자연 완료 비용 표본의 수용은 계속 유지한다.
  - 16시 반복경고 수리: full native 검증을 통과한 원16일 고정 제외5건은 exact stage/report/input_manifest·ID/행 SHA·사유에 묶어 역사 감사 진단으로 분리한다. 새 결손/새 세대/원천·비용 변경/현재 계약 실패는 경보 유지, PnL null·원 보고서·선택 수량 정책 불변. 원 SELL 재관측 중복 오판은 현재 코드의 native custody/시각/payload 대조로 수리되어 있으며 다음 자연 표본은 별도 수용이다. [코드 검토·적용 근거](../audits/preopen-alert-repair-2026-10-19.md#16시-역사-수량-제외와-현재-장애-분리).
  - 10:50 후속: 큰 실행 행의 bounded 필드 복원·이월 snapshot의 native SHA 검증 후 부분 디코드·과거 registry prefix의 날짜 없는 native 대사 이벤트를 수리했다. 431+3,132회귀 PASS와 정식 완료 prefix→fact→수량 재생성/현재 trailing 연구/PID 수용은 분리한다. [진행 근거](../audits/preopen-alert-repair-2026-10-19.md#1050-원천-계약-경보-후속-수리).
  - 재기동 복구: 보존 hard link가 원문 바이트 변경 없이 ctime을 변경하여 99e158af1 기동의 Main stop 검증이 실패했다. 실패 전환·시작 보류를 보존하고 원문 전체 hash 검증 및 정확한 starting/timeout 복구를 새 검토 릴리스로 수행한다. 원 정책/PREOPEN/strict/controller는 수정하지 않는다.
  - 10:01 후속: 이월 snapshot 전체 디코드로 인한 swap/I/O 경보와 SELL 재관측 중복 판정을 함께 수리한다. 연구 비용3건의 격리 복원·475회귀 통과와 운영 재생성/PID 수용을 분리하며 원 비용·custody·정책 결속 결손은 유지한다. [후속 근거](../audits/preopen-alert-repair-2026-10-19.md#1001-io-경보와-수량-원천-후속-수리).
  - 10/19 추가 경고: 기존 완료13건의 비용/수량 결손과 운영 research-cost index 부재를 확인했다. native completion prefix→fact→quantity를 재생성하고 연구 배분/실제 비용/복구 불가 결손을 구분한다. [실행 검토](../audits/preopen-alert-repair-2026-10-19.md).
  - 재개 근거: [10/17 수량 정밀 점검](../audits/initial-quantity-runtime-postclose-result-review-2026-10-17.md)의 IQ171~IQ175와 [전체 장후 후속 수리](../audits/postclose-complete-semantic-repair-2026-10-17.md). 기존 계획의 완료 이력은 보존하고 새로 재현된 producer/consumer·유효 빈 모집단 오판만 재개한다.
  - Source: [원 producer/consumer 계획](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md), source date `2026-10-16`의 봉인된 completion snapshot·native fact·수량 refresh report/evaluation 및 원 attempt/PID/start ticks에 연결된 수집 영수증.
  - Acceptance: 완료거래 prefix→동일 세대 fact→수량 연구→AI writer 종료 후 holding suffix 순서를 검증한다. 표시 300건 제한 이전 전체 모집단, emitted_date 보존, 대용량/gzip 원천의 bounded native 계약, DB 교체 중 변경 rollback, 후보 시간창별 finished/interrupted 구분과 늦은 영수증 cache 무효화를 확인한다.
  - 원천 비용·terminal·과거 중단 자료 부재는 `null`/제외/명시적 `source_gap`으로 남기며 `valid_empty` 또는 0원으로 대체하지 않는다. 기존 6개 유형 10/15/20/25/25%와 분할·timeout 프로필을 보존하고 추가 경제성 승인 gate·주문·provider·threshold 변경을 만들지 않는다.
  - 코드/장후 재생성 완료와 다음 자연 수집 수용은 별개다. 새 배포 이후 실제 시작/종료/중단 영수증과 비용 원천의 정확한 대사를 확인하며, 10/19 PREOPEN·PID 소비는 기존 `DirectFamilyPreopenPolicyHandoff`만 소유한다.


- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-21`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - Historical-source repair candidate 81c93baf9: immutable source20 disposition binds decision49389 and two original reasons to exact report/source hashes and repaired collection49391. New/current loss remains actionable. Native handoff 63 tests pass; actual PID and final health are pending.
  - 10/20 장후 신규 실패:88351 원 run a6533581·손절44a4ab85가21:38:57 `ProjectionReader.fill(size)` 인자 계약 불일치로 실패했다. 원 로그/status/selector 바이트를 보존하고 기존 reader·source index 경계 회귀와 native 마지막 producer 복구 후 final-handoff 재개를 기존 owner에서 보완했다. 대상174 PASS·compile/bash/diff 검증을 통과했으며 원 성공 기계/AI 재실행은 불필요하다. 장후 복구 승인 후22:16 기존 lock/CAS로72617981b를 선택하고 대기 controller/tuning만 종료했다. Main 없음·기동 없음; 손절f54015a1 성공→Main1b31f585 DONE→whole strict/controller done·tuning 성공·10/21 prepared_verified까지 실제 소비했다. 후속220127 통합 배포/P5는 DirectFamily owner에서 별도 검증 중이다. 수리 code와 실제 손절→summary→strict/controller→최종화 소비는 별도이며, 실제 복구 전 OPEN을 유지한다. [원인·수리·최소 재개](../audits/postclose-root-cause-recovery-review-2026-10-19.md#2026-10-20-postclose-stop-projection-refill-failure).
  - 11:40 후속:04be/PID457081 기동 후 report2a68의 원49389 BUY 결속 결손2사유가 새 report 세대마다 재통보됐다. 기존 native semantics/incident owner에서 정확한 원 signal/terminal 해시로 사건을 식별하고 원 손실·OPEN은 유지한다. BUY 결손의 조기 policy 검사 생략도 수리한다. 동일 원문 재게시 중복, 새 원문/사유/불완전 관측의 계속 탐지, 실제 새 PID 보고서→탐지기 소비를 수용한다. [인과·리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md#1140-원-사건-buy-결손의-반복-통보-계약-수리).
  - 10/20 이관: 49389의 정수 잔고 표시가/원 분할체결 평균가 BUY identity 복원 결함과 native SELL ACK 결함은 a7c0b0dc5/PID4094188에서 복구했다. 오늘 원 snapshot의 BUY 세대 누락은 당시 증거 결손으로 유지한다. 보고서 terminal 재관측1,026회의 중복 집계와 문자열 typed context 수리를 리뷰·배포 후 실제 새 보고서/탐지기에서 확인한다. 원 비용·first crossing·자연 수용 Acceptance는 아래 그대로다.
  - 10/19 20:05 원천 수용:append_chain_gap의 원 cache snapshot/raw를 보존하고 전체 prefix를 재검증했다. 실제 선택deb reader에서1,769,045,113B/raw273,086/selected4,083 native generation verified, 마지막 gap19:46:05다. 신규 bounded cleanup은29회귀·source-only 소비, 과거deb closure 보존은36회귀로 검증했다. 연구 현재 code 결속 warning은 원 보고서/정책을 유지한 채 OPEN이며20:00 terminal005930 미해결은 실제 journal/broker terminal로 대사한다. 종료/비용 null·자연 AVG_DOWN stale/cutoff 차단을 성공으로 대체하지 않는다. [현재 reader 근거](../../tmp/avg-down-sor-deploy-20261019/selected-native-readback.json), [검토](../audits/avg-down-runtime-postclose-repair-review-2026-10-16.md#원천-복구-완료와-이미-소비한-generation-보존).
  - 10/19 추가 수리: 현재 선택 코드와 불일치한 all-scope trailing 보고서를 native holding suffix로 재생성해 후행 인계한다. 역사적 first-crossing5건과 자연 terminal/비용 Acceptance는 유지한다. [실행 검토](../audits/preopen-alert-repair-2026-10-19.md).
  - 10/16→10/19 인계: 원 Acceptance·Source·이력은 아래 그대로 보존한다. 과거 PID는 당시 이력이며 현재 Main은 EOD 뒤 자연 정지 상태다. c63d44bcb는 당시의 선택 이력이다. 이후 선택은 runtime release selector와 최신 검증 기록으로 확인하며 실제 PREOPEN/PID·자연 성과와 구분한다. [이번 검토](../audits/postclose-semantic-recovery-review-2026-10-16.md).
  - 10/17 후속: native holding/trailing의 현재 코드·target 10/19·전체 scope 원천 세대를 재검증하며, snapshot 이전 AI writer 미종결·구 세대 보고서의 정상 오판을 허용하지 않는다. [전체 장후 후속 수리](../audits/postclose-complete-semantic-repair-2026-10-17.md).
  - 10/16 정규 장후 신규 결함: native 보유 연구 feature 87,655바이트가 64KiB cache row 한도를 넘어 실패했다. 정상 관측32개를 기존 tree로 무손실 분할·검증 복원하고 단일 과대 관측은 기존 streaming으로 보존한다. 원 실패·완료 prefix를 보존하며 세 파일만으로 snapshot 완료를 주장하지 않는다. [수리 범위](../proposals/semantic-monitor-producer-consumer-currentization-plan-2026-10-16.md#14-장후-보유-연구-캐시의-물리-레코드-분할). 코드 검증 뒤 native exit snapshot→stop/summary/strict/controller→10/19 준비를 재점검하며 역사적 TP5건·비용 결손·실제 다음 PID 수용은 별도 유지한다.
  - 14:11:56 통합922b9cbc3 배포·재기동 완료: 요청91ff/e04를 포함한 새PID3729660/start19142841의 실제 소비·release-set·원 정책/수동 제외 보존 확인. 기동후holding14:12:23 native7.35초/새 결속 결손0, BUY14:13:46 현재PID/세대 verified·scanner 코호트 partial, full14:14:32 새실패0. broker 전후수량·미체결0·원장동일, fixed5 실제0B/0D 확인. 과거TP5건·역사적세대/자연편입·부분보유/경제성OPEN 유지. [최종 검증](../audits/main-probe-partial-integrated-deployment-review-2026-10-16.md#실제-배포와-기동-후-검증).
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

  - 10/19 09:18 현재 보유 경계: 알테오젠196170의 사용자 수동 지정은 해제했으나09:15:08 기존 hard-stop 규칙이-1.51%에서 새 auto_hard_stop_handoff를 생성했다. operator 수동 소유권으로 재등록하지 않으며 hard safety를 임의 해제하지 않는다. 큐리옥스49362 직접 청산은 별도 broker1+2주 영수증/원장0/DB COMPLETED로 닫았다. 최종 observer는 semantic partial, full artifact 검사는 resource contention deferred이므로 전체 건강 완료와 구분한다.

