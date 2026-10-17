# 05:45 장후 인계·장전 준비 세대 경보 복구 — 2026-10-16

대상 경보는 `postclose_handoff_generation_invalid`, `next_preopen_prepared_contract_invalid`다. 원천일10/15와 적용일10/16을 보존하고, 기존 `DirectFamilyPreopenPolicyHandoff`의 인계 범위에서 복구한다. 매매 기동·주문·정책 수치 변경 권한을 추가하지 않는다.

## 원인과 보존

05:35:02 정기 최종화가 summary·checklist를 갱신했고05:41:36 전체 strict PASS를 발행했다. 그러나 controller 완료 영수증 갱신 전 `summary_handoff_refresh_failed`로 종료됐다. 약600초 경과와 최신 controller attempt 부재는 wrapper의 시간 제한 중단과 일치한다. 원 controller와 준비본은 전일23:30/23:34 세대를 가리켜 새 summary·checklist 해시와 어긋났다. 탐지기가 올바르게 두 경고를 발행한 사례이며, 이전05:08 점검 결과로 새 실패를 덮지 않는다.

[경보·이전 controller/strict/summary/checklist/준비본·보호 정책 원본](../../tmp/finalization-alert-recovery-20261016-0620/before-manifest.json)을 보존했다. 원 연구 단계·원 정책과 실제 PID 영수증을 새 실행으로 재라벨링하지 않는다.

## 복구 실행

관련 finalization/controller 회귀35개 PASS 후 선택본 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`에서 기존 `run_postclose_finalization.sh 2026-10-15 --recover-closed-target`를 실행했다. 선택본의 owned-log runner와 원 finalization 잠금을 사용한다. Router는 recovery flag를 전달하지 않아 실행 전 인자 오류로 거부했고, 이를 보존한 후 선택본 wrapper를 직접 호출했다. 거래용 env/lock/provider/threshold·cron과 코드·release 선택은 바꾸지 않았다. 수동 외부 메시지 전송은 하지 않는다.

06:28:16 전체 strict PASS,06:32:24 새 controller DONE/독립 producer 요구/blocked reason0을 확인했다. controller는 기존600초 제한 안에서 종료했다. 대형 원천을 반복 대조하는 비용은 [진행 계측](../../tmp/finalization-alert-recovery-20261016-0620/progress.jsonl)에 남기며, guard 생략이나 시간 제한 상향으로 처리하지 않았다.

## 최종 소비 수용

- controller 영수증 전체 재확인 PASS 뒤06:38:10 정리가 정상 종료됐다. storage 유지보수 실패0, purge0을 유지한다.
- 06:41:49 새 `prepared_verified`를 발행했다. 새 controller SHA `5dd00a1d307d37972878872fe835dff4d1c8ba28a0c487edd9f56a348f6eca96`에 결속됐고 원천10/15·적용10/16·선택 commit을 유지한다. native bootstrap 검증은 PASS/findings0, 실제 PID 소비는 false다.
- 06:41:57 정규 full detector는7/7 초기화·FAIL0·운영 mutation0이며, 실제 알림 consumer의 경보 분류도0건이다. handoff는 `done/findings=[]`, prepared는 `pass/findings=[]`다. 같은 run `cron-20261016T064149-2909271`의 보고서 SHA `e892f674475e7e28aec06d9acd8e8f1c7d46e0f34d00c2710f70712898beb8bd`를 finalization marker가 결속한다.
- 06:42:04 native `postclose_finalization`과 `postclose_final_detector`가 모두 DONE/exit0으로 종료했다. marker의 chain SHA는 `c7a65ab7e4bacba0916687319b0396eb0fcaa4932fdddd1ecc358c1ba53fea9f`, snapshot SHA는 `30e181aa7aa80526dbfac1bf7ea75b7d43c411a3d82fce4b993666f2e7c4fcea`다. 예정된06:50 종료 상한 전에 종결했다.
- 종료 후 별도 읽기 전용 full 검사에서도7/7 초기화·FAIL0·경보 consumer0건, cron finalization `pass`를 확인했다. 첫 독립 호출은 필수 prepared effective date를 빠뜨려 진단 실패를 냈으므로 원본을 별도 보존했다. source/effective date를 정규 wrapper와 동일하게 명시한 호출로 수정했으며 canonical 보고서나 원천을 변경해 통과시키지 않았다.

[최종 검증 결과](../../tmp/finalization-alert-recovery-20261016-0620/result.json), [정규 최종 detector 원본](../../tmp/finalization-alert-recovery-20261016-0620/native-final-detector-preserved.json), [종료 후 독립 검사](../../tmp/finalization-alert-recovery-20261016-0620/after-finalization-detector.json).

선택본·current 정책·10/16 후보·누적 등록·수동 제외5개 원본은 모두 불변이다. 원 연구6단계는 영수증/run까지 불변이고 summary handoff만 정규 재결속됐다. 코드와 선택 release는 변경하지 않았다. 체크리스트의 기존 OPEN ID11개와 단일 AUTO 블록을 보존했고 print-only parser·링크·diff 검증을 통과했다. 외부 동기화와 수동 Telegram 전송은 수행하지 않았다.

07:35 PREOPEN·07:55 기동의 print-only 라우팅은 같은 선택본을 가리키며 startup hold·restart flag는 없다. Main은 정지 상태이고 실제 기동·당일 정책 소비·자연 주문·비용 후 성과는 이번 수용 범위에 포함하지 않는다. EOD 미수신4종목과 과거 관측/holding 오류, 경제성 원천 결손은 경고·OPEN으로 보존한다. 반복 원천 I/O 비용과 향후 정규 성능 수용은 기존 구조 개선 owner의 경계이며, 이번 재실행 성공을 비용 문제의 코드 수리로 표현하지 않는다.
