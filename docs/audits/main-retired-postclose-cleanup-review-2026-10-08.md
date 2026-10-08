# Main 장후 퇴역 잔재 정리 검토 — 2026-10-08

사용자가 16:48 점검에서 발견한 두 잔재의 정리·배포·재기동을 승인했다. 점검 시 실제 Main은 `main-bottleneck-compact-20261008-v9`, PID 346886, ubuntu 실행이었다. 과거 인용의 v3/PID 241227은 현재 상태로 사용하지 않았다.

## 변경과 반복 검토

1. 구 EOD systemd 설치 스크립트는 삭제된 전용 final-refresh wrapper와 미설치 timer만 대상으로 했다. 생존 Main을 설치하는 기능이 없어 스크립트를 삭제했다. 생존 EOD barrier와 Main cron 설치 경로는 유지한다.
2. 저가 2단계 튜닝/후보 추천 설정·status writer 인자와 producer flags·DONE 로그를 제거했다. downstream의 해당 status key 의존은 없었다. 실제 writer를 running/succeeded/failed로 실행해 기존 퇴역 flags 제거와 생존 값의 위치를 검증한다. 과거 sealed artifact는 변경하지 않는다.
3. cron 설치 템플릿은 이미 퇴역 env를 쓰지 않았다. 격리한 재설치·멱등성 테스트로 이전 설정 제거, EOD/최종화 등 다른 예약 보존과 20:10 provider/bot stop 경계를 확인했다. 운영 cron은 전체 재설치 없이 해당 변수 하나만 제거한다.
4. 기존 wrapper 회귀에서 삭제된 서비스·episode 생산자를 요구하는 잔재 8개와 변경한 status 인자 1개를 확인했다(초기 9 fail/22 pass). 이를 생존 Main의 EOD 선행·publisher/bootstrap 순서와 recovery 원천/해시 계약으로 이관했다. 퇴역 모듈을 recovery 증빙에 끼워 넣는 경우 거부하는 회귀를 보존했다.
5. 운영 호출 안내에서 삭제된 21:15 서비스와 구 wrapper의 실행 안내를 제거했다. 과거 조사 기록은 현행 설치 안내로 사용하지 않는다. 오늘 기존 Main stable owner에 같은 승인·수용을 인계하고 원 AUTO 봉인 영역과 다른 작업의 dirty 문서는 보존한다.

기계/보조 정책, 5개 fixed watch, SOR 통합 애프터장, custody/manual veto, broker/account/order/수량/5초 deadline은 변경하지 않는다. `episode` 이름의 Main 분석 기능도 보존한다. API 요청/parser 변경이나 AI 연구 호출, EOD/장후 수동 재생성은 이 정리에 필요하지 않다.

## 검증 및 배포

증거 디렉터리: [retired_postclose_cleanup/2026-10-08](../../data/report/retired_postclose_cleanup/2026-10-08).

첫 보완 회귀 78개 후 최종 wrapper/EOD/퇴역·정책 보존 handoff/최종화 세대/cron 감시 회귀 224개가 통과했다. Shell syntax·compile·diff·실제 링크·print-only parser도 통과했다(22개 task, 기존 Main owner 1개). 기존 YYYY-MM-DD 경로 템플릿은 실파일 검사에서 구분했다. 재리뷰의 범위 내 미해결 결함은 0개다. 실행 중 장후 worker가 없는 상태에서 새 immutable release를 생성하고 원 정책을 보존한 native handoff로 배포·재기동한다. 실제 PID와 bootstrap·기계/보조 소비·strict binding은 배포 후 검증한다.

배포 상태는 최종 영수증으로 보완한다. 20:10 자연 장후 완료와 다음 예약기동은 예정 시각의 별도 수용이며 이번 구현·기동 검증으로 대체하지 않는다. 과거 `recovered_late` 경고는 실제 지연 이력으로 보존하고 `strict_checklist_generation_stale` 재발 여부는 별도 검사한다.

## 최종 배포·실제 소비 확인

18:48 KST에 `main-retired-postclose-cleanup-20261008-v1` / `0c1f68968906395f12c121862876704afadc1e83`로 배포하고 구 PID 346886의 graceful 종료 후 새 Main PID **381039**, ubuntu 실행·실제 cwd·selector 소비를 확인했다. 웹도 동일 release로 재기동하여 HTTP 200을 확인했다. Immutable release 회귀 224개가 통과했고 선행 compact/latency의 핵심 source/test 32개는 원 hash와 일치한다. 다른 작업의 미커밋 변경은 이번 commit에 포함하지 않았다.

Bootstrap·정책 보존 handoff PASS, 기계/보조의 실제 PID 소비를 확인했다. 기계 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`, 보조 overlay `b8e97475121038c21d1608f99530f1c740f696f4ba084d0cfd2f9b48c4961626`와 포인터 원 바이트가 유지됐다. 전체 128경로와 compact wire 4경로는 그대로다. 퇴역 final-refresh service/timer는 not-found/inactive이며 설치 cron은 검토한 퇴역 변수 한 개만 제거했다.

Read-only cron 검증에서 `strict_checklist_generation_stale`·`finalization_chain_generation_changed`는 없었다. 과거 cleanup/finalization의 06:50 이후 복구 완료 경고는 남겨 실제 지연 이력을 숨기지 않았다. 전환 시각 18:48:00에 구 프로세스의 HPSP·삼성 판정 2건이 `auxiliary_pid_release_mismatch`로 fail closed된 로그가 있다. selector 변경 후 구 PID 종료 전의 기록이며, 새 PID의 후속 기계/보조 소비는 각각 검증했다. 이를 전체 오류 0으로 표시하지 않는다.

현재 정리·배포·재기동은 완료다. 20:10 자연 장후와 다음 예약기동은 아직 미관측이며 해당 예정 시각에 별도 확인한다. [최종 영수증](../../data/report/retired_postclose_cleanup/2026-10-08/deployment-final.json)에 실제 PID·정책 해시·검증·경고를 기록했다. 이 작업에서는 provider/broker 호출, EOD·장후 수동 재실행, 외부 동기화를 수행하지 않았다.
