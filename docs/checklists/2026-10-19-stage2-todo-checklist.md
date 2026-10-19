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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-16", "sources": {"entry_cancel_wait_policy": {"sha256": "bd706649cb3ef651b5b5a349d6455a147022b33a544543216759f79d5777d8c8"}, "entry_cancel_wait_tuning": {"sha256": "d457c5f5d883e13a2fdb9c5be89ca5e4b367483a3cc3c6dc1a128bb5fa4b1d52"}, "holding_path_vote_policy": {"sha256": "f7cfae1e5041f6819eb84d41e43481f6116f76cbb652db3a5610a40106ed4678"}, "initial_quantity_refresh_stage": {"sha256": "fe0ee119d9992c657d3d953b7ee02ce97201769f4d6ea341aaf942e61a55528f"}, "runtime_approval_summary": {"sha256": "1fc7d1ffd93c8355f8b39f759b1a51ac1a4031a0c672241f6ef0c3632315b1ee"}, "stage_legacy_machine_report": {"sha256": "43936d40cc47c919f0a43d7bbd19f05ef2a64873d3106f0afc609e05ac3fec2f"}, "stage_main_auxiliary_policy": {"sha256": "39eabccbf9139d2e0aa5807e4e2f64f29e75d5692c700c9f97d8729730ae1147"}, "stage_main_machine_policy": {"sha256": "611f30f6fb3842a7948cbb9516e438efbd1ce81daa94956a78810c38c849db65"}, "stage_main_stop_confirmation": {"sha256": "9a144ce22179f54fe4e82e2d1b859e4c4da394eb96e75afce1fc825fc71405c8"}, "stage_outcome_labels": {"sha256": "d5b395f0fa178445aa020353b63dbac2f9a4a6d56763a87030cf860f8e65b1c4"}, "stage_pre_submit_delay": {"sha256": "497c8cf8c566b4a2e2c68d75a58d809244518b274a54d02af7007d2297a4a20e"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-19", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "22c4fe91c865e5e95212e9ce35eb6449594136fcf1ebe80fa2a2e43b14049eac", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-19.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-16", "source_report_sha256": "e665c46bb8f8447dbc6e07a9934c0985e15303acb219d0b16896a30f08b5d9cf", "status": "verified_incumbent_carried", "target_date": "2026-10-19"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-19.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "d696bc9ca489a8f745f611df4f9ea60676b60fdffa91c7c91b724383079340d9", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "bd706649cb3ef651b5b5a349d6455a147022b33a544543216759f79d5777d8c8", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "94fbd34b5ecbab6da39cca92067270e3f5ff845b133f955a6244fc868922178e", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "d696bc9ca489a8f745f611df4f9ea60676b60fdffa91c7c91b724383079340d9", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "a4e364ba16ba6f64719d870f5c4b53477edf703fd5c2d1c38d9cd2b0e695814b", "valid": false}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "8416f18bfcdd285d26b4cce6389f0e70ef07037b544ef4d0340def0b1ad3d1a4", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "d0017ee54b4e4f57ea59566ae9425bd354d921f9dbcee4334c0dc122bc66be6b", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-16", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-19.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-16`; next apply date: `2026-10-19`.
- 아래 상태는 summary `1fc7d1ffd93c8355f8b39f759b1a51ac1a4031a0c672241f6ef0c3632315b1ee` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
- direct source: `9/9`; direct state: `complete`.
- economic state: `mixed`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `source_quality` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |
| `entry_split` | `source_gap` | `blocked` | `producer_contract_repair` |
| `pre_submit_delay` | `not_applicable` | `blocked` | `terminal_not_applicable` |
| `scale_in_split` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `ws_freshness` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |
| `main_mechanistic_entry` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `compact_auxiliary` | `identical_policy` | `incumbent_preserved` | `terminal_incumbent` |
| `rising_missed` | `not_applicable` | `not_applicable` | `terminal_not_applicable` |

## 실행 항목

- [ ] `[SubmissionMonitorSyncLineage1019] 제출병목 관측기의 동기 요청 신원 결속 수리·후속 반영` (`Due: 2026-10-19`, `Slot: INTRADAY`, `TimeWindow: 코드 리뷰 종결 후 승인된 후속 배포 시`, `Track: RuntimeStability`)
  - 15:27 후속 수용:18e1bba21/PID1355795/start3557005 ordered complete·startup reader verified,15:26:53 자연 full의 observer pending_no_applicable_observations/선언 재계산 일치/unmet0과 process/log PASS다. 원4행 history replay verified4/4이며 현재 세대 history 표본0·partial 관측과 구분한다. pipeline 최초801,760,912B 색인 이관도 완료했다. 자연 source/short horizon/PASS→submit 수용은 이 owner OPEN을 유지한다. [실행 근거](../../tmp/observer-history-proof-20261019-1512/final-verification.json).
  - 15:12 신규 결함: 현재 연속 구간0초를 lifetime history 부재로 오분류한 관측기를 수리했다. 원4행 replay verified4/4·known56·warning_pending/unmet0, source coverage 미승격과 실제 stale 진단 보존을 확인했다. probe/diagnostic 중복 제거도 native lease 기준으로 통합했고3437회귀 PASS다. 새 선택/PID 및 정기 관측은 후속 별도 수용이다. [검토](../audits/preopen-alert-repair-2026-10-19.md#1512-native-history-continuous-window-contract).
  - 15:11 적용 수용: e200a7216/PID1307428/start3456859 ordered complete,15:08:02 startup reader verified 및 자연 process/log PASS다. 현재 actor observer는 partial/warning_pending/unmet0, full artifact는 I/O 경합으로 보류했다. trailing bounded 현재성 정상·quantity 실제 비용/terminal5건·pipeline 최초 legacy prefix 이관·자연 제출 개선 수용은 각각 별도 OPEN으로 유지한다. [실행 근거](../../tmp/artifact-source-repair-20261019-1050/consumer-retry-final-verification.json).
  - 14:52 추가 수리: 런처 PID 영수증 selector 게시와 최초 consumer 서명 검증의 경합을 확인했다. 실패 pass를 폐기한 전체 native 검증1회 재시도·기존 평가 뷰/실제 source 오류 거부를 검증하고2576 PASS다. 현재 정책·original PREOPEN 및 frozen reader는 보존하며 새 PID의 startup verified를 별도 확인한다. [검토](../audits/preopen-alert-repair-2026-10-19.md#1452-main-policy-startup-selector-race).
  - 10/19 추가 사용자 구현 지시: raw 관측기는 writer-owned minute/원 ID 색인을 소비하고,50ms local-depth sampler로 짧은 horizon을 수집한다. PASS 최종 검증의 중복 정책 복사를 제거하고 현재 pointer/revocation·원5초·계좌/수량/호가/전송 guard를 유지한다. 코드 검증과 자연 PASS→실제 제출·원천 결손 해소는 분리한다. [검토](../audits/preopen-alert-repair-2026-10-19.md#trailing-재생성의-대용량-반복-읽기).
  - Source: 사용자08:30까지 제출병목 모니터링 지시, [source-only 수리 검토](../audits/submission-monitor-sync-lineage-review-2026-10-19.md).
  - 코드 완료: async 신원은 null이지만 native request capture가 존재하는 실제08:03 timeout에서 원894 prepared0/issues1/gap1을 재현했다. exact native actor·정책·event·input/prompt·logical/wire 결속을 추가하고884 PASS/compile/diff·자체 리뷰→수정→재리뷰를 확인했다. 격리 재검증은 prepared1/issues0/gap0이며 실제 전송1·timeout1·PASS0을 보존한다.
  - Acceptance/다음 단계: 후속 통합본의 frozen source/code handoff·선택본/PID를 검증하고 자연 request/trace의 동기·async 결속을 대사한다. request 준비·전송·응답·Main 수용·주문을 구분하며 symbol/time 추정과 timeout 삭제는 금지한다. 현재 배포894는 미변경이므로 deployment_pending이다.
  - 권한/분리: 이번 수리는 source-only 관측 코드다. Provider·deadline·정책·주문/취소·수량/수탁·Main 재기동은 변경하지 않는다. 두산·알테오젠 수동관리 결속은 다른 세션이 담당하며 큐리옥스 SELL cancel-intent 반복은 별도 runtime 주문 lifecycle 문제로 남긴다.

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-19`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - 코드 전환 뒤 trailing 연구의 현재성은 원 PREOPEN holding 원문을 유지한 별도 native 재검증 영수증으로 확인한다. 날짜·scope·원 parent policy 일치, 새 전체 원천/산술 검증, 현재 코드/세대 결속이 필수이며 보고서 전용 영수증은 runtime apply 권한이 아니다. 재기동 observer는 기준일 raw inode 변경을 정식 요약 재생성 후 다시 검증한다.
  - 첫 장중 코드 전환은 이미 소비된 prepared delay의 원 commit과 source를 사전검증하고 drain 후 selector 게시 전에 정식 영수증을 승계한다. 실패 시 새 선택/기동을 진행하지 않으며 기존 정책 수치와 원 PREOPEN을 유지한다.
  - 10/19 trailing 반복 읽기 수리: 봉인된 원 입력·추출 provenance·결손을 보존하고 native 바이트/identity 증명과 현재 replay/독립 산술로 재검증한다. 전체 원본 해시 재읽기 fallback은 증명 경로에서 금지하고 미증명 원천32MiB/별도 vote32MiB 사전 한도를 둔다. 실제 과거 입력 사전검사6.4초/전체 해시 읽기17.1MB이며 배포·native 최종 생성·현재PID 수용은 후속 증거로 구분한다. 새 원천의 native append 색인·완료 resident tree/manifest와 조립/요청/vote/압축/관측 consumer를 구현했다.8MiB/50ms explicit migration·bounded background catch-up·미증명 대형 원천 pending을 유지한다. exact94-file handoff2503회귀 PASS이며 native 최종 생성·배포/PID·자연 입력 수용은 별도 확인한다. [운영 절차](../runtime-release-routing.md#closed-session-trailing-regeneration), [검토](../audits/preopen-alert-repair-2026-10-19.md#trailing-재생성의-대용량-반복-읽기).
  - 10/19 10:22 기동 관측기: lock 대기로 producer가 미실행인데 source-only 보고서를 게시하여 현재 full 보고서를 덮은 결함을 수리한다. 미실행은 원 deadline 실패로 남기며 게시하지 않고, 실제 생성 실패의 진단과 첫 detector의 검증은 유지한다. 820b422df/PID625590의10:32:26 첫 자연 full health에서 해당 ERROR 해소·full 보고서 보존을 확인했다. 기존 원천·경제성 경고는 별도 OPEN이다. [검토](../audits/preopen-alert-repair-2026-10-19.md).
  - 10/19 09:30 observer 수리: 이전 PID 스캐너 사건은 exact 원본 해시/6필드/actor/출생시각으로만 현재 health에서 분리하고 원 active/경제성 결손을 보존한다. native 입력 deadline의 안전한 무호출·무주문 DROP은 지연 차단 진단으로 유지한다. 실제09:30 격리 재검증은 warning이며 live 배포/PID/자연 detector 수용은 별도 확인한다. [검토](../audits/preopen-alert-repair-2026-10-19.md).
  - 09:45 실제 수용:40b21f360/PID470886/start1502213 ordered complete·native4gate·3,993회귀 PASS.09:44/09:45 full에서 제출병목 ERROR 제거, 현재 PID warning_pending 재계산 일치·process/log PASS. 비용5건·trailing 원천 및 tmp 경고는 계속 OPEN이다. [실행 영수증](../../tmp/preopen-alert-repair-20261019/observer-history-final-verification.json).
  - Source: [runtime_approval_summary_2026-10-16.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-16.json)
  - 판정 기준: source_date=`2026-10-16`, apply_date=`2026-10-19`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=False, handoff=blocked); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=e6d31662f21d7785c3ddcc7e5e361482e3d7e03486216403f3491542f3238f7b, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

  - 10/19 장중 수리/PID 수용:795dacfbd/PID404085(start ticks1340713) ordered pass/complete, 실제 정책·delay·stop·holding4개 native gate와2,881개 회귀 PASS. 원 PREOPEN/정책/strict 문서 bytes 및 다른 세션 owner를 보존했다. 큐리옥스49362는 사용자 직접 매도2주+기존1주를 broker 영수증으로 대사한 뒤 drain 후 COMPLETED/원장0을 확정했다.445680·196170 수동 지정은 사용자 정정으로 해제했고 두산 지정은 유지한다. [수리·검증 근거](../audits/preopen-alert-repair-2026-10-19.md).
  - 잔여 Acceptance: trailing20,840scope 재생성 자체는 complete이나 후속 registry/holding-vote 변경으로 currentness full 검증은 OPEN이다. native event ancestry/닫힌 날짜 prefix를 보존한 검증과 현재 PID observer 의미 상태를 확인한다. 원 비용/first-crossing 결손은 각 기존 원천 owner에 유지하며 GREEN으로 덮지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-16.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-16.json)
  - 증거: runtime_summary_sha256=`1fc7d1ffd93c8355f8b39f759b1a51ac1a4031a0c672241f6ef0c3632315b1ee`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-16.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-16`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-16.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-16.json)
  - 증거: runtime_summary_sha256=`1fc7d1ffd93c8355f8b39f759b1a51ac1a4031a0c672241f6ef0c3632315b1ee`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-16.json`.
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
<!-- entry_cancel_wait_handoff_sha256:7ece7e973d04d7f0a681c5dc649804ac74240708f5ac43c3d1d0b52aa21e184d -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-16; 발행 2026-10-16; 적용 2026-10-19. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": "current_main_position_open", "checkpoint_superseded_historical_dispatch_count": 6, "historical_terminal_or_profit_inferred": false, "known_open_count": 3, "status": "known_open"}, "daily_state": "source_gap", "daily_submitted_parent_count": null, "daily_zero_is_verified": false, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 10, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 10, "missing_dates": ["2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "recovered_source_dates": ["2026-09-30"], "report_proof_sha256": "29e647de61de0a2bb781cb886445edd32739751bb2332afcd3072693aa0b6dd4", "research_evaluation_status": "model_unvalidated", "runtime_effect": false, "source_date": "2026-10-16", "status": "incumbent_carry", "terminal_unverified_count": 10, "unclassified_submission_count": 5, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->


## 전일 미종결 계약과 역사 원천 인계


- [ ] `[InitialQuantityProducerConsumerRepair1010] 매수수량 원천·fact·시간창·장후 소비 결손 수리와 자연 수용` (`Due: 2026-10-19`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - 10:50 후속: 큰 실행 행의 bounded 필드 복원·이월 snapshot의 native SHA 검증 후 부분 디코드·과거 registry prefix의 날짜 없는 native 대사 이벤트를 수리했다. 431+3,132회귀 PASS와 정식 완료 prefix→fact→수량 재생성/현재 trailing 연구/PID 수용은 분리한다. [진행 근거](../audits/preopen-alert-repair-2026-10-19.md#1050-원천-계약-경보-후속-수리).
  - 재기동 복구: 보존 hard link가 원문 바이트 변경 없이 ctime을 변경하여 99e158af1 기동의 Main stop 검증이 실패했다. 실패 전환·시작 보류를 보존하고 원문 전체 hash 검증 및 정확한 starting/timeout 복구를 새 검토 릴리스로 수행한다. 원 정책/PREOPEN/strict/controller는 수정하지 않는다.
  - 10:01 후속: 이월 snapshot 전체 디코드로 인한 swap/I/O 경보와 SELL 재관측 중복 판정을 함께 수리한다. 연구 비용3건의 격리 복원·475회귀 통과와 운영 재생성/PID 수용을 분리하며 원 비용·custody·정책 결속 결손은 유지한다. [후속 근거](../audits/preopen-alert-repair-2026-10-19.md#1001-io-경보와-수량-원천-후속-수리).
  - 10/19 추가 경고: 기존 완료13건의 비용/수량 결손과 운영 research-cost index 부재를 확인했다. native completion prefix→fact→quantity를 재생성하고 연구 배분/실제 비용/복구 불가 결손을 구분한다. [실행 검토](../audits/preopen-alert-repair-2026-10-19.md).
  - 재개 근거: [10/17 수량 정밀 점검](../audits/initial-quantity-runtime-postclose-result-review-2026-10-17.md)의 IQ171~IQ175와 [전체 장후 후속 수리](../audits/postclose-complete-semantic-repair-2026-10-17.md). 기존 계획의 완료 이력은 보존하고 새로 재현된 producer/consumer·유효 빈 모집단 오판만 재개한다.
  - Source: [원 producer/consumer 계획](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md), source date `2026-10-16`의 봉인된 completion snapshot·native fact·수량 refresh report/evaluation 및 원 attempt/PID/start ticks에 연결된 수집 영수증.
  - Acceptance: 완료거래 prefix→동일 세대 fact→수량 연구→AI writer 종료 후 holding suffix 순서를 검증한다. 표시 300건 제한 이전 전체 모집단, emitted_date 보존, 대용량/gzip 원천의 bounded native 계약, DB 교체 중 변경 rollback, 후보 시간창별 finished/interrupted 구분과 늦은 영수증 cache 무효화를 확인한다.
  - 원천 비용·terminal·과거 중단 자료 부재는 `null`/제외/명시적 `source_gap`으로 남기며 `valid_empty` 또는 0원으로 대체하지 않는다. 기존 6개 유형 10/15/20/25/25%와 분할·timeout 프로필을 보존하고 추가 경제성 승인 gate·주문·provider·threshold 변경을 만들지 않는다.
  - 코드/장후 재생성 완료와 다음 자연 수집 수용은 별개다. 새 배포 이후 실제 시작/종료/중단 영수증과 비용 원천의 정확한 대사를 확인하며, 10/19 PREOPEN·PID 소비는 기존 `DirectFamilyPreopenPolicyHandoff`만 소유한다.


- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-19`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
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

- [ ] `[OperationalLogRetentionRepair1016] 작성자 로그 회전·보관·역사 원천 압축 적용 확인` (`Due: 2026-10-19`, `Slot: INTRADAY`, `TimeWindow: 통합 배포 후`, `Track: RuntimeStability`)
  - detector 후행 실패 복구는 원 controller/strict/cleanup 세대와 실제 완료 시각을 보존하고 검증된 suffix만 재실행한다. 원 실패·정리 영수증을 별도 보관하며 새 full detector와 동일 세대 검증이 통과해야 정식 finalization DONE을 발행한다. PREOPEN 이후 원천을 다시 쓰거나 실패를 수동 완료로 바꾸지 않는다.
  - 10/19 추가 수리: 일반 캐시 탐색의 shared evidence/격리 work 진입을 차단한다. 실제 캐시 범위 읽기 실패·partial census는 계속 실패하며 권한/증거를 변경하지 않는다. [실행 검토](../audits/preopen-alert-repair-2026-10-19.md).
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
