# 2026-06-29 Intraday Scanner Watchlist 코드수정 목록

작성일: `2026-06-29 KST`
대상 목표: `08:00 이후 승격시점 대비 상승하였는데 BUY 하지 못한 종목` 20분 단위 진단 및 병목 해소
관련 커밋: `02128215 Fix scanner watchlist early eviction bottlenecks`

## 1. 판정

- 이번 세션의 핵심 병목은 BUY hardgate 자체보다 `SCANNER 승격 직후 WATCHING 레코드가 FIFO/dynamic watch cap 정리로 감시만료되는 경로`였다.
- NAVER는 포착 후 BUY 없이 `EXPIRED`로 종료되었고, 이는 실주문 제출 실패가 아니라 watchlist pool/FIFO 압력에 의한 관측 시간 부족으로 판정한다.
- 코드 변경은 real order authority, broker guard, hard/protect/emergency safety, BUY threshold를 우회하지 않는다.
- 런타임 값 변경이 빈번할 수 있는 지점은 hot runtime key로 분리했으며, 값 반영만 필요한 경우 봇 재기동 없이 적용 가능하도록 정리했다.

## 2. 코드수정 목록

### 2.1 `scalping_scanner_watch_eviction_v5` source-quality unresolved 보호

- 파일: `src/engine/kiwoom_sniper_v2.py`
- 내용:
  - 상승 중인 SCANNER 후보가 buy window 안에서 `insufficient_history` 또는 source-quality unresolved stale 경로에 걸릴 때, 표준 stale guard의 count/age 조건만으로 즉시 evict하지 않도록 변경했다.
  - `ws_gap_recovery_deferred_priority` 재점검 경로는 유지했다.
- 충돌 검토 포인트:
  - source-quality unresolved 보호가 hard safety, stale quote submit block, broker submit guard보다 앞서면 안 된다.
  - 이후 수정 시 이 보호를 BUY 승인 근거로 사용하지 말고, 관측 유지 근거로만 사용한다.

### 2.2 상승 후보 fresh terminal hardgate 재점검

- 파일: `src/engine/kiwoom_sniper_v2.py`
- 추가 hot runtime key:
  - `KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_ENABLED`
  - `KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_DELAY_SEC`
  - `KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_MAX_ATTEMPTS`
- 내용:
  - 상승 중인 SCANNER 후보가 buy window 안에서 `blocked_strength_momentum`, `blocked_liquidity` 같은 fresh terminal hardgate에 걸리면 첫 bounded attempt에서는 즉시 evict하지 않는다.
  - 재점검 예약 필드 `_scanner_rising_terminal_hardgate_recheck_after_epoch`를 부여하고 reason은 `terminal_hardgate_recheck_pending`으로 남긴다.
  - max attempts를 넘기면 기존 evict 경로로 닫는다.
- 연결 파일:
  - `src/engine/sniper_state_handlers.py`
  - `_scanner_active_rising_recheck_reason`에서 `terminal_hardgate_recheck_pending`을 노출한다.
  - `_scanner_active_full_eval_budget_source`에서 `not_applicable_terminal_hardgate`로 분류한다.
- 충돌 검토 포인트:
  - 이 재점검은 hardgate 해제가 아니라 fresh context 재평가 유예다.
  - liquidity/strength guard 자체를 완화하는 수정과 결합할 때는 같은 stage의 동시 canary가 되는지 별도 보고해야 한다.

### 2.3 런타임 attach/cap 관측 보강

- 파일: `src/engine/kiwoom_sniper_v2.py`
- 추가 관측 필드:
  - `scanner_attach_capacity_cap`
  - `scanner_attach_capacity_watching_count`
  - `scanner_attach_capacity_candidate_overflow`
- 내용:
  - `_scanner_runtime_target_event_fields`에 cap 상태를 포함했다.
  - `handle_scalping_scanner_promoted_target`가 capacity skip payload에 `scanner_attach_capacity_candidate_overflow=True`를 남긴다.
- 목적:
  - “타겟포착 직후 감시만료” 로그가 실제 cap/FIFO 압력인지, 다른 BUY blocker인지 구분한다.
- 충돌 검토 포인트:
  - 이 필드는 관측성 보강이며 runtime decision authority가 아니다.
  - 이후 report/parser에서 이 필드를 사용하더라도 source-quality contract 없이 EV/live approval 근거로 승격하면 안 된다.

### 2.4 FIFO 신규 승격 grace

- 파일: `src/engine/kiwoom_sniper_v2.py`
- 기본 상수:
  - `SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC = 60.0`
- 추가 hot runtime key:
  - `KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC`
- 내용:
  - `_scalping_fifo_overflow_candidates`에서 최근 승격된 SCANNER 후보를 grace 시간 동안 overflow ordering 뒤쪽으로 보낸다.
  - grace 안의 후보끼리는 더 오래된 후보부터 먼저 정리한다.
- 운영 메모:
  - 세션 중 operator runtime override에는 `KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC=180`을 반영했다.
  - 이 값은 hot runtime key라서 값 변경만으로는 봇 재기동이 필요하지 않다.
- 충돌 검토 포인트:
  - grace가 지나치게 길면 오래된 저품질 WATCHING이 pool을 붙잡을 수 있으므로, 다음 점검에서는 `scanner_attach_capacity_candidate_overflow`와 FIFO expiration 분포를 같이 본다.
  - grace는 관측 시간 보장이지 BUY threshold 완화가 아니다.

### 2.5 테스트 격리 및 회귀 테스트

- 파일: `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
- 내용:
  - `_disable_scanner_operator_runtime_overrides` helper를 추가해 로컬 operator override 파일이 단위 테스트에 누수되지 않게 했다.
  - 추가/보강 테스트:
    - 상승 source-quality unresolved stale guard 보호
    - terminal hardgate recheck와 max-attempt evict
    - terminal hardgate recheck runtime ordering
    - cap observability field
    - FIFO new-promotion grace 보존
- 파일: `src/tests/test_state_handler_fast_signatures.py`
- 내용:
  - runtime skip fields가 `terminal_hardgate_recheck_pending`을 유지하는지 검증했다.

## 3. 런타임 및 재기동 기록

- 재기동 방식:
  - `./restart.sh` 기반 우아한 재기동만 사용했다.
  - KILL 명령은 사용하지 않았다.
- 관측 PID:
  - `11402`
  - `15222`
  - `18488`
  - 최종 `21129`
- 최종 runtime handoff:
  - `missing_family_count=0`
  - `pid_passed=true`

## 4. 검증 결과

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'scalping_scanner_promoted_target or scalping_fifo_overflow or scanner_watch_rising_strength_hardgate or scanner_rising_insufficient_history_keeps_priority_recheck_after_standard_stale_guard_before_cutoff or runtime_iteration_targets_prioritizes_due_terminal_hardgate_recheck'`
  - `22 passed, 128 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_state_handler_fast_signatures.py -k 'terminal_hardgate_recheck_state or active_epoch_reason_over_stale_state'`
  - `2 passed, 130 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/engine/sniper_state_handlers.py`
  - 통과
- `git diff --check`
  - 통과

## 5. 세션 종료 시 관측 결론

- 10:00 진단 기준:
  - `promoted_symbol_count=281`
  - `rising_missed_buy_count=56`
  - `real_submit_symbol_count=0`
  - `falling_real_submitted_count=0`
- 09:03 이후 확인 구간에서 `scalping_dynamic_watch_cap_capacity` count는 0이었다.
- FIFO expiration은 남아 있었지만, 즉시 cap skip 병목은 완화된 것으로 봤다.
- 남은 주요 blocker:
  - WS/strength history freshness
  - `insufficient_history`
  - AI WAIT/score block
  - stale entry revalidation
  - liquidity check
- 손절/MFE:
  - 목표 window 안에서는 실제 submit과 신규 손절 분석 대상이 없었다.
  - `stop_loss_recovery_backtest` 업데이트 후보는 발생하지 않았다.
- scale-in:
  - 실제 scale-in 실행은 0건이었다.
  - 남은 blocker는 safety, PnL, flow 계열로 분류했다.

## 6. 다음 세션 점검 순서

1. 최신 intraday diagnostic artifact에서 `rising_missed_buy_count`, `real_submit_symbol_count`, `scanner_attach_capacity_candidate_overflow`를 먼저 확인한다.
2. NAVER와 유사하게 `WATCHING -> EXPIRED`가 짧은 시간에 발생한 종목은 promotion timestamp, FIFO ordering, grace 적용 여부를 같이 본다.
3. `terminal_hardgate_recheck_pending` 후보가 재평가 뒤 BUY 후보로 살아나는지, 아니면 max-attempt evict로만 닫히는지 확인한다.
4. `insufficient_history`와 WS/strength freshness가 계속 major blocker이면 threshold가 아니라 source-quality/collector freshness 쪽을 먼저 검토한다.
5. threshold 변경이 필요하다고 판단되면 실매매 한정 runtime override로 분리하고, 같은 entry stage의 기존 canary 또는 이번 FIFO/grace 관측 보강과 충돌하는지 먼저 보고한다.

## 7. 금지 사용 및 안전 경계

- 이 문서는 2026-06-29 intraday 코드수정 추적 문서이며, 단독으로 live-auto approval, threshold apply approval, EV 판정 근거가 될 수 없다.
- 신규 관측 필드는 source-quality contract가 닫히기 전까지 `instrumentation` 또는 `source_quality_review` 근거로만 사용한다.
- FIFO grace와 terminal hardgate recheck는 BUY 승인 권한이 아니며, broker/order/quantity/stale quote/hard safety를 우회할 수 없다.
- 다음 세션에서 동일 로직을 다시 수정할 때는 이 문서의 변경 목록과 최신 누적 diagnostic artifact를 함께 검토한 뒤 방향을 정한다.

## 8. 관련 산출물

- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_0840_goal.json`
- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_0920_goal.json`
- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_0940_goal.json`
- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1000_goal.json`
- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_0920_after_buy_window_reopen_goal.json`
- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_0940_after_fifo_grace_goal.json`

## 9. 09:50 이후 목표 루프 관측 보강

작성 시각: `2026-06-29 10:18 KST`

### 9.1 신규 관측 producer

- 파일: `src/engine/monitoring/intraday_entry_flow_report.py`
- 테스트: `src/tests/test_intraday_entry_flow_report.py`
- 산출물:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1018.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1018.csv`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 같은 내용으로 갱신했다.
- 내용:
  - 09:50 이후 감시대상별 `BUY 전 stage sequence`, 상승 여부, 주 blocker, BUY 전 통과신호, 실제 submit count를 산출한다.
  - `stale_eval_count`, `max_quote_age_ms`, `dominant_stale_eval_stage`, `stale_eval_rollup`을 추가해 strength/liquidity/AI blocker 안에 stale quote 평가가 섞이는지 분리한다.
- 권한 경계:
  - `decision_authority=source_quality_and_blocker_observation_only`
  - `runtime_effect=false`
  - forbidden uses: runtime threshold apply, order submit, provider route change, bot restart, broker guard bypass

### 9.2 10:18 루프 판정

- 최신 진단: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1015_goal.json`
- 09:50 이후 flow report summary:
  - `symbol_count=112`
  - `rising_symbol_count_by_max_delta=25`
  - `rising_missed_buy_count_in_latest_diagnostic=42`
  - `rising_missed_symbol_count_in_report=30`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=4`
  - `stale_eval_symbol_count=38`
  - `rising_stale_eval_symbol_count=11`
- 주요 변화:
  - 전체 blocker에는 `scanner_fast_precheck_stability_pending=41`, `ws_snapshot_missing_or_zero=9`가 남아 있다.
  - 상승 종목 기준 주 blocker는 `blocked_strength_momentum`, `blocked_liquidity`, `ai_confirmed_terminal_no_budget`, `blocked_ai_score` 쪽으로 이동했다.
  - 상승 종목 25개 중 11개는 stale 평가가 섞여 있어, blocker downsizing 전에 fresh/stale 평가 분리가 먼저 필요하다.
- blocker downsizing 검토:
  - `scanner_fast_precheck/ws_missing`은 08:00~10:00 대비 줄었지만 전체 watch pool에서는 여전히 많다. 다만 10:18 상승 종목의 1차 major blocker는 아니다.
  - `strength/liquidity/AI` blocker가 중복으로 보이는 종목이 있으나, quote age 3초 초과 stale 평가가 섞여 있으므로 지금 즉시 threshold 또는 guard downsizing을 적용하면 stale submit bypass 위험이 있다.
  - downsizing 후보는 fresh 평가만 남긴 뒤 `below_window_buy_value`, `below_strength_base`, `first_ai_wait_big_bite_not_confirmed`, `blocked_ai_score_below_buy_score_threshold`의 중복 차단 여부를 다시 봐야 한다.

### 9.3 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py`
  - `3 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_flow_report.py`
  - 통과

## 10. 10:33 목표 루프 관측 결과

작성 시각: `2026-06-29 10:33 KST`

### 10.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1033_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1033.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 같은 내용으로 갱신했다.

### 10.2 10:18 대비 변화

- 09:50 이후 진단 summary:
  - `promoted_symbol_count=252`
  - `rising_missed_buy_count=48` (`10:18`의 42에서 증가)
  - `real_submit_symbol_count=0`
  - `falling_real_submitted_count=0`
  - `rising_missed_low_ai_or_negative_pressure_eval_quality.stale_or_delayed_eval=176` (`10:18`의 104에서 증가)
- 09:50 이후 flow summary:
  - `symbol_count=178`
  - `rising_symbol_count_by_max_delta=32`
  - `rising_missed_symbol_count_in_report=37`
  - `buy_signal_or_pre_submit_pass_seen_symbols=8`
  - `stale_eval_symbol_count=77`
  - `rising_stale_eval_symbol_count=22`
- runtime log:
  - `10:32:40` loop elapsed가 `50539.0ms`까지 늘었고, 직전/직후 `WS_SUBSCRIPTION_PRUNE`가 여러 번 발생했다.

### 10.3 blocker 판단

- 전체 watch pool 기준:
  - `scanner_fast_precheck_stability_pending=65`
  - `ws_snapshot_missing_or_zero=21`
  - `blocked_strength_momentum/below_window_buy_value=28`
- 상승 종목 기준:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=6`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `blocked_strength_momentum/below_strength_base=4`
  - `blocked_strength_momentum/insufficient_history=3`
  - `scanner_fast_precheck_stability_pending=1`
- stale 평가:
  - 상승 종목 32개 중 22개가 stale 평가를 포함했다.
  - stale stage는 `blocked_strength_momentum`, `blocked_vpw`, `blocked_liquidity`, `blocked_overbought`, `ai_confirmed`에 분산되어 있다.

### 10.4 blocker downsizing 판정

- `scanner_fast_precheck_stability_pending`과 `ws_snapshot_missing_or_zero`는 전체 watch pool 병목으로는 다시 커졌지만, 10:33 상승 종목의 직접 1차 blocker는 아니다. 따라서 이 둘만 보고 entry threshold나 BUY score를 낮추는 것은 부적절하다.

- `strength/liquidity/AI` blocker가 중복으로 보이는 종목이 늘었지만, stale 평가가 상승 종목 22개에 섞여 있다. 지금 downsizing을 적용하면 stale quote submit block 또는 broker guard 우회 위험이 있다.
- 이번 루프의 조치는 코드 변경이 아니라 관측 유지다. 다음 루프에서 `fresh-only 상승 종목`만 분리해도 같은 blocker가 반복되면 그때 downsizing 후보를 `below_window_buy_value`, `below_strength_base`, `blocked_ai_score_below_buy_score_threshold`, `first_ai_wait_big_bite_not_confirmed` 순서로 좁힌다.

## 11. 10:37 08:00 기준 목표 루프 관측 및 리포트 제목 수정

작성 시각: `2026-06-29 10:37 KST`

### 11.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1037_0800_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1037.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준으로 재생성했다.

### 11.2 08:00 이후 flow summary

- `symbol_count=365`
- `rising_symbol_count_by_max_delta=79`
- `rising_missed_buy_count_in_latest_diagnostic=71`
- `rising_missed_symbol_count_in_report=71`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=21`
- `stale_eval_symbol_count=161`
- `rising_stale_eval_symbol_count=64`

### 11.3 주요 blocker 위치

- 전체 watch pool:
  - `scanner_fast_precheck_stability_pending=239`
  - `ws_snapshot_missing_or_zero=85`
  - `entry_cooldown_active=14`
- 상승 종목:
  - `scanner_fast_precheck_stability_pending=42`
  - `entry_cooldown_active=14`
  - `ws_snapshot_missing_or_zero=10`
  - `blocked_overbought/-=4`
  - `blocked_strength_momentum/below_window_buy_value=3`
- stale 평가:
  - 상승 종목 79개 중 64개에 stale 평가가 포함됐다.
  - stale stage는 `blocked_strength_momentum=78`, `blocked_liquidity=29`, `blocked_vpw=26`, `blocked_overbought=14`, `ai_confirmed=13`으로 분산된다.

### 11.4 코드 수정

- 파일:
  - `src/engine/monitoring/intraday_entry_flow_report.py`
  - `src/tests/test_intraday_entry_flow_report.py`
- 내용:
  - flow markdown 제목이 `09:50 이후`로 고정되어 있어 08:00 리포트와 불일치하던 관측 품질 결함을 수정했다.
  - 제목은 `event_window_since`에서 계산한 `HH:MM 이후`를 사용한다.
  - 08:00 제목 회귀 테스트를 추가했다.
- 충돌 검토:
  - 리포트 렌더링 표기 수정이며 runtime threshold, order submit, provider route, bot restart, stale submit block, broker guard에는 영향이 없다.

### 11.5 10:37 판정

- 08:00 이후 전체 흐름에서는 상승 미진입의 대부분이 `scanner_fast_precheck_stability_pending`, `ws_snapshot_missing_or_zero`, `entry_cooldown_active`에서 막혔다.
- 상승 후 BUY/pre-submit 신호까지 간 종목은 21개지만 실제 submit은 0개다. SK이터닉스, LG에너지솔루션 계열처럼 BUY 또는 latency pass 후에도 `stale_context_or_quote` revalidation block이 존재하므로 stale submit bypass는 금지한다.
- 이번 루프에서는 blocker downsizing보다 observation freshness/WS snapshot/strength history 쪽이 major issue다. 10:37 직전 런타임 로그에서 10:32 `50539ms`, 10:36 `39708ms`, 10:37 `31825.9ms` loop pressure가 보였으므로 다음 루프에서 30초 이상 loop가 반복되면 `restart.flag` 기반 graceful restart를 검토한다.

### 11.6 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py`
  - `4 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_flow_report.py`
  - 통과
- `git diff --check`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - 통과

## 12. 10:40 graceful restart 기록

작성 시각: `2026-06-29 10:40 KST`

### 12.1 재기동 사유

- 10:32 `50539.0ms`, 10:36 `39708.3ms`, 10:37 `31825.9ms`, 10:38 `32611.3ms` loop 지연이 반복되어 observation freshness/WS snapshot 병목 완화가 필요했다.
- 코드/리포트 변경은 review gate 검증을 통과했고 봇 runtime decision authority를 바꾸지 않는 범위라, threshold/order/provider 변경 없이 runbook 표준 graceful restart만 수행했다.

### 12.2 실행 경로

- 명령:
  - `./restart.sh`
- 방식:
  - `restart.flag` handoff
  - KILL 명령 미사용
  - 직접 중복 봇 기동 미사용

### 12.3 결과

- 이전 PID:
  - `21129`
- 신규 PID:
  - `48856`
- runtime env handoff:
  - `passed=true`
  - `missing_family_count=0`
  - `pid_passed=true`
- 봇 재진입:
  - `10:40:22` 스나이퍼/스캐너 루프 재진입
  - `10:40:23` 웹소켓 감시 8종목 등록
- 재기동 후 첫 loop metric:
  - `10:40:39 loop_elapsed_ms=9126.1`

### 12.4 후속 판정

- 재기동 직후 30초대 loop 지연은 해소된 것으로 보이나, 아직 첫 샘플이다.
- 다음 15분 루프에서 `LOOP_METRICS`, `stale_eval_symbol_count`, `rising_stale_eval_symbol_count`, `stale_context_or_quote` submit block 재발 여부를 함께 확인한다.

## 13. 10:45 목표 루프 관측 결과

작성 시각: `2026-06-29 10:45 KST`

### 13.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1045_0800_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1045_0950_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1045.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1045.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준 최신 내용으로 재생성했다.

### 13.2 08:00 이후 flow summary

- `symbol_count=372`
- `rising_symbol_count_by_max_delta=79`
- `rising_missed_buy_count_in_latest_diagnostic=71`
- `rising_missed_symbol_count_in_report=71`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=23`
- `stale_eval_symbol_count=172`
- `rising_stale_eval_symbol_count=67`

### 13.3 09:50 이후 flow summary

- `symbol_count=199`
- `rising_symbol_count_by_max_delta=37`
- `rising_missed_buy_count_in_latest_diagnostic=51`
- `rising_missed_symbol_count_in_report=41`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=10`
- `stale_eval_symbol_count=95`
- `rising_stale_eval_symbol_count=27`

### 13.4 blocker 판단

- 08:00 이후 누적 기준 상승 종목 blocker:
  - `scanner_fast_precheck_stability_pending=42`
  - `entry_cooldown_active=14`
  - `ws_snapshot_missing_or_zero=10`
  - `blocked_overbought/-=4`
  - `blocked_strength_momentum/below_window_buy_value=3`
- 09:50 이후 최근 기준 상승 종목 blocker:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=9`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `blocked_strength_momentum/insufficient_history=4`
  - `blocked_strength_momentum/below_strength_base=4`
  - `blocked_overbought/below_window_buy_value=2`
  - `blocked_liquidity/first_ai_wait_big_bite_not_confirmed=2`
- stale 평가:
  - 08:00 이후 상승 79개 중 67개가 stale 평가를 포함했다.
  - 09:50 이후 상승 37개 중 27개가 stale 평가를 포함했다.

### 13.5 재기동 후 runtime 관측

- `10:40:39 loop_elapsed_ms=9126.1`
- `10:42:02 dynamic watch cap reduce loop_elapsed_ms=82079.5`
- `10:42:11 loop_elapsed_ms=8135.0`
- `10:42:48 dynamic watch cap reduce loop_elapsed_ms=35894.0`
- `10:43:35 loop_elapsed_ms=4199.2`
- 판정:
  - 재기동 직후 초기 재구독/재초기화 구간에서 다시 큰 spike가 있었지만, 이후 loop metric은 8초대와 4초대로 내려왔다.
  - 현 시점에는 즉시 2차 재기동하지 않는다. 다음 루프에서 30초 이상 loop 지연이 2회 이상 다시 반복되면 runtime pressure를 재발로 보고 재검토한다.

### 13.6 10:45 판정

- 08:00 이후 누적 기준 병목은 여전히 scanner/WS observation freshness다.
- 09:50 이후 최근 상승 종목만 보면 blocker가 AI score, strength, liquidity, overbought 쪽으로 내려오지만, stale 평가가 27/37개에 섞여 있어 threshold downsizing은 아직 보류한다.
- SK이터닉스, LG에너지솔루션, 케이씨텍, 테스처럼 BUY/pre-submit 경로까지 간 종목도 실제 submit은 0건이며, 원인은 latency danger 또는 `stale_context_or_quote` 계열이다. stale submit bypass와 broker guard bypass는 금지 유지한다.
- scale-in은 executed_count=0이며, 주요 blocker는 `pnl_out_of_range`, `profit_not_enough`, `flow_hold_interval` 계열이다. quantity cap release나 scale-in guard bypass는 하지 않는다.

## 14. 10:47 hot runtime pressure relief

작성 시각: `2026-06-29 10:47 KST`

### 14.1 조치 사유

- 10:40 graceful restart 이후에도 다음 loop pressure가 반복됐다.
  - `10:45:45 loop_elapsed_ms=30094.5`
  - `10:46:54 loop_elapsed_ms=36803.8`
- `10:46:52`에 scanner promoted target이 한 루프에 12개 attach되며 `target_count=25`, `watching=21`까지 상승했다.
- 같은 blocker에 재기동을 반복하기보다, hot reload 가능한 scanner full-eval throughput만 낮춰 observation pressure를 줄이는 쪽으로 조치했다.

### 14.2 runtime override

- 파일:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
- git 상태:
  - 이 파일은 `.gitignore` 대상 runtime env이므로 커밋되지 않는다. 다음 세션 추적을 위해 이 문서에 기록한다.
- 추가 최종 export:
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=12`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=4`
- rollback:
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=24`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=16`
- 검증:
  - `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
    - 통과
  - local parser check:
    - `_scanner_full_eval_max_per_loop()=12`
    - `_scanner_full_eval_backlog_extra_per_loop()=4`
    - `_scanner_full_eval_effective_limit({"scanner_watching_count": 40})=16`

### 14.3 안전 경계

- 이 조치는 SCALPING SCANNER observation/evaluation 처리량 완화만 수행한다.
- BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity guard, provider route, hard/protect/emergency stops는 변경하지 않았다.
- `KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_EXTRA_PER_LOOP=12`는 현재 코드에서 hot key가 아니므로 이번 조치에 포함하지 않았다. 반복적으로 조정할 필요가 있으면 별도 코드 변경으로 hot key화한 뒤 review gate를 거친다.

## 15. 11:00 목표 루프 관측 결과

작성 시각: `2026-06-29 11:00 KST`

### 15.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1100_0800_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1100_0950_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1100.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1100.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준 최신 내용으로 재생성했다.

### 15.2 08:00 이후 flow summary

- `symbol_count=385`
- `rising_symbol_count_by_max_delta=80`
- `rising_missed_buy_count_in_latest_diagnostic=71`
- `rising_missed_symbol_count_in_report=71`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=24`
- `stale_eval_symbol_count=180`
- `rising_stale_eval_symbol_count=70`

### 15.3 09:50 이후 flow summary

- `symbol_count=219`
- `rising_symbol_count_by_max_delta=40`
- `rising_missed_buy_count_in_latest_diagnostic=51`
- `rising_missed_symbol_count_in_report=42`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=11`
- `stale_eval_symbol_count=108`
- `rising_stale_eval_symbol_count=33`

### 15.4 blocker 판단

- 08:00 이후 누적 기준 상승 종목 blocker:
  - `scanner_fast_precheck_stability_pending=44`
  - `entry_cooldown_active=15`
  - `ws_snapshot_missing_or_zero=9`
  - `blocked_overbought/-=4`
  - `blocked_strength_momentum/below_window_buy_value=3`
- 09:50 이후 최근 기준 상승 종목 blocker:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=9`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `blocked_liquidity/first_ai_wait_big_bite_not_confirmed=4`
  - `blocked_strength_momentum/below_strength_base=4`
  - `blocked_strength_momentum/insufficient_history=3`
  - `scalping_scanner_watching_runtime_skip/scanner_fast_precheck_stability_pending=2`
- stale 평가:
  - 08:00 이후 상승 80개 중 70개가 stale 평가를 포함했다.
  - 09:50 이후 상승 40개 중 33개가 stale 평가를 포함했다.

### 15.5 runtime pressure 판정

- hot override 이후 최근 loop:
  - `10:47:37 loop_elapsed_ms=11381.8`
  - `10:48:50 loop_elapsed_ms=19603.4`
  - `11:01:12 loop_elapsed_ms=8481.2`
- 판정:
  - 30초 이상 loop 지연 반복은 10:47 hot override 이후 일단 해소됐다.
  - 재기동은 추가로 수행하지 않는다.

### 15.6 11:00 판정

- BUY/pre-submit 경로까지 간 종목은 늘었지만 실제 submit은 여전히 0건이다.
- 신규 submit-path blocker로 대우건설이 `pre_submit_liquidity_guard_action=BLOCK`, `pre_submit_liquidity_reason=below_min_liquidity`, `entry_submit_revalidation_warning=stale_context_or_quote`로 차단됐다.
- 최근 상승 종목 blocker는 AI score/strength/liquidity 쪽으로 내려왔지만 stale 평가가 33/40개에 섞여 있으므로 broad threshold downsizing은 아직 보류한다.
- 다음 루프에서는 fresh-only 상승 종목과 BUY/pre-submit pass 이후 `latency_block`, `entry_submit_revalidation_block`, `pre_submit_liquidity_guard BLOCK` 종목만 분리해서 볼 필요가 있다.

## 16. 11:15 목표 루프 관측 결과

작성 시각: `2026-06-29 11:15 KST`

### 16.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1115_0800_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1115_0950_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1115.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1115.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준 최신 내용으로 재생성했다.

### 16.2 08:00 이후 flow summary

- `symbol_count=406`
- `rising_symbol_count_by_max_delta=82`
- `rising_missed_buy_count_in_latest_diagnostic=71`
- `rising_missed_symbol_count_in_report=71`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=25`
- `stale_eval_symbol_count=188`
- `rising_stale_eval_symbol_count=71`

### 16.3 09:50 이후 flow summary

- `symbol_count=244`
- `rising_symbol_count_by_max_delta=41`
- `rising_missed_buy_count_in_latest_diagnostic=52`
- `rising_missed_symbol_count_in_report=42`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=12`
- `stale_eval_symbol_count=119`
- `rising_stale_eval_symbol_count=37`

### 16.4 blocker 판단

- 08:00 이후 누적 기준 상승 종목 blocker:
  - `scanner_fast_precheck_stability_pending=45`
  - `entry_cooldown_active=16`
  - `ws_snapshot_missing_or_zero=8`
  - `blocked_overbought/-=4`
  - `blocked_strength_momentum/below_window_buy_value=4`
- 09:50 이후 최근 기준 상승 종목 blocker:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=8`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `blocked_liquidity/first_ai_wait_big_bite_not_confirmed=4`
  - `blocked_strength_momentum/below_strength_base=4`
  - `blocked_strength_momentum/insufficient_history=3`
  - `scalping_scanner_watching_runtime_skip/scanner_fast_precheck_stability_pending=3`
- stale 평가:
  - 08:00 이후 상승 82개 중 71개가 stale 평가를 포함했다.
  - 09:50 이후 상승 41개 중 37개가 stale 평가를 포함했다.

### 16.5 runtime pressure 판정

- hot override 이후 11:01~11:15 loop metric은 대체로 3.7초~25.2초 범위에 머물렀다.
- 30초 이상 loop 지연 반복은 10:47 hot override 이후 재발하지 않았다.
- 신규 graceful restart 또는 KILL은 수행하지 않는다.

### 16.6 11:15 판정

- 08:00 이후 누적 흐름의 주 병목은 여전히 scanner/WS observation freshness와 entry cooldown이다.
- 09:50 이후 최근 흐름에서는 AI score, strength, liquidity 계열 blocker가 직접 표면화됐지만, 상승 종목 stale 평가 비율이 37/41로 높다. 따라서 BUY score, strength, liquidity threshold를 광범위하게 낮추는 조치는 보류한다.
- BUY/pre-submit 경로까지 간 종목은 25개로 늘었지만 실제 submit은 여전히 0건이다. 져스텍, SK이터닉스, 테스, 대우건설처럼 BUY 또는 budget/latency pass가 보인 종목도 latency, liquidity, stale context revalidation 단계에서 막혔다.
- falling real submitted는 0건이라 하락 후 submit 유형 개선이나 손절/MFE 업데이트 대상은 아직 발생하지 않았다.
- 다음 루프에서는 fresh-only 상승 종목과 BUY/pre-submit pass 이후 submit-path blocker를 분리해서 본다. stale submit, broker guard, order guard bypass는 금지 유지한다.

## 17. 11:20 목표 루프 관측 및 hot runtime pressure relief p2

작성 시각: `2026-06-29 11:20 KST`

### 17.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1120_0800_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1120_0950_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1120.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1120.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준 최신 내용으로 재생성했다.

### 17.2 09:50 이후 flow summary

- `symbol_count=254`
- `rising_symbol_count_by_max_delta=44`
- `rising_missed_buy_count_in_latest_diagnostic=55`
- `rising_missed_symbol_count_in_report=46`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=13`
- `stale_eval_symbol_count=125`
- `rising_stale_eval_symbol_count=38`

### 17.3 blocker 판단

- 09:50 이후 상승 종목 blocker:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=8`
  - `blocked_strength_momentum/below_strength_base=5`
  - `blocked_liquidity/first_ai_wait_big_bite_not_confirmed=5`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `scalping_scanner_watching_runtime_skip/scanner_fast_precheck_stability_pending=4`
  - `blocked_strength_momentum/insufficient_history=3`
- stale 평가:
  - 09:50 이후 상승 44개 중 38개가 stale 평가를 포함했다.
  - 09:50 이후 diagnostic의 `stale_or_delayed_eval=397`, `fresh_eval=130`으로 stale/지연 평가가 여전히 우세하다.
- submit/price path:
  - 실제 submit은 0건이다.
  - 최근 submit-path blocker는 대우건설과 아모레퍼시픽의 `entry_submit_revalidation_warning=stale_context_or_quote` 및 `entry_submit_revalidation_block`이다.
  - price/submit guard diagnostic은 `block_or_unfilled_count=30`, `candidate_failure_count=4`, 실패 reason은 모두 `invalid_price`다.

### 17.4 runtime pressure relief p2

- 재발 근거:
  - `11:18:12 loop_elapsed_ms=54549.8`
  - `11:19:41 loop_elapsed_ms=41648.6`
- 조치:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env` EOF의 최종 export를 다음 값으로 조정했다.
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=8`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=2`
- rollback:
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=12`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=4`
- 검증:
  - `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
    - 통과
  - local parser check:
    - `_scanner_full_eval_max_per_loop()=8`
    - `_scanner_full_eval_backlog_extra_per_loop()=2`
    - `_scanner_full_eval_effective_limit({"scanner_watching_count": 40})=10`

### 17.5 안전 경계 및 판정

- 이번 조치는 SCALPING SCANNER observation/evaluation 처리량만 낮춘다.
- BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않았다.
- runtime hot reload가 5초 주기로 적용 가능하므로 즉시 재기동하지 않는다. 다음 루프에서 30초 이상 loop 지연이 계속 반복되면 그때 `restart.flag` 기반 graceful restart를 재검토한다.
- broad threshold downsizing은 보류한다. 현재는 stale 평가와 loop pressure가 blocker 판정에 섞여 있어 fresh-only 표본으로 분리되기 전까지 실매매 threshold를 낮추면 stale submit bypass 위험이 있다.

## 18. 11:30 목표 루프 관측 결과

작성 시각: `2026-06-29 11:30 KST`

### 18.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1130_0800_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1130_0950_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1130.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1130.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준 최신 내용으로 재생성했다.

### 18.2 09:50 이후 flow summary

- `symbol_count=269`
- `rising_symbol_count_by_max_delta=44`
- `rising_missed_buy_count_in_latest_diagnostic=55`
- `rising_missed_symbol_count_in_report=46`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=13`
- `stale_eval_symbol_count=129`
- `rising_stale_eval_symbol_count=38`

### 18.3 blocker 판단

- 09:50 이후 상승 종목 blocker:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=8`
  - `blocked_strength_momentum/below_strength_base=5`
  - `blocked_liquidity/first_ai_wait_big_bite_not_confirmed=5`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `scalping_scanner_watching_runtime_skip/scanner_fast_precheck_stability_pending=4`
  - `blocked_strength_momentum/insufficient_history=3`
- stale 평가:
  - 09:50 이후 상승 44개 중 38개가 stale 평가를 포함했다.
  - 09:50 이후 diagnostic의 `stale_or_delayed_eval=428`, `fresh_eval=131`으로 11:20보다 stale/지연 평가가 늘었다.
- submit/price path:
  - 실제 submit은 0건이다.
  - BUY/pre-submit pass는 13개로 11:20과 동일하다.
  - 최근 submit-path blocker는 계속 `entry_submit_revalidation_warning=stale_context_or_quote`, `entry_submit_revalidation_block`, `pre_submit_liquidity_guard BLOCK`, `invalid_price` 계열이다.

### 18.4 runtime pressure 판정

- p2 hot override 이후 주요 loop:
  - `11:21:18 loop_elapsed_ms=21435.7`
  - `11:22:25 loop_elapsed_ms=14869.2`
  - `11:23:43 loop_elapsed_ms=25780.9`
  - `11:24:55 loop_elapsed_ms=5522.3`
  - `11:30:23 loop_elapsed_ms=10883.2`
- 30초 이상 loop 지연은 p2 이후 재발하지 않았다.
- 신규 graceful restart 또는 KILL은 수행하지 않는다.

### 18.5 11:30 판정

- 09:50 이후 rising missed는 55로 11:20과 같지만, 감시 종목과 stale eval은 증가했다.
- 직접 blocker는 AI score, strength, liquidity로 보이지만 source freshness가 닫히지 않아 broad threshold downsizing은 여전히 보류한다.
- stale submit, broker guard, order guard bypass는 금지 유지한다.
- falling real submitted는 0건이라 하락 후 submit 개선과 손절/MFE 업데이트 대상은 아직 없다.
- 다음 11:45 루프에서는 p2 이후 stale 평가가 줄어드는지와 fresh-only 상승 종목 blocker가 여전히 동일한지 분리해서 본다.

## 19. 11:45 목표 종료 루프 관측 결과

작성 시각: `2026-06-29 11:45 KST`

### 19.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1145_0800_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1145_0950_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1145.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0950_to_1145.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 08:00 기준 최신 내용으로 재생성했다.

### 19.2 09:50 이후 flow summary

- `symbol_count=291`
- `rising_symbol_count_by_max_delta=49`
- `rising_missed_buy_count_in_latest_diagnostic=57`
- `rising_missed_symbol_count_in_report=49`
- `real_submit_symbol_count_in_latest_diagnostic=0`
- `buy_signal_or_pre_submit_pass_seen_symbols=13`
- `stale_eval_symbol_count=138`
- `rising_stale_eval_symbol_count=43`

### 19.3 blocker 판단

- 09:50 이후 상승 종목 blocker:
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold=8`
  - `blocked_strength_momentum/below_strength_base=5`
  - `blocked_liquidity/first_ai_wait_big_bite_not_confirmed=5`
  - `blocked_strength_momentum/below_window_buy_value=5`
  - `scalping_scanner_watching_runtime_skip/scanner_fast_precheck_stability_pending=5`
  - `blocked_strength_momentum/insufficient_history=4`
  - `blocked_strength_momentum/below_buy_ratio=4`
- stale 평가:
  - 09:50 이후 상승 49개 중 43개가 stale 평가를 포함했다.
  - 09:50 이후 diagnostic의 `stale_or_delayed_eval=465`, `fresh_eval=143`으로 stale/지연 평가 우위가 유지됐다.
- submit/price path:
  - 실제 submit은 0건이다.
  - BUY/pre-submit pass는 13개로 11:20, 11:30과 동일하다.
  - price/submit guard diagnostic은 `block_or_unfilled_count=30`, `candidate_failure_count=5`, 실패 reason은 모두 `invalid_price`다.

### 19.4 runtime pressure 판정

- p2 hot override 이후에도 중간 spike는 재발했다.
  - `11:35:11 loop_elapsed_ms=48124.3`
  - `11:38:16 loop_elapsed_ms=35471.0`
- 다만 종료 직전 구간은 회복됐다.
  - `11:40:59 loop_elapsed_ms=2122.1`
  - `11:42:41 loop_elapsed_ms=8664.9`
  - `11:43:45 loop_elapsed_ms=8579.8`
  - `11:44:59 loop_elapsed_ms=14893.6`
- 목표 종료 시각이 지났으므로 추가 graceful restart 또는 KILL은 수행하지 않는다.

### 19.5 종료 판정

- 11:45 이후 목표 기능을 종료한다.
- 주요 병목은 `scanner_fast_precheck_stability_pending`, `ws_snapshot_missing_or_zero`, stale/지연 strength/liquidity/AI 평가, 그리고 submit 직전 `stale_context_or_quote`/`invalid_price` 계열이다.
- blocker downsizing은 보류한다. 직접 blocker가 AI score/strength/liquidity로 보이지만 stale 평가가 43/49개에 섞여 있어, 실매매 threshold를 낮추면 stale submit 또는 broker/order guard 우회 위험이 있다.
- real submit은 0건이고 falling real submitted도 0건이라, 하락 후 submit 개선/손절/MFE 업데이트/scale-in 복구 검증 대상은 발생하지 않았다.
- p2 runtime pressure relief는 최종 hot value `KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=8`, `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=2`로 남겨둔다. rollback은 각각 `12`, `4`다.

## 20. hot runtime pressure relief 자동관측/자동조절 구현

작성 시각: `2026-06-29 KST`

### 20.1 변경 목록

- `src/engine/kiwoom_sniper_v2.py`
  - `SCANNER_FULL_EVAL_PRESSURE` governor를 추가했다.
  - `LOOP_METRICS`의 `loop_elapsed_ms`를 관측해 다음 loop의 scanner full-eval effective limit을 메모리 상태로 자동 감압/회복한다.
  - hot override 가능 env:
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED`
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT`
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MS`
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RELIEF_MS`
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_COOLDOWN_SEC`
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RECOVERY_STREAK`
- `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 감압, 점진 회복, disabled base 유지 테스트를 추가했다.

### 20.2 권한/충돌 검토

- 이 변경은 scanner full-eval 관측 예산만 조절한다.
- BUY threshold, AI score threshold, 주문가, 주문수량, provider route, broker/account/order/quantity/cooldown guard, stop/exit 로직은 변경하지 않는다.
- operator runtime override 파일은 직접 수정하지 않는다. hot 값은 읽기만 하고, 자동 감압 상태는 프로세스 메모리에만 둔다.
- buy window가 아닐 때는 pressure streak/recovery streak를 진행하지 않아 감시 외 시간의 loop 지연이 자동 감압 근거가 되지 않는다.
- 기존 p2 hot override `FULL_EVAL_MAX_PER_LOOP=8`, `BACKLOG_EXTRA_PER_LOOP=2`와 충돌하지 않는다. governor는 해당 base 위에서 일시적으로 아래 방향만 감압하고, 정상 loop가 누적되면 base까지 회복한다.

### 20.3 운영 판정

- 반복 수동감시 후 값 조정이 필요한 구간은 자동 governor가 우선 흡수한다.
- 런타임에 더 강한 감압/완화가 필요하면 위 hot override env만 바꾸면 되고, threshold/order/provider/bot authority 변경으로 해석하지 않는다.

## 21. 11:30 이후 stale/quote freshness 병목 해소 패치

작성 시각: `2026-06-29 12:04 KST`

### 21.1 누적 변경목록 충돌 검토

- 기존 2.1~2.4 변경은 WATCHING 유지, terminal hardgate 재점검, attach/cap 관측, FIFO grace에 한정되어 있었다.
- 이번 변경은 BUY threshold, broker submit guard, stale submit block, account/order/quantity/cooldown guard를 완화하지 않고, pre-AI 평가 입력의 quote freshness와 리포트 stale 분류만 보강한다.
- 따라서 기존 FIFO/grace 관측 보강과 직접 충돌하지 않는다. 다만 같은 entry stage의 병목을 다루므로 이후 strength/liquidity/AI threshold downsizing을 추가할 때는 fresh-only 표본과 stale-mixed 표본을 분리한 뒤 별도 보고가 필요하다.

### 21.2 리포트 stale 분리

- 파일: `src/engine/monitoring/intraday_entry_flow_report.py`
- 테스트: `src/tests/test_intraday_entry_flow_report.py`
- 내용:
  - `stale_eval_category_rollup`, `dominant_stale_eval_category`, `stale_refresh_recovered_count`를 추가했다.
  - refresh가 fresh snapshot으로 회복된 row는 `stale_eval_count`에서 제외하고 `refresh회복`으로 별도 표시한다.
  - hard stale submit block은 `pre_submit_stale_context_or_quote`, WS 결손은 `ws_snapshot_missing_or_zero`, quote age 기반 진단 stale은 `diagnostic_quote_age_stale`로 분리한다.
- 권한 경계:
  - `decision_authority=source_quality_and_blocker_observation_only`
  - `runtime_effect=false`
  - forbidden uses: runtime threshold apply, order submit, broker guard bypass

### 21.3 pre-AI quote-only WS refresh

- 파일: `src/engine/sniper_state_handlers.py`
- 테스트: `src/tests/test_sniper_entry_latency.py`
- 내용:
  - `_pre_ai_refresh_quote_ws_snapshot`를 추가해 strength history가 아직 비어 있어도 최신 WS quote가 fresh이면 pre-AI overbought/strength/liquidity 평가 입력을 최신 snapshot으로 갱신한다.
  - refresh 성공 시 `curr`, `v_pw`, `fluctuation`, orderbook total, `intraday_surge`, liquidity value를 함께 재계산한다.
  - 기존 `_pre_ai_refresh_strength_momentum_ws_snapshot`는 quote refresh가 적용되지 않았을 때만 수행한다. quote refresh가 적용된 snapshot에 strength history가 있으면 그대로 사용하고, history가 없으면 기존 strength/insufficient_history blocker가 유지된다.
- 권한 경계:
  - stale submit block, broker/account/order/quantity/cooldown guard, hard/protect/emergency safety는 변경하지 않았다.
  - BUY score/VPW/strength/liquidity threshold 값은 변경하지 않았다.
  - runtime 반영에는 봇 코드 재로딩이 필요하므로 review gate 통과 후 `restart.flag` 방식으로만 적용한다.

### 21.4 12:04 관측 결과

- 08:00 이후 누적 flow:
  - `symbol_count=444`
  - `rising_symbol_count_by_max_delta=88`
  - `rising_missed_buy_count_in_latest_diagnostic=74`
  - `rising_missed_symbol_count_in_report=74`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=26`
  - `stale_eval_symbol_count=202`
  - `rising_stale_eval_symbol_count=74`
  - `stale_refresh_recovered_symbol_count=184`
- 11:30 이후 flow:
  - `symbol_count=82`
  - `rising_symbol_count_by_max_delta=25`
  - `rising_missed_symbol_count_in_report=25`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
  - `stale_eval_symbol_count=51`
  - `rising_stale_eval_symbol_count=19`
  - `stale_refresh_recovered_symbol_count=29`
- 11:30 이후 남은 stale category는 전부 `diagnostic_quote_age_stale`로 분류됐다. refresh 회복 row가 별도 분리된 뒤에도 stale-mixed blocked_overbought/blocked_strength_momentum/ai_confirmed가 남아 있으므로, 다음 루프에서는 runtime 재기동 후 `diagnostic_quote_age_stale` 감소 여부와 fresh-only strength/liquidity/AI blocker를 분리 확인한다.

### 21.5 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py src/tests/test_sniper_entry_latency.py -k 'intraday_entry_flow or pre_ai_strength_ws_snapshot_refresh or pre_ai_quote_ws_snapshot_refresh or strength_source_quality'`
  - `14 passed, 71 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/engine/sniper_state_handlers.py src/tests/test_intraday_entry_flow_report.py src/tests/test_sniper_entry_latency.py`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - 통과
- `git diff --check`
  - 통과

### 21.6 런타임 반영

- 실행:
  - `./restart.sh`
- 방식:
  - `restart.flag` handoff
  - KILL 명령 미사용
  - 직접 중복 봇 기동 미사용
- 결과:
  - 이전 PID `48856`
  - 신규 PID `79579`
  - `restart.flag` 소모 확인
  - runtime env handoff `passed=true`, `missing_family_count=0`, `pid_passed=true`
  - `12:08:58` 스나이퍼/스캐너 루프 재진입
  - `12:09:04 loop_elapsed_ms=196.6`
- 12:09 리포트 재생성:
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md` 갱신
  - 11:30 이후 보조 리포트 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_1130_to_1209.md` 생성
  - 재시작 직후 신규 감시 이벤트가 충분히 쌓이기 전이라 12:04와 summary 수치는 동일하다.
- 다음 루프 확인:
  - 새 PID 기준 `pre_ai_ws_snapshot_refresh_applied=True`가 overbought/strength/liquidity 전단 stale-mixed row를 줄이는지 확인한다.
  - `diagnostic_quote_age_stale`가 유지되면 full-eval 지연/WS subscription freshness 쪽을 다음 major issue로 재분해한다.
