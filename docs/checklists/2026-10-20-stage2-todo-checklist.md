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
  - 22시 사용자 배포·재기동 테스트 승인: 정상 종료된 기존 소비 PID의 native 종료/EOD/정지/동결 원천을 읽기 전용으로 검증한 뒤 clean candidate의 정책 parity·4종 code·currentness·P5를 선행한다. ordered 전환과 실제 새 PID/start/cwd 소비·첫 observer/full health는 아직 미완료이며 기존 실패를 보존한다.
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
  - native 재발행 추가 원인:16일 파이프라인 gzip의 물리 경로/SHA가 timeout 재생성에 유입됐다. 논리 원천 영수증 보존 경로를 보완해 원 구현1FAIL·수정405PASS·정확 code 인계84PASS를 확인했다. 실제 cache/proof 복구는 동시 배포 담당 확정 후 원 source19/date/hash로 제한 수행하며 원 실패는 보존한다.
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

## 제출병목 관측기 계약 수리

- [ ] `[SubmissionMonitorSyncLineage1019] 제출병목 관측기 계약 수리·정규 소비 수용` (`Due: 2026-10-20`, `Slot: INTRADAY`, `TimeWindow: 승인된 순차 반영과 후속 정규 관측`, `Track: RuntimeStability`)
  - 22시 후속 보수: 장 종료/정상 정지된 실제 소비 세대의 원 증거를 대조하는 읽기 경로와 장후 단계 시작 전 대기 판정을 보완했다. 현재 실행 결손·혼합 세대는 계속 실패이며 새 PID 소비는 별도 검증한다. 원 실패/회귀: `tmp/main-errors-repair-20261020`; 배포·원 검사 재수용은 pending.
  - 20:10 신규 재발:현재88351/PID3835821·cbb 관측 실행은 완료됐으나20:00 정상 engine 종료 뒤 pending 판정에 장중 신선도를 계속 요구하는 detector 결함이다. 원본/종료 heartbeat 보존, 종료 시점 보고서14.95초·body32.23초/current actor·projection 대조와1632 회귀를 통과했다. 종료 구간의 검증 불가 warning만 보존하고 원 결손·full coverage false를 유지한다. EOD/postclose/controller/tuning 실행 중 selector 변경 금지로 후속 반영은 미실행이며 기존 승인은 유지된다. [재발 원인·수리·후속 수용](../audits/postclose-root-cause-recovery-review-2026-10-19.md#closed-window-empty-observer-recurrence-2026-10-20).
  - 승인 후68213 실제 전환 실패:최종 parity/4인계/report/P5 12consumer/금지0은 PASS이나19:37:24 starting PID 인계 timeout이다. Main3745840의 native 최종 검증에서 shared vote index configure SQLITE_BUSY가 발생했고 원 실패/보호 hold/선택 미소비 상태를 보존한다. 기존 ordered owner에 원천 readonly 연결의 drain→launch→attest 생존을 추가해 동일5ms/96MiB WAL 재현12/16 실패→0/16,323 회귀 PASS다. 새 후보 native/P5를 통과한 후 문서화된 stopped recovery로 같은 원인 수용을 진행한다. 원6e source coverage와19:40 비현행 observer 후속 경보는 원 ID/실패로 유지한다.
  - 후속 사용자 승인(리뷰·보완·배포·재기동):49ef의 fresh parity/4종 인계 PASS 뒤 필수 trailing 현재성에서 정지했다. native 재검증은 정상 release/data 경로를 금지 링크로 오인하는 cursor 소비 결함을 재현했다(1FAIL/5PASS). 기존 원천 재사용 owner만 정확 mount/날짜/세대 경계로 보완해187 회귀와 native6 proof/미증명21809006B 사전검사를 통과했다. 원 영수증/실패와6e PID를 보존하며 새 인계·정규 재검증·P5·ordered/PID/최초 observer/full health 수용을 진행한다.
  - 사용자 결함 보완 지시:105f6f031 기반 격리 후보에서 기존 self-SIGTERM 전 summary drain→이미 로드된 엔진의 단일 관측 shutdown→기존 큐 drain을 연결했다. registry/commit admission 종료 경합·sampler 실패·실제 cutoff·큐 실패 표시를 보완했고 원6건을 소급 복구하지 않는다. 원6회귀 FAIL→수정 PASS, 기능1235·정확한 후속/역사 인계135 PASS, compile9·최종 scoped finding0이다. 코드 수용은 완료하며 새 commit의 native parity/currentness/P5·실제 PID/자연 종료 소비는 별도 미실행이다. 선택6e/PID3081598 유지, 배포·재기동 미실행. [수리·제거 disposition](../audits/postclose-root-cause-recovery-review-2026-10-19.md#controlled-delay-observation-shutdown-repair-2026-10-20).
  - 6e037d078 배포17:29:05/PID3081598/start12943211·원 manifest 소비는 PASS다. 첫17:30:52 관측 미완료는 d927과 같은 배분 결함의 재발로 보존한다. --notify 없는 기동에도 CLI가 알림용15초를 예약해 남은25초 중 검증이10초로 줄어든 것이 최초 파손 계약이다. 격리 real-CLI 재현2 FAIL→조건부 게시5초/알림포함15초 수리 후3 PASS, 전체1129·신규 exact-source15·발행 predecessor60 회귀 PASS. 총150초/child 종료/late admission/정규 알림 가드는 유지한다. 운영6e의 정규17:35 관측·17:36:49 소비는 회복됐으나 새 보완의 배포/PID·첫 startup0 소비는 별도 미실행 OPEN이다. [같은 리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md#startup-observer-notification-reserve-repair-2026-10-20).
  - 10/20 후보 보완: 선택661260e5f와 요청d8acaa0aa를 통합하여 immutable 전달·완료 직접 게시·필드 검사 비용과 역할별 OpenAI 모델 단일 설정을 구현한다. compact 고정 계약·원 기한·현재 원천/주문 guard는 유지하며 구 tier/중복 초기화/미사용 GPT 브리핑·overnight 경로를 제거한다. 과거 캡처는 읽기 호환만 보존한다. [동일 리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md#local-completion-latency-and-role-model-integration-2026-10-20), [후보 검증](../../tmp/entry-local-latency-20261020/). 구현·회귀·원 정책 인계/P5·깨끗한 후보와 실제 선택/PID/자연 제출·경제성은 분리하며 기존 OPEN/Acceptance를 유지한다.
  - 15:49 실제 소비:10f8d1ba6/PID2622195/start12335630의 최초 producer/observer exit0와 full health fail0를 확인했으며 수동 보고서 복구는 없다. 정규 소비에서 fresh fixture의 새 세대 연결3개가 누락된 후속 결함을 발견해 기존 exact-pair owner에서 보완한다. 원 보고서/fixture/역사 상태를 보존한944 회귀와 native3건 대조는 통과했고 최종 후속 후보의 P5·ordered 소비를 확인한다. 과거 BUY/비용 결손·warning_pending/full coverage false는 별도 유지한다.
  - 추가 승인 통합: ced0351f4 지연정책 코드·다음 적용일 정책 게시·재기동과 ce70080ae 퇴역 PYRAMID helper 제거를 함께 검증한다. 원0ce/PID2108660은 최종 gate 전까지 유지한다. 수량15:00 경고는 monitor proof의 validation_digest_session 이전 코드 결속을 재현했으며, 원 stage/정책/과거 비용 제외를 보존한 native proof 재발행과 정상/중단 배포 모두의 기동 전 검사를 보완한다. snapshot/session append 결함도 수리했다. Core345 PASS이며 최종 parity·영향 보고서·P5·새 PID 최초 producer/observer exit0·full health는 실제 영수증으로만 완료한다. [통합 검토](../audits/postclose-root-cause-recovery-review-2026-10-19.md#delay-v4-and-retired-pyramid-final-integration-2026-10-20)
  - 이전 [10/19 동일 ID의 Acceptance·이력](2026-10-19-stage2-todo-checklist.md#실행-항목)을 보존해 이관한다. 자연 request/trace 동기·async 결속, source/short-horizon/PASS→Main 제출은 정책·주문·경제성과 분리하여 OPEN을 유지한다.
  - 12:54 코드 수용: 순서 결함041caf05e 배포·native P512consumer/금지0·ordered complete·실제PID1054501/start11276382와 기동 후 current observer/full health 재계산 일치·fail0을 확인했다. 원6순열 수리와 source gap/partial 보존은 [최종 소비 증명](../../tmp/submission-coverage-degraded-20261020/native/verification.json)으로 결속한다. 자연 source/short-horizon/PASS→제출·경제성 Acceptance는 기존 OPEN을 유지한다.
  - 0aedc579d 후속 통합: TIME ETF 유입·복원 probe 재배정을 단일 상품 필터로 차단하고 기존 이력·일반 주식·hard guard를 보존한다. native exact dependency3파일 후속 세대를 추가했으며462+73회귀 PASS다. 승인된 배포/P5/새 PID 소비는 [동일 검토](../audits/postclose-root-cause-recovery-review-2026-10-19.md#etf-product-intake-integration)에서 확인한다. 이전14건 무수신·과거 손실 및 기존 자연 수용 Acceptance는 분리한다.
  - 통합 수용:21d822a64/PID1175053/start11403252 ordered complete·P5 12consumer/금지0·자연 product3 제외/일반 probe 지속·13:26 full fail0이다. utility 지문의 trailing 현재성 누락은 기존 native 생산자로20840scope 재검증해 generation_current로 닫았다. 다음 반영은 report code_contract 현재성을 incumbent 종료 전에 확인한다. 기존 SQLite 일시 잠금의 근본 원인은 미확정 OPEN이며 원 실패·과거 손실·경제성 수용은 보존한다. [종결 증명](../../tmp/etf-intake-integration-20261020/native/verification.json).
  - 13:44 원인 조사: shared vote DB의 WAL98,921,232B·비상주 연결과 checkpoint 대상 누락을 확인했다. 선택 코드의 동일 readonly PRAGMA에서 격리 동시 조회12/16 SQLITE_BUSY_RECOVERY를 두 번 재현했고 연결 유지/사전 정리 대조군은 각각0/16이다. 원 Main 실패는 상세 DB 증거가 없어 동일 원인으로 확정하지 않는다. 기존 store의 checkpoint·읽기 session 수리는 미구현 OPEN이며 timeout/경보 완화·운영 DB 변경은0이다. 과거 BUY49389 복원은 현재 코드/원 체결로 재검증했고 원 신호 결손과 수량6건·cancel-wait/WS 결손은 분리 보존한다. [원인·범위·수리 수용검사](../audits/postclose-root-cause-recovery-review-2026-10-19.md#historical-source-gaps-and-sqlite-cold-open-investigation-2026-10-20).
  - 14:13 SQL 코드 수리: 기존 기동 준비/6 namespace PASSIVE checkpoint·DB별 날짜 전환 timer·검증 세션 내 최대6개 연결 재사용·실패 read transaction 정리·DB/단계/SQLite code 진단을 보완했다. 정확한 store/digest/진단3파일 후속 인계와 발행21d822a64 fixture를 분리해 혼합/누락/변조를 계속 거절한다. 핵심406·인계189 회귀 PASS, 같은 native generation의 동시 조회 실패12/16→0/16이다. 코드 리뷰/보완 수용이며 운영 재생성·배포·새 PID 소비는 미실행 OPEN, 원 BUY/수량/cancel-wait/WS 결손은 원 ID/null로 보존한다. [리뷰와 제거 disposition](../audits/postclose-root-cause-recovery-review-2026-10-19.md#shared-vote-sqlite-lifecycle-repair-2026-10-20). 코드 커밋 `c550a4c43b1070c29ccae89b9e70fbf4c1517c20`.
  - 14:36 통합 리뷰: 사용자 승인3d8abd012+c550a4c43를 선택21d822a64 기반으로 병합했다. 대표 파일만 구세대로 되돌려 검증 세대가 내려가는 결함6건을 재현하고 정리6파일 전체 결속으로 보완했다. 과거23파일 정책 fixture의 현재25파일 혼용도 원 발행 inventory로 수정했다. incumbent은 유지하며 전체 회귀→native currentness/parity/P5→ordered 새 PID 소비를 확인한다. [동일 리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md#clean-refactor-and-sqlite-integration-2026-10-20).
  - 14:59 기동 보완:0ce816f7c 통합1409 회귀/native parity·P5 12소비자·4인계/ordered PASS, PID2108660/start11987479를 확인했다. 첫 source-only/유예는 실패 시도로 보존했다. 원인은 남은150초 중 observer45초 예약으로 약46초 Sentinel을 조기 종료한 배분이다. 원 late-admission·observer 최소20초·정리5초는 유지하고 admitted 예약을30초로 보완, 원 코드 재현2 FAIL→기동 회귀27 PASS다. 새 후보의 첫 자연 startup producer/observer0·full health/PID 재확인까지 기존 owner에서 수용한다.
  - 12:26 신규 계약 결함: 구 PID 사건의 원문 증거가 유효한데 앞의 커버리지 사건에서 검사를 중단하여 순서에 따라 artifact 실패가 달라진다. 기존 최대256건 검사를 끝까지 수행하고 원천 품질 경고와 실제 current/unknown 실패를 보존한다. 원22 probe 중4 covered·비용 null은 복구로 간주하지 않는다. [원인·회귀·반영 검토](../audits/postclose-root-cause-recovery-review-2026-10-19.md#submission-observer-incident-order-repair).

## 익절 원천 수리 인계

- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유 익절 원천·재생·의미 계약 수리` (`Due: 2026-10-20`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
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

- [x] `[MainPolicyLoadAndExitValidation1018] 현재 intraday 보존 정책의 P5 native closure 계약 복구` (`Due: 2026-10-20`, `Slot: ADHOC`, `TimeWindow: 10:20~`, `Track: RuntimeStability`)
  - 기존 [정책 로딩 검증 owner](../proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md)의 새 현재 실패로 재개. 원천 감소 1~8과 별도로 기존 P5 parent/직접 child context가 소유한다. 원 실패 run `09335ec448134a4e907e9a55506b2333`, source19/apply20, current bundle `5ac1768ad97ae21e1ea36f215c031e87df1045e9ee25c24773e6d73dac6644aa`.
  - 닫힘 검사: 실제 선택본의 native preserved-code-handoff 경로와 P5가 요구하는 auxiliary manifest 경계를 fixture로 재현하고 실제 소비 계약에 맞게 수정한다. 현재 source/code/policy/PID의 검증 가능한 원천 closure를 같은 invocation에 결속해야 한다. 빈 manifest 강제 허용·과거 PASS 재사용·새 정책 발행·불변 릴리스 편집은 금지한다. source/date/generation/원천 변경 거절을 유지하고 fresh clean 후보의 P512consumer·child 종료·무부작용 PASS를 확인한다. 그 후에만 새 exact handoff와 ordered 배포를 진행한다.
  - 남은 수용: 현재 code handoff가 제공하는 native 검증 범위와 P5 위임 범위의 호환 설계/회귀·실제 child는 미완료다. 전체 결함0·배포 가능·자연 수용 완료를 주장하지 않는다.
- 최종 보완 회귀: startup/readiness/digest 239 PASS/15.37초, exact source-reader handoff 36 PASS/30.44초. 전체 handoff 파일을 잘못 포함한 중간 검증은 중단해 통과 증거에서 제외하고 필요한 세션/통계·동세대/변조 거절만 재검증했다. compile5, `bash -n`3, 문서 parser·diff 검사 PASS. 새 운영 후보로 배포하지 않았고 최종 작업본 기록 commit은 사전 검증7f5cd9c54와 구분한다.
- 배포 보류 최종 clean 작업본 commit `49a734bd3` (source/test 보완과 기록); 불변 사전 검증 후보 `7f5cd9c54`와 별도다. shared 운영 코드는 수정하지 않았다.
- 마감 증감(선택 기반 `a7c0b0dc5` 대비, 코드49a734bd3): non-test source +521/−180 = +341, tests +427/−4 = +423, 후보 docs +87/−0. 앞선+518/+420은 중간 검증 시점 수치다. source 순증은 bounded reader/index 및 정확한 코드 handoff·시작 진단 검증이며 새 module/entrypoint/framework는0이다.


### 0255cb05f 통합과 장중 보존 P5 계약 수리

- 사용자 통합 지시에 따라0255cb05f의8개 선행 commit을 이번 원천/holding 에러 수리와 함께 인수한다. 이전 failed P5/run09335ec4와 배포 보류는 당시 이력으로 보존하며 미완료 gate를 PASS로 바꾸지 않는다.
- 실제 보존 경로는 auxiliary transition manifest 없이 기존 준비본·정책을 사용한다. 같은 native 검증 호출의 전체 bootstrap 성공, 소비된 handoff/receipt, 준비본·선택·정책·원천 hash를 별도 typed closure로 묶는다. 빈 manifest만으로는 실패를 유지하며 current/full 경로에는 기존 manifest 계약이 그대로 적용된다. incumbent의 중첩 target-day digest는 지워지기 전에 같은 PID/boot/root/date로 기록하며 과거 PASS/cache를 재사용하지 않는다.
- 리뷰에서0255의 cumulative postclose reader 한 파일이 P5 Main 코드 목록에 들어오지만 새 source pair가 없음을 확인했다. 원a7c→0255의 정확한 두 hash만 기존 preparation-history owner에 추가한다. merged22-file reader/census 및 P5 두 owner는 하나의 complete dependency generation으로 검증하며 per-file 대안 조합은 금지한다.
- source-reader842 PASS, P5/policy/reuse1152 PASS, source proof/currentness/census/quantity469 PASS(중복 suite 합산 아님). 새 typed preservation은 실제 격리 child의 양성/변조·누락11개와 native producer 수집/old a7c 중첩 session으로 검증했다. 원본을 다시 읽는 native 동작은 최소 source19 frozen-input 재검증과 실제 P5 후속에서만 수행하며 정지 전까지 incumbent PID4094188/start10221444를 유지한다.
- 원천 reader 변경으로 extractor 코드 세대가 바뀐09/30·10/15·10/16의 기존 normalized cache만 명시적 native predecessor로 재검증한다. 원문/과거 cache/정책/strict/controller를 보존하며 normal32MiB reader budget을 늘리거나 inline migration하지 않는다. native 연구/currentness, clean 후보 P512consumer·child종료·보호 원천 불변과 ordered 배포/PID는 아직 실제 영수증으로 닫아야 한다.


- 10:55 실제 P5/run2d922451은 원 준비본a45fe9f1과 활성본4e2e42eb를 같은 hash로 요구한 intake 결함으로 실패했다. 원 실패를 보존하고 기존 closure owner에서 두 세대를 각자의 native 원본에 결속한다. source19 연구416c4c0a/20840scope의 전체 현재 검증은 완료했으며 새 P5·ordered 배포·PID 수용은 미완료다. Main4094188/start10221444는 유지했다.

- P5/run6c360700의 추가 intake 실패는18,459B native gzip 증명과 기존1MiB delegation 하한의 불일치다. 작은 증명은 위임하지 않고 native child가 직접 읽도록 기존 수집 owner를 보완하며 원 실패/guard를 보존한다.

- P5/runab23d496은 실제 격리 child의 main_stop vote-index DB 접근에서 차단됐다.2.8MB 원 JSONL을 기존 bounded canonical reader로 직접 검증하도록 기존 owner를 보완한다. native12 consumer의 성공·격리/금지 시도0·종료와 신규 정책/PID 수용은 새 영수증으로만 닫으며 원 실패는 보존한다.

- P5/runb87d8e1b은 금지 접근0이나 native 캐시 adapter의 `binding` 누락으로12개 중 손절/holding2개 로드가 실패했다. 기존 adapter에 검증 전용 역할을 명시해 장후 producer admission은 계속 금지한다. 실제 새 P5와 배포/PID는 미완료다.


- 11:22 23d30a55b/PID390249 기동 후 실제 observer는 sentinel parser 인계 실패로 unobservable다. `[MainPolicyLoadAndExitValidation1018]`의 현재 source-only 소비 후속으로 fc39→f305의 정확한 parser-equivalent migration을 수리하고 native sentinel→current observer→full health를 다시 검증한다. 기동/P5 성공을 전체 report 건강으로 대체하지 않는다.

- 12:11 통합 수용:99c51c85f에0255·c696과 원 holding 사건 식별 수리를 포함해 native P5/c992f414의12 consumer·격리·종료·load PASS 및 ordered complete/pass, PID782998/start11032230을 확인했다. `[MainPolicyLoadAndExitValidation1018]`의 보존 정책 P5 code/native/PID 수용은 완료한다. 원 실패 이력은 위에 유지한다. 기동 뒤 holding12:10:40을 full health12:11:47이 같은 SHA로 읽었고 새 source gap은0, 원49389 두 사유는 보존한다. `[HoldingProfitExitSourceContractRepair]`·수량/비용·자연 수용과 현재 partial 관측을 완료 처리하지 않는다. [최종 소비](../../tmp/postclose-monitoring-20261019/holding-probe-integration-native/verification.json).

- 12:20 정규 통보 수용:`[HoldingProfitExitSourceContractRepair]`의 원49389 두 사유는 native source_gap으로 유지되며, 새 report 세대에서도 같은 사건 식별자를 받아 실제 재전송0을 확인했다(last_seen12:20:27, last_sent12:15:28). code/통합 배포/PID/중복 통보 수용을 원 자료 복구·자연 비용/관측 완료와 구분한다. [실제 정규 consumer](../../tmp/postclose-monitoring-20261019/holding-probe-integration-native/natural-duplicate-cycle-verification.json).


## 리팩터링 후보 구현 — CodeRefactorRetiredReview1020

- [x] **CodeRefactorRetiredReview1020** — 확정 우선순위 1~3의 제거·통합과 격리 후보 검증.
  - Source: 사용자 `후보 우선순위 구현하고 코드리뷰 후 수정보완 반복하고 배포본 준비`; [운영 handoff 계약](../runtime-release-routing.md#authorized-intraday-policy-preserving-code-handoff).
  - Scope/owner: matrix runtime·overnight retirement·automation dual review owner. 신규 정리 대상이나 framework 없이 기존 owner 안에서 구현한다. 배포 인프라 owner가 새 코드 세대의 선행 의존성 검사를 함께 담당한다.
  - 기준: 선택 릴리스 `etf-product-intake-20261020-21d822a64`, commit `21d822a64a9f4b9047d06babab26febf59f6ae61`. 격리 작업본 `/home/ubuntu/KORStockScan-worktrees/refactor-retired-review-20261020`, branch `codex/refactor-retired-review-20261020`.
  - 운영 분리: 확인한 Main PID `1175053`/start ticks `11403252`; selector SHA `7a80c567b8f9ca589b80d796b8a2d1d6d9a490fe401c23544bcabf0ea74e4d03`. 기본 작업본의 source·shell·선택 포인터·PID·정책은 변경하지 않는다. 병행 세션의 기본 체크리스트 편집도 덮지 않는다.
  - Acceptance: 제거 함수의 실제 호출자 0, 보존 public 함수·False gate 출력 동일, family별 검토 schema/decision/provider 계약 동일, 기존 정책 digest 유지와 새 코드 의존성의 정확한 검증, 영향 테스트·compile·문서 parser·diff 검사, clean 후보 커밋 및 불변 릴리스 패키지. 실제 선택/PID/자연 소비는 이 구현 완료와 별개다.

### 대체·제거 판정

| 기존 경로/함수 | 대체 | 판정·소비 근거 |
| --- | --- | --- |
| `scalp_entry_adm_runtime._read_payload`, `_matched_bucket`, `_prompt_context` | none | removed; 퇴역 후 public builder에서 도달하지 않는다. 정적 import·module alias·getattr·CLI/등록 경로 검사와 기존 ADM 테스트로 검증 |
| `holding_exit_matrix_runtime`의 `_safe_float/_safe_int/_safe_bool`, `_holding_matrix_ai_score_context`, `_holding_score_prior_fields`, `_holding_matrix_current_micro_support`, `_read_matrix_payload`, `_matched_entries`, `_prompt_context`, `_exit_to_hold_candidate_actions` 및 전용 상수/import | none | removed; 보존 함수의 AST는 기준본과 동일. Main/AI의 public builder·merge·scale-in safety veto는 retained |
| `sniper_overnight_gatekeeper`의 `OvernightRecordSnapshot`과 나머지 퇴역 helper 14개 | none | removed; helper 전용 테스트 11개도 제거. `_eod_label`, `_overnight_gatekeeper_enabled`, `run_scalping_overnight_gatekeeper`는 retained: 비활성 로그·true override 거절 및 역사/회귀 consumer. 활성 Main holding·same-session terminal·manual custody 테스트 유지 |
| 두 보고서의 `_parse_ai_review_response`·중첩 `_contract_validator` | 기존 `automation/dual_candidate_review.parse_candidate_review_response`·`validate_candidate_review_response` | consolidated; 직접 parser 호출 4곳과 provider callback 2곳 이관. 새 wrapper/module 없음. reviewer·decision enum·metadata·ensure_ascii·retry·오류 판정 유지 |
| matrix public API·bucket/date reader·`TRADING_RULES` 테스트 표면 | 기존 구현 유지 | retained; `ai_engine_openai`, `sniper_state_handlers`, 역사 replay와 현행 retirement/true-override 테스트가 소비. 파일 전체 삭제로 확대하지 않음 |
| 기존 native handoff의 이전 cleanup/product-intake 의존성 세대 | 새 정확한 `REVIEWED_RETIRED_REVIEW_DEPENDENCY_VARIANTS` | retained + successor; 역사 SHA/정책 digest/contract extension은 수정하지 않고 검토한 6파일과 전체 선행 의존성을 결속. 새로운 코드 세대의 native gate 준비에 필요한 보완 |

### 리뷰·검증

- Official Kiwoom Reference Gate: `2026-10-20T14:05:26.447978+09:00`, upstream `Kiwoom-Securities/Kiwoom-REST-API` HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 ka10003/ka10080 요청·응답, `postman/kiwoom-openapi.postman_collection.json` PRD/MOCK 확인. `kiwoom_docs`는 해당 revision에 없음. 퇴역 helper의 조회 callsite만 제거했으며 API/parser/실요청 변경 없음.
- 자체 리뷰→수정→재리뷰: 격리 폴더명을 고정한 기존 테스트를 실제 project root 기준으로 수정했다. 새 부정 입력 fixture의 공유 `FORBIDDEN_USES` 변형이 뒤 테스트를 오염시키는 문제를 deepcopy로 수정했다. 불필요 import를 제거했다.
- 배포 준비 회귀: 원 verifier가 새 overnight SHA를 `entry_consumer_reviewed_dependency_unreviewed`로 거절하는 실패를 먼저 재현했다. 기존 verifier에 정확한 후속 세대를 추가하고, 과거 product-intake fixture는 원 commit `21d822a64`로 고정하여 현재 파일과 섞이지 않게 했다.
- 영향 회귀: 기존 12개 테스트 파일 **450 PASS**, skip/실행 제외 0. Main/AI cache·holding/context·retirement·두 report consumer·provider contract·위치 gate 포함. 실제 네트워크는 seccomp로 connect/send 계열을 차단했다. 기존 pandas 경고 1건은 별도이며 변경하지 않았다.
- 기준본 차등 검증: matrix context 120개·merge 720개 결과 동일; 두 review parser 및 실제 provider callback은 family별 67개 입력의 반환/예외·전달 인자 동일. 일회성 parity 검증 **4 PASS**. 운영 입력/provider/주문 호출 없음.
- native handoff 표적 회귀 **236 PASS**: 새 세대 72건과 기존 cleanup/reader 선행 세대 164건. 정상 수용·누락/dirty/커밋된 변조 거절 및 전체 선행 의존성 보존. 이 범위 실행에 skip 없음; 파일 내 비영향 3,030건은 수집 후 선택 제외했다. 앞선 450건과 합계 **686 PASS**이며 차등 검증 4건은 별도다.
- Python compile **12파일 PASS**, Ruff `F401/F811/F821` PASS, 문서 print-only parser PASS(기존 OPEN 22건), AST import/alias/getattr 대사·diff 검사 PASS. sampler shell은 변경하지 않았고 `bash -n` PASS. 검토한 범위의 미해결 코드 결함 0; 전체 코드베이스 무결함을 뜻하지 않는다.
- 증감(base `21d822a64`): non-test source 7파일 **+224/-1,263, 순감 1,039줄**; test 5파일 **+122/-292, 순감 170줄**; docs 2파일 **+41/-0**. 새 모듈·wrapper·검증 프레임워크 없음. 공유 parser로 중복을 없앤 증가와 정확한 native 의존성 세대 20줄 증가를 포함한 수치다.
- 재현 로그·명령·원본 실패·일회성 차등 검증과 최종 패키지 검증은 `/home/ubuntu/KORStockScan/tmp/refactor-retired-review-20261020/`에 보존한다. 검증 자료를 운영 모듈이나 새 framework로 등록하지 않는다.

### 배포 대기 경계

- 구현 종료 후 불변 패키지를 준비하되 기본 작업본 shell·selector·PID·active policy는 변경하지 않는다. 현재 정책의 native confirmation parity, exact-date candidate handoff와 정지 전 최종 검사는 실제 실행 시점의 원천·commit·날짜에 결속해야 한다. 기존 영수증 재사용이나 정책 hash 치환은 허용하지 않는다.
- 병행 편집 중인 기본 체크리스트를 후보의 과거 snapshot으로 덮지 않는다. 실제 배포 준비 시 그 시점의 운영 문서와 본 절을 합친 뒤 기존 strict-bound 원본·사용자 편집본을 모두 보존하고 CAS handoff를 수행한다. 그 변경으로 commit이 바뀌면 후보 결속 영수증도 다시 준비한다.
- 역사 AVG_DOWN replay의 matrix 구현 SHA는 과거 영수증 그대로 유지한다. 새 코드의 자연 연구·PID 수용을 이 오프라인 동등성 검사로 대체하지 않는다. 새로운 원천/경제성 연구나 전체 원천 재생성은 이번 제거 묶음에 포함하지 않는다.


## 매수 지연 근거 재검토 — 2026-10-20

- [ ] `[PreSubmitDelaySituationResearch1017] 체결 기준 가격경로·단기 선택·정책 근거 수리의 자연 소비 확인` (`Due: 2026-10-21`, `Slot: PREOPEN`, `TimeWindow: 07:35~09:30`, `Track: RuntimeStability`)
  - 종료 원천 수리:기존 관측 registry의 admission을 봉인하고 실제 종료 cutoff로 observation_only 검열 영수증을 게시한 뒤 큐/요약을 비우도록 단일 owner에 통합했다. native raw/compact/summary→monitor에서 정시 검열과 이미 overdue인 누락의 계속 탐지를 함께 검증했다. 코드 기능1235·후속/역사 인계135 PASS, scoped finding0이며 원 stale2/미수집4·실제 latency/liquidity 차단·비용 null·21PREOPEN Acceptance를 보존한다. 운영 반영·자연 종료 수용은 별도다. [동일 코드 리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md#controlled-delay-observation-shutdown-repair-2026-10-20).
  - Source: 사용자 `다음액션 실행`, [기존 계획](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md#체결-이후-하락과-0초-선택-근거-재검토--2026-10-20), [원인·수리·회귀·재계산](../audits/pre-submit-delay-situation-research-implementation-review-2026-10-17.md#체결-기준-재검토와-단기-선정-보완--2026-10-20). 원10/17 완료/배포 이력은 보존하고 새 wire 별칭 해시·단기 선정/감시·체결 reader 결함만 재개한다.
  - 구현/연구: 선택21d822a64 기준 격리 작업본 `pre-submit-delay-evidence-20261020`에서 보완했다. 포지션585건·기회357건, 정확 fill/owner13건을 보존하고 후보 v4는105개 price_ready cell 중 판단 불충분92개·관측 pair 즉시 우위11개·중복 부모/자식180초2개다. 현재0초를 최적 시간으로 판정하지 않는다. source10/19→effective10/21 후보는 별도 출력에만 존재한다.
  - Acceptance 유지/확장: 원 short clock/P0/미래·과거 호가/회차예산/만료·예외·불확실/과거 projection hash/후보 pair·고정 split·0초 fallback/출력 한도 반례를 유지한다. f6/f7만 통합하고 다른 prompt/risk/model/validator는 분리하며, 정상 append snapshot과 미영수 append/재작성을 구분한다. 실제 시간별 coverage·정확 fill leg·successor/terminal 및 정책 근거를 같은 native ID로 대사한다.
  - 재인수: 병행 운영 전환0ce816f7c를 격리 merge fd7071c0f에 보존했고 통합 회귀1,511개와 최종 보고서49개가 통과했다. 후보 값·원 정책/PREOPEN은 같고 이번 수리의 운영 반영은 미실행이다.
  - 다음: 정식 코드·정책 인계 승인 범위에서 `DirectFamilyPreopenPolicyHandoff`의 원 정책/현재 PID 보존 검증과 새 정책 준비를 진행한다. 실제 배포·PREOPEN·PID·자연1/3/5초 선택/재점검은 미실행이며 자료 부족만으로 초기정책의 추가 경제성 승인 gate를 만들지 않는다. 과거 결손569건과 비용후 EV null은 현재 코드 수리와 별개로 남긴다.
## PYRAMID 전용 helper 제거 — CodeRefactorPyramidHelpers1020

- [x] **CodeRefactorPyramidHelpers1020** — 후속 조사 1번 묶음만 제거하고 격리 후보 검증으로 종결.
  - Source: 사용자 `다음액션 실행`; 직전 합의의 helper 8개·전용 변수 제거, 기존 테스트 보존/정리, 리뷰·검증·clean 후보 커밋. Opening Rotation·entry reader 통합은 이번 범위 밖이다.
  - Owner: `sniper_state_handlers`/scale-in. 기준 commit `0ce816f7c1e2c495c24fc11fd4ab0a7d837c56ca`, 선택 경로 `/home/ubuntu/KORStockScan-runtime-releases/clean-sqlite-integration-20261020-0ce816f7c`; 시작 시 selector 상태는 `pid_receipt_attested`. 후보 `/home/ubuntu/KORStockScan-worktrees/refactor-pyramid-helpers-20261020`, branch `codex/refactor-pyramid-helpers-20261020`.
  - 종료점: 제거 이름의 source/test/CLI/등록 참조 0, 보존 소스 AST 동일, 활성 AVG_DOWN·보유·청산과 역사 lineage·정책 세대 계약 검증, clean 후보 커밋. 기본 작업본의 병행 편집·shell·선택 포인터·PID·정책은 이 작업에서 수정하지 않는다.

### 대체·제거와 소비 근거

| 기존 대상 | 대체 | 판정·근거 |
| --- | --- | --- |
| `_pyramid_runtime_prior_default`, `_pyramid_runtime_prior_report_date`, `_load_pyramid_runtime_prior_payload`, `_pyramid_runtime_prior_is_stale`, `_pyramid_prior_rows_stats`, `_pyramid_runtime_prior_context` | none | removed; 퇴역 PYRAMID 원천 reader 내부 호출만 존재. 외부 실행 dispatch 없음 |
| `_pyramid_scale_in_decision_lineage`, `_recent_exit_candidate_pyramid_block_context` | none | removed; 외부 참조는 전용 테스트뿐. module alias/getattr·dependency binding·Main 진입점·CLI/shell/등록 경로 조사에서도 실행 호출 없음 |
| `_PYRAMID_RUNTIME_PRIOR_REPORT_DIR`, `_PYRAMID_RUNTIME_PRIOR_MAX_AGE_SEC`, `_PYRAMID_RUNTIME_PRIOR_CACHE` | none | removed; 삭제 함수 전용. 조사 시 기재한 경로·캐시 외에 최대 유효시간 상수도 같은 소유 범위임을 확인 |
| 전용 테스트 3개, lineage 생산 helper 테스트 1개 | 역사 pending lineage 직접 검증 | removed 3 / consolidated 1; 역사 journal ID의 정확한 record·symbol·promotion 인계와 누락·다른 promotion·결정 ID 부재 거절은 보존. 기본값/true override × 전략 3개에서 영구 퇴역·주문 차단 검증 |
| PYRAMID 퇴역 public 진입점, 역사 필드/reader, 활성 AVG_DOWN·보유·청산, shared import | 기존 구현 | retained; 현재 Main·역사 receipt·replay/test 소비자. 삭제 대상을 제외한 모듈 AST 전체가 기준본과 동일하며 추가로 고아가 된 import/global 없음 |

### 리뷰·검증 및 경계

- 자체 리뷰→보완→재리뷰: helper 삭제 테스트 중 역사 pending 인계 검증을 보존했다. handoff 테스트가 과거 AVG_DOWN 세대에 현재 파일을 혼합하는 문제를 확인했다(최초 후보 4 FAIL, 변경 전 기준본에서도 2 FAIL). 기존 테스트 입력을 실제 발행 commit `deb996a22689ac08e171ea38966d070d63d236ee`의 원본 Git bytes·103개 dependency·selector에 결속하고, 미검토 변경/누락 거절 검증을 유지했다. 생산 verifier·allowlist·정책·원 영수증은 변경하지 않았다.
- 영향 검증: 8파일 **1,506 PASS**, 제외/skip 0. 수정 handoff 파일 전체 **74 PASS**, 역사 holding handoff 파일 **340 PASS**로 총 10파일 **1,920 PASS**. 네트워크 connect/send는 기존 seccomp runner로 차단했고 provider·실주문 호출은 없다. 최초 실패와 수정 전후 로그는 후보의 `tmp/refactor-pyramid-helpers-20261020/`에 보존한다.
- Python compile 3파일, 제거 심볼 참조 0, 보존 AST 동등성, 문서 링크/owner/print-only parser·`git diff --check` 통과. Ruff `F811/F821` 0; 기존 두 파일의 `F401` 18건은 기준본과 동일하며 신규 지적 0. 수정 handoff 테스트는 `F401/F811/F821` 통과. 기존 pandas 경고 1건은 그대로다. shell/cron 변경이 없어 shell 계약·`bash -n`은 해당 없음.
- 증감(base `0ce816f7c`): non-test source **+0/-368**, test **+81/-165**(순감84), docs **+25/-0**. 새 모듈·wrapper·framework·보고서 producer·파일 이동 없음. 테스트 추가는 역사 입력 고정과 퇴역 경계 보존에 사용했다.
- 코드 세대 경계: `avg_down_policy_replay`는 삭제한 함수도 loaded-code identity에 포함했으므로 원 역사 fingerprint/정책 영수증은 그대로 보존한다. 현재 snapshot 수용과 변경된 implementation 거절 회귀는 통과했지만 이 후보용 운영 handoff를 발행한 것은 아니다. 향후 배포 준비 owner는 해당 시점의 incumbent·정책·후보 commit에 대한 새 native parity/delay/stop/holding handoff를 검증해야 한다. 기존 PASS 재사용·hash 치환·실제 배포/재기동·자연 소비 완료는 이번 종료점에 포함하지 않는다.

## Opening Rotation 미사용 helper 제거 — CodeRefactorOpeningRotation1020

- [x] **CodeRefactorOpeningRotation1020** — 후속 조사에서 확정한 runtime helper 4개 제거와 격리 후보 검증.
  - Source: 사용자 `다음액션 실행`; 범위는 `scalping/opening_rotation.py`의 미사용 함수와 직접 영향 검증뿐이다. entry 관측 reader 통합이나 다른 퇴역 모듈 정리는 포함하지 않는다.
  - Owner: Opening Rotation metadata/retirement. 기준은 선택 commit `10f8d1ba69ca513bc2ec25f64a91204a4a655258`, release `delay-cleanup-final-20261020-10f8d1ba6`. 격리 작업본 `/home/ubuntu/KORStockScan-worktrees/refactor-opening-rotation-20261020`, branch `codex/refactor-opening-rotation-20261020`.
  - 종료점: 아래 4개 runtime 함수 제거·잔여 호출자 0, 보존 AST와 역사 reader 원본 동일, 영향 테스트·compile·문서 parser·diff 검사 통과 및 clean 후보 커밋. 기본 작업본의 병행 문서 변경·운영 shell·선택 포인터·PID·정책은 수정하지 않는다.

| 기존 대상 | 대체 | 판정·소비 근거 |
| --- | --- | --- |
| runtime `_blocked`, `_entry_micro_gate_preview` | none | removed; public evaluator는 영구 퇴역 반환만 수행. 정적 import·별칭·attribute/getattr·CLI/등록 확인에서 별도 실행 호출 없음 |
| runtime `_number`, `_boolean` | none | removed; preview만 사용하던 전용 변환 함수. 2개 상위 helper 제거 후 남을 중복도 함께 정리 |
| `lifecycle/archive/opening_rotation_readers.py`의 동명 함수 | 기존 역사 구현 | retained; 역사 `evaluate_entry`와 backtest reader가 실제 호출. 파일 bytes/SHA와 과거 평가 규칙을 보존 |
| runtime public evaluator·profile·position tag·시각/가격·정책 reader | 기존 구현 | retained; scanner·state handlers·sync·execution receipts·역사 backtest/tuning metadata 소비자. 보존 소스 AST 전체가 기준본과 동일하고 신규 고아 import/global 없음 |

- 자체 리뷰→보완→재리뷰: 기존 `test_opening_rotation.py`의 autouse fixture가 Main evaluator를 역사 구현으로 바꾸는 점을 확인했다. 기존 retirement/tuning 테스트 파일에서 원 runtime module을 직접 호출하는 검증 2건을 보완해 `enabled=False/True` 모두 WATCH/HOLD·`allowed_runtime_apply=False`, 상태 보존과 파일 I/O 없음까지 확인했다. 새 module·wrapper·framework·보고서 producer·파일 이동 없음.
- 검증: `test_opening_rotation.py`, `test_opening_rotation_backtest.py`, `test_opening_rotation_tuning.py` 전체 **184 PASS**, 제외/skip 0. scanner의 `test_watch_budget_opening_config_ignores_legacy_per_field_env` **1 PASS**로 총 **185 PASS**. 기존 seccomp runner로 connect/send를 차단했으며 운영 원천·provider·주문 호출은 없다. 재현 로그와 AST/import 검토는 후보 `tmp/refactor-opening-rotation-20261020/`에 보존한다.
- Python compile 2파일·Ruff `F401/F811/F821`·문서 링크/owner/print-only parser·`git diff --check` 통과. runtime 제거 함수의 import/attribute/getattr 참조 0, public import 9곳의 계약 보존 확인. shell/cron 및 broker API/parser/계좌/주문 callsite 변경이 없어 shell 검사와 Official Kiwoom Reference Gate는 해당 없음.
- 증감(base `10f8d1ba6`): non-test source **+0/-158**, test **+30/-0**, docs **+20/-0**. 테스트 증가는 역사 fixture에 가려졌던 원 runtime 퇴역 경계 검증이며 생산 코드는 삭제만 했다.
- 검토 범위의 미해결 코드 결함 0으로 구현 종결. 정책 handoff 발행·불변 배포 패키지·선택/PID 전환·재기동·자연 소비는 수행하지 않았다. 향후 배포 준비에서는 당시 선택본과 후보 commit의 기존 native handoff 계약을 검증하며, 이번 pytest 결과를 운영 적용 영수증으로 사용하지 않는다.


## Entry 관측 reader 통합 — CodeRefactorEntryObservation1020

- [x] **CodeRefactorEntryObservation1020** — 동일 정규화 구현 33개를 기존 owner로 통합하고 격리 후보를 검증.
  - Source: 사용자 `구현하고 코드리뷰 후 수정보완 반복하고 배포본 준비`; 확정 범위는 entry event 정규화·역사 ADM reader·기존 호환 import·직접 영향 테스트다.
  - Owner: `scalping/entry_observation_events.py`(공통 정규화), `lifecycle/archive/scalp_entry_action_decision_matrix_readers.py`(역사 전용 집계). 기준 선택 commit `d927d0d70f1daef2e2a6bf9aeccc0e0f1a028f26`, release `entry-role-latency-integrated-20261020-d927d0d70`.
  - 격리 작업본 `/home/ubuntu/KORStockScan-worktrees/refactor-entry-readers-20261020`, branch `codex/refactor-entry-readers-20261020`. 기준본의 Opening Rotation source/test는 앞선 `d8acaa0aa`와 동일하며 중복 적용하지 않았다. 기본 작업본의 병행 문서·선택 포인터·PID·운영 shell·정책은 수정하지 않는다.
  - 종료점: 중복 구현 제거·소비자 이관·동등성/퇴역 검증·clean 후보 커밋과 불변 배포 대기 패키지. Sentinel/reversal 통합, 성능·source-quality 의미 변경, 배포·재기동은 범위 밖이다.

| 기존 대상 | 대체 | 판정·소비 근거 |
| --- | --- | --- |
| 역사 reader의 공통 함수 33개·동일 상수 11개 | 기존 `entry_observation_events` 구현 | consolidated; 중복 함수 본문909줄 제거. 역사 집계가 직접 사용하는 helper 5개와 상수 2개만 import하고 별도 구현을 남기지 않음 |
| 역사 reader의 pipeline/threshold/snapshot 경로 전역값 3개 | canonical event reader의 기존 경로 | removed; 실제 경로 소비·테스트 patch를 canonical owner로 이관. 두 파일의 기본 project root 해석은 동일 |
| 역사 reader 전용 14함수·ADM/post-sell 경로·clean baseline | 기존 역사 reader | retained; 역사 sim outcome/누적/lookup/unknown 집계가 소비. 보존 함수 AST 전부 기준본과 동일 |
| root 호환 표면의 공통 함수 7개 import | canonical owner 직접 import | consolidated; 기존 이름은 명시적 재수출로 유지. 나머지 역사 export와 retired builder/render/CLI 유지; 문서 owner가 역사 명령을 퇴역시킬 때 이 호환 표면을 별도 제거 |
| 현행 정규화·source adapter·dedupe/followup·Main WAIT6579 상수 | 기존 구현 | retained; gate backtest·intraday probe·Main이 소비. 두 현행 파일 bytes는 기준본과 동일하며 runtime/order/provider 권한을 추가하지 않음 |

- 자체 리뷰→보완→재리뷰: 전역 경로 patch를 옛 module에 남기면 canonical import가 다른 경로를 읽을 위험을 제거했다. 호환 import는 명시적 재수출로 정리해 기존 API를 보존했다. 손상 JSON fixture가 token filter에서 조기 제외되던 것을 수정해 실제 decoder 실패 경로도 확인했다. 검토 범위의 미해결 코드 결함 0이며 전체 코드베이스 무결함을 의미하지 않는다.
- 검증: 기존 영향5파일 변경 전 **192 PASS**, 최종 **199 PASS**, skip/제외0. 미압축·gzip·공존·snapshot, 날짜/재시도/cancel-wait 제외, 중복 source, 누락·빈 입력·손상 JSON의 기존 판정, source-only 결과와 retired builder/render/CLI 무권한 종료를 확인했다. 역사 sim/누적·정규화/score lineage·gate/probe consumer의 기존 회귀를 보존했다.
- 격리: 기존 seccomp runner로 network connect/send를 차단하고 fixture의 원천/retirement 경로를 tmp에 결속했다. 정규 보고서·원천 재생성, provider/주문/취소 호출은 없다. 원래 source-quality 판정을 바꾸거나 과거 계보/손익을 새로 만들지 않았다.
- Python compile4파일·Ruff `F401/F811/F821`·static import/별칭/attribute/getattr·CLI/등록 확인·문서 owner/print-only parser·`git diff --check` 통과. 제거 정의33개·미이관 consumer0·역사14함수 AST 동일·canonical2파일 bytes 동일. shell/cron 및 broker API/parser/계좌/주문 callsite 변경이 없어 shell 검사와 Official Kiwoom Reference Gate는 해당 없음.
- 증감(base `d927d0d70`): non-test source **+29/-1,248, 순감1,219줄**; test **+113/-28, 순증85줄**; docs **+26/-0**. 새 module·wrapper·report producer·validator/framework·파일 이동 없음. 테스트 증가는 실제 source adapter/호환 reader 경로와 퇴역 CLI를 검증한다.
- 재현/리뷰 자료는 후보 `tmp/refactor-entry-readers-20261020/`의 `baseline-tests.log`, `final-tests.log`, `removal-scope.json`, `review.json`, `docs-parser.log`에 보존한다.
- 배포 대기 패키지 owner는 deployment infrastructure. 최종 clean commit을 `/home/ubuntu/KORStockScan-runtime-releases/entry-readers-20261020-v1`에 detached로 준비하고 기존 `runtime_release_router.validate_release`로 source/commit·공유 경로·영구 퇴역 guard를 검증한다. 최종 결과는 같은 후보 evidence directory의 `release-validation.json`에 남긴다.
- 선택/PID 전환·실제 배포·재기동·자연 소비는 미실행이다. 공유 docs는 기존 운영 문서를 유지한다. 실제 배포 시에는 당시 선택본과 이 후보의 ancestry/문서 변경을 다시 통합하고, 정확한 active-policy native handoff/parity 및 pre-drain 검증을 새로 수행해야 한다. 이번 code/package 검증을 그 영수증으로 재사용하지 않는다.
