# 10/2 daemon 동일 사고 반복 ERROR 수리

## 직접 원인과 구현

07:56~07:59 bot_main의 같은 `postclose_finalization` 실패가 매분 기록됐다. 기존 ADMIN publish에는 조건이 있었지만 ERROR 로그는 조건 밖이었다. standalone daemon에도 같은 무조건 로그가 있었다.

기존 `error_detector.py`의 순수 전이 함수를 두 daemon이 공유한다. detector/심각도/요약/검사일과 cron 원천/선행 실패의 identity가 같은 동안 출력만 억제한다. 전체 검사·health 저장·bot heartbeat는 계속된다. WARNING은 recovery가 아니며 날짜 전환 PASS는 과거 실패가 복구됐다고 표시하지 않는다. handler가 실패하면 state를 commit하지 않아 다음 관측에서 재시도한다. state는 process 한정이며 재기동 후 첫 관측은 다시 기록한다.

## 검증·적용 경계

수정→리뷰→보완→재리뷰 뒤 기존 bot import/scheduler·detector·log scanner·ADMIN notifier 회귀를 수행한다. 두 실제 daemon loop를 fake engine/handler로 네 주기 실행해 health FAIL 네 건·로그 한 건을 확인한다. 새 원천·새 선행 실패·severity·warning·PASS·재발·날짜 전환·handler 실패도 검사한다. broker/Provider/Telegram 외부 호출 및 장후 계산은 실행하지 않는다.

현재 실행 PID의 코드는 배포·정식 기동 인계 전까지 기존 코드다. 원 10/1 finalization FAIL은 그대로 남기며 준비·PID 소비를 FAIL 복구로 표시하지 않는다. [현재 수용 owner](../checklists/2026-10-02-stage2-todo-checklist.md)는 `ErrorDetectorDaemonLogDedup1002`다.

최종 표적 회귀 **76 PASS / 2.55초**, 4개 Python compile·diff·print-only parser 통과. 매매/정책/주문/Provider 코드는 변경하지 않았다. 이전 목록 현행화 문서 7개도 함께 보존했다. 배포/PID 자연 결과는 후속 receipt로 별도 대사한다.

## 불변 릴리스 검증과 당일 적용 차단

- 커밋 `24bf9ab6804a4b12095b33c5066e87fee6e685df`, 불변 root `daemon-log-dedup-20261002-24bf9ab6`. root 안의 표적 회귀 **76 PASS / 4.64초**, runtime source clean. 기존 `9dcbd482`와 실제 src 변경은 bot_main/error_detector 두 파일과 그 표적 테스트뿐이다.
- release-set 검증 후 정식 selector 전환을 시도했다. `next_preopen_readiness --prepare --source-date 2026-09-30 --target-date 2026-10-02`는 당일 PREOPEN 이후 새 준비를 금지하는 `preopen_target_not_next_operating_day`로 거부됐다. PREOPEN 재생·정책 재발행·restart request는 실행하지 않았다. 단순히 예전 PREOPEN 영수증의 commit을 새 commit으로 바꾸지 않는다.
- 현재 Main을 중단하기 전에 동일 release-set/selection lock 아래 원 selector `9dcbd482`를 복원했다. Main PID `2748464`·today env/manifest·정식 PREOPEN status·prepared index가 그대로임을 byte 대사했고, 08:12 bootstrap PID 검증 PASS/findings0이다. 독립 owner pin·cron 예약도 유지한다.
- [적용 차단 영수증](../../data/runtime/startup_readiness/2026-10-02/daemon_log_dedup_transition/apply.blocked.json), [복구 대사](../../data/runtime/startup_readiness/2026-10-02/daemon_log_dedup_transition/rollback.readback.json). 코드 수정 완료와 현재 daemon 소비는 분리한다. 현재 PID는 원 코드이므로 동일 ERROR 반복 출력은 아직 해소되지 않았다.
- 다음 조치 owner는 `ErrorDetectorDaemonLogDedup1002`다. 기존 20:10 Main 정상 종료 후 검증된 root의 선택·새 적격 원천 장후/정식 다음 거래일 준비를 결속하고, 다음 Main PID에서 두 연속 관측의 health FAIL 유지·동일 ERROR 추가 없음으로 자연 수용한다. 그 전에 장중 코드 전용 인계를 만들려면 정확일자 정책·원 PREOPEN·old PID·새 코드 보존을 증명하는 정식 계약 보완이 필요하다. cutoff/commit 검증을 우회하지 않는다.
