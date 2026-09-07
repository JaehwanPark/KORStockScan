# 2026-09-07 장후 실행 모니터링·복구 검토

판정: **복구 진행 중 / 현재 RED**, 관찰 기준 21:59 KST. 대상 거래일은 2026-09-07로 고정한다. 메인·위젯·후행 작업이 terminal 전이므로 GREEN/fixed-point 완료를 주장하지 않는다.

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

## 남은 실행

Main verifier/controller/follower, tuning monitoring, widget evaluation, machine final refresh와21:55 finalization/final detector의 terminal을 계속 확인한다. Authoritative implement-now/위젯/에피소드 intake와 Pass1/2는 운영 체인 terminal 후 수행한다. 현재 intake/fixed-point 미완료이며 생성 전 산출물을 빈 추천으로 대체하지 않는다. 기존 `AutomationTriggerDecisionSummary0907` 실행 확인 owner를 재사용한다.

## 21:44 verifier 실패와 최소 복구 진행

- 21:44:45 메인 verifier FAIL, wrapper exit1. Controller는 기존 tail recovery를 실행한 뒤 `verify_postclose_chain_pending_done_failed`로 terminal blocked했다. 원본 verifier는 `tmp/postclose_monitor_20260907/verifier_first_fail_214445.json`, 후속 산출물 원본/hash는 `pre_recovery_generation/manifest.json`에 보존했다.
- Entry source-only weak-contract workorder5개의 `mapped_family/threshold_family`가 퇴역 LDM을 가리켜 mixed-report filter가 제거했다. Producer를 기존 `entry_submit_drought_attribution`으로 결속하고 파일 안내도 현행 `scalping/main_lifecycle_paired.py`로 수정했다. 퇴역 필터와 실주문 권한은 유지한다.
- Workorder producer는 `source_quality_blocked`를 필수 root-cause followup으로 세지만 verifier는 누락했다. 같은 상태를 필수 검사에 추가했다. 불완전한 followup은 계속 FAIL이다.
- 관련2개 test file **330 PASS**, compile/diff check PASS. 필터 통과 후 필수6개 ID 보존과 source-quality-blocked의 완전/불완전 계약 반례를 확인했다. 이 변경의 review finding0.
- 21:51 workorder 최소 재생성 후 current view16개/필수 Entry6개 보존, root-cause contract14/14 PASS. generation ID는 source 기반이라 같을 수 있으므로 실제 변경은 원본/신규 artifact byte hash와 코드 diff로 별도 대사한다.
- Samsung/저가주 보고서가 소비한 audit hash가 후속 audit 재생성으로 stale해졌다. 두 producer와 후보만 기존 CLI로 재생성했다. Samsung 계약 PASS, 저가주 candidate valid, policy mutations0, runtime_effect=false. live env·매매 process 변경 없음.
- 아직 미복구 smoothing: force-exit1행의 phase/terminal reason 필드 결손; cumulative journal335행의 scalar phase 계수와 compact tail50행을 비교한 계약 불일치. 병행 daily report 수정과 중복하지 않도록 해당 파일은 변경하지 않았다. 수정 완료·review·재생성 뒤 verifier/controller를 다시 닫아야 한다.
- Main AI cycle은 source-only blocked/deferred, 준비6단계 exit0이며 Provider 호출false. Invalid historical materialized binding, observer timestamp exclusion 증거와 lifecycle receipt/custody gap은 별도 source-only workorder로 남아 있다. 이를 운영 DONE이나 경제성 acceptance로 바꾸지 않는다.

- 추가 리뷰: owner 매핑 변경을 이전 source generation과 구분하도록 producer contract를 `code_improvement_workorder_producer_v4`로 올렸다. 재검증330 PASS 후 21:58:50 신규 generation `2026-09-07-e930940341be` / byte SHA256 `e92eeb89f9c072a0c74a6900572c0d65d8292c8d29242e7087fc625a36555ef2`, 필수 ID 누락0·followup14/14 PASS. 근거 `workorder_recovery_gate.json`.
- 21:55 finalization은 predecessor terminal failure로 cleanup을 건너뛰고 bounded detector를 실행했다. 21:55:03 detector artifact 존재; finalization은 FAIL이며 최신 성공으로 복구해야 한다.
