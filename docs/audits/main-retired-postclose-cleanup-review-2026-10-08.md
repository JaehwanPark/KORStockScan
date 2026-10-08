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
