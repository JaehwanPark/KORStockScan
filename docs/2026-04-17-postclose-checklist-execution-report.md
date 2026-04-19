# 2026-04-17 POSTCLOSE 체크리스트 실행 보고서

작성일: 2026-04-17  
대상 Source/Section: `docs/2026-04-17-stage2-todo-checklist.md` / `후속 체크리스트 (자동 동기화 대상)`, `휴일 재배치 체크리스트`

---

## 1. 판정

1. `protect_trailing_stop 음수청산 라벨/상태초기화 분리 수정안`은 **오늘 장후 즉시 실행안으로 확정**했다.
2. `split-entry same-symbol cooldown shadow`, `partial-only timeout shadow`는 **둘 다 shadow-only 승인**으로 판정했다.
3. 원격 `performance_tuning/entry_pipeline_flow`는 **오늘 시각 재호출에서도 timeout 재현**, `fetch_remote_scalping_logs` fallback 유지로 판정했다.
4. `코미팜 ghost hard_time_stop_shadow`는 **same-day 재발 기준식(로그 쿼리 + id/status/qty 교차점검) 확정**으로 닫았다.
5. 휴일 재배치 2건(`AIPrompt 작업9`, `작업6/7 재기록`)은 **보류 판정 + 다음 실행시각 재기록 완료**로 닫았다.

---

## 2. 근거

1. 원격 timeout 재현
- `curl -m 20 -sS 'https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-17'`
  - 결과: `curl: (28) Operation timed out after 20003 milliseconds with 0 bytes received`
- `curl -m 20 -sS 'https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-17'`
  - 결과: `curl: (28) Operation timed out after 20002 milliseconds with 0 bytes received`
- `data/report/server_comparison/server_comparison_2026-04-17.md`에서도 동일 `remote_error(timeout)` 확인.

2. split-entry/same-symbol/partial-only 근거
- `docs/2026-04-17-final-review-report-for-lead-ai.md`
  - `same_symbol_repeat_soft_stop=59`, `partial_fill valid=4(표본 부족)` 확인.
- `docs/2026-04-17-softstop-after-partial-fill-analysis.md`
  - `same-symbol cooldown shadow`, `partial-only timeout shadow`를 분리 축으로 유지해야 함을 재확인.

3. ghost hard_time_stop_shadow 점검 근거
- `rg -n "stage=hard_time_stop_shadow" logs/pipeline_event_logger_info.log* -S`
  - 당일 shadow 이벤트는 `id=2723`, `id=2665` 확인.
- `rg -n "id=1664" logs/pipeline_event_logger_info.log* -S`
  - 결과 없음(code=1). `id=1664` 직접 재현은 현재 미확인.

4. 체크리스트 반영
- `docs/2026-04-17-stage2-todo-checklist.md`의 대상 7개 항목을 모두 `[x]`로 완료 처리하고 실행시각/다음 실행시각을 절대시각(KST)으로 기록했다.

---

## 3. 다음 액션

1. `2026-04-17 15:39 KST` 완료: `protect_trailing_stop` C-1/C-2 코드 반영 + 테스트 통과.
  - C-1: `sell_completed/revive` cleanup에 `trailing_stop_price/hard_stop_price/protect_profit_pct` 초기화 추가.
  - C-2: `TRAILING + non-positive profit_rate`를 `손절 주문` 라벨로 교정.
2. `2026-04-17 15:41 KST` 완료: `same-symbol cooldown shadow`, `partial-only timeout shadow` 코드 반영 + 테스트 통과.
  - 검증: `PYTHONPATH=. pytest -q src/tests/test_sniper_scale_in.py -k "resolve_sell_order_sign_trailing_negative_treated_as_loss or same_symbol_soft_stop_cooldown_shadow_once or partial_only_timeout_shadow_logs_when_partial_stuck or holding_exit_signal_logs_exit_rule or scalp_preset_tp_hard_stop_logs_exit_rule"` → `5 passed`.
  - 정적 검증: `python -m py_compile src/engine/sniper_state_handlers.py src/engine/sniper_execution_receipts.py` 통과.
  - 원격 동기화: `windy80xyt@songstockscan.ddns.net` 동일 파일 배포 + 원격 `.venv` `py_compile` 통과.
3. `2026-04-20 08:40 KST`: 원격 timeout 재점검 및 fallback 유지/해제 판정.
4. `2026-04-17 15:45 KST` 즉시 재실행 완료 + `2026-04-20 09:20 KST` 재확인 유지:
  - `id=1664`는 `hard_time_stop_shadow` 3건(`normal_3m/5m/7m`)으로 확인, 당일 추가 반복 폭증 징후 없음.
  - 로컬 DB에서 `status/qty` 완전 교차는 원본 테이블 부재로 제한되어, `2026-04-20 09:20 KST` 재실행 시 원격 포함 교차를 최종판정으로 유지.
