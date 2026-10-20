# 2026-10-20 Stage2 To-Do Checklist

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
- 에러 수리에는 [AGENTS §6 공통 에러처리 절차](../../AGENTS.md#6-error-resolution-procedure)를 적용한다. 최초 원인·회귀 검증·실제 소비 근거 없이 경보 해소나 과거 결손 제외만으로 완료하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-10-19", "sources": {"entry_cancel_wait_policy": {"sha256": "3da051f5ad37fce14d19dd7892518241eb0405d3012eddede9e0f10a43b7af5a"}, "entry_cancel_wait_tuning": {"sha256": "34f96e135b1c4242edaabdcf34b5301ad0e77c2f18a13ec1e8e8ac2230e912f4"}, "holding_path_vote_policy": {"sha256": "8518c4cbb56057733b8f490abedef7dea78605cbf82b33296aa22bd02744a3db"}, "initial_quantity_refresh_stage": {"sha256": "4f3e04811174fa6fe7c8559c65994103d26d99116c572f16b159a9bd1577e82c"}, "runtime_approval_summary": {"sha256": "4612b1791a70f73a3b64e093cafc86c8eb69b711afb93345544364e206c72101"}, "stage_legacy_machine_report": {"sha256": "8f5572329b7572d2e16589c01905b373f1d5eadb45e63b8e09770b26f7e6f079"}, "stage_main_auxiliary_policy": {"sha256": "faa3e0e4a6c0d9a5978c21993916c42fcd8b71a81341f7b1d4bb5fd58a1e27d6"}, "stage_main_machine_policy": {"sha256": "097d5e7100ca4db70808a04234422228e7fdf339863e411989f355843fe64626"}, "stage_main_stop_confirmation": {"sha256": "b9a898822ea0553056fd5c1491f7ded382bd7cff0c7f1d129210a69b9480a307"}, "stage_outcome_labels": {"sha256": "1530370ca9e90c57f8bd1a8320e23d35e40b402b49fc8caf64f3d405648ab394"}, "stage_pre_submit_delay": {"sha256": "eb1ebd42638694003561c0dabd5180820fec1b78cc8c91c3a651edcd4ffb1bf7"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"actual_pid_consumed": false, "allowed_runtime_apply": false, "apply_date": "2026-10-20", "expected_state": "future_due", "holding_path_vote_policy": {"allowed_runtime_apply": true, "bundle_sha256": "c44a4e4ac0a08b6b92b64ad5db1ccf657782e77cd5dec67ce20a2e8872720286", "cell_count": 12, "evidence_grade": "verified_incumbent_carry", "path": "/home/ubuntu/KORStockScan/data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-20.json", "policy_set_sha256": "ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc", "realized_paired_ev_krw": null, "source_date": "2026-10-19", "source_report_sha256": "d74eef5c73d0805c57bd9809644c3da9bd2af4ae38f3bee15dafce9f59484786", "status": "verified_incumbent_carried", "target_date": "2026-10-20"}, "manifest_content_sha256": null, "manifest_env_sha256": null, "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-20.json", "manifest_sha256": null, "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "a6f1626f5031268e51499216ee25d4e42ce8627dbff30328d7562a5ebf12d441", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "3da051f5ad37fce14d19dd7892518241eb0405d3012eddede9e0f10a43b7af5a", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "913853c2a56d9674191eaacfe0d36bf9e083e2202b66bd014c9a586334119fea", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "a6f1626f5031268e51499216ee25d4e42ce8627dbff30328d7562a5ebf12d441", "valid": true}, {"owner": "pre_submit_delay", "policy_owner": "pre_submit_delay_policy", "policy_sha256": "ae8afbfb035c1f482cfe72f013b1ee032cf2c6ba399468e33023f2a412129fcc", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "51f9c069538b34eef1d9dc76711dd801ebf6da6bb8fd8d27d280007efe21b7d2", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "b156d00beec56f4562c2fa9ee6d1c3f1b79aedaac398a534ab3c85bbbc54eed9", "valid": true}], "release_selection_sha256": null, "runtime_effect": false, "schema": "direct_family_future_handoff_v2", "selected_release_commit": null, "source_date": "2026-10-19", "source_preopen_state": "pending", "source_reported_pid_receipt": false, "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-20.json", "verification_sha256": null} -->

## Family 직접 증거 상태

- source date: `2026-10-19`; next apply date: `2026-10-20`.
- 아래 상태는 summary `4612b1791a70f73a3b64e093cafc86c8eb69b711afb93345544364e206c72101` 생성 당시 snapshot이다. 현재 준비·활성·PID 상태는 같은 날짜·세대의 별도 소비 영수증으로 확인한다.
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

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-10-20`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - 09:35 신규 결함으로 재개: 소비 후 운영 체크리스트 변경 시 원 strict 세대와 launch snapshot의 조회 연결 누락을 수리한다. 403870/49389 매도는 주문0017685/체결9708/9주 terminal 이후 outbox ACK 결함이며 새 주문 없이 native 복구를 검증한다. 정수 잔고 표시가와 정확한 분할체결 평균가 사이의 매수 identity 복원 결함, fixture 상대경로·코드 세대 연결도 함께 리뷰한다. 새 선택/PID·원 finalization DONE 재검증 전에는 완료로 닫지 않는다.
  - 10/20 완료: 원07:35 실패 보존, native 복구08:36 종료·PREOPEN08:42:40 성공. 최종 코드 `a98ff7a95d533b8ba33222c206bc77f941fffe99`, PID3964551/start10071650의 같은 manifest `4e2e42ebe1e4c4eb7b929d80d726b275d155c2559e75152e6aca1e485ae63d78` 소비와09:30:34 현재 관측을 확인. source19 최종화·detector09:32:03 native DONE. 원 strict-bound 체크리스트는 native archive로 보존. 실제 진입/체결/비용 후 EV와 관측 full coverage는 이 완료에 포함하지 않는다. [전체 원인 수리·종료 검토](../audits/postclose-root-cause-recovery-review-2026-10-19.md)
  - Source: [runtime_approval_summary_2026-10-19.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-19.json)
  - 판정 기준: source_date=`2026-10-19`, apply_date=`2026-10-20`, preopen_state=`pending`, due_policy_receipts=`compact_auxiliary(valid=True, handoff=incumbent_preserved); entry_cancel_wait(valid=True, handoff=blocked); entry_split(valid=True, handoff=blocked); main_mechanistic_entry(valid=True, handoff=incumbent_preserved); pre_submit_delay(valid=True, handoff=initial_quote_timing_policy_published); rising_missed(valid=True, handoff=not_applicable); scale_in_split(valid=True, handoff=not_applicable); main_stop_confirmation(policy=e136d47f46547b79c8b48c84a5aa5661e9da59e680a4cdc75adc3f567858cb19, pid_unobserved)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-19.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-19.json)
  - 증거: runtime_summary_sha256=`4612b1791a70f73a3b64e093cafc86c8eb69b711afb93345544364e206c72101`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-19.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-19`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-19.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-19.json)
  - 증거: runtime_summary_sha256=`4612b1791a70f73a3b64e093cafc86c8eb69b711afb93345544364e206c72101`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-19.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-19`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 기준 정비 완료

- [x] `[ErrorRootCauseProcedure] 반복 에러의 원인 수리·재발 검증 기준 통합`
  - 범위: 기준 commit `7d6565f1dcb71f11a33040e1e93f35da4999b19a`의 작업본에서 기존 변경을 보존하고 문서 5개만 수정. AGENTS §6을 공통 절차 owner로 추가하고 Plan Rebase·장중·장후·당일 기준에서 참조한다. 이 기록은 문서 완료이며 개별 장애 수리·배포·자연 수용 완료가 아니다.
  - 대체/보존: 장중 §4.3의 중복 일반 단계와 §7의 요약 루프는 공통 절차로 통합(`consolidated`). 장중 실제 원천 경로, 장후 §6의 권한·최소 재생성·terminal 절차는 현행 소비자용으로 보존(`retained`). 새 실행 코드·보고서·검증기·framework는 만들지 않는다.
  - 증감: 작업 시작 시점 대비 비테스트 소스 `+0/-0`, 테스트 `+0/-0`, 문서 `+30/-11`(순증19줄), 이동0. 새 공통 절차와 소비 문서 링크·완료 기록이 순증 원인이며 기존 장중 중복 단계는 제거했다.
  - 검증: 자체 리뷰→보완→재리뷰, 링크/owner/authority, print-only parser·`git diff --check` 통과. parser의 기존 OPEN 19건은 내용·owner 그대로이며 새 중복 OPEN은 없다. strict-bound 원 체크리스트는 기존 SHA256 archive를 검증해 보존했다. Python/매매 suite·provider·재생성·배포·재기동은 문서 범위 밖으로 실행하지 않았다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- entry_cancel_wait_handoff:start -->
<!-- entry_cancel_wait_handoff_sha256:ea2416dce3de108e209de292508e1151f7845c0d74125ec40968b6b9a44463aa -->

## Entry cancel-wait 장후 handoff

- 평가 2026-10-19; 발행 2026-10-19; 적용 2026-10-20. `source_gap` / `incumbent_preserved`.
- 당일/과거 대사: `{"actual_pid_consumed": false, "allowed_runtime_apply": false, "closure_test": "same_date_original_source_ledger_policy_and_consumer_projection", "current_custody": {"blocker": "current_main_position_open", "known_open_count": 2, "status": "known_open"}, "daily_state": "submitted_orders_observed", "daily_submitted_parent_count": 5, "daily_zero_is_verified": false, "economic_population_status": "eligible_population_partitioned", "economic_tuning_input_allowed": false, "evaluation_status": "source_gap", "filled_cost_unresolved_count": 21, "findings": [], "historical_state": "source_gap", "historical_zero_is_verified": false, "known_open_order_count": 0, "known_unresolved_custody_count": 26, "missing_dates": ["2026-10-01"], "owner": "EntryCancelWaitSourceReconciliation1002", "reconciliation_contract_version": "entry_cancel_wait_source_reconciliation_v1", "recovered_source_dates": ["2026-09-30"], "report_proof_sha256": "159b3da056eaa992b2efd53ba0224c6b65144e67d0720ec2b3d81c04995f421b", "research_evaluation_status": "model_unvalidated", "runtime_effect": false, "source_date": "2026-10-19", "status": "incumbent_carry", "terminal_unverified_count": 26, "unclassified_submission_count": 11, "unresolved_prior_custody_count": null, "whole_native_chain_done_claimed": false}`.
- common timeout `{"breakout": 120, "pullback": 600, "reserve": 1200, "standard": 90}` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `[null, null]`.
- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.

<!-- entry_cancel_wait_handoff:end -->


## 장후 원천·자연 수용 이관

- [ ] `[InitialQuantityProducerConsumerRepair1010] 매수수량 원천·fact·시간창·장후 소비 결손 수리와 자연 수용` (`Due: 2026-10-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~23:59`, `Track: RuntimeStability`)
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
## 원천 reader 보완 후보 — SourceReadReduction1020

- [x] `[SourceReadReduction1020] 활성 경로 1~8 보완·리뷰·격리 검증 후 배포 대기` (`Due: 2026-10-20`, `Slot: ADHOC`, `TimeWindow: 09:20~`, `Track: RuntimeStability`)
  - 사용자 승인 범위: 활성 경로 1~8. 별도 작업본 구현·리뷰·수정·검증까지이며 운영 원천 재생성, provider/주문 호출, 정책 변경, 배포·재기동은 실행하지 않는다.
  - 후보 작업본: `/home/ubuntu/KORStockScan-worktrees/source-read-reduction-20261020`; branch `codex/source-read-reduction-20261020`.
  - 시작 기반 `4b278bbb3241a2ac5cb60fce52fe7da93391b1e4`; 작업 중 선택본이 `a98ff7a95d533b8ba33222c206bc77f941fffe99`로 변경되어 해당 기반으로 rebase했다. incoming 6파일 중 detector 및 그 테스트 2파일의 변경을 함께 보존했다. 기본 작업본·운영 shell·selector는 수정하지 않았다.
  - 재확인 운영 PID `3964551`, start ticks `10071650`, cwd `/home/ubuntu/KORStockScan-runtime-releases/current-observer-finalization-20261020-a98ff7a95/src`. 이는 다른 배포의 상태이며 이 후보의 소비가 아니다.
  - 코드 커밋 `9b45af5fd` → 최종 보완 `c30e4e5c2`; 선택본 체크리스트 원본 SHA `7a91512b9e36e795d20be0f68f1e44208ef9f5d289546626771b5ab982944996`는 원래 commit/release에 보존한다. 본 기록은 격리 후보 문서이며 현재 strict/checklist 영수증을 재작성하지 않는다.

### 대체·제거와 유지 경계

| 순위 | owner·대체 | disposition·검증 기준 |
| --- | --- | --- |
| 1 | `continuous_reversal_postclose.completed_bars`: `*/*/*.json` 전체 날짜 탐색 후 본문 필터 → `day/*/*.json` 선별 | **removed**: 다른 날짜 본문 읽기. embedded date·route·native 우선순위·원천 SHA 검사는 유지. 다른 날짜의 손상 파일도 open하지 않음. |
| 2 | `rising_missed_intraday_feedback._PipelineReplay`: 단일 gzip 반복 전량 해제 → 최대 128행/약 1MiB 압축 블록과 stage/code index; rolling 3개 reader는 실행 내 과거 보고서 해석 공유 | **consolidated**: 무관 블록 반복 해제. 순서·unknown fields·raw prefix SHA·전체 결과 보존. 1,029행 중 선택 5행만 unpickle하는 회귀. **retained**: 매 실행 원본 prefix 1회 봉인과 전체 watermark/후행 관측 계산; 영속 offset/pending-state 계약이 없으므로 재시작 후 신규 raw만 읽는다고 주장하지 않음. |
| 3 | `log_archive_service.load_monitor_snapshot(section_names=...)` → performance 첫 reader의 `recent_trades`/`meta` 구조 투영 | **removed**: 해당 소비자의 전체 completed census 객체화 및 투영 실패 시 전체 파일 fallback. 원본·gzip 우선순위와 필요한 row/경고 보존. **retained**: 전체 결과가 필요한 dashboard·custody reader의 기존 기본 API. |
| 4 | `artifact_freshness._semantic_object` → 기존 `DigestSession`의 실행 내 작은 입력 재사용 | **consolidated**: 같은 파일·세대·limit·모드의 반복 해석. PID·TTL·inode/size/mtime/ctime/경로 identity 확인, 반환 복사 격리, 1MiB/항목·4MiB/실행 cap. 외부 의존성·validator 판정은 매번 실행; 큰 원천의 검증은 유지. |
| 5 | `artifact_freshness._terminal_skip_status` → `tail_log_lines`; `log_archive_service._read_matching_lines` → 같은 실행의 날짜별 소규모 결과 재사용 | **removed**: 전체 `read_text().splitlines()[-5000:]`. **retained**: 날짜 interval/completeness가 없는 numeric/closed rotation의 최초 탐색과 raw 우선·archive fallback. 파일명이나 mtime만으로 과거 파일을 제외하지 않음. late/rotate·마지막 줄·한글·대규모 비선택 행 회귀. |
| 6 | `_read_machine_projection` → 기존 `Reader`+`FrozenRows`; `FrozenRows` canonical bytes를 hash/copy에 직접 사용 | **removed**: 최대 1GiB 전체 bytes/JSON list와 동일 행의 hash용 decode/encode. kernel preflight·논리 크기 cap·generation/content hash 거절 유지; 추가 원천·정책 권한 없음. |
| 7 | `continuous_reversal_source.iter_normalized_symbols` → population/operating/cumulative 세 reader | **removed**: 세 호출자의 `gzip.decompress(read_bytes())` 전체 symbol 객체화. 개인 임시 spool에서 한 종목 단위로 처리하며 원래 sorted-symbol 순서·모든 row·gzip CRC·generation 검사 보존. pickle은 현재 호출이 만든 비공개 임시 파일에만 사용. |
| 8 | `pipeline_event_summary.load_summary_rows(include_samples=False)` → 기존 `slim_summary_projection`; `jsonl_io` strict receipt → 최초 읽기에서 물리/논리 SHA 결속 | **consolidated**: 같은 날짜·세대·strict 계약의 요약 반복 decode, strict 영수증의 두 번째 read/decompress/decode. 요약 변경·손상·읽는 중 교체는 재검증/거절. **retained**: audit의 raw 전체 분모와 family 의미 검증, 신규/late partition 봉인. sampling 요약을 원본 전체 모집단으로 대체하지 않음. |

- 코드 증감(기반 `a98ff7a95` 대비): non-test source +422/−174 = **+248줄**; tests +323/−1 = +322줄. docs +51/−0줄(기존 체크리스트 1개). 이동 0, 다른 세션 변경 미포함.
- 새 모듈·wrapper·validator framework·운영 스케줄 없음. 소스 증가분은 기존 owner 안의 구조 읽기·블록 index·세대 제한 재사용에 사용한다. 조건부 후보 9~11 및 과거 원천·정책·owner custody는 범위 밖이다.
- 유지/후속 조건: (2) 영속 증분 전환은 producer의 정확한 prefix 세대/재시작·partial-line·pending-horizon 계약이 있을 때 rising-missed owner가 동일 cutoff 전체 결과 회귀로 닫는다. (5) 최초 날짜 무관 log open 제거는 log/archive owner가 원천 세대와 결속한 날짜 interval/completeness를 제공할 때 late/rotation 대사로 닫는다. 이번 후보의 절감 결과를 그 두 조건의 완료로 해석하지 않는다.

### 리뷰·실패 재현·검증

- 초기 실패: 다른 날짜 손상 bar open, 디스크 행 reader 미존재, strict receipt 공존본 decode 3회(2회가 계약), public slim summary 재해석 2회(1회로 감소).
- 자체 리뷰 보완: reader import 위치 수정; 읽는 도중 summary 교체 시 혼합 세대 반환 제거; JSON 숫자의 소수점·지수 chunk 경계 및 비-JSON whitespace 회귀 후 수정; log cache의 비선택 대용량 행 상주를 1MiB 이내로 제한; CRC·논리 크기 초과·구 kernel·hash 변경 거절 확인.
- 성능 리뷰 보완: snapshot 초기 구현 4.658초의 회귀를 발견하여 작은 JSON 값은 bounded native decoder로 검증하도록 수정(0.193초); FrozenRows hash/copy의 반복 decode/encode 제거.
- 검증 결과: 최신 기반에서 **25파일 통합 1,930 PASS / 215.10초**, 마지막 보완 후 **9파일 780 PASS / 48.74초**. 후자는 겹치는 표적 재검증이며 합쳐서 고유 테스트 수로 보고하지 않는다. 제외·skip 0, Python compile 27파일 PASS, `git diff --check` PASS, print-only 문서 parser PASS. shell/cron 변경 0이므로 `bash -n`·배포 shell 실행은 대상 없음.
- 추가 성능 보완: 단일 65MiB JSON 행의 반복 decode 회귀를 geometric refill로 해소하여 기존 회귀 테스트 42.30→2.05초. source/field 크기 cap은 그대로다. 빈/작은 객체가 많아도 4,096 cache entries를 초과하지 않으며 과거 보고서 cache도 합계 4MiB로 제한한다.
- Ruff `F821/F822/F823/F811` 확인: 이번 변경 지적 0. `continuous_reversal_operating_postclose`의 기존 지역 alias `R` 재정의 F811 1건은 기반에도 있어 범위 밖으로 유지한다. 전체 Ruff clean 선언은 하지 않는다.
- 최종 자체 재리뷰: 이번 변경의 producer/첫 consumer, 원천 변경·손상·압축 공존, 비용 null·전체 분모·결과 hash, 경로·쓰기·provider/주문 권한 경계에서 미해결 구현 결함 0. 운영 전체 원천 크기에서의 성능/임시 I/O와 실제 배포는 별도 gate다.

### 동일 합성 입력의 비용 비교

운영 데이터가 없는 격리 `tmp/reader-fixtures`만 사용했다. 아래 값은 OS page cache를 비우지 않은 개별 프로세스 1회 측정이며 운영 cold 성능/실제 10/19 전체 원천 성능의 증거가 아니다. 비교별 건수와 결과 digest는 동일하다. 전후 physical read가 달라 wall 차이만으로 운영 성능 향상을 확정하지 않는다. wall과 CPU는 초, RSS는 KiB.

| 경로·분모 | wall 전→후 | CPU 전→후 | peak RSS 전→후 | I/O와 한계 |
| --- | --- | --- | --- | --- |
| machine 70,000 rows | 0.272→0.684 | 0.272→0.666 | 144,796→39,464 | 새 경로 임시 파일 약 26.2MB write/read. 메모리 절감과 CPU/I/O 증가를 구분. |
| normalized 150,000 rows/30 symbols | 0.276→0.503 | 0.276→0.471 | 94,812→25,736 | 새 경로 임시 spool 약 9.9MB write; 종목별 완전한 label 입력 유지. |
| snapshot recent 20 rows/전체 29.7MB | 0.209→0.193 | 0.148→0.192 | 152,836→36,604 | 전체 JSON 구조 검증 I/O는 유지; 큰 census 객체 상주 제거. |
| rising 20,000 rows, 선택 20 rows × 3 | 0.297→0.178 | 0.297→0.143 | 48,908→39,428 | raw rchar 약 21.9MB 동일; 선택 reader 구간 0.163→0.00038초. 원본 1회 봉인 자체는 유지. |

- 상세 rchar/physical `read_bytes`/`write_bytes`, 입력 SHA 및 명령 증거: 후보 작업본 `tmp/review-evidence.json`, `tmp/measurement-*.json`, `tmp/validation-commands.txt`; 실행 스크립트 `tmp/measure_readers.py` SHA `a02126cf4fb3549b2521b98c5b14a2762c36a5ecfd6bf4f496c2025111676b39`(일회성 검증 자료, 운영 코드/새 framework 아님).
- 재현: 후보에서 `PYTHONPATH=. .venv/bin/python tmp/measure_readers.py prepare`, 이후 `... tmp/measure_readers.py {machine,symbols,snapshot,rising} {before,after}`를 각각 실행. baseline 함수는 `4b278bbb3`에서 읽으며 해당 측정 함수는 `a98ff7a95`와 동일하다.
- 배포 전 남은 gate: 실행 시 selector·PID·active policy 재고정, 후보에 결속한 native parity/handoff 및 운영 크기 임시 디스크 여유 확인. 이 후보는 실제 릴리스 선택·PID·자연 장후 소비·비용 조정 수익성 완료 증거가 아니다.

### 장중 반영 승인 후 재기동 사전 리뷰

- 후속 사용자 지시로 장중 반영·재기동이 승인됐다. 앞선 배포 대기 완료와 분리해 정지 전 native 검증 → ordered 배포 → 정확한 PID/관측 소비를 수행한다. 정책·threshold·주문 호출 수동 변경은 범위 밖이다.
- 동시 배포 `a7c0b0dc5`가 09:55:31 ordered complete한 뒤 해당 코드를 기반으로 재통합했다. 원 `24ffba227`은 보존 branch에 남기고 다른 세션의 15파일과 checklist 이력을 유지했다. predecessor PID `4094188`, start ticks `10221444`이며 실행 직전 다시 고정한다.
- 실제 정지 전 결함 재현: delay `pipeline_event_summary`, stop `log_archive_service`, holding `research_json_stream`의 미등록 코드 세대로 거절됐다. 실패 증거는 `tmp/source-read-deploy-20261020/contract-probe.json`; Main 정지/selector 변경은 이 검사에 없다.
- 기존 handoff owner에 검토한 reader 16파일의 정확한 원본/후속 SHA와 완전한 dependency 세대를 연결했다. 이전 세대 map은 과거 영수증의 현행 검증 소비자 때문에 **retained**하며 무조건 통과/새 wrapper는 없다. 같은 origin의 새 reader 허용 3건 실패 회귀 후 12건 통과(누락·dirty·새 commit으로 변조 거절 포함). rising/auxiliary는 원 보고서와 원 fixture를 보존하고 후속 독립 fixture를 요구하며 관련 20회귀 통과.
- native 고정 workload 128 scopes / 76,800 rows / 598 hits의 기존·후속 signal SHA가 일치했다. 원천/정책 재생성이나 provider 호출은 없었다. 최종 후보 commit에 다시 결속한 proof만 배포에 사용한다. 임시 디스크는 108GiB 여유를 확인했고 실제 전체 장후 workload의 CPU/I/O 비용은 이전 측정 한계를 유지한다.
- 재기동·router·bootstrap·auxiliary·startup isolation 기존 회귀와 최종 native 사전 검증을 진행 중이다. 결과와 실제 배포/PID 수용은 아래 후속 기록으로 확정한다.

- 변경된 기본 작업본 `AGENTS.md` §6을 재확인해 원 실패 보존 → 최초 파손 계약 → 최소 수리 → 직접 소비 검증으로 후속 작업을 수행했다.
- 재기동 회귀 첫 실행: 9파일 **4,513 PASS / 41 FAIL / 561.15초**. 실패 24건은 과거 broker fixture가 현재 reader를 원 코드로 사용한 오류, 2건은 capability 최신 세대 fixture, 나머지 15건은 시작 검증 세션·통계 및 과거 날짜 fixture 문제로 분리했다. 원 로그 `tmp/restart-review-pytest.txt`를 보존한다.
- 실제 시작 검증 결함: P5의 source-date 세션과 내부 CLI의 target-date 세션이 갈라져 native digest closure가 빠졌다. 같은 PID·역할·data root의 상위 세션만 유지하도록 기존 CLI를 수정했고 다른 프로세스/원천 재사용을 추가하지 않았다. 캐시 producer의 `semantic_reused_reads`를 기존 시작 검증 reader가 거절한 문제도 정수·비음수 계약으로 결속했다. 구/신 field 호환은 기존 진단 reader 안에 있으며 판정 재사용은 없다.
- 역사 fixture는 원 코드 commit `a7c0b0dc5`에 고정하고 transaction fixture는 명시한 날짜 clock을 사용한다. 실제 만료 가드는 유지하며 정상 child 뒤 날짜 만료 실패와 음수/bool/string/null 통계 거절 회귀를 추가했다. 원천 변경/실패·격리 실패·child 종료·native closure 검증도 그대로다.
- 수정 후 검증: handoff source-reader/broker 36 PASS, capability 20 PASS; 최종 startup/readiness/digest/policy-generation **4파일 1,088 PASS / 20.17초**, 제외·skip 0. 겹치는 재검증 수는 합산하지 않는다. 처음 통과한 다른 회귀를 이유 없이 전량 반복하지 않는다.
- 새 module/wrapper/validator 생성 0. `next_preopen_readiness.main`의 중첩 세션과 `main_startup_validation`의 통계 판정은 **consolidated**; 원천·정책 native 검증/만료/프로세스 격리·이전 세대 영수증은 현재 소비자가 있어 **retained**. 실주문/provider·정책 동작 변경 없음.
- 배포 전 baseline detector(10:04)의 stop/holding report source 경고, 기존 cron 지연 및 tmp 보존량 경고는 별도 원인으로 보존한다. 이번 candidate PID/observer 검증과 구분하며 전체 운영 경고 0으로 선언하지 않는다.
- 현재 선택 기반 `a7c0b0dc5` 대비 최종 source +518/−180, tests +420/−4, docs +70/−0. 새 파일·이동 0. compile 4파일, 문서 parser, diff 검사 PASS; 수정 경로 재리뷰 미해결 결함 0. 후보 clean commit 후 native 사전 검증과 실제 PID 소비를 별도 기록한다.
- 최종 startup 수정 후 pre-drain에서 `main_startup_validation.py`의 이전 dependency SHA가 남은 것을 확인(6f7f61905 실패 로그 보존), 기존 source-reader map을 검토한 startup 두 파일까지 총18개로 확장했다. 해당 reader/CLI/decoder의 missing·dirty·committed-change 거절과 정상3family를 36 PASS/19.78초로 검증. 코드 값/판정 우회는 없으며 실제 정지 전 결함이다.

### 실제 P5 intake 차단과 배포 보류

- `7f5cd9c54b115cadc3776ab94c6f68c7e1f33d4d` 불변 후보에서 active-policy·delay·stop·holding native 사전 검사 PASS. native parity는 128 scopes/76,800 rows/598 hits, signal SHA `958e471cca3b0e833e20486dbef9aecd6973b0273c53979d8ff1d9a4eb1a42fc` 동일. 증거 `tmp/source-read-deploy-20261020/7f5cd9c54/native-preflight.json`, `active-policy-parity.json` 및 현재 capability fixtures.
- 실제 P5 명령: 후보에서 `PYTHONPATH=. .venv/bin/python -B -m src.engine.automation.main_startup_validation --workspace /home/ubuntu/KORStockScan --target-date 2026-10-20 --candidate-root /home/ubuntu/KORStockScan-runtime-releases/source-read-reduction-20261020-7f5cd9c54`. 원 실패 `data/report/main_startup_validation/2026-10-20/09335ec448134a4e907e9a55506b2333/final.json`: `intake / startup_native_machine_closure_invalid`, candidate child 미실행.
- 동일 원천을 다시 생성하지 않고 native 관측 경계만 1회 진단했다. selected `a7c0b0dc5`의 원 CLI는 `intraday_preserved_historical_generation` PASS, bundle 3개(현재5ac 포함)·delay 선택2개지만 auxiliary transition manifest/frozen verifier0개다. P5의 `main_startup_validation._native_preparation_check`와 `startup_validation_code_context.bind_main_preparation/_check_native_closure`는 manifest 최소1개를 필수로 요구한다. 후보 child 이전의 기존 선택본 intake 계약 차단이며, manifest 0을 성공/과거 영수증의 새 검증으로 승격하지 않는다.
- 구 선택본의 nested target-day digest 세션에는 full164/reuse102, full1,935,791,930bytes가 있지만 P5 source-day outer에는0이다. 이 캐시 계보 결손은 후보 CLI에서 수정됐으나 기존 선택본이 실행한 진단에 소급 적용하지 않았다. 진단 `native-closure-diagnosis.json`, 원 stdout SHA `da5dae6d950d4620740b112dfe2922bb60c4893ee62cde938ca03d52efc88a24`, stderr SHA `e3a0ebd8467360f074b81500f61fb6afcc8088bc98c5bcbba52941aea2e5008f` 보존. nested native counter `admitted_native_proofs/bytes`도 정수·비음수로 검증하도록 직접 consumer를 보완했다.
- 이 진단은 전체 운영 원천 성능 측정이 아니다. 최초 native intake 30.42초/rchar3,257,008,127, 관측 보존 진단16.24초/rchar3,257,103,353; 동일 결정적 실패를 세 번째 전량 재실행하지 않는다. 정상 원천/정책을 삭제·재발행하거나 size/timeout을 늘리지 않는다.
- **배포 gate는 BLOCKED**. 승인 철회/권한 대기가 아니라 필수 P5 증거 결손이다. incumbent `a7c0b0dc5`, PID4094188/start10221444를 보존했고 이번 작업의 stop·selector 전환·restart·provider/주문 실행은0이다. candidate fixture/PASS를 실제 새 PID나 자연 성능으로 보고하지 않는다.

- [ ] `[MainPolicyLoadAndExitValidation1018] 현재 intraday 보존 정책의 P5 native closure 계약 복구` (`Due: 2026-10-20`, `Slot: ADHOC`, `TimeWindow: 10:20~`, `Track: RuntimeStability`)
  - 기존 [정책 로딩 검증 owner](../proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md)의 새 현재 실패로 재개. 원천 감소 1~8과 별도로 기존 P5 parent/직접 child context가 소유한다. 원 실패 run `09335ec448134a4e907e9a55506b2333`, source19/apply20, current bundle `5ac1768ad97ae21e1ea36f215c031e87df1045e9ee25c24773e6d73dac6644aa`.
  - 닫힘 검사: 실제 선택본의 native preserved-code-handoff 경로와 P5가 요구하는 auxiliary manifest 경계를 fixture로 재현하고 실제 소비 계약에 맞게 수정한다. 현재 source/code/policy/PID의 검증 가능한 원천 closure를 같은 invocation에 결속해야 한다. 빈 manifest 강제 허용·과거 PASS 재사용·새 정책 발행·불변 릴리스 편집은 금지한다. source/date/generation/원천 변경 거절을 유지하고 fresh clean 후보의 P512consumer·child 종료·무부작용 PASS를 확인한다. 그 후에만 새 exact handoff와 ordered 배포를 진행한다.
  - 남은 수용: 현재 code handoff가 제공하는 native 검증 범위와 P5 위임 범위의 호환 설계/회귀·실제 child는 미완료다. 전체 결함0·배포 가능·자연 수용 완료를 주장하지 않는다.
- 최종 보완 회귀: startup/readiness/digest 239 PASS/15.37초, exact source-reader handoff 36 PASS/30.44초. 전체 handoff 파일을 잘못 포함한 중간 검증은 중단해 통과 증거에서 제외하고 필요한 세션/통계·동세대/변조 거절만 재검증했다. compile5, `bash -n`3, 문서 parser·diff 검사 PASS. 새 운영 후보로 배포하지 않았고 최종 작업본 기록 commit은 사전 검증7f5cd9c54와 구분한다.
- 마감 증감(선택 기반 `a7c0b0dc5` 대비, 코드49a734bd3): non-test source +521/−180 = +341, tests +427/−4 = +423, 후보 docs +87/−0. 앞선+518/+420은 중간 검증 시점 수치다. source 순증은 bounded reader/index 및 정확한 코드 handoff·시작 진단 검증이며 새 module/entrypoint/framework는0이다.
