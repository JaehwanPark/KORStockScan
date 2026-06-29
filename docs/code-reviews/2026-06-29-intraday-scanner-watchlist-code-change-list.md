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
