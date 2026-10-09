# 2026-10-07 EOD 제외 장후작업 사용자 중단

사용자가 오늘 EOD를 제외한 장후작업을 중지하고, 개선 완료 후 별도 지시로 재개하도록 요청했다. 기존 배포·재기동 승인은 이번 중단을 자동 해제하는 근거로 사용하지 않는다. 실행 owner는 오늘 체크리스트의 `DirectFamilySourceRepairMainMechanisticEntry`를 유지한다.

20:41:47 KST에 정확한 PID/start ticks/cwd/PGID를 확인한 뒤 장후 wrapper `1074504`, controller `1074507`, tuning `1074508` 그룹에 SIGTERM을 전달했다. 세 그룹의 살아 있는 자식은 0이며 EOD `1071853`의 PID/start ticks는 중단 전후 동일하다. Main과 독립 episode 프로세스는 종료·재기동하지 않았다.

20:44:43 KST부터 다음 cron 5개를 `OPERATOR_POSTCLOSE_HOLD_20261007` 주석으로 임시 보류했다. 다른 cron 행은 그대로 보존했고 `crontab -n` 문법 검증을 통과했다.

- `THRESHOLD_CYCLE_POSTCLOSE`
- `POSTCLOSE_DONE_CONTROLLER`
- `TUNING_MONITORING_POSTCLOSE`
- `POSTCLOSE_FINALIZATION_0500` — 다음 날 실행하는 오늘 원천의 최종화 포함
- `DASHBOARD_DB_ARCHIVE_2050`

21:15 예약의 `korstockscan-machine-microstructure-final-refresh.timer`는 stop/disable했고 해당 서비스는 inactive/MainPID=0이다. 이전 타이머 상태는 enabled/active였다. EOD·PREOPEN·Main start·일반 error detection 예약은 enabled로 유지한다. 보류한 장후 예약은 사용자 재개 지시 전에는 이후 날짜에도 자동 실행하지 않는다.

중단된 실행의 실패·부분 진행 상태를 DONE/PASS로 바꾸지 않았다. 기존 원천, 요청/응답 원장, 정책, 잠금 파일은 보존한다. 이번 중단은 다음 영업일의 새 정책·PREOPEN 준비 완료를 의미하지 않는다. 원장 저장 구조 개선은 별도 작업이며 이번 중단 요청에서 구현하지 않는다.

재개 시에는 아래 영수증의 5개 원래 cron 행만 현행 crontab과 대조하여 복원하고, 현재 타이머/서비스가 중복 실행 중이 아닌지 확인한 뒤 기존 타이머를 enable/start한다. 전체 crontab 백업을 통째로 덮어쓰거나 EOD를 재실행하지 않는다. 오늘 원천의 재개는 개선된 reviewed release와 정확한 source date로 한 체인만 실행하며, 기존 요청/실제 응답·불확실 예약을 먼저 대사한다.

근거: [프로세스 중단](../../data/report/postclose_operator_stop/2026-10-07/operator-stop-processes.json), [예약 보류와 원래 행](../../data/report/postclose_operator_stop/2026-10-07/operator-stop-schedules.json), [예약·타이머 검증](../../data/report/postclose_operator_stop/2026-10-07/operator-stop-validation.json). 전체 crontab 백업은 같은 디렉터리에 mode 0600으로 보존했다.

검증은 정확한 프로세스 소멸, 보호 PID 유지, cron 문법·대조, native schedule contract의 disabled/enabled 구분, 타이머 inactive/disabled에 한정한다. 거래 코드·provider 호출·장후 재생성·장후 모니터링은 실행하지 않는다.
