# 2026-09-07 장후 실행 모니터링·복구 검토

판정: **Postclose Control State: YELLOW**. 대상 거래일 `2026-09-07`, 최종 관찰 `23:25 KST`. 최신 finalization cleanup은 23:23:29, final detector는 **23:23:30 DONE**이다. 오류 detector `pass`, 초기화 실패 0, critical/error 0을 확인했다. 운영 복구와 허용된 구현/review fixed-point는 닫혔으나 source 근거 대기 9건·외부 자연 source 추적 3건·native 추천 ID 결손 26행은 완료로 세지 않는다.

| Owner | Target date | Latest state | First failure | Repair | Validation | Latest terminal |
| --- | --- | --- | --- | --- | --- | --- |
| EOD | 2026-09-07 | completed | 없음 | 기존 자연 EOD 대기 | quote date/2629행 | completed |
| Main postclose | 2026-09-07 | succeeded | 21:44 verifier FAIL | source-only tail repair | exact date/status | 22:32:59 DONE |
| Final verifier | 2026-09-07 | warning terminal | source/workorder/smoothing mismatch | 직접 producer·consumer 보완 | 구조적 blocker 0; source warning 보존 | 최신 controller generation terminal |
| DONE controller/follower | 2026-09-07 | done / completed_offline_only | warning/empty-source/candidate 검증 | source-only terminal 분류·hash 검증 | consumer terminal=true, Provider 신규 0 | 23:19:09 DONE |
| Tuning monitoring | 2026-09-07 | success | 정상 main 대기 | 자동 재개 | parquet/archive/shadow 완료 | 22:35:39 DONE |
| Dashboard archive | 2026-09-07 | done | 없음 | 불필요 | exact-date DONE | 20:50:30 DONE |
| Widget evaluation | 2026-09-07 | success | 정상 EOD 대기 | 자동 진행 | unit exit0/Result=success | 22:08:41 |
| Episode recommendations | 2026-09-07 | source-only terminal | audit hash/immutable ingress 분류 | source/handoff만 재생성 | independent owner 및 policy 변경 0 | Pass 2 source hash 대사 PASS |
| Machine final refresh | 2026-09-07 | success | attribution/timing source gap | 영향 4 producer CLI 재생성 | unit 6단계 성공 + CLI exit0 | service 22:13:18; 최신 Pass 1 generation 별도 |
| Finalization/error detector | 2026-09-07 | done / pass | 이전 predecessor 및 cleanup FAIL | 과거 semantic artifact 비압축 보존·receipt 보존 | source/hash/I/O guard 유지; critical/error0 | 23:23:30 DONE |

[Pass 1/2 전수 ledger](./2026-09-07-postclose-recommendation-intake-ledger.json): 67→66행, implement-now 10→9, 신규/decision 변경/누락 0. 해결된 window ID 1건은 이전 generation의 구현 완료 이력으로 분리했다. 다음 검증은 [9/8 checklist](../checklists/2026-09-08-stage2-todo-checklist.md)의 `PostcloseRecoverySourceAcceptance0908`이 소유한다.

아래는 최초 발견 시각부터의 복구 이력이다. 당시 진행 상태는 위 최종 상태와 구분한다.

## 운영 근거

- 메인 wrapper PID895257, immutable snapshot SHA256 `63cb2f238beb056818574bbdc457b22bdc2f606cb8fab960c37177d9b0e7c695`. 삭제된 임시 pathname의 원문을 `/proc/895257/fd/255`에서 읽어 보존했다. 현재 작업 트리와 실행 snapshot을 혼동하지 않는다.
- EOD completed, latest quote date2026-09-07, 당일 DB2629행. 일부 짧은 OHLCV 이력 종목은 명시 제외했다.
- Dashboard archive: 20:50:30 대상일 DONE.
- Low-price 확장 source 수집은 shared-read defer/exit75 후 기존 wrapper의 재개 경로를 사용했다. cache18개를 재사용했고 21:20 산출물로 후속 진행했다. 수동 retry/호출량 상향 없음.
- 메인 source-quality audit 앞의 가용메모리3945.8MiB<4096MiB 대기는 기존300초 bound 안에서5349.4MiB로 회복해21:30:03 통과했다. Guard 변경 없음.
- Widget evaluation은 EOD gate를2610초 대기 후 통과해 signal policy 연구 중이다. Machine final refresh Job33099는 설치된 After=widget evaluation 순서에 따라 대기한다.
- 21:05 AI replay는 exact-date 메인 선행 대기이며 FD9/inode320009의 FLOCK 점유를 직접 확인했다. acquiring PID가 종료되어 lslocks에 표시되지 않는 경우를 미점유로 처리하지 않는다.

## Detector 결함 보완

1. 긴 상세 로그가 START를 tail5000행 밖으로 밀어내 `no start/completion within window` 오탐을 만들었다. Once 작업은 같은 rotated bundle의 대상일 lifecycle marker를 streaming으로 읽고 마지막128개만 보존한다. 새 START 이후 marker를 독립 run으로 보며 JSON 본문에 인용된 marker를 terminal로 세지 않는다. 기존 완료시각 기준·실패 우선순위·recurring 판정은 유지했다.
2. Lock mtime만으로 오래된 파일을 stale로 세고 미점유 inode를 삭제하던 동작을 제거했다. Nonblocking 점유 확인만 수행하고 unheld marker도 보존한다. Held는 owner health 성공/실패가 아니라 별도 PID/start/progress 대조가 필요한 관측이다. 접근 불가는 unknown warning으로 유지한다. 예전 cleanup flag로 삭제 권한을 재생성하지 않는다.

변경 owner: `src/engine/error_detectors/{cron_completion,stale_lock}.py`와 직접 테스트2개. 별도 작업 트리에서 구현→재리뷰→회귀를 닫고 메인 snapshot에 detector import가 없음을 확인했다. 반영 직전 root 파일이 원본과 동일함을 대조해 병행 변경을 보존했다. 매매 bot·위젯/에피소드 매매 process·주문·provider·threshold·cap·operator lock은 변경하지 않았다.

## 검증

- 최종 직접 회귀4개 파일 **59 PASS**, Python compile·Ruff production/lock tests·diff check PASS.
- 추가 회귀: 6000행 상세 출력, rotation 후 신규 run, 과거 DONE과 현재 START 분리, JSON 내 가짜 DONE, deadline 이후 미완료, old unheld inode 보존, held mutex 보존, dry-run 동일 비삭제, 접근 불가 상태.
- 실제 읽기 전용 재판정: cron pass/main in_progress; lock7개 중 replay/tuning2개 held. Probe 후 점유/파일 inode 보존.
- 자연21:30 run `cron-20260907T213001-960939`: cron_completion PASS/main in_progress, stale_lock PASS/read-only occupancy. 전체 warning은 아직 생성 전인 후행 artifact 경고이며 두 오탐은 해소됐다.
- 이 detector 변경 범위의 미해결 review finding0. 전체 작업 트리나 실거래 경제성 완료를 의미하지 않는다. 운영 재시작/비싼 report 재생성 없이 다음 정기 detector가 소비했다.
- Evidence: `tmp/postclose_monitor_20260907/{start_receipt,detector_review_gate,error_detector_before,error_detector_after_natural_2130,detector_corrected_readonly}.json`, `observations.jsonl`.

## 초기 관찰 당시 남은 실행

Main verifier/controller/follower, tuning monitoring, widget evaluation, machine final refresh와21:55 finalization/final detector의 terminal을 계속 확인한다. Authoritative implement-now/위젯/에피소드 intake와 Pass1/2는 운영 체인 terminal 후 수행한다. 현재 intake/fixed-point 미완료이며 생성 전 산출물을 빈 추천으로 대체하지 않는다. 기존 `AutomationTriggerDecisionSummary0907` 실행 확인 owner를 재사용한다.

## 21:44 verifier 실패와 최소 복구 진행

- 21:44:45 메인 verifier FAIL, wrapper exit1. Controller는 기존 tail recovery를 실행한 뒤 `verify_postclose_chain_pending_done_failed`로 terminal blocked했다. 원본 verifier는 `tmp/postclose_monitor_20260907/verifier_first_fail_214445.json`, 후속 산출물 원본/hash는 `pre_recovery_generation/manifest.json`에 보존했다.
- Entry source-only weak-contract workorder5개의 `mapped_family/threshold_family`가 퇴역 LDM을 가리켜 mixed-report filter가 제거했다. Producer를 기존 `entry_submit_drought_attribution`으로 결속하고 파일 안내도 현행 `scalping/main_lifecycle_paired.py`로 수정했다. 퇴역 필터와 실주문 권한은 유지한다.
- Workorder producer는 `source_quality_blocked`를 필수 root-cause followup으로 세지만 verifier는 누락했다. 같은 상태를 필수 검사에 추가했다. 불완전한 followup은 계속 FAIL이다.
- 관련2개 test file **330 PASS**, compile/diff check PASS. 필터 통과 후 필수6개 ID 보존과 source-quality-blocked의 완전/불완전 계약 반례를 확인했다. 이 변경의 review finding0.
- 21:51 workorder 최소 재생성 후 current view16개/필수 Entry6개 보존, root-cause contract14/14 PASS. generation ID는 source 기반이라 같을 수 있으므로 실제 변경은 원본/신규 artifact byte hash와 코드 diff로 별도 대사한다.
- Samsung/저가주 보고서가 소비한 audit hash가 후속 audit 재생성으로 stale해졌다. 두 producer와 후보만 기존 CLI로 재생성했다. Samsung 계약 PASS, 저가주 candidate valid, policy mutations0, runtime_effect=false. live env·매매 process 변경 없음.
- 당시 미복구 smoothing: force-exit1행의 phase/terminal reason 필드 결손; cumulative journal335행의 scalar phase 계수와 compact tail50행을 비교한 계약 불일치. 병행 daily report 수정과 중복하지 않도록 해당 파일은 변경하지 않았다. 수정 완료·review·재생성 뒤 verifier/controller를 다시 닫아야 한다.
- Main AI cycle은 source-only blocked/deferred, 준비6단계 exit0이며 Provider 호출false. Invalid historical materialized binding, observer timestamp exclusion 증거와 lifecycle receipt/custody gap은 별도 source-only workorder로 남아 있다. 이를 운영 DONE이나 경제성 acceptance로 바꾸지 않는다.

- 추가 리뷰: owner 매핑 변경을 이전 source generation과 구분하도록 producer contract를 `code_improvement_workorder_producer_v4`로 올렸다. 재검증330 PASS 후 21:58:50 신규 generation `2026-09-07-e930940341be` / byte SHA256 `e92eeb89f9c072a0c74a6900572c0d65d8292c8d29242e7087fc625a36555ef2`, 필수 ID 누락0·followup14/14 PASS. 근거 `workorder_recovery_gate.json`.
- 21:55 finalization은 predecessor terminal failure로 cleanup을 건너뛰고 bounded detector를 실행했다. 21:55:03 detector artifact 존재; finalization은 FAIL이며 최신 성공으로 복구해야 한다.


## 22:14 후속 복구와 현재 경계

- 병행 daily report 세션의 최종 반영 기록을 확인한 뒤 해당 변경을 보존하고 smoothing 부분만 보완했다. Force-exit `holding_context_cannot_defer`의 누락 phase/terminal reason은 기존 telemetry helper로 기록한다. 실행 guard·청산 판단은 변경하지 않았다.
- 현재 raw의 결손 force-exit1행은 원본을 보존하고 해시·결손 필드·input/output/excluded 보존식을 가진 `smoothing_force_exit_row_exclusion_v1`로 decision input에서 제외했다. Verifier가 해시·날짜·실제 필드 결손과 보존식을 독립 검증한다. 다른 ingestion failure는 유지한다.
- Cumulative `smoothing_source_only_path_journal_v3`의 전수 rows와 exclusion receipt는 diagnostic tail50 compaction에서 제외했다. 전체335행과 scalar phase 계수를 다시 대사한다.
- 직접6개 테스트 파일 **595 PASS**, compile/format/diff check PASS, 해당 변경 범위 review finding0. 실제 loader9493행 포함/1행 제외/receipt issues0. 22:11:43 daily/cumulative 재생성 exit0, smoothing verifier PASS. AI review는 `skipped_no_review_candidates`, new Provider call=false.
- Widget evaluation22:08:41 Result=success/exit0. Machine final refresh22:13:18 expansion·attribution·weakness·timing·policy·checklist 모두 exit0, Result=success.
- Controller 최소 tail recovery에서 workorder·EV·runtime summary·다음 exact-date PREOPEN 정식 handoff·runtime gap·pending verifier가 exit0이었다. full-wrapper rerun은 명시 false로 유지했다. 새 machine timing source-quality structural shortage가 DONE/status reconciliation을 차단해 아직 완료가 아니다.
- 현재 삼성 위젯 native execution signal ID의 attribution 연결과 closed collector ingress receipt loss의 terminal quarantine 분류를 후속 보완 중이다. 원본 timestamp 거절2건은 exact row receipt가 없어 당일 경제성 입력으로 복구하지 않는다. 이후 자연 수집과 실주문 효과는 별도 acceptance다.
- 위 595-test 증거: `tmp/postclose_monitor_20260907/{smoothing_review_gate,smoothing_actual_loader_replay,smoothing_regenerated_verifier}.json`. 병행 세션이 커밋한 HEAD `b54c3a5d`와 현재 후속 변경을 구분한다.


## Machine source-only 구조 분류 보완

- 삼성 위젯 signal anchor가 generic advisory에만 event ID를 찾았다. 해당 owner의 native `symbol:date:ENTRY:session:timestamp` ID를 실행 원장의 exact symbol/date/session 계약으로 검증해 사용한다. ID 합성·근접 join·다른 owner advisory 대체는 없다.
- Closed/reconciled collector에서 enqueue 전 timestamp 거절이 확정되고 exact rejected-row receipt가 없으면, 같은 날짜 재생성으로 source를 복원할 수 없다. 모든 선언 loss counter=0, authority false, 정확한 exclusion reason/count, 완료된 당일 canary·source hash가 확인될 때만 `immutable_ingress_receipt_loss` 진단을 낸다. 이 진단은 source eligibility를 통과시키지 않는다.
- Timing은 모든 실제 anchor가 여전히 source blocked이고 별도 repairable companion gap이 없을 때 기존 exact-date quarantine→다음 runtime receipt acceptance로 연결한다. 수집 중·불완전 counter·추가 capture loss·남은 event ID 결손은 quarantine 종결로 숨기지 않는다.
- 관련 attribution/timing/controller/verifier **379 PASS**, compile·diff·parser PASS와 실제 원본 재현을 확인했다. attribution→weakness→timing→approval→checklist 최소 재생성 모두 exit0. 당일 anchor8건 blocked/eligible0, winner/runtime winner 없음, runtime effect/allowed apply=false 유지. source shortage는 해결됐다고 보고하지 않는다.
- Controller는 이 신규 generation으로 다시 tail verification 중이다. 증거: `tmp/postclose_monitor_20260907/{machine_repair_gate,machine_source_readonly_replay}.json`, `pre_machine_repair/artifact_manifest.json`, `machine_*_recovery.log`.


## 22:35 메인 복구와 follower 확인

- Controller는 verifier의 `microstructure_diagnostic:warning`과 `conversion_lane_no_candidates`를 무조건 실패로 처리했다. Micro handoff issues0·필수 workorder ID·runtime/apply false와 conversion source-present·candidate0·lineage blocker0를 확인하는 조건부 terminal warning 계약을 추가했다. 결손 section, authority true, 비어 있지 않은 후보 또는 lineage 오류는 계속 차단한다.
- Controller/verifier 직접 **260 PASS**, compile/diff PASS, 실제 verifier read-only tail acceptance PASS. 22:32:59 main status `succeeded`와 최신 DONE이 이전 FAIL을 대체했다. full_wrapper_rerun=false, 매매 process 조작 없음.
- Tuning monitoring22:35:39 success/DONE. Parquet/검증 archive/shadow diff 후행이 완료됐다.
- AI replay KRX는 exact control0/충돌0 manifest를 `control_manifest_not_ready` 예외로 처리했고 기존3회 재시도를 소진했다. 원본 excluded_counts와 missing natural stages를 보존한 terminal no-exact-control 처리와 invalid/conflicting manifest 실패의 경계를 검토 중이다. 신규 Provider 호출 또는 source 품질 완화로 복구하지 않는다.


## AI replay exact-control zero terminal 보완

Control manifest의 target date/cohort, self-hash, explicit non-authority, controls empty, signature conflicts0, 전체 missing-stage census와 제외 사유 계수를 검증한 경우에만 기존 `hold_no_exact_entry_control`을 반환한다. 원본 `control_manifest_gap_fix_required`와 excluded counts는 보존하고 Provider 호출0·source gap은 미래 exact source가 필요한 상태로 기록한다. Invalid hash/date/cohort, promotion failure, conflicts, controls 존재, 잘못된 counter 또는 authority에는 이 경로를 적용하지 않는다. Batch/optimizer/consumer 직접 **54 PASS**, compile/diff PASS, 실제 당일 manifest read-only 검증 PASS. 기존 follower가 terminal 실패한 뒤만 코드를 반영했다. 재실행으로 가격·수량·provider route·prompt를 변경하지 않는다.

### Consumer 및 controller terminal 연결 보완

Optimizer에 Entry cohort가 없더라도 frozen batch의 기존 지원 cohort를 consumer census에 보존했다. 57개 targeted test와 실제 source-only 재생성에서 `entry_followup_terminal_ready=true`를 확인했다. 모델 입력이 없는 blocked candidate의 계약 hash 부재는 source-only terminal로만 처리하며 날짜·파일/self hash·reference·권한 OFF 및 exact KRX zero-sample cohort를 모두 검증한다. 모델 계약이나 실전 승격 권한은 생성하지 않는다.

### 23:00 cleanup 실패

23:00:44 cleanup FAIL의 최초 원인은 8/25~9/4 과거 9개 R2/R3 artifact set의 현행 semantic contract 불일치였다. 압축 검증 실패 0, partition 실패 0, source unlink 0이며 원본을 보존했다. 읽기 전용 census에서 `r3_manifest_research_projection_mismatch` 또는 `r2_current_run_blocker_binding_invalid`만 재현됐다. 저장소 소유자는 이 과거 원본을 수정하거나 튜닝 입력으로 승인하지 않고 비압축 보존 warning으로 분리한다. 당일/protected-date·hash·I/O·중간 publish 오류는 기존 실패 경로를 유지한다. 실패 상세 JSON 삭제도 제거해 각 실행 receipt를 보존한다. Evidence: `tmp/postclose_monitor_20260907/storage_readonly_diagnosis.json`.

### Pass 1 intake 및 코드 보완

운영 체인은 23:10:09 final detector DONE으로 정상 terminal이 됐다. 동결 intake는 67행: implement-now 10, 비구현 추천/추적 57, native ID 중복 0 및 JSON/Markdown main 38 ID 대사 PASS. ID 없는 26행은 원본 pointer로만 보존하고 권한을 만들지 않았다. `tmp/postclose_monitor_20260907/pass1_intake/ledger.json`이 전체 원본·hash·분모를 보존한다.

수정: scale-in 전용 rolling source의 exact date/content hash를 window consumer에 연결해 유효 source의 paired 0과 source 부재를 구별했다. 현재 sample floor 미달과 apply OFF는 유지한다. Submit 2건만으로 receipt/fill/taxonomy 결손을 확정하던 workorder 문구를 exact join 검증 대기로 바로잡고 producer v5로 generation을 분리했다. Machine objective followup도 timing과 동일한 검증된 irreversible ingress loss를 소비해 같은 과거 날짜 재실행을 요구하지 않는다. 과거 원본을 복원한 것으로 보고하지 않는다.

### Pass 1 보충 review 및 Pass 2

581개 회귀 PASS 후 실제 daily 재생성에서 candidate builder가 새 날짜/hash 필드를 전달하지 않는 결손을 추가로 발견했다. producer→candidate→window 전체 경로를 보완하고 테스트를 실제 candidate builder를 통과하도록 변경했다. 추가 176 PASS와 실제 재생성에서 `primary_source_available=true`, `primary_sample_count=0`, `hold_sample`, window audit issue 0을 확인했다.

Pass 2 generation `2026-09-07-18b622a64a1e`(producer v5): 전체 66 = 구현 요청 9 + 비구현 57. Pass 1의 해결된 window order 1건은 removed history로만 남긴다. 신규 native ID 0, native decision 변경 0, 미분류/누락 0. 현행 eligible 9 = `blocked_missing_evidence` 9 + actionable open 0. 비구현 57 = observed 25 + deferred 2 + rejected 1 + external dependency 3 + native ID/authority 결손 26. 각 원본 위치·hash·owner·consumer·acceptance는 [전체 ledger](./2026-09-07-postclose-recommendation-intake-ledger.json)를 따른다. blocked는 구현 완료가 아니며 전체 GREEN을 주장하지 않는다.

현재 코드 변경 범위의 P0~P2 review finding 0, compile/bash syntax/diff/parser validation PASS. 중복된 테스트 실행을 합산한 단일 고유 테스트 수로 보고하지 않는다. 실주문·실거래 process·provider route·threshold·수량·cap·operator lock 변경은 없고, 새 로그 계측의 다음 PID 소비와 비용 차감 EV는 별도 acceptance다.
