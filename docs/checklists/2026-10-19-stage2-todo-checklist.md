# 2026-10-19 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-16", "sources": {"entry_cancel_wait_policy": {"sha256": "7ff2830f67f728867508209cb7ada66cc9c8657e636ba08018965384278c05fe"}, "entry_cancel_wait_tuning": {"sha256": "8de6359a286bcebbac693bd1c67b539463dbb8c0bbd63825672b5b5f57a84a9d"}, "holding_path_vote_policy": {"sha256": "bd6f568e6fa41b95664015facb364bf434b83ed6af952e0ef7b7319f6ac3ef9a"}, "initial_quantity_refresh_stage": {"sha256": "3498bba900a84ab67c0428e1b2e4b4d39a0798d1227f696a05333263e84ff0df"}, "runtime_approval_summary": {"sha256": "251fdcd9c2bfb1723558ce7e9694a6d45ad7cef377a339e8b574af074198af86"}, "stage_legacy_machine_report": {"sha256": "43936d40cc47c919f0a43d7bbd19f05ef2a64873d3106f0afc609e05ac3fec2f"}, "stage_main_auxiliary_policy": {"sha256": "39eabccbf9139d2e0aa5807e4e2f64f29e75d5692c700c9f97d8729730ae1147"}, "stage_main_machine_policy": {"sha256": "611f30f6fb3842a7948cbb9516e438efbd1ce81daa94956a78810c38c849db65"}, "stage_main_stop_confirmation": {"sha256": "c7a2ea821adb7c70859ef3442ad2cd00e7c34d598f6446a5c1a4c71fa3c23cd7"}, "stage_outcome_labels": {"sha256": "d5b395f0fa178445aa020353b63dbac2f9a4a6d56763a87030cf860f8e65b1c4"}, "stage_pre_submit_delay": {"sha256": "b0fe63c7f8887c68daf50c94222e32c7122191f4d086410e3ffe8b6d3dec1daf"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-19", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "d973d1984621638708cd36828e3d5fecea6446ae925d1c0d41890ced304c33b1", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-19.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-16", "source_report_sha256": "eb1defcc1300aaf8bcea9429eacdb896c486a980e306f60e65cbb81478d08eef", "status": "verified_incumbent_carried", "target_date": "2026-10-19"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-19.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "6c153aeb50e5063fa1d78dd912bc052952e78e4dbfa6f8c22555a2299ebc4881", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "7ff2830f67f728867508209cb7ada66cc9c8657e636ba08018965384278c05fe", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "94fbd34b5ecbab6da39cca92067270e3f5ff845b133f955a6244fc868922178e", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "6c153aeb50e5063fa1d78dd912bc052952e78e4dbfa6f8c22555a2299ebc4881", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "a7c669184e0359f12f98baf119d3af3c27302eb6830885e418b3157a66986865", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "5d005ad8e0e895d88e80cf12e979070567aeb62da8e3fb52ea8a808e0c027d72", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "d0017ee54b4e4f57ea59566ae9425bd354d921f9dbcee4334c0dc122bc66be6b", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-16", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-19.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-16`; next apply date: `2026-10-19`.
- 아래 상태는 summary `251fdcd9c2bfb1723558ce7e9694a6d45ad7cef377a339e8b574af074198af86` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
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

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-19`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-16.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-16.json)
  - 판정 기준: source_date=`2026-10-16`, apply_date=`2026-10-19`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=8f9c91c04f6949869c7f32db8175851a386c97afd9bafb8b4dbb4f1fa847f5d4, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-16.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-16.json)
  - 증거: runtime_summary_sha256=`251fdcd9c2bfb1723558ce7e9694a6d45ad7cef377a339e8b574af074198af86`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-16.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-16`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-16.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-16.json)
  - 증거: runtime_summary_sha256=`251fdcd9c2bfb1723558ce7e9694a6d45ad7cef377a339e8b574af074198af86`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-16.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-16`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:88b08282765bc788111d3fdcde12f77525796c7cba61c2de78c98bfe21cf9de9 -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-16; 발행 2026-10-16; 적용 2026-10-19. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": "current_main_position_open", "checkpoint_superseded_historical_dispatch_count": 6, "historical_terminal_or_profit_inferred": false, "known_open_count": 3, "status": "known_open"}, "daily_state": "source_gap", "daily_submitted_parent_count": null, "daily_zero_is_verified": false, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 10, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 10, "missing_dates": ["2026-09-30", "2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "report_proof_sha256": "dd29ec0607507e2315bd33fc2bad027cd4c835cca81ce7d319e7e7a5b5183cd5", "research_evaluation_status": "model_unvalidated", "runtime_effect": false, "source_date": "2026-10-16", "status": "incumbent_carry", "terminal_unverified_count": 10, "unclassified_submission_count": 3, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->


## 전일 미종결 계약과 역사 원천 인계


- [ ] `[InitialQuantityProducerConsumerRepair1010] 매수수량 원천·fact·시간창·장후 소비 결손 수리와 자연 수용` (`Due: 2026-10-19`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - 재개 근거: [10/17 수량 정밀 점검](../audits/initial-quantity-runtime-postclose-result-review-2026-10-17.md)의 IQ171~IQ175와 [전체 장후 후속 수리](../audits/postclose-complete-semantic-repair-2026-10-17.md). 기존 계획의 완료 이력은 보존하고 새로 재현된 producer/consumer·유효 빈 모집단 오판만 재개한다.
  - Source: [원 producer/consumer 계획](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md), source date `2026-10-16`의 봉인된 completion snapshot·native fact·수량 refresh report/evaluation 및 원 attempt/PID/start ticks에 연결된 수집 영수증.
  - Acceptance: 완료거래 prefix→동일 세대 fact→수량 연구→AI writer 종료 후 holding suffix 순서를 검증한다. 표시 300건 제한 이전 전체 모집단, emitted_date 보존, 대용량/gzip 원천의 bounded native 계약, DB 교체 중 변경 rollback, 후보 시간창별 finished/interrupted 구분과 늦은 영수증 cache 무효화를 확인한다.
  - 원천 비용·terminal·과거 중단 자료 부재는 `null`/제외/명시적 `source_gap`으로 남기며 `valid_empty` 또는 0원으로 대체하지 않는다. 기존 6개 유형 10/15/20/25/25%와 분할·timeout 프로필을 보존하고 추가 경제성 승인 gate·주문·provider·threshold 변경을 만들지 않는다.
  - 코드/장후 재생성 완료와 다음 자연 수집 수용은 별개다. 새 배포 이후 실제 시작/종료/중단 영수증과 비용 원천의 정확한 대사를 확인하며, 10/19 PREOPEN·PID 소비는 기존 `DirectFamilyPreopenPolicyHandoff`만 소유한다.


- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-19`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
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

- [ ] `[OperationalLogRetentionRepair1016] 작성자 로그 회전·보관·역사 원천 압축 적용 확인` (`Due: 2026-10-19`, `Slot: INTRADAY`, `TimeWindow: 통합 배포 후`, `Track: RuntimeStability`)
  - 10/16→10/19 인계: 원 Acceptance·Source·이력은 아래 그대로 보존한다. 과거 PID는 당시 이력이며 현재 Main은 EOD 뒤 자연 정지 상태다. c63d44bcb는 당시의 선택 이력이다. 이후 선택은 runtime release selector와 최신 검증 기록으로 확인하며 실제 PREOPEN/PID·자연 성과와 구분한다. [이번 검토](../audits/postclose-semantic-recovery-review-2026-10-16.md).
  - 10/17 추가 계약: Parquet source receipt의 물리 파일 고정이 무손실 압축 뒤 consumer를 거부하는 결함을 수리한다. 원 decoded SHA/크기와 producer CRC 검증 후 archive inode/ctime 세대를 봉인하며, health는 작은 issued 세대만 점검하고 full native 검증은 원 producer/finalizer가 소유한다. [전체 수리](../audits/postclose-complete-semantic-repair-2026-10-17.md).
  - 반복 읽기 보완: 정규 postclose snapshot 및 손절 CLI의 단일 호출 동안만 기존 digest session을 공유한다. 첫 전체 검증·ctime 변경 검출·producer 실패와 lock/wrapper gate는 유지하고 호출 종료 후 캐시는 폐기한다. 저장 압축 인계와 의미/경제성 수용은 분리한다.
  - 후속 사용자 지시: 비압축 보존 임시책을 논리 원천 인계로 대체한다. 원문 해시·inode/ctime과 압축 세대/해시·왕복 일치 영수증으로 holding/trade/projection을 압축한 채 정책·window·손절·bootstrap을 검증한다. 큰 원문은 선택 함수에서 decode하지 않으며 동일 세대 digest와 작은 metadata를 재사용한다. 실행 중16a5 체인은 교체하지 않으며 종료 후 다음 기동 선택·준비·strict를 재검증한다. [후속 계약](../proposals/semantic-monitor-producer-consumer-currentization-plan-2026-10-16.md#16-사용자-지시-후-논리-원천-인계를-갖춘-압축으로-전환).
  - 10/16 장후 보완: archive가 과거 holding 원문을 제거해 현재 정책의 재귀 handoff가 incumbent_unverified가 되는 결함을 확인했다. 보유 정책 원문은 압축 제거 대상에서 보존하고, 기존 gzip과 원 정책 해시가 일치하는5개 원문만 복원한다. 실제 policy→archive→native verify 회귀와 다음 장전 소비를 [후속 계약](../proposals/semantic-monitor-producer-consumer-currentization-plan-2026-10-16.md#15-압축-후-보유-정책의-원문-ancestry-보존)으로 확인하며 원 실패·정책·summary/strict는 보존한다.
  - Source: [운영 계약](../operational-log-retention.md), [원 점검](/home/ubuntu/KORStockScan/tmp/log-retention-audit-20261016-114851/report.md).
  - Acceptance: LR01~LR09의 cron/닫힌 세대/열린 FD·pin·참조 보호, 실패 cooldown 미갱신, 독립 달력 주기, 당시 strict/checklist 원본을 보존한 검증 압축, tmp 보호·용량 경보, journal 설정을 실제 적용 영수증으로 확인한다. 증거 미확인 파일은 삭제하지 않는다. 자연 만료 삭제·새 신호·실제 주문/경제 성과는 코드 PASS와 구분한다.


장기4개 통합 후속: 67c0cee49의 원 failed transition을 보존한 복구/PID18623 소비를 확인했다. `DirectFamilyPreopenPolicyHandoff`는 drain 전 active policy 인계 강제 검사와 기동 직후 observer 게시 순서를 수리·최종 PID로 수용한다. `OperationalLogRetentionRepair1016`는 과거4일 검증 압축12,174,530,638bytes 절감 및 당시 증거 보존을 확인했고, 손절 원천 소비의 gzip 전환 오판 수리 후 detector 재검증을 소유한다. 손절 수치와 원 정책은 유지한다. 상세 결과는 기존 통합 검토에 기록한다.

삼성 선택 연구 원천 삭제 확인: 사용자가 과거 원천을 의도적으로 삭제했음을 확인하여 이번 세션이 추가한 복구 작업을 취소했다. 삭제 원천을 복원하거나 연구 성공으로 대체하지 않는다. 남아 있는 optional forward 검증은 과거 후보의 source seal을 재확인하기 때문에 실패하며, 당일 분석은 별도의 당일 관측·가격·체결 자료를 사용한다. Main 정책·기동의 필수 조건이 아니다. 과거 연구 종료 또는 예약 호출 제거는 이 확인과 구분한다.

후속 전수 검토(10/17): 원 실행·과거 경고는 [후속 검토](../audits/postclose-semantic-recovery-review-2026-10-16.md#1017-후속-전수-검토와-재생성)로 구분한다. 분할진입의 현재 atomic 계획8·주문10·residual2 연결과 발행 모집단 보존, 현재 Main custody3건, 기계58건 정산/미계상0을 확인했다. cancel/rising/auxiliary/holding의 새 native generation4개도 검증했다. 경제성 결손·과거TP5건과 자연 PREOPEN/PID Acceptance는 별개이며 기존 owner를 유지한다.

- 10/17 비영업일 점검의 담당자 연결은 검증된 source 10/16 DONE 및 target 10/19 prepared PASS가 일치할 때 이 체크리스트의 기존 OPEN stable ID를 사용한다. 관측일을 10/19로 바꾸거나 새 실행 권한을 만들지 않으며, 실제 PREOPEN/PID 소비 확인은 기존 DirectFamilyPreopenPolicyHandoff가 소유한다.
