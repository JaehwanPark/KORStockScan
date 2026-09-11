# 자동 hard-stop 수동관리 이관 감시 판정 수정

사용자는 자동 hard-stop 수동관리 전환으로 자동 청산 감시에서 제외된 경우 이를 오류로 인식하지 않도록 명시 지시했다. 기존 7/14 운영 정책과 일치하며, 이번 변경은 감시 분류만 소유한다.

`src/engine/error_detectors/process_health.py`에서 현재 파일 원천이 정확히 `auto_hard_stop_handoff`이고 현재 main exclusion도 유효한 보유를 `expected_hard_stop_manual_handoff`로 분리했다. `expected_hard_stop_handoffs`와 건수를 남기고 전체 최근 제외 보유 분모도 유지한다. 해당 원천이 없거나 다른 자동 제외·유사 토큰이면 기존 오류 판정이다. 다른 process/thread 실패를 PASS로 덮지 않는다. 이관 목록을 지우거나 주문·정책·청산 동작을 변경하지 않는다.

관련 process-health/manual-control 테스트114개 PASS, Python compile·git diff --check PASS. 혼합 정상 이관/미귀속 제외, 원천 부재 및 유사 사유 반례를 검증했다. 현재 원천으로 직접 read-only check한 결과 process-health PASS, ICTK456010/record42892 expected handoff1/active error0, source event11:16:34.471060. 증거 `tmp/hard-stop-handoff-detector-review-20260911.json`. 과거 FAIL artifact를 수정하지 않았다.

설치된5분 주기 `deploy/run_error_detection.sh full`은 workspace의 코드를 읽는다. 다음 예약 감시부터 자동 소비하며 봇 재기동은 필요 없다. 선택된 고정 main/장후 release e2388dbb의 코드는 변경하지 않았으므로 해당 고정 release 내부에서 별도로 실행하는 detector에는 아직 이 변경이 포함되지 않는다. 다음 배포에 동반해야 하는 경계는 기존 RuntimeEnvIntradayObserve0911에 기록한다. 현행 cron의 자연 산출물 확인과 전체 시스템의 다른 장애 유무는 직접 process-health 검증과 구분한다.

검토 범위 미해결 코드 finding0. 미래 확인 때문에 정상 이관을 계속 인수 미확인 오류로 취급하지 않는다. 문서 및 체크리스트 print-only parser 검증 완료; 외부 sync 미실행.

## 12시 모니터링 중 실제 main 소비 보완

메인 내부 detector가 같은 canonical 보고서를 쓰므로 외부5분 소비만으로 반영 완료를 주장할 수 없었다. 후속 모니터링에서 기존 필요시 재기동 승인과 사용자 분류 변경 지시를 적용하여 c15a02cb/PID231446으로 최소 detector2파일 배포·우아한 재기동을 완료했다. release114 tests/runtime verify PASS, 전후 잔고 동일/미체결0. [모니터링 근거](2026-09-11-intraday-monitoring-1200.md). 위 미배포 경계는 이 시점에 해소됐고 이후 자연 canonical 결과를 확인한다.
