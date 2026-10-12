# 배포 전환과 오류감시의 동시 실행 결함 보완

2026-10-12 14:15 알림의 `postclose_handoff_generation_invalid`와 `strict_checklist_generation_stale`는 감시기가 배포 중간 세대를 읽어 발생했다. 원래 최종화·PREOPEN 정책을 다시 생성할 결함으로 판단하지 않는다.

## 확인한 원인

- 감시 wrapper는 14:15:01에 `machine-aux-delivery-20261012-v2`에서 시작했다.
- 배포는 14:15:02.099535에 새 릴리스를 선택하고 14:15:02.117699에 공유 체크리스트를 발행했다.
- 14:15:07 감시 당시 새 PID의 소비 영수증이 없었다. 역사 체크리스트 검증은 `intraday_observer_consumed_historical_handoff_required`로 거절했다.
- 새 PID 소비는 14:15:25.533813, 배포 완료는 14:15:27.690791이다. 사후 native 최종화 검증은 이슈 없이 통과했다.
- 당시 전체 감시 원천: [고정 원천](../../tmp/route-coverage-repair-20261012/alert-1415-exact-source.json). 전환 원천: `data/runtime/release_transitions/2026-10-12/51c293732a6a2750de87686440f01ac929fbdf92/status.json`.

## 보완 및 리뷰

배포 자동화가 기존 `tmp/run_error_detection.lock`을 함께 사용한다. 실행 중인 감시의 보고서 발행·알림 완료를 최대 60초 기다린 뒤 preflight를 시작한다. 이 대기 중에는 기존 Main을 종료하거나 selector·체크리스트·startup hold를 변경하지 않는다. 새 PID 검증까지 잠금을 유지하며 성공·실패·예외 시 해제한다. 잠금 파일을 삭제하거나 기존 감시 프로세스를 종료하지 않는다.

예약 감시는 잠금 점유 시 다음 예약으로 넘긴다. 명시적 장후 감시 요청은 완료로 처리하지 않고 재시도 코드 75를 반환한다. 잠금 획득 직후 선택 릴리스를 재검증하여 실행이 지연된 구 릴리스 감시도 새 보고서를 발행하지 않는다. 선택 자체가 손상되면 오류로 남긴다. 최종화 해시·소비 영수증·PID·정책 검증과 과거 실패 기록은 유지한다.

구현 소유는 기존 `automation/ordered_intraday_deploy.py`, `infrastructure/runtime_release_router.py`, 오류감시 wrapper이다. 새 engine-root 모듈이나 거래 정책은 추가하지 않았다. 관련 운영 계약은 [릴리스 운영 문서](../runtime-release-routing.md#ordered-intraday-deployment)에 반영했다. 기존 checklist `OrderedIntradayDeploymentRepair1012`를 보완하며 다른 OPEN owner를 이동하지 않는다.

## 검증 및 완료 경계

- 배포 단계별 실패, 실제 flock 경합과 해제, 감시 종료 후 배포 진입, timeout 시 사전 변경 없음, wrapper 예약/명시 호출 반환값, 구 reader/손상 selector 차단을 검증했다.
- 관련 배포·라우터·장중 인계·최종화·cron·artifact·wrapper 회귀 611건 통과. Python compile, `bash -n`, `git diff --check`와 문서 print-only parser로 마감한다.
- 코드 리뷰에서 해결되지 않은 범위 내 결함은 없다. 실제 배포·새 PID·변경 없는 보호 파일·다음 자연 감시 결과는 [완료 증빙](../../tmp/deployment-detector-serialization-20261012/completion.json)으로 별도 대사한다.
- 거래 조건·5초 기한·수량·custody·퇴역 기능은 변경하지 않았다. 과거 cron 지연 복구 경고나 장후 경제성 OPEN 작업의 완료를 의미하지 않는다. 외부 문서 동기화·수동 알림·provider 호출·장후 재생성은 수행하지 않는다.
