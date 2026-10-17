# 장후 잔여 FAIL 재점검·종결 — 2026-10-16

05:08:30 KST, 원천일10/15의 정식 오류 보고서를 현재 선택본 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`에서 다시 생성했다. 필수 탐지기7/7 초기화, 초기화 실패0, FAIL0, 운영 mutation0이며 전체 판정은 `warning`이다. 원 실패를 삭제하거나 부분관측을 PASS로 바꾸지 않았다. [검증 결과](../../tmp/residual-fail-repair-20261016/result.json), [정식 보고서](../../data/report/error_detection/error_detection_2026-10-15.json).

## 원인과 실제 처리

- 전일 제출 observer는 원천 부재와 검증 시간 초과 때문에 부분관측으로 남았다. 보존된 selector, 원 observer의 run/date/code seal, 성공한10/15 Main terminal을 기존 closed-day reader가 대조해 `historical_generation_verified / historical_observation_only`로 수용했다. 원천일은10/15, 점검 시각은10/16으로 구분한다. `current_generation_verified=false`, `current_observation_verified=false`, `full_coverage_proven=false`를 유지한다.
- 시간 초과를 원 고정 시각의 격리 진단으로 재현했다.25초 계산 예산에서7,394,107,688 bytes 원천의 cold SHA 검증이 지배 비용이었다. 완료된 파일 해시 checkpoint를 보존한 후 같은 계산 예산으로 이어 검증하니 entry execution9.38초, machine5.24초, 합계14.62초에 종료됐다. 기존40초 observer 예산의 마지막15초 publication 여유를 늘리지 않았다. [재현](../../tmp/residual-fail-repair-20261016/entry-semantics-profile.json), [checkpoint 재개](../../tmp/residual-fail-repair-20261016/checkpoint-resume.json).
- 위 재생은 과거 고정 시각의 계산 완료 증거다. 과거 bootstrap·선택 코드 세대 불일치와 원천 결손은 그대로 남으며 semantic PASS, 정규 cron 성공 또는 현재 거래 관측을 증명하지 않는다. 과거 full observer exit75와 source-only partial 원본도 유지했다. 미래 날짜의 cold cache 성능이나 자연 수용까지 완료했다고 주장하지 않는다.
- 이전 정식 오류 보고서와 보호 대상 원본을 보존한 뒤 기존 오류 탐지 잠금 아래 native `error_detector --mode full --postclose-source-date 2026-10-15`로 정식 보고서를 게시했다. wrapper와 같은 `validate_report_contract`의 동일 run/date 검증 결과는 결함0이다. 수동 알림 전송은 수행하지 않았다.

## 검증과 남은 경계

Closed-day 판정의 정상 사례와 archive/seal/code/terminal/동일 날짜/미완료 실행 거부 회귀7개가 PASS다. 원 observer·장후 controller/strict·선택본·current 정책·수동 제외·준비 receipt·동결 체크리스트 등15개 보호 비교는 전부 불변이다. 코드와 release 선택을 변경하지 않았고 매매 프로세스 재기동·provider 호출·주문을 실행하지 않았다.

별도10/16 현재 날짜의 읽기 전용 full 검사도7/7 PASS, FAIL0, mutation0이다. 이 검사에서 PREOPEN과 제출 observer는 `not_yet_due`이며 새 거래일의 자연 관측 성공으로 해석하지 않는다. [현재 날짜 검사](../../tmp/residual-fail-repair-20261016/current-day-detector.json). 문서 링크8개, 현재 체크리스트 OPEN ID11개의 유일성, print-only parser, diff 검증을 통과했다.

10/16 준비본은 현재 원천과 선택본의 `sealed_generation` 재검증 PASS다. 이는 전일 `current_full_contract` PASS의 seal을 재검증한 것으로 새 전체 검증이나 실제 PID 소비 영수증이 아니다. 장후 controller DONE과 strict 원본도 보존한다. [준비본 재검증](../../tmp/residual-fail-repair-20261016/prepared-seal.json), [이전 복구 리뷰](main-postclose-origin-parent-custody-repair-review-2026-10-15.md).

남은 경고는 EOD 미수신4종목, 역사적 holding sentinel 오류·로그, 제출 관측/원천 결손이다. 비용 후 경제성 source gap 두 family와 compact 표본 부족도 종료시키지 않는다. 현재 [10/16 체크리스트](../checklists/2026-10-16-stage2-todo-checklist.md)의 `NonfixedDispatchReadinessReview1012`, `DirectFamilyPreopenPolicyHandoff`, 기존 family source-repair owner와 Acceptance를 유지한다. 체크리스트의 frozen bytes와 OPEN 소유자는 변경하지 않았다.

이번 점검 시각에는 설치된05:35 finalization,07:35 PREOPEN,07:55 Main 기동이 아직 예정 전이다. 정기 실행은 자체 exact-date terminal과 실제 PID 영수증으로 별도 확인해야 하며, 이번 결과로 정상 기동 완료나 실제 거래·손익을 보증하지 않는다. 외부 동기화는 실행하지 않고 문서 print-only parser와 링크/diff 검증만 수행한다.
