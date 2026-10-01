# 10/2 daemon 동일 사고 반복 ERROR 수리

## 직접 원인과 구현

07:56~07:59 bot_main의 같은 `postclose_finalization` 실패가 매분 기록됐다. 기존 ADMIN publish에는 조건이 있었지만 ERROR 로그는 조건 밖이었다. standalone daemon에도 같은 무조건 로그가 있었다.

기존 `error_detector.py`의 순수 전이 함수를 두 daemon이 공유한다. detector/심각도/요약/검사일과 cron 원천/선행 실패의 identity가 같은 동안 출력만 억제한다. 전체 검사·health 저장·bot heartbeat는 계속된다. WARNING은 recovery가 아니며 날짜 전환 PASS는 과거 실패가 복구됐다고 표시하지 않는다. handler가 실패하면 state를 commit하지 않아 다음 관측에서 재시도한다. state는 process 한정이며 재기동 후 첫 관측은 다시 기록한다.

## 검증·적용 경계

수정→리뷰→보완→재리뷰 뒤 기존 bot import/scheduler·detector·log scanner·ADMIN notifier 회귀를 수행한다. 두 실제 daemon loop를 fake engine/handler로 네 주기 실행해 health FAIL 네 건·로그 한 건을 확인한다. 새 원천·새 선행 실패·severity·warning·PASS·재발·날짜 전환·handler 실패도 검사한다. broker/Provider/Telegram 외부 호출 및 장후 계산은 실행하지 않는다.

현재 실행 PID의 코드는 배포·정식 기동 인계 전까지 기존 코드다. 원 10/1 finalization FAIL은 그대로 남기며 준비·PID 소비를 FAIL 복구로 표시하지 않는다. [현재 수용 owner](../checklists/2026-10-02-stage2-todo-checklist.md)는 `ErrorDetectorDaemonLogDedup1002`다.

최종 표적 회귀 **76 PASS / 2.55초**, 4개 Python compile·diff·print-only parser 통과. 매매/정책/주문/Provider 코드는 변경하지 않았다. 이전 목록 현행화 문서 7개도 함께 보존했다. 배포/PID 자연 결과는 후속 receipt로 별도 대사한다.
