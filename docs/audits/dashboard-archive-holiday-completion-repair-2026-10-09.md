# Dashboard archive 휴장일·완료 감시 결함 수리

점검일: 2026-10-09 KST. 배포 후속 owner: `MainMarketSourceConsolidation1009`.

21:05 `dashboard_db_archive: no completion marker after window end`는 16:55 전환 경고와 다른 실제 자동화 결함이다. 20:50 시작한 PID 236231은 휴장 EOD의 `skipped_non_trading_day`를 완료로 인정하지 않아 90분 대기 중이었다. 압축 모듈은 아직 호출되지 않았다. 감시기는 휴장일 제외가 없고 21:00 완료를 요구했다. 영업일에도 기본 EOD 대기 90분과 감시 창 10분이 불일치했다.

## 변경과 검증

- Archive wrapper가 기존 KRX source calendar helper를 사용해 휴장일에 EOD 대기·압축 전 `[SKIP] reason=non_trading_source_date no_archive_mutation=true`로 종료한다. 휴장 SKIP을 실제 압축 DONE으로 기록하지 않는다.
- Cron detector의 archive는 영업일에만 완료를 요구한다. 20:50 시작+기존 기본 EOD 대기 90분+압축 여유 10분으로 완료 창은 22:30이다. 명시 FAIL은 마감 전에도 실패이며 마감 후 미완료·이전 날짜 DONE은 실패다.
- 기존 감시 예약을 보존하고 22:35 `ERROR_DETECTION_FULL_ARCHIVE_TERMINAL`을 추가해 22:30 마감 후 미완료를 당일 검사한다. 재설치 멱등성과 다른 예약/최종화 보존을 검증했다.
- 관련 wrapper·detector·router 테스트는 작업본과 불변 릴리스 각각 **158 passed**. 공휴일·주말 SKIP, 영업일 EOD 결손 실패, EOD 대기 중 조기 실패 방지, 마감 후 결손 실패, 즉시 FAIL·정상 DONE·과거 DONE 거절을 확인했다. `bash -n`, 변경 Python compile 및 diff 검사를 수행했다.

## 배포와 운영 확인

최종 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/main-archive-calendar-20261009-v1`.
Commit: `9773aefb1fb8e5ea6d09113c40b9beccd4c4e8e8`.
부모: `main-market-source-20261009-v1` / `9d6cff39d0c9455386647612c18055d6825944d6`.

부모에 이번 runtime/test 6파일만 통합했다. 다른 미커밋 작업은 보존했다. release 선택과 10/12 PREOPEN 재준비를 배포 잠금 아래 수행했다. 기계·보조 정책 candidate/current는 원 byte 그대로이고 bundle `ac267bfb42f355a51dc3be080495336a2456c39668160d888e53b2b12ad96889`도 같다. 정책 발행·AI/Provider 호출·Main 재기동·거래 실행은 없다.

21:14:20 기존 archive 대기 PID 236231의 cwd·명령·start ticks `4406741`과 휴장 EOD를 대조한 뒤 해당 프로세스와 sleep 자식만 SIGTERM 종료했다. 새 선택 릴리스의 exact-date archive 재실행은 SKIP을 출력하고 압축 없이 종료했다. EOD를 성공으로 조작하거나 과거 로그를 삭제하지 않았다. 기존 필수 예약은 보존하고 22:35 감시만 추가했다.

10/12 source 10/8 PREOPEN 전체 검증은 PASS다. 실제 10/12 Main PID 소비는 아직 false다. 영업일의 22:35 자연 검사와 G5 성능 수용을 현재 완료로 주장하지 않는다. 최종 감시·문서 검사 결과는 아래 영수증에 기록한다.

**21:15:07 자연 정기 감시의 7개 detector 모두 PASS**를 확인했다. `dashboard_db_archive_status=skip_non_trading_day`이며 해당 실패가 해소됐다. 별도 수동 전체 감시·알림 호출로 이 결과를 만들지 않았다. release-set·필수 cron 경로와 기존 최종화 세대도 재검증한다.

## 근거

- [배포 구성](../../data/report/dashboard_archive_holiday_fix/2026-10-09/build.json)
- [불변 릴리스 회귀](../../data/report/dashboard_archive_holiday_fix/2026-10-09/release-tests.log)
- [기존 대기 PID 종료 근거](../../data/report/dashboard_archive_holiday_fix/2026-10-09/old-waiter-stop.json)
- [PREOPEN 전체 검증](../../data/report/dashboard_archive_holiday_fix/2026-10-09/preopen-verify.json)
- [정책 및 기존 장후 완료 검사](../../data/report/dashboard_archive_holiday_fix/2026-10-09/preselection-contract.json)
- [최종 확인](../../data/report/dashboard_archive_holiday_fix/2026-10-09/final-check.json)

실제 영업일 DB 압축과 장후 연구 전체는 이번 휴장 결함 점검에서 다시 실행하지 않았다. 문서 parser는 print-only로 실행하며 외부 Project/Calendar 동기화는 수행하지 않는다.
