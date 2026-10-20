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

## 익절 원천 수리 인계

- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-20`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
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
