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

## 2026-06-30 09:40 목표 루프 관측 보강

작성 시각: `2026-06-30 09:45 KST`

### 판정

- 09:31/09:40 루프에서 `rising_missed_buy_count=0`, `deferred_never_evaluated=0`, `real_submit_symbol_count=16`으로 BUY 전 actionable major blocker는 실질 잔여 없음으로 판정했다.
- 반복 root cause priority는 BUY 전 submit drought가 아니라 `entry_price_or_submit_price_guard_block`의 evidence 품질 문제였다. `entry_order_cancel_*` 이벤트는 실제 주문가를 `submitted_price`로 남기는데 diagnostics가 `submitted_order_price`만 읽어 recent issue에 주문가가 `null`로 표시됐다.
- 이 문제는 주문/취소 로직 결함이 아니라 관측 producer의 필드 정규화 누락이다. 주문가 완화, cancel wait 변경, stale/broker guard 우회는 수행하지 않았다.

### 코드수정

- 파일: `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
- 내용:
  - `entry_order_cancel_requested/confirmed` recent issue가 `submitted_order_price -> submitted_price -> order_price -> resolved_order_price` 순서로 주문가를 복원하도록 보강했다.
  - 목적은 미체결/취소 품질 분석에서 missing-to-null evidence를 제거하고, 방어가 주문가가 bid 대비 얼마나 낮았는지 즉시 볼 수 있게 하는 것이다.
- 테스트: `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - cancel 이벤트가 `submitted_price`만 보유해도 `entry_price_execution.recent_issues[].submitted_order_price`에 값이 채워지는 회귀 테스트를 추가했다.

### 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_blocker_diagnostics.py -k "entry_price or submitted_price"`
  - `4 passed, 22 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 통과
- 09:40 diagnostics 재생성:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_0940_goal.json`
  - 최근 cancel issue의 `submitted_order_price`가 `16690/174500/10440` 등으로 정상 복원됨을 확인했다.

### 운영 경계

- `runtime_effect=false`
- forbidden uses: `stale_submit_bypass`, `broker_guard_bypass`, `intraday_order_price_relaxation_without_operator_override`
- 실주문 권한, hard/protect/emergency safety, broker/account/order/quantity/cooldown guard, threshold, provider route, bot restart는 변경하지 않았다.

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

## 22. 12:20 목표 루프 및 full-eval pressure p3 hot override

작성 시각: `2026-06-29 12:21 KST`

### 22.1 12:20 관측

- 11:30 이후 flow:
  - `symbol_count=97`
  - `rising_symbol_count_by_max_delta=27`
  - `rising_missed_symbol_count_in_report=30`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=1`
  - `stale_eval_symbol_count=59`
  - `rising_stale_eval_symbol_count=21`
  - `stale_refresh_recovered_symbol_count=44`
- 변화:
  - BUY/pre-submit 통과는 0에서 1로 늘었고, 올릭스는 `entry_armed -> budget_pass -> latency_pass:safe_normal_entry_allowed`까지 도달했다.
  - 실제 submit은 여전히 0건이다.
  - refresh 회복 row는 29에서 44로 늘었지만, 남은 stale category는 전부 `diagnostic_quote_age_stale`다.
- 새 PID 이후 loop pressure:
  - `12:09:04 loop_elapsed_ms=196.6`
  - `12:10:31 loop_elapsed_ms=86224.6`
  - `12:14:43 loop_elapsed_ms=59536.2`
  - `12:15:23 loop_elapsed_ms=38388.8`
  - `12:19:46 loop_elapsed_ms=9483.0`
- 판정:
  - pre-AI quote refresh는 일부 stale-mixed row를 `refresh회복`으로 분리했지만, full-eval/WS prune pressure가 다시 stale source를 만들고 있다.
  - 다음 major issue는 threshold downsizing이 아니라 scanner full-eval pressure와 WS subscription freshness다.

### 22.2 p3 hot override

- 파일:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
- 추가 값:
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED=true`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=4`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MS=10000`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RELIEF_MS=5000`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_COOLDOWN_SEC=20`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RECOVERY_STREAK=4`
- 목적:
  - p2 기준 `FULL_EVAL_MAX_PER_LOOP=8`, `BACKLOG_EXTRA_PER_LOOP=2` 위에서 자동 governor가 `8 -> 6`까지만 감압하던 한계를 완화해, pressure 반복 시 4까지 낮출 수 있게 한다.
  - cooldown을 60초에서 20초로 줄여 반복 pressure에 빠르게 반응한다.
- rollback:
  - `AUTO_PRESSURE_MIN_LIMIT=6`
  - `AUTO_PRESSURE_MS=12000`
  - `AUTO_RELIEF_MS=7000`
  - `AUTO_COOLDOWN_SEC=60`
  - `AUTO_RECOVERY_STREAK=3`

### 22.3 권한/충돌 검토

- 이 변경은 real SCALPING SCANNER observation throughput만 조절한다.
- BUY score, AI threshold, liquidity/latency/stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.
- hot reload 가능 key이므로 즉시 재기동하지 않는다. 다음 루프에서 runtime이 반영하지 못했을 때만 `restart.flag`를 재검토한다.

### 22.4 검증

- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과

## 23. 12:28 dynamic watch cap hot reload 및 p4 pressure override

작성 시각: `2026-06-29 12:28 KST`

### 23.1 누적 관측

- p3 full-eval hot override는 런타임에 반영되었다.
  - `12:22:03 [SCANNER_FULL_EVAL_PRESSURE] ... effective_limit=4 min_limit=4`
- 그러나 p3 반영 뒤에도 loop pressure가 남았다.
  - `12:22:31 loop_elapsed_ms=26957.2 target_count=25 watching=21`
  - `12:23:53 loop_elapsed_ms=41439.2 target_count=20 watching=16`
  - `12:27:15 loop_elapsed_ms=13661.4 target_count=18 watching=14`
- `12:28:05 [SCALPING_DYNAMIC_WATCH_CAP] action=recover ... base_cap=22 effective_cap=17` 로그로 보아 기존 running process는 watch cap 값을 old env 기반으로만 읽고 있었다.

### 23.2 코드 수정

- 파일:
  - `src/engine/kiwoom_sniper_v2.py`
  - `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
- 변경:
  - `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK`
  - 위 key들을 scanner hot runtime override allowlist에 추가했다.
  - dynamic watch cap getter가 `os.getenv` 대신 `_scanner_hot_or_env_value`를 사용하도록 변경했다.
  - 기존 env-only 테스트는 실제 `operator_runtime_overrides.env` 영향을 받지 않도록 격리했다.
  - hot reload 테스트에 dynamic watch cap key 재로딩 검증을 추가했다.

### 23.3 p4 hot override

- 파일:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
- 추가 값:
  - `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=20`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED=true`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=10000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS=5000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=20`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK=4`
- 목적:
  - full-eval limit이 이미 4까지 내려갔는데도 loop spike와 WS prune burst가 반복되어, WATCHING pool pressure도 같이 낮춘다.
  - p4 이후에는 코드상 같은 key가 hot reload 대상이므로 값 조정만으로는 봇 재기동이 필요하지 않다.
- rollback:
  - `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=22`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=16`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=12000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS=7000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=60`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK=3`

### 23.4 권한/충돌 검토

- 이 변경은 SCALPING WATCHING pool throughput과 loop pressure 자동조절만 다룬다.
- BUY score, AI threshold, liquidity/latency/stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.
- watch cap을 낮추면 저우선순위 WATCHING 정리는 빨라질 수 있으므로, 다음 루프에서 `rising_missed_symbol_count`, `refresh회복`, `stale_eval`, `scanner_fast_precheck_stability_pending`, `ws_snapshot_missing_or_zero`를 같이 본다.
- `operator_runtime_overrides.env`는 `.gitignore` 대상이라 커밋에는 직접 포함되지 않는다. 지속성은 런타임 파일 자체와 이 수정목록 문서로 관리한다.

### 23.5 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'scalping_fifo_max_active_env or scalping_dynamic_watch_cap or scanner_rest_quote_budget_hot_reloads_operator_override_file or scanner_full_eval_pressure'`
  - `8 passed, 145 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 통과
- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과

### 23.6 런타임 후속

- 이번 변경은 코드 deploy가 필요하므로 기존 PID에는 hot reload가 적용되지 않는다.
- review gate 및 `git diff --check` 통과 후 `restart.flag` 방식의 우아한 재기동을 사용한다.

### 23.7 12:30 재기동 전 flow 기준선

- 11:30 이후 flow:
  - `symbol_count=108`
  - `rising_symbol_count_by_max_delta=29`
  - `rising_missed_symbol_count_in_report=31`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=1`
  - `stale_eval_symbol_count=69`
  - `rising_stale_eval_symbol_count=23`
  - `stale_refresh_recovered_symbol_count=53`
- 08:00 이후 누적 참조 flow:
  - `symbol_count=451`
  - `rising_symbol_count_by_max_delta=89`
  - `rising_missed_symbol_count_in_report=74`
  - `buy_signal_or_pre_submit_pass_seen_symbols=27`
  - `stale_eval_symbol_count=213`
  - `rising_stale_eval_symbol_count=76`
  - `stale_refresh_recovered_symbol_count=198`
- 판정:
  - p3 이후 refresh 회복 표본은 늘었지만 재기동 전까지 stale source는 계속 증가했다.
  - p4 코드 반영 후 다음 루프에서 watch cap base/min이 `20/12`로 읽히는지와 loop spike가 줄어드는지를 확인한다.

## 24. 12:41 p4 반영 후 루프 관측

작성 시각: `2026-06-29 12:42 KST`

### 24.1 재기동 및 runtime 반영

- 재기동:
  - 방식: `./restart.sh` 기반 `restart.flag` 우아한 재기동
  - PID: `79579 -> 87721`
  - 새 PID 시작: `Mon Jun 29 12:31:39 2026`
  - runtime env handoff: `passed=true`, `missing_family_count=0`, `pid_passed=true`
- 새 PID env 확인:
  - `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=20`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=10000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=20`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=4`

### 24.2 p4 효과

- 새 PID 로그:
  - `12:30:40 loop_elapsed_ms=14351.1 target_count=20 watching=16`
  - `12:33:21 [SCALPING_DYNAMIC_WATCH_CAP] action=reduce ... base_cap=20 effective_cap=17 min_cap=12`
  - `12:33:21 [SCANNER_FULL_EVAL_PRESSURE] action=reduce ... effective_limit=6 min_limit=4`
  - `12:33:55 [SCALPING_DYNAMIC_WATCH_CAP] action=reduce ... effective_cap=14 min_cap=12`
  - `12:33:55 [SCANNER_FULL_EVAL_PRESSURE] action=reduce ... effective_limit=4 min_limit=4`
  - `12:34:23 [SCALPING_DYNAMIC_WATCH_CAP] action=reduce ... effective_cap=12 min_cap=12`
  - `12:41:19 loop_elapsed_ms=4252.6 target_count=16 watching=12`
- 판정:
  - p4는 런타임에 반영되었고 watch cap governor가 `20 -> 12`까지 감압했다.
  - loop spike는 재기동 직후 한 차례 남았지만, cap 최저값 도달 뒤 12:41 루프는 4.2초로 안정됐다.
  - 따라서 기존 `full-eval pressure + watch pool pressure` 병목은 해소 방향으로 이동했다.

### 24.3 12:41 flow

- 11:30 이후 flow:
  - `symbol_count=115`
  - `rising_symbol_count_by_max_delta=31`
  - `rising_missed_symbol_count_in_report=32`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=1`
  - `stale_eval_symbol_count=76`
  - `rising_stale_eval_symbol_count=24`
  - `stale_refresh_recovered_symbol_count=59`
- 08:00 이후 누적 참조 flow:
  - `symbol_count=451`
  - `rising_symbol_count_by_max_delta=90`
  - `rising_missed_symbol_count_in_report=74`
  - `buy_signal_or_pre_submit_pass_seen_symbols=27`
  - `stale_eval_symbol_count=218`
  - `rising_stale_eval_symbol_count=77`
  - `stale_refresh_recovered_symbol_count=201`

### 24.4 다음 major blocker

- 실제 submit은 여전히 0건이다.
- 11:30 이후 rising blocker는 다음으로 이동했다.
  - `blocked_strength_momentum/below_buy_ratio`
  - `blocked_strength_momentum/insufficient_history`
  - `blocked_strength_momentum/below_strength_base`
  - `blocked_overbought/below_window_buy_value`
  - `ai_confirmed/blocked_ai_score_below_buy_score_threshold`
- stale category는 아직 전부 `diagnostic_quote_age_stale`다.
- 다음 루프에서는 fresh-only 표본과 stale-mixed 표본을 분리해, strength/AI blocker가 중복 또는 과도한 차단인지 확인한다. stale submit hard block은 계속 유지한다.

## 25. 12:45 fresh-only/stale-mixed blocker 관측 보강

작성 시각: `2026-06-29 12:46 KST`

### 25.1 코드 수정

- 파일:
  - `src/engine/monitoring/intraday_entry_flow_report.py`
  - `src/tests/test_intraday_entry_flow_report.py`
- 변경:
  - summary에 `rising_fresh_only_symbol_count`를 추가했다.
  - markdown/report에 `rising fresh-only blocker rollup`과 `rising stale-mixed blocker rollup`을 추가했다.
  - 기존 stale category와 refresh recovered 분류는 유지했다.
- 목적:
  - blocker downsizing 검토 전에 fresh-only 표본과 stale-mixed 표본을 자동으로 분리한다.
  - stale가 섞인 strength/AI blocker를 바로 threshold 완화 근거로 쓰지 않도록 한다.

### 25.2 12:45 flow 기준선

- 11:30 이후 flow:
  - `symbol_count=118`
  - `rising_symbol_count_by_max_delta=31`
  - `rising_missed_symbol_count_in_report=32`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=1`
  - `stale_eval_symbol_count=77`
  - `rising_stale_eval_symbol_count=24`
  - `rising_fresh_only_symbol_count=7`
  - `stale_refresh_recovered_symbol_count=62`
- 08:00 이후 누적 참조 flow:
  - `symbol_count=452`
  - `rising_symbol_count_by_max_delta=90`
  - `rising_missed_symbol_count_in_report=74`
  - `buy_signal_or_pre_submit_pass_seen_symbols=27`
  - `stale_eval_symbol_count=219`
  - `rising_stale_eval_symbol_count=77`
  - `rising_fresh_only_symbol_count=13`
  - `stale_refresh_recovered_symbol_count=203`

### 25.3 fresh-only blocker

- 11:30 이후 rising fresh-only blocker:
  - `2: ai_confirmed / blocked_ai_score_below_buy_score_threshold`
  - `1: blocked_strength_momentum / insufficient_history`
  - `1: blocked_strength_momentum / below_strength_base`
  - `1: blocked_overbought / insufficient_history`
  - `1: blocked_overbought / -`
  - `1: ai_confirmed / below_buy_ratio`
- 판정:
  - fresh-only 기준으로는 `blocked_ai_score_below_buy_score_threshold`가 최상위지만 2건이라 아직 live threshold 완화 근거로 쓰기에는 얇다.
  - 다음 12:50 루프에서도 fresh-only AI score block이 반복되면, BUY threshold 변경이 아니라 score/action 재평가 또는 AI WAIT 재평가 cadence부터 검토한다.

### 25.4 p4 이후 loop 상태

- 새 PID p4 적용 뒤 주요 loop:
  - `12:41:19 loop_elapsed_ms=4252.6 target_count=16 watching=12`
  - `12:42:29 loop_elapsed_ms=6548.3 target_count=16 watching=12`
  - `12:43:53 loop_elapsed_ms=11081.5 target_count=13 watching=9`
  - `12:45:20 loop_elapsed_ms=8521.1 target_count=17 watching=13`
- 판정:
  - p4 이후 loop는 대체로 4~8초대까지 내려왔고, 12:43에 11초 한 번이 있었다.
  - WS prune burst는 남아 있으나 full-eval/watch cap pressure는 이전 30~80초대보다 완화됐다.

### 25.5 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py`
  - `5 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_flow_report.py`
  - 통과

## 26. 12:55 5분 루프 전환 및 attach burst pressure p6

작성 시각: `2026-06-29 12:59 KST`

### 26.1 목표 변경 반영

- 사용자 목표가 `14:00 종료`, `5분 단위 감시`로 변경되었다.
- 기존 13:00 대기 세션은 중단하고 즉시 12:55 기준 리포트/로그를 재생성했다.

### 26.2 12:55 관측

- 11:30 이후 flow:
  - `symbol_count=130`
  - `rising_symbol_count_by_max_delta=32`
  - `rising_missed_symbol_count_in_report=34`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=3`
  - `stale_eval_symbol_count=82`
  - `rising_stale_eval_symbol_count=24`
  - `rising_fresh_only_symbol_count=8`
  - `stale_refresh_recovered_symbol_count=71`
- 변화:
  - BUY/pre-submit 통과는 1개에서 3개로 늘었다.
  - 실제 submit은 여전히 0건이다.
  - fresh-only 최상위 blocker는 `ai_confirmed/blocked_ai_score_below_buy_score_threshold=2`로 유지되어 live threshold 완화 근거로는 아직 얇다.

### 26.3 p5 hot override

- 파일:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
- 추가 값:
  - `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=16`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=8`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=8000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS=4000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=10`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK=8`
- 효과:
  - hot reload로 `base_cap=16`, `min_cap=8`이 반영되었다.
  - `12:52:39 effective_cap=10`, `12:53:03 effective_cap=9`, `12:53:50 effective_cap=8`까지 감압했다.
- 한계:
  - `12:55:21 loop_elapsed_ms=27331.1 target_count=24 watching=20`이 재발했다.
  - 짧은 시간에 `SCALPING_SCANNER_PROMOTED_TARGET attached`가 burst로 발생하면서 기존 WATCHING이 FIFO로 정리되기 전에 pool이 다시 부풀었다.

### 26.4 코드 수정 p6

- 파일:
  - `src/engine/kiwoom_sniper_v2.py`
  - `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
- 추가 hot runtime key:
  - `KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED`
- 변경:
  - `_scalping_attach_replace_enabled()`를 추가했다.
  - `_scalping_attach_capacity_allows()`에서 현재 WATCHING 수가 effective cap 이상이고 replacement가 disabled이면, 신규 scanner attach를 즉시 skip한다.
  - 기존 기본값은 `true`라 기존 high-priority replacement 동작은 유지된다.
  - p6 runtime override에서만 `false`로 설정해 pressure 구간의 attach burst를 막는다.
- p6 hot override:
  - `KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED=false`
- rollback:
  - `KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED=true`

### 26.5 권한/충돌 검토

- 이 변경은 WATCHING attach pressure만 제한한다.
- BUY score, AI threshold, liquidity/latency/stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.
- 단점:
  - pressure 구간에서 일부 신규 scanner 후보는 attach 자체가 skip될 수 있다.
  - 그러나 기존 방식은 attach burst로 loop/stale가 재발하여 전체 BUY 제출 가능 경로를 막고 있었으므로, 5분 목표 루프에서는 submit-path 회복을 위해 attach burst 제한을 우선 적용한다.

### 26.6 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'scalping_scanner_promoted_target_blocks_capacity_replacement_when_hot_disabled or scalping_scanner_promoted_target_allows_higher_priority_capacity_candidate or scalping_fifo_max_active_env or scalping_dynamic_watch_cap'`
  - `6 passed, 148 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 통과
- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과

### 26.7 런타임 후속

- p6는 코드 배포가 필요하므로 review gate 통과 후 `restart.flag` 방식의 우아한 재기동을 사용한다.
- 새 PID에서 `KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED=false`가 들어갔는지 확인한다.
- 13:00 이후 5분 루프에서 attach burst skip 로그, loop time, BUY/pre-submit pass, 실제 submit 여부를 확인한다.

## 27. 13:04 submit stale 중복판정 p7

작성 시각: `2026-06-29 13:08 KST`

### 27.1 관측

- p6 배포/재기동:
  - commit `fbed53b3`
  - 새 PID `98342`
  - runtime env handoff `pass`
  - PID env에서 `KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED=false` 확인
- 13:03 11:30 이후 flow:
  - `symbol_count=139`
  - `rising_symbol_count_by_max_delta=32`
  - `rising_missed_symbol_count_in_report=35`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=4`
  - `stale_eval_symbol_count=89`
  - `rising_stale_eval_symbol_count=24`
  - `rising_fresh_only_symbol_count=8`
- submit-path 사례:
  - `화천기공(000850)`은 `ai_confirmed BUY score=80`, `entry_armed`, `budget_pass`, `latency_pass`까지 진행했다.
  - 그러나 `sniper_state_handlers` 로그에서 `[ENTRY_SUBMIT_REVALIDATION_BLOCK] ... warning=stale_context_or_quote`로 실제 submit 전 차단됐다.
  - event payload에는 `pre_submit_rest_orderbook_refresh_applied=True`, `pre_submit_rest_orderbook_refresh_age_ms=394.641`, `quote_consistency_reason=rest_only_fresh`, `quote_consistency_age_ms=394.568`가 있었지만 `quote_age_at_submit_ms=2085`만으로 stale warning이 남았다.

### 27.2 코드 수정 p7

- 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/tests/test_sniper_scale_in.py`
- 변경:
  - `_build_entry_submit_revalidation_fields()`에서 standard lifecycle에 한해 quote consistency가 runtime effect로 fresh context를 제공하고 entry block이 아니며 `quote_consistency_age_ms <= max_quote_age_ms`이면 WS quote stale 판정을 fresh quote consistency로 재평가한다.
  - stale hard guard를 끄지 않고, 이미 확보된 fresh REST/orderbook 기반 quote context를 submit revalidation 입력으로 인정한다.
  - quote consistency 자체가 entry block이면 기존 `quote_consistency_*` warning/block을 유지한다.
- 신규 관측 필드:
  - `entry_submit_revalidation_quote_freshness_override_applied`
  - `entry_submit_revalidation_quote_freshness_override_reason`
  - `entry_submit_revalidation_quote_consistency_age_ms`
- 권한/충돌:
  - BUY score, AI threshold, liquidity guard, broker/account/order/quantity/cooldown guard, provider route, order quantity, hard/protect/emergency stop은 변경하지 않는다.
  - passive probe stale-submit block은 기존 경로를 유지한다.

### 27.3 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k 'submit_revalidation or pre_submit_liquidity_relief'`
  - `17 passed, 280 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/tests/test_sniper_scale_in.py`
  - 통과
- `git diff --check`
  - 통과

### 27.4 p7 이후 관측

- commit:
  - `a1a1686c`
- 재기동:
  - 새 PID `100032`
- 13:10 `S-Oil(010950)` submit-path:
  - `ai_confirmed BUY score=74`
  - `latency_pass`
  - `entry_submit_revalidation_quote_freshness_override_applied=True`
  - `entry_submit_revalidation_warning=""`
  - `quote_stale_at_submit=False`
  - 다음 blocker는 `PRE_SUBMIT_LIQUIDITY_GUARD_BLOCK liquidity=272267400 min=350000000`
- 판정:
  - p7은 submit revalidation stale 중복판정을 실제 새 샘플에서 해소했다.
  - 실제 submit은 아직 0건이며, p7 이후 submit 직전 blocker는 stale가 아니라 pre-submit liquidity guard로 이동했다.
  - liquidity guard는 하드성 submit guard라 단일 샘플만으로 완화하지 않는다.

## 28. 13:18 11:30 이후 flow 시간창 보정 p8

작성 시각: `2026-06-29 13:19 KST`

### 28.1 관측

- `intraday_entry_flow_report --since 11:30` 실행 결과가 08:00 전체 집계와 동일하게 나왔다.
- 원인:
  - `src/engine/monitoring/intraday_entry_flow_report.py`의 `_parse_ts()`가 ISO datetime만 허용해 `11:30`, `08:00`, `13:18` 같은 time-only 입력을 파싱하지 못했다.
  - 그 결과 `since_ts=None`으로 처리되어 event/diagnostic 필터가 사실상 꺼졌고, 제목도 `전체 이후`로 출력됐다.
- 영향:
  - 목표 0번의 11:30 이후 감시대상 흐름 산출물이 과대 집계되어 blocker 판단을 왜곡했다.
  - 주문/threshold/provider/broker guard에는 영향이 없고 관측 산출물 정확도 문제다.

### 28.2 코드 수정 p8

- 파일:
  - `src/engine/monitoring/intraday_entry_flow_report.py`
  - `src/tests/test_intraday_entry_flow_report.py`
- 변경:
  - `_parse_ts(value, target_date=...)`가 ISO datetime을 우선 파싱하고, 실패 시 `HH:MM` 또는 `HH:MM:SS`를 `target_date` 당일 시각으로 해석한다.
  - `build_report()`, `_window_label()`, `_default_output_paths()`가 target date를 넘기도록 수정했다.
  - `--since 11:30`, `--generated-at 13:18`이 각각 필터/제목/기본 output path에 반영된다.
- 신규 테스트:
  - time-only `since`가 11:30 이전 diagnostic/event row를 제외하는지 확인.
  - time-only `since` 제목이 `11:30 이후`로 출력되는지 확인.
  - time-only `since`/`generated_at` 기본 파일명이 `1130_to_1318`로 생성되는지 확인.

### 28.3 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py`
  - `8 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_flow_report.py`
  - 통과
- `git diff --check`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - `count=25`

### 28.4 재생성 결과

- 13:20 11:30 이후 flow:
  - 최신 diagnostic: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1319_1130_goal.json`
  - `symbol_count=223`
  - `rising_symbol_count_by_max_delta=38`
  - `rising_missed_buy_count_in_latest_diagnostic=45`
  - `rising_missed_symbol_count_in_report=39`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `buy_signal_or_pre_submit_pass_seen_symbols=6`
  - `stale_eval_symbol_count=101`
  - `rising_stale_eval_symbol_count=28`
  - `rising_fresh_only_symbol_count=10`
  - `stale_refresh_recovered_symbol_count=91`
- rising fresh-only blocker:
  - `2: scalping_scanner_watching_runtime_skip / scanner_fast_precheck_stability_pending`
  - `2: ai_confirmed / blocked_ai_score_below_buy_score_threshold`
  - `1: blocked_strength_momentum / insufficient_history`
  - `1: blocked_strength_momentum / below_strength_base`
  - `1: ai_confirmed / first_ai_wait_big_bite_not_confirmed`
  - `1: blocked_overbought / -`
  - `1: ai_confirmed / below_buy_ratio`
  - `1: ai_confirmed_terminal_no_budget / below_buy_ratio`
- 판정:
  - 11:30 이후 시간창 기준으로 fresh-only threshold 완화 근거는 아직 2건이라 약하다.
  - p7 이후 stale submit block은 새 샘플에서 해소됐고, submit 직전 병목은 liquidity guard로 이동했다.
  - 최신 diagnostic root priority는 `scanner_strength_history_or_stale_eval`이며, 다음 루프에서는 `scanner_fast_precheck_stability_pending`/`ws_snapshot_missing_or_zero`가 fresh-only에도 남는 원인을 먼저 본다.

## 29. 13:25 dynamic watch cap hot-min 반영 p9

작성 시각: `2026-06-29 13:25 KST`

### 29.1 관측

- p6/p8 이후 loop는 대체로 안정화됐지만 `SCALPING_SCANNER_PROMOTED_TARGET skipped ... reason=scalping_dynamic_watch_cap_capacity cap=8`가 반복됐다.
- 13:20~13:25 주요 로그:
  - `13:20:32 loop_elapsed_ms=5273.4 target_count=12 watching=8 holding=4`
  - `13:21:55 loop_elapsed_ms=13843.1 target_count=12 watching=8 holding=4`
  - `13:23:13 loop_elapsed_ms=21120.4 target_count=12 watching=8 holding=4`
  - `13:24:20 loop_elapsed_ms=27210.1 target_count=12 watching=8 holding=4`
  - 같은 구간 scanner attach skip은 계속 `cap=8`로 찍혔다.
- p9 hot override:
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=10`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=12000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS=7000`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=5`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK=2`
- 문제:
  - hot override parser는 마지막 값을 정상 파싱하지만, 기존 `_SCALPING_DYNAMIC_WATCH_CAP_STATE["effective_cap"]=8`이 새 `min_cap=10` 아래로 남아 있었다.
  - `_scalping_dynamic_watch_cap_effective()`가 기존 effective cap을 새 min cap으로 clamp하지 않아 hot min 상승이 즉시 반영되지 않았다.

### 29.2 코드 수정 p9

- 파일:
  - `src/engine/kiwoom_sniper_v2.py`
  - `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
- 변경:
  - `_scalping_dynamic_watch_cap_effective()`에서 기존 effective cap을 현재 base/min 범위로 clamp한다.
  - hot override로 `DYNAMIC_MIN_ACTIVE`가 올라가면 기존 effective cap이 새 min 아래에 고정되지 않고 즉시 min으로 보정된다.
- 권한/충돌:
  - scanner watchlist pool pressure relief에 한정한다.
  - BUY score, AI threshold, stale-submit, liquidity/latency, broker/account/order/quantity/cooldown guard, provider route, order price, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.

### 29.3 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'scalping_dynamic_watch_cap or scalping_scanner_promoted_target_blocks_capacity_replacement_when_hot_disabled or scalping_scanner_promoted_target_allows_higher_priority_capacity_candidate'`
  - `6 passed, 149 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 통과

### 29.4 런타임 후속

- 코드 반영이 필요하므로 review gate 통과 후 `restart.flag` 방식으로 우아한 재기동한다.
- 새 PID에서 p9 hot override가 반영되어 cap이 10 이상으로 올라가는지 확인한다.

## 30. 13:35 dynamic watch cap 후속 hot override p10

### 30.1 관측

- `restart.flag` 기반 우아한 재기동 후 새 PID `109469`에서 p9 env handoff는 통과했다.
- 13:30 이후 이벤트 기준:
  - `scalping_scanner_runtime_target_attach` 19건 중 12건이 `runtime_target_attach_reason=scalping_dynamic_watch_cap_capacity`.
  - capacity skip은 `scanner_attach_capacity_cap=10`, `scanner_attach_capacity_watching_count=10`으로 찍혔다.
  - 같은 구간 실제 submit 관측은 0건이며, AI 평가까지 간 fresh/혼합 표본은 주로 `WAIT`/score 58~66으로 종료됐다.
- p9는 cap=8 고착 문제를 해소했지만, 신규 상승 후보가 cap=10에서 다시 감시열 진입 전에 막히는 병목이 남았다.

### 30.2 조치

- 파일:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
- 변경:
  - EOF effective override로 `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12`를 추가했다.
  - base `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=16` 범위 안의 bounded relief이며 attach replacement는 계속 비활성 상태로 둔다.
- 권한/충돌:
  - 기존 p9와 같은 scanner watchlist pool pressure relief 축의 후속 조치다.
  - BUY score, AI threshold, stale-submit, liquidity/latency, broker/account/order/quantity/cooldown guard, provider route, order price, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.

### 30.3 검증

- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과
- 단순 last-wins 파싱:
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12`

### 30.4 런타임 후속

- hot override 파일 경로이므로 우선 재기동 없이 다음 루프의 `scanner_attach_capacity_cap`이 12로 올라가는지 확인한다.
- 반영되지 않으면 `restart.flag` 방식으로만 우아한 재기동한다.
- 13:35~13:40 관측:
  - `scalping_scanner_runtime_target_attach` 46건 중 18건이 계속 `scalping_dynamic_watch_cap_capacity`.
  - capacity skip은 계속 `scanner_attach_capacity_cap=10`, `scanner_attach_capacity_watching_count=10`으로 찍혔다.
  - 같은 구간 `져스텍(153890)`은 `ai_confirmed BUY score=78`까지 갔지만 `quote_stale=True`, `quote_age_ms=4955` 상태였고 submit 관측은 없었다.
  - 따라서 p10 파일 값은 last-wins 기준 `12`로 정리됐지만, 13:40 목표 종료 전 런타임 이벤트 반영 증거는 확보하지 못했다.
- 13:40 목표 종료 조건 때문에 추가 감시/restart는 수행하지 않았다. 다음 세션에서 이 목표를 이어갈 경우 첫 조치는 `restart.flag` 우아한 재기동 후 `scanner_attach_capacity_cap=12` 반영 여부 확인이다.

## 31. 13:45 restart 후 cap=12 반영 및 져스텍 stale/fresh 관측 보강 p11

### 31.1 관측

- `restart.flag` 방식으로 재기동했고 새 PID는 `115839`다.
- 새 PID 환경:
  - `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=16`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED=true`
  - `KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED=false`
- 13:45 이후 `scalping_scanner_runtime_target_attach` 이벤트:
  - `new_watching_target_attached=7`
  - `scalping_dynamic_watch_cap_capacity=4`
  - capacity skip은 `scanner_attach_capacity_cap=12`, `scanner_attach_capacity_watching_count=12`로 찍혀 p10 반영을 확인했다.
- 져스텍(`153890`) 경로:
  - 13:35에는 `ai_confirmed BUY score=78`, AI 입력 `quote_stale=True`, `quote_age_ms=4955`.
  - pre-submit 단계에서는 `pre_submit_ws_snapshot_refresh_applied=True`, `quote_stale=False`, `quote_consistency_entry_blocked=False`로 fresh quote 회복이 됐다.
  - 최종 차단은 stale submit block이 아니라 `latency_block`, `latency_state=DANGER`, `reason=latency_state_danger`였다.
  - 기존 snapshot에는 AI 입력 당시 `quote_age_ms=4955`와 pre-submit fresh 재평가가 섞여 남아 리포트가 stale 차단과 latency 차단을 혼동할 수 있었다.

### 31.2 코드 수정 p11

- 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/tests/test_sniper_entry_latency.py`
- 변경:
  - `_pre_submit_effective_quote_log_fields()`를 추가했다.
  - `latency_block` 이벤트와 `scalp_entry_action_decision_snapshot`에 아래 관측 필드를 추가한다.
    - `pre_submit_effective_quote_stale`
    - `pre_submit_effective_quote_age_ms`
    - `pre_submit_effective_quote_age_source`
    - `pre_submit_ai_input_quote_stale`
    - `pre_submit_ai_input_quote_age_ms`
    - `pre_submit_refresh_recovered_stale_ai_context`
- 목적:
  - stale AI 입력이 fresh pre-submit refresh로 회복됐는지 명시한다.
  - refresh 이후에도 차단된 경우 stale submit blocker가 아니라 latency/spread/other danger blocker로 분류할 수 있게 한다.
- 권한/충돌:
  - 관측 보강 전용이다.
  - BUY score, AI threshold, latency guard, stale submit block, broker/account/order/quantity/cooldown guard, provider route, order price, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.
  - `quote_stale=False`로 재평가된 사실을 기록할 뿐, stale submit guard를 우회하지 않는다.

### 31.3 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_entry_latency.py -k 'pre_submit_effective_quote_fields or real_pre_submit_ws_snapshot_refresh_uses_fresh_ws_manager_snapshot'`
  - `3 passed, 79 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_entry_latency.py`
  - `82 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/tests/test_sniper_entry_latency.py`
  - 통과
- `git diff --check`
  - 통과

### 31.4 런타임 후속

- 코드 반영을 위해 review-gate 통과 후에만 `restart.flag` 방식으로 우아한 재기동한다.
- 다음 관측에서는 져스텍과 유사한 BUY+stale AI 입력 케이스가 `pre_submit_refresh_recovered_stale_ai_context=True`로 찍히고, 최종 차단이 latency/spread인지 stale인지 분리되는지 확인한다.

## 32. 14:00 stale_or_delayed_eval 분해 p12

작성 시각: `2026-06-29 14:00 KST`

### 32.1 관측

- 13:40~14:00 루프에서 실제 real submit/fill은 1건으로 증가했다.
  - `LG에너지솔루션(373220)`은 `ai_confirmed BUY score=83 -> entry_armed -> budget_pass -> latency_pass -> order_bundle_submitted -> holding_started`까지 연결됐다.
- 13:40 이후 기준 `falling_real_submitted_count=0`으로 승격시점 대비 하락 submit 유형은 아직 관측되지 않았다.
- `stale_or_delayed_eval`은 반복 major blocker로 남았지만, 기존 요약이 원인별로 분해되지 않아 full-eval delay, WS quote 결손, pre-AI stale/history gap, pre-submit hard stale, 단순 diagnostic quote-age stale를 구분하기 어려웠다.

### 32.2 코드 수정 p12

- 파일:
  - `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - `src/tests/test_intraday_entry_blocker_diagnostics.py`
- 변경:
  - `stale_or_delayed_eval` 하위 원인을 `diagnostic_quote_age_stale`, `full_eval_delay`, `ws_quote_missing`, `pre_ai_stale_or_history_gap`, `pre_submit_hard_stale`로 분해한다.
  - `rising_missed_stale_or_delayed_eval_category_counts`를 summary와 root-cause evidence에 추가했다.
  - `entry_submit_revalidation_warning`을 blocker reason resolver에 추가해 pre-submit hard stale rows가 reason 없이 누락되지 않게 했다.
- 권한/충돌:
  - 진단/관측 보강 전용이다.
  - BUY score, AI threshold, order price, stale-submit hard guard, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않는다.

### 32.3 검증 및 14:00 산출물

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_blocker_diagnostics.py`
  - `20 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 통과
- 14:00 diagnostic:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1400_1340_goal.json`
  - `real_submit_symbol_count=1`
  - `rising_missed_buy_count=16`
  - `rising_missed_full_eval_budget_deferred_count=0`
  - `rising_missed_stale_or_delayed_eval_category_counts={diagnostic_quote_age_stale:56, full_eval_delay:0, ws_quote_missing:0, pre_ai_stale_or_history_gap:3, pre_submit_hard_stale:0}`
- 14:00 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_1340_to_1400.md`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 같은 diagnostic 기준으로 갱신했다.

### 32.4 판정

- 반복 major blocker는 실제 pre-submit hard stale가 아니라 대부분 diagnostic quote-age stale로 분해됐다.
- full-eval delay와 WS quote missing은 14:00 summary 기준 stale_or_delayed 하위 원인에서는 0이고, full-eval deferred도 13:40 이후 창에서는 0건이다.
- 다음 루프는 diagnostic stale가 실제 stale submit 차단인지, pre-AI 이벤트의 오래된 age 필드가 fresh refresh 이후에도 max-age 방식으로 과대 집계되는지 확인한다.

## 33. 14:10 fast-precheck history provenance 전파 p13

작성 시각: `2026-06-29 14:15 KST`

### 33.1 관측

- 14:10 diagnostic 기준 반복 major blocker는 계속 `scanner_strength_history_or_stale_eval`이었지만, p12 분해 결과는 다음과 같았다.
  - `full_eval_delay=0`
  - `ws_quote_missing=0`
  - `pre_submit_hard_stale=0`
  - `pre_ai_stale_or_history_gap=6`
  - 대부분은 `diagnostic_quote_age_stale=90`
- `서산(079650)`, `동아엘텍(088130)`에서 직전 `scalping_scanner_fast_precheck`는 `ws_strength_history_count > 0`을 기록했지만, 이어지는 `scalping_scanner_watching_runtime_skip`은 `ws_strength_history_count=0`으로 남아 repeated zero-history workorder로 집계될 수 있었다.
- 이는 stale quote hard guard가 아니라 fast-precheck 관측 payload가 skip 이벤트에 전달되지 않는 진단 provenance gap이다.

### 33.2 코드 수정 p13

- 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/kiwoom_sniper_v2.py`
  - `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - `src/tests/test_state_handler_fast_signatures.py`
  - `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
- 변경:
  - `_defer_emit_scanner_fast_precheck()`가 계산한 fast-precheck fields를 stock에 보관한다.
  - fast-precheck not-eligible skip 이벤트에 `fast_precheck_fields`를 전달한다.
  - `scalping_scanner_watching_runtime_skip` 이벤트에 아래 observation-only provenance 필드를 추가한다.
    - `fast_precheck_observed_ws_strength_history_count`
    - `fast_precheck_observed_ws_last_strength_history_age_ms`
    - `fast_precheck_observed_quote_age_ms`
    - `fast_precheck_observed_quote_age_source`
    - `fast_precheck_observed_snapshot_source`
    - `fast_precheck_observed_result`
    - `fast_precheck_observed_reason`
  - diagnostics는 `fast_precheck_observed_ws_strength_history_count`가 양수이면 skip 이벤트의 `ws_strength_history_count=0`만으로 zero-history source-quality workorder를 만들지 않는다.
- 권한/충돌:
  - 관측/진단 보강 전용이다.
  - BUY score, AI threshold, order price, quantity/cap, provider route, broker/account/order/cooldown guard, stale-submit hard guard, hard/protect/emergency stop은 변경하지 않는다.
  - p12 stale_or_delayed_eval 분해와 충돌하지 않고, p12의 `pre_ai_stale_or_history_gap` 중 진단 provenance gap을 축소하는 후속 수정이다.

### 33.3 검증 계획

- targeted pytest:
  - `src/tests/test_state_handler_fast_signatures.py`
  - `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - `src/tests/test_kiwoom_sniper_market_regime_runtime.py -k scanner_fast_precheck_not_eligible`
- `py_compile`
- `git diff --check`
- 검증 후 runtime 반영이 필요한 경우에만 `restart.flag` 방식으로 우아한 재기동한다.

### 33.4 검증 결과

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_state_handler_fast_signatures.py -k 'scanner_watching_runtime_skip or scanner_fast_precheck'`
  - `19 passed, 114 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_blocker_diagnostics.py`
  - `21 passed`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'scanner_fast_precheck_not_eligible or scalping_scanner_promoted_target_refresh_resets_eval_state'`
  - `2 passed, 153 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/engine/kiwoom_sniper_v2.py src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 통과
- `git diff --check`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - parser 통과, backlog count `25`

### 33.5 자체 리뷰 판정

- review-gate 결과 추가 결함 1건을 발견해 보완했다.
  - `_scanner_fast_precheck_fields`가 promotion refresh 후에도 남을 수 있어 `_reset_scanner_runtime_eval_state()` 제거 목록에 추가했다.
  - 기존 refresh reset 테스트에 해당 내부 키 제거 검증을 추가했다.
- 재리뷰 결과 런타임/order/provider/threshold 권한 누수는 없다.
- runtime 반영을 위해 검증 후 `restart.flag` 방식의 우아한 재기동 대상이다.

## 34. Entry Price 0원 핸드오프 복원 p14

작성 시각: `2026-06-29 15:00 이후 KST`

### 34.1 관측

- `entry_ai_price_canary` 진입 시 `current_price`, `best_bid`, `best_ask`는 유효하지만 `defensive_order_price`, `reference_price`, `resolved_order_price`, `planned_order_price`가 모두 0인 실주문 후보가 확인됐다.
- 이 케이스는 주문가 완화 대상이 아니라, latency/budget 경로 이후 real submit 후보에서 누락된 defensive order price/order plan handoff를 복원해야 하는 contract gap으로 분류한다.

### 34.2 코드 수정 범위

- 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/tests/test_sniper_scale_in.py`
- 변경:
  - `USE_DEFENSIVE` action 한정 zero-price recovery helper를 추가했다.
  - `best_bid > 0`, `current_price > 0`, `best_ask == 0 or best_bid <= best_ask` 조건에서만 후보 가격을 만든다.
  - `entry_price_gap_profile_bps > 0`이면 기존 fresh defensive price 재계산을 사용하고, 없으면 `best_bid` tick clamp 가격을 사용한다.
  - real submit path는 canary에 `requested_qty`와 real subject 여부만 넘기고, canary 내부에서 AI action이 `USE_DEFENSIVE`로 확정된 뒤 `planned_orders`가 비어 있고 `requested_qty > 0`이며 real scalping subject인 경우에만 DAY LIMIT 1개를 복원한다.
  - 복원 후보 가격이 `above_best_ask` 또는 pre-submit price guard 등에 걸리면 주문을 만들지 않고 기존 `entry_ai_price_canary_fallback` 또는 `entry_price_order_contract_gap`으로 fail-closed한다.

### 34.3 관측 provenance

- 추가 필드:
  - `entry_price_zero_context_recovered`
  - `entry_price_zero_context_recovery_reason`
  - `entry_price_zero_context_basis_price`
  - `entry_price_zero_context_candidate_price`
  - `entry_price_zero_context_planned_order_rebuilt`
  - `entry_price_zero_context_forbidden_uses`
- forbidden uses:
  - stale submit bypass
  - broker guard bypass
  - threshold mutation
  - order-price relaxation beyond defensive recovery

### 34.4 권한/금지

- threshold, AI score, provider route, quantity cap, broker/account/order/cooldown guard, stale quote guard, hard/protect/emergency stop은 변경하지 않는다.
- 복원 가격은 aggressive ask chasing이 아니라 defensive/bid-side recovery로 제한한다.
- 복원된 주문도 기존 `above_best_ask`, pre-submit price guard, submit revalidation, broker/account/order/quantity/cooldown guard를 그대로 통과해야 한다.

### 34.5 검증 계획

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k 'entry_ai_price_canary or pre_submit_price_guard'`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_entry_latency.py -k 'price_guard or defensive_order_price or quote_fresh_composite'`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/tests/test_sniper_scale_in.py src/tests/test_sniper_entry_latency.py`
- `git diff --check`
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`

### 34.6 검증 결과

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k 'entry_ai_price_canary or pre_submit_price_guard'`
  - `10 passed, 292 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_entry_latency.py -k 'price_guard or defensive_order_price or quote_fresh_composite'`
  - `5 passed, 77 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/tests/test_sniper_scale_in.py src/tests/test_sniper_entry_latency.py`
  - 통과
- `git diff --check`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - parser 통과, backlog count `22`

### 34.7 자체 리뷰 판정

- review-gate 1차에서 `planned_orders` 복원이 AI action 확정 전이면 `USE_DEFENSIVE` 한정 원칙을 엄밀히 만족하지 못하는 결함을 발견했다.
- 보완:
  - real submit path는 canary에 `requested_qty`와 real subject 여부만 전달한다.
  - canary 내부에서 `USE_DEFENSIVE` action, zero-price handoff, fresh bid/current 조건, price guard 통과가 모두 확인된 뒤에만 empty planned order를 복원한다.
- 재리뷰 결과:
  - threshold/provider/quantity cap 변경 없음.
  - stale quote, broker/account/order/cooldown, pre-submit price guard, hard/protect/emergency stop 우회 없음.
  - 복원 실패 또는 canary 거절 시 fail-closed한다.

## 35. 15:00 이후 watch cap tail relief 및 buy-window 마감 관측

작성 시각: `2026-06-29 15:20 이후 KST`

### 35.1 산출물

- 최신 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1520_1500_goal.json`
- 최신 flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_1500_to_1520.csv`
  - 사용자 지정 누적 참조 파일 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`도 15:00 이후 기준으로 갱신했다.

### 35.2 15:00 이후 판정

- `promoted_symbol_count=43`
- `rising_missed_buy_count=10`
- `real_submit_symbol_count=0`
- `falling_real_submitted_count=0`
- flow summary:
  - `symbol_count=20`
  - `rising_symbol_count_by_max_delta=8`
  - `rising_missed_symbol_count_in_report=8`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
  - `stale_eval_symbol_count=14`
  - `rising_stale_eval_symbol_count=7`
  - `rising_fresh_only_symbol_count=1`
  - `stale_refresh_recovered_symbol_count=12`
- `rising_missed_stale_or_delayed_eval_category_counts`:
  - `diagnostic_quote_age_stale=91`
  - `pre_ai_stale_or_history_gap=3`
  - `full_eval_delay=0`
  - `ws_quote_missing=0`
  - `pre_submit_hard_stale=0`

### 35.3 반복 blocker 및 조치

- 15:00~15:09 로그에서 `SCALPING_SCANNER_PROMOTED_TARGET skipped ... reason=scalping_dynamic_watch_cap_capacity cap=12`가 반복됐다.
- 단순 재진단 대신 hot runtime tail relief를 적용했다.
- 파일:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env` (`.gitignore` 대상 runtime env, 커밋 대상 아님)
- 최종 effective tail:
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=16`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=18000`
- rollback:
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=12000`
- 검증:
  - `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - hot parser readback: `min_active=16`, `pressure_ms=18000`

### 35.4 조치 후 관측

- 15:10:37에 신규 scanner 승격 3개가 attach됐다.
- 15:11~15:17 loop는 `16879.8ms -> 15980.8ms -> 9144.9ms -> 18502.3ms -> 29479.8ms -> 13247.2ms`로 30초 이상 반복 조건은 충족하지 않았다.
- 15:20 직전 `SCANNER_FULL_EVAL_PRESSURE`가 full-eval limit을 자동으로 줄였고, 15:20:16 loop는 `6510.1ms`로 회복됐다.
- 따라서 `restart.flag` 재기동은 수행하지 않았다.

### 35.5 남은 병목과 안전 경계

- 15:00 이후 상승 미체결의 직접 blocker는 `blocked_ai_score`, `first_ai_wait_big_bite_not_confirmed`, `blocked_strength_momentum`, `blocked_overbought`, `entry_ai_price_canary_fallback:invalid_price`로 이동했다.
- `diagnostic_quote_age_stale`가 여전히 많지만 `pre_submit_hard_stale=0`, `ws_quote_missing=0`이므로 stale submit block을 완화하지 않는다.
- 15:13 `LG에너지솔루션(373220)`은 `scalp_trailing_take_profit`으로 `+1.05%` 청산됐고, 15:00 이후 신규 손절 분석 대상은 없었다.
- scale-in은 `executed_count=0`, 주요 blocker는 `profit_not_enough`와 `pnl_out_of_range` 계열이다. quantity cap release, scale-in guard bypass, hard/protect/emergency stop 완화는 하지 않았다.
- 15:20 이후는 buy window 밖으로 판단해 추가 감시/변경을 일시정지한다.

## 36. zero-context blocker 관측 보강

작성 시각: `2026-06-29 KST`

### 36.1 배경

- `entry_ai_price_canary` 0원 handoff 패치 이후, 가격 외 수량/WS/scanner source/strength-momentum 영역에서도 `0` 값이 block/fallback/skip/fail에 연결되는지 확인할 필요가 있다.
- 이번 변경은 guard 완화가 아니라 관측 보강이다. `actual_zero`, `missing_defaulted_zero`, `stale_defaulted_zero`, `not_applicable_zero`, `guard_intended_zero`를 이벤트 필드에서 분리해 후속 버그픽스 후보를 판단할 수 있게 한다.

### 36.2 수정 범위

- `src/engine/sniper_state_handlers.py`
  - 공통 `zero_context_*` provenance helper 추가.
  - `scalping_scanner_watching_runtime_skip`에 WS/quote zero context 분류 추가.
  - `blocked_strength_momentum`에 strength/momentum zero context 분류 추가.
  - `blocked_zero_qty`/`auth_zero_qty`, `skip_order_leg_zero_qty`, `scale_in_qty_block`에 수량 zero context 분류 추가.
- `src/scanners/scalping_scanner.py`
  - `scalping_scanner_candidate_observed`와 `scalping_scanner_real_source_guard_block`에 scanner source zero context 분류 추가.
  - `cntr_str_available=False`와 `cntr_str=0.0`을 `missing_defaulted_zero`로 구분할 수 있게 했다.
- 테스트:
  - `src/tests/test_state_handler_fast_signatures.py`
  - `src/tests/test_scalping_scanner_candidate_pool.py`
  - `src/tests/test_sniper_scale_in.py`

### 36.3 추가 필드

- 공통:
  - `zero_context_observed`
  - `zero_context_domain`
  - `zero_context_blocker`
  - `zero_context_primary_state`
  - `zero_context_defaulted_zero_field_count`
  - `zero_context_forbidden_uses`
- 도메인별:
  - `zero_context_ws_curr_state`, `zero_context_ws_received_type_count_state`, `zero_context_ws_strength_history_count_state`
  - `zero_context_current_flu_rate_state`, `zero_context_rank_jump_state`, `zero_context_spike_rate_state`, `zero_context_cntr_str_state`
  - `zero_context_window_buy_value_state`, `zero_context_window_net_buy_qty_state`, `zero_context_window_buy_ratio_state`, `zero_context_sample_count_state`
  - `zero_context_qty_state`, `zero_context_template_qty_state`, `zero_context_would_qty_state`, `zero_context_effective_qty_state`, `zero_context_cap_qty_state`

### 36.4 권한/금지

- threshold, provider route, order price, quantity cap, broker/account/order/cooldown guard, stale quote guard, hard/protect/emergency stop은 변경하지 않는다.
- `zero_context_*`는 진단/후속 workorder 판단용이며 real execution quality approval이나 guard 완화 근거로 단독 사용하지 않는다.

### 36.5 검증 계획

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_state_handler_fast_signatures.py -k 'scanner_watching_runtime_skip or zero_context_strength_momentum'`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_scalping_scanner_candidate_pool.py -k 'real_source_guard or invalid_stock_filter'`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k 'dynamic_scale_in_qty_blocks_weak_pyramid_evidence'`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/scanners/scalping_scanner.py src/tests/test_state_handler_fast_signatures.py src/tests/test_scalping_scanner_candidate_pool.py src/tests/test_sniper_scale_in.py`
- `git diff --check`
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`

### 36.6 검증 결과

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_state_handler_fast_signatures.py -k 'scanner_watching_runtime_skip or zero_context_strength_momentum'`
  - `10 passed, 124 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_scalping_scanner_candidate_pool.py -k 'real_source_guard or invalid_stock_filter'`
  - `12 passed, 42 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k 'dynamic_scale_in_qty_blocks_weak_pyramid_evidence'`
  - `1 passed, 301 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_observation_source_quality_audit.py -k 'scanner_source_guard_contracts or blocked_strength_momentum'`
  - `1 passed, 67 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/scanners/scalping_scanner.py src/tests/test_state_handler_fast_signatures.py src/tests/test_scalping_scanner_candidate_pool.py src/tests/test_sniper_scale_in.py`
  - 통과
- `git diff --check`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - parser 통과, backlog count `22`

### 36.7 자체 리뷰 판정

- review-gate 1차에서 `buy_capacity`의 미적용 cap `0`이 `guard_intended_zero`로 보일 수 있는 관측 오분류를 발견했다.
- 보완:
  - cap이 적용되지 않은 경우 `not_applicable_cap_qty`로 기록해 `not_applicable_zero`로 분류되게 수정했다.
- 재리뷰 결과:
  - threshold/provider/order price/quantity cap 변경 없음.
  - stale quote, broker/account/order/cooldown, hard/protect/emergency stop 우회 없음.
  - 신규 `zero_context_*` 필드는 진단/후속 workorder 판단용 관측 필드이며, 기존 block/submit 판단은 변경하지 않는다.

## 37. 16:00 buy-window 정정 후 full-eval backlog relief

작성 시각: `2026-06-29 16:20 KST`

### 37.1 buy window 정정 및 루프 판정

- 사용자 정정 기준 buy window: `16:00~19:45 KST`.
- 16:00 이후는 buy window 안이므로 감시/변경을 재개했다.
- `outside_scalping_buy_window`는 16:00:02 경계 이벤트 1건만 확인됐고, operator env에는 이미 `16:00:00-19:45:00` window가 포함되어 있어 buy-window override는 추가하지 않았다.

### 37.2 갱신 산출물

- 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1600_1500_goal.json`
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1620_1500_goal.json`
- 고정 flow report:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_1500_to_1600.csv`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_1500_to_1620.csv`

### 37.3 16:20 진단 요약

- `entry_event_count=14358`
- `promoted_symbol_count=87`
- `real_submit_symbol_count=0`
- `rising_missed_buy_count=18`
- `buy_signal_or_pre_submit_pass_seen_symbols=0`
- `rising_missed_stale_or_delayed_eval_category_counts`:
  - `diagnostic_quote_age_stale=117`
  - `pre_ai_stale_or_history_gap=14`
  - `full_eval_delay=0`
  - `ws_quote_missing=0`
  - `pre_submit_hard_stale=0`
- root priority는 계속 `scanner_strength_history_or_stale_eval`이며, `top_symbols`는 `SK이터닉스(475150)`, `LS ELECTRIC(010120)`이다.
- rising missed의 low-AI/negative-pressure eval quality는 `fresh_eval=25`, `stale_or_delayed_eval=131`, `unknown_eval_quality=19`다.

### 37.4 반복 blocker 및 해소 조치

- 16:00~16:15 이벤트에서 반복 blocker:
  - `scanner_heavy_eval_stale_snapshot_recheck=114`
  - `scanner_fast_precheck_stability_pending=62`
  - `scanner_fast_precheck_subscription_recheck_snapshot_applied=32`
  - `scanner_full_eval_loop_budget_deferred=18`
  - `ws_snapshot_missing_or_zero=13`
- zero-context 분해:
  - `ws_quote/non_zero/scanner_heavy_eval_stale_snapshot_recheck=109`
  - `ws_quote/missing_defaulted_zero/ws_snapshot_missing_or_zero=13`
  - `ws_quote/stale_defaulted_zero/scanner_heavy_eval_stale_snapshot_recheck=5`
  - `strength_momentum/stale_defaulted_zero/stale_ws_snapshot=6`
  - `strength_momentum/stale_defaulted_zero/trade_tick_quiet=6`
- 조치:
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env` EOF에 full-eval backlog tail relief를 적용했다.
  - effective value: `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=0`
  - rollback: `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=2`
- 이 값은 full-eval pacing만 줄이는 hot-runtime pressure relief다. BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, watch attach cap, scale-in guard는 변경하지 않았다.

### 37.5 runtime 반영 확인

- hot parser readback:
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=8`
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=0`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=16`
  - `KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=18000`
- log 반영:
  - 16:01~16:13 `SCANNER_FULL_EVAL_PRESSURE base_limit=10`
  - 16:15:02 이후 `base_limit=8`
- `restart.flag`는 생성하지 않았다. hot runtime 반영이 확인됐고, 봇 프로세스 kill 조건도 없다.

### 37.6 남은 병목과 다음 루프

- 실제 submit/fill은 아직 없다.
- `pre_submit_hard_stale=0`, `ws_quote_missing=0`이므로 stale-submit guard 또는 broker guard 완화는 금지 유지한다.
- 다음 20분 루프에서는 `base_limit=8` 반영 후에도 `scanner_heavy_eval_stale_snapshot_recheck`와 `pre_ai_stale_or_history_gap`가 계속 증가하는지 확인한다.
- scale-in은 `executed_count=0`, 주요 blocker는 `profit_not_enough`, `flow_hold_interval`, `pnl_out_of_range` 계열이다. scale-in guard/quantity cap 완화는 하지 않았다.

## 38. delayed heavy-eval fresh subscription recheck 적용 위치 보완

작성 시각: `2026-06-29 16:40 KST`

### 38.1 배경

- 16:20 이후 `scanner_full_eval_loop_budget_deferred`는 감소했지만, `scanner_heavy_eval_stale_snapshot_recheck`, `ws_snapshot_missing_or_zero`, `rest_quote_without_realtime_strength`가 계속 반복됐다.
- 상세 이벤트에서 `ws_recovery_outcome=ws_snapshot_arrived_after_subscription_recheck`, `ws_subscription_recheck_status=subscribed_fresh_snapshot`, `ws_subscription_recheck_entry_realtime_fresh=True`인 케이스가 같은 루프에서 `scanner_heavy_eval_stale_snapshot_recheck`로 skip 기록되는 사례를 확인했다.
- root cause:
  - delayed heavy-eval flush에서 초기 recheck가 stale이라 repair 분기로 들어간 뒤, recovery 중 fresh subscription snapshot이 도착해도 snapshot 적용 helper를 호출하지 않고 skip 후 `continue`했다.

### 38.2 수정 범위

- `src/engine/kiwoom_sniper_v2.py`
  - delayed heavy-eval repair 분기에서 `_recover_missing_ws_snapshot()` 이후 `_apply_subscription_recheck_snapshot_if_ready(..., phase="heavy_eval_repair")`를 호출한다.
  - fresh subscription snapshot이 적용된 경우 `eval_ws_data`로 채택하고 heavy eval을 계속 진행한다.
  - 적용되지 않은 경우에만 기존처럼 `scanner_heavy_eval_stale_snapshot_recheck` skip을 기록하고 `continue`한다.
- `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - heavy-eval repair 경로에서 fresh subscription recheck 적용이 skip보다 먼저 위치하는지 확인하는 회귀 테스트를 추가했다.

### 38.3 권한/안전

- 이 변경은 fresh subscription snapshot을 이미 받은 경우의 적용 위치 보완이다.
- BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않았다.
- stale snapshot 자체를 통과시키지 않는다. 적용 조건은 기존 helper의 `subscribed_fresh_snapshot`, fresh age, positive `curr` 조건을 그대로 사용한다.

### 38.4 검증 결과

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'subscription_recheck_snapshot_is_applied_before_fast_precheck_retry or subscription_recheck_snapshot_is_applied_before_heavy_eval_recheck_skip'`
  - `2 passed, 154 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 통과
- `git diff --check`
  - 통과

### 38.5 runtime 반영 계획

- 코드 변경이므로 현재 실행 중인 봇에는 hot 반영되지 않는다.
- review-gate와 parser 검증 후, buy window 안에서 동일 blocker가 계속 반복되면 `restart.flag` 기반 우아한 재기동으로 반영한다.
- 직접 KILL은 검토하지 않는다.

### 38.6 runtime 반영 결과

- `./restart.sh`로 `restart.flag` 기반 우아한 재기동을 수행했다.
- old PID: `162571`
- new PID: `173143`
- `restart.flag`는 소모됐고, runtime env handoff verification은 `passed=true`, `pid_passed=true`다.
- `logs/bot_history.log` 기준:
  - `16:37:11` 스나이퍼 엔진 재가동
  - `16:37:11` 메인 관제탑 루프 진입
  - `16:37:13` WS 연결/로그인 성공
  - `16:37:13` 주문/체결통보 및 장운영구분 감시망 등록 완료
- KILL은 사용하지 않았다.

## 39. intraday_entry_flow 스냅샷 정리 및 미체결 취소 TR 수정

작성 시각: `2026-06-29 16:46 KST`

### 39.1 리포트 파일 관리 결정

- 사용자 요청에 따라 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`를 고정 갱신 대상 artifact로 유지한다.
- `data/report/intraday_entry_flow/intraday_entry_flow_*` timestamp 스냅샷은 고정 md 갱신 후 삭제 가능한 중간 산출물로 판정했다.
- 근거:
  - 원천 이벤트는 `data/pipeline_events`, `data/threshold_cycle`에 남는다.
  - 루프별 진단 JSON은 `data/report/intraday_entry_blocker_diagnostics/`에 별도 보존한다.
  - 목표 원칙 0의 필수 artifact는 고정 md 갱신이다.
- 조치:
  - 고정 md를 제외한 기존 timestamp flow md/csv 스냅샷을 삭제했다.
  - 이후 flow report는 `--output-md data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`, `--output-csv /tmp/...csv`로 실행하고 temp CSV를 삭제한다.

### 39.2 16:46 루프 관측

- `intraday_entry_blocker_diagnostics_2026-06-29_1646_1500_goal.json`
  - `promoted_symbol_count=87`
  - `real_submit_symbol_count=1`
  - `rising_missed_buy_count=17`
  - stale category:
    - `diagnostic_quote_age_stale=227`
    - `pre_ai_stale_or_history_gap=36`
    - `full_eval_delay=0`
    - `pre_submit_hard_stale=0`
    - `ws_quote_missing=0`
- fixed flow md 갱신 결과:
  - `symbol_count=28`
  - `rising_symbol_count_by_max_delta=10`
  - `real_submit_symbol_count_in_latest_diagnostic=1`
  - `rising_missed_buy_count_in_latest_diagnostic=17`
  - `stale_refresh_recovered_symbol_count=12`
- `--since 2026-06-29T15:00:00+09:00` 사용 시 `intraday_entry_flow_report`가 timezone-aware/naive 비교로 실패했다.
  - 이번 루프는 `--since 15:00`으로 우회했다.
  - 별도 report CLI robustness 보완 후보로 남긴다.

### 39.3 실제 submit 이후 미체결/취소 병목

- `올릭스(226950)`에서 재기동 후 실제 submit이 관측됐다.
  - `order_leg_request`: qty `8`, price `166300`, best bid `166800`, best ask `167300`, `price_below_bid_bps=30`, `quote_age_at_submit_ms=1683`
  - `order_leg_sent`: broker order no `0059624`
  - `order_bundle_submitted`: `actual_order_submitted=True`, `broker_order_submitted=True`, `quote_stale_at_submit=False`
- 이후 fill/HOLDING 전환은 관측되지 않았고, timeout cancel이 반복 실패했다.
  - `entry_order_cancel_failed`
  - message: `[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)`
- 같은 미체결 주문에 대한 cancel failure가 2회 이상 반복되어 단순 진단을 중단하고 root cause를 분해했다.

### 39.4 root cause 재확인 및 수정

- 사용자 지적 후 `docs/reference/키움 REST API 문서.xlsx`를 재확인했다.
  - `kt10002`: 주식 정정주문
  - `kt10003`: 주식 취소주문
- 따라서 `send_cancel_order()`의 `api-id=kt10003`은 맞고, 이전의 `kt10002` 변경 판단은 잘못된 판정이었다.
- 실제 root cause 후보:
  - `kt10003` 취소 body는 `dmst_stex_tp`, `orig_ord_no`, `stk_cd`, `cncl_qty`가 맞다.
  - 반복 실패 메시지 `[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)`는 SOR로 취소 요청했지만 원주문이 SOR로 인식되지 않는 거래소 구분 불일치 유형이다.
  - 기존 코드는 이 실패 후 같은 SOR 취소를 반복했다.
- 수정:
  - `src/utils/kiwoom_utils.py`
    - `ka10075` 미체결조회 helper `get_unfilled_order_snapshot_ka10075()`를 추가했다.
    - 주문 row 정규화에 `remaining_qty`, `stex_tp`, `stex_tp_txt`, `sor_yn`을 추가했다.
  - `src/engine/sniper_state_handlers.py`
    - `571412` SOR mismatch 실패에 한해 `ka10075` 미체결 스냅샷으로 원주문 거래소를 확인한다.
    - `sor_yn=N`이고 `stex_tp=1/2` 또는 거래소 텍스트로 `KRX/NXT`가 명확할 때만 해당 거래소로 1회 재취소한다.
    - `sor_yn=Y`이거나 거래소가 불명확하면 재시도하지 않고 `entry_order_cancel_exchange_resolution` 관측만 남긴다.
- 이 변경은 취소 주문의 broker API 계약 보정이다.
  - BUY score, AI threshold, order price, stale-submit, account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않았다.
  - stale quote 또는 broker guard를 우회하지 않는다.

### 39.5 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_orders.py -k 'send_cancel_order_uses_requested_exchange'`
  - `1 passed, 22 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k 'pending_entry_cancel'`
  - `6 passed, 298 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_orders.py src/tests/test_kiwoom_order_ref_snapshot.py src/tests/test_sniper_scale_in.py src/tests/test_intraday_entry_flow_report.py src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'send_cancel_order_uses_requested_exchange or unfilled_order_snapshot_ka10075_preserves_exchange_fields or pending_entry_cancel or offset_aware_since or time_only_since or filters_diagnostic_promotions or subscription_recheck_snapshot_is_applied_before_fast_precheck_retry or subscription_recheck_snapshot_is_applied_before_heavy_eval_recheck_skip'`
  - `15 passed, 480 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/tests/test_sniper_scale_in.py src/engine/kiwoom_orders.py src/tests/test_kiwoom_orders.py src/utils/kiwoom_utils.py`
  - 통과
- `git diff --check`
  - 통과

### 39.6 runtime 반영 계획

- 현재 실행 중인 봇은 아직 SOR mismatch 보정 없는 취소 경로를 사용 중이다.
- review-gate와 revalidation 통과 후 buy window 안에서 `restart.flag` 기반 우아한 재기동으로 반영한다.
- 직접 KILL은 사용하지 않는다.

### 39.7 flow report since 파싱 보강

- `--since 2026-06-29T15:00:00+09:00` 입력에서 `intraday_entry_flow_report`가 timezone-aware/naive 비교로 실패했다.
- 수정:
  - `src/engine/monitoring/intraday_entry_flow_report.py`의 `_parse_ts()`가 timezone-aware timestamp를 KST naive timestamp로 정규화하도록 보강했다.
  - `src/tests/test_intraday_entry_flow_report.py`에 offset-aware `--since` 회귀 테스트를 추가했다.
- 검증:
  - `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py -k 'offset_aware_since or time_only_since or filters_diagnostic_promotions'`
    - `5 passed, 4 deselected`
  - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_flow_report.py`
    - 통과
  - 실패했던 ISO KST since 명령으로 fixed flow md 갱신 재실행
    - 성공

### 39.8 runtime 반영 및 주문 결과

- `./restart.sh`로 `restart.flag` 기반 우아한 재기동을 수행했다.
- old PID: `173143`
- new PID: `179347`
- `restart.flag`는 소모됐고, runtime env handoff verification은 `passed=true`, `pid_passed=true`다.
- KILL은 사용하지 않았다.
- `올릭스(226950)` 주문 `0059624`는 재기동 직전 `16:53:01`에 전량 체결됐다.
  - `logs/bot_history.log`
    - `16:53:01` `[WS 주문상태] 226950 | 주문번호: '0059624' | 상태: '체결' | 구분: '+매수'`
    - `16:53:01` `[WS 실제체결] 226950 BUY 8주 @ 166300원 (주문번호: 0059624)`
  - `data/pipeline_events/pipeline_events_2026-06-29.jsonl`
    - `position_rebased_after_fill`: `fill_qty=8`, `remaining_qty=0`, `avg_buy_price=166300.00`, `fill_quality=FULL_FILL`
    - `holding_started`: `actual_order_submitted=True`, `buy_price=166300.00`, `buy_qty=8`, `fill_price=166300`, `fill_qty=8`
- 따라서 해당 표본은 `미체결 취소 실패 후 뒤늦은 전량체결/FULL_FILL` 유형으로 분류한다.
- 새 `ka10075` 기반 cancel exchange recovery는 이번 주문에는 사후 반영됐고, 다음 동일 `571412` 취소 실패 표본에서 검증한다.
- 재기동 후 `올릭스`는 `HOLDING` 흐름으로 관측되고 있으며, `stat_action_decision_snapshot` 기준 scale-in blocker는 `profit_not_enough`다. scale-in guard 또는 quantity cap은 변경하지 않았다.

## 40. persistent WS gap repair REG TTL hot 반영 보강

작성 시각: `2026-06-29 16:58 KST`

### 40.1 배경

- 16:56 진단 후 주요 blocker는 다시 `scanner_strength_history_or_stale_eval`로 이동했다.
- 대표 표본:
  - `SK이터닉스(475150)` `scanner_fast_precheck_stability_pending`
  - `ws_received_type_count=0`, `ws_strength_history_count=0`
  - `ws_recovery_outcome=rest_quote_applied_entry_realtime_still_stale`
  - `rest_quote_price_recovery_only=True`
  - `ws_repair_batch_queued=True`, `ws_repair_batch_force=True`
- root cause:
  - scanner WS repair cycle은 6~8초 단위로 동작하지만, `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=30`이 먼저 적용되어 persistent repair REG가 같은 코드에 대해 전송 전에 억제될 수 있다.
  - 해당 값은 `kiwoom_websocket.py`에서 `os.getenv()`만 읽어 hot runtime override 동적 반영 대상도 아니었다.

### 40.2 수정 및 override

- `src/engine/kiwoom_websocket.py`
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC`를 WS hot runtime override key family에 추가했다.
  - `_recent_reg_ttl_sec()`가 `_ws_hot_or_env_value()`를 사용하도록 변경했다.
- `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8`을 provenance/rollback과 함께 추가했다.
  - rollback: `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=30`
- 이 변경은 WS repair pacing과 quote/strength freshness 회복 전용이다.
  - BUY score, AI threshold, order price, stale-submit, account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, scale-in guard는 변경하지 않았다.

### 40.3 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_websocket.py -k 'recent_reg_filter or persistent_repair_passes_repair_cycle'`
  - `4 passed, 30 deselected`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py`
  - 통과
- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과
- source readback:
  - `WS_REG_RECENT_TTL_SEC=8`

### 40.4 runtime 반영 계획

- `kiwoom_websocket.py` 코드 변경이므로 현재 실행 중인 봇에는 완전 반영되지 않는다.
- review-gate와 revalidation 후 `restart.flag` 기반 우아한 재기동으로 반영한다.
- KILL은 사용하지 않는다.

### 40.5 runtime 반영 결과

- `./restart.sh`로 `restart.flag` 기반 우아한 재기동을 수행했다.
- old PID: `179347`
- new PID: `181081`
- `restart.flag`는 소모됐고, runtime env handoff verification은 `passed=true`, `pid_passed=true`다.
- PID env readback:
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8`
  - `KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC=6`
  - `KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC=8`
- `logs/bot_history.log` 기준:
  - `16:58:01` 스나이퍼 엔진 재가동
  - `16:58:03` 주문/체결통보 감시망 등록
  - `16:58:08` 이후 REG 중복 생략 로그가 `ttl_sec=8.0`으로 변경됨
  - `16:58:08~16:58:14` `006400`, `226950`, `010120`, `034020`, `073240`, `161000`, `373220`, `376900`, `347850`, `183190`, `004980`, `445090` 첫 실시간 데이터 수신 확인
- KILL은 사용하지 않았다.

## 41. 17:00 loop fixed flow 갱신 및 kt10003 정정 확인

작성 시각: `2026-06-29 17:01 KST`

### 41.1 고정 flow artifact 운용

- 사용자 요청에 따라 `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`만 고정 갱신 대상으로 유지한다.
- 17:00 loop 갱신 명령:
  - `PYTHONPATH=. .venv/bin/python -m src.engine.monitoring.intraday_entry_flow_report --target-date 2026-06-29 --since 2026-06-29T15:00:00+09:00 --diagnostic-path data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1700_1500_goal.json --output-md data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md --output-csv /tmp/intraday_entry_flow_2026-06-29_1500_to_1700.csv --print-summary`
- `/tmp/intraday_entry_flow_2026-06-29_1500_to_1700.csv`는 갱신 직후 삭제했다.
- 현재 `data/report/intraday_entry_flow/`에는 고정 md 1개만 남아 있다.

### 41.2 17:00 진단 판정

- source diagnostic: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1700_1500_goal.json`
- summary:
  - `entry_event_count=21751`
  - `promoted_symbol_count=89`
  - `real_submit_symbol_count=1`
  - `falling_real_submitted_count=0`
  - `rising_missed_buy_count=17`
- stale split:
  - `diagnostic_quote_age_stale=257`
  - `pre_ai_stale_or_history_gap=40`
  - `full_eval_delay=0`
  - `pre_submit_hard_stale=0`
  - `ws_quote_missing=0`
- root priority는 여전히 `scanner_strength_history_or_stale_eval`이지만, 이번 loop의 `top_unresolved_stale_eval_symbols=[]`, `unresolved_stale_or_delayed_low_ai_or_pressure_events=0`이다.
- 판정:
  - 직전 조치인 `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8` 및 hot override key 추가 후 `full_eval_delay`, `pre_submit_hard_stale`, `ws_quote_missing`은 신규 major blocker로 남지 않았다.
  - stale aggregate는 15:00 이후 누적 window의 과거 diagnostic stale 비중이므로, 현재 신규 submit 차단으로 해석하지 않는다.
  - 다음 20분 loop에서 같은 blocker가 fresh window에 재발하는지 관측한다.

### 41.3 다른 blocker 분포

- `ai_wait_or_baseline_prior_score_block`은 priority 3으로 남아 있으나, `latest_ai_score`가 대체로 `60~63`이고 `latest_entry_score_threshold=75`인 표본이므로 장중 BUY score/threshold 완화는 하지 않는다.
- `entry_price_execution`은 `올릭스(226950)` 취소 실패 이벤트가 여전히 최근 issue에 남아 있으나, 해당 주문 `0059624`는 `16:53:01` 전량체결/FULL_FILL로 종료됐다.
- `scale_in_diagnostics`:
  - `executed_count=0`
  - 주요 blocker는 `profit_not_enough`, `pnl_out_of_range`, `flow_hold_interval`
  - scale-in guard, quantity cap, cooldown, hard safety는 변경하지 않는다.

### 41.4 kt10003/kt10002 재확인

- 사용자 지적 기준으로 재확인했다.
- `docs/reference/키움 REST API 문서.xlsx` 기준:
  - `kt10002`: 주식 정정주문
  - `kt10003`: 주식 취소주문
- 따라서 `src/engine/kiwoom_orders.py`의 취소 주문 `api-id`는 `kt10003`이 맞다.
- `src/tests/test_kiwoom_orders.py::test_send_cancel_order_uses_requested_exchange`는 취소 주문이 `kt10003`을 사용하는지 검증하도록 유지한다.
- 16:50대 취소 실패의 해소 방향은 TR 변경이 아니라 `SOR` 취소 실패 `571412` 발생 시 `ka10075` 미체결 스냅샷에서 실제 거래소(`KRX`/`NXT`)를 확인해 한 번만 재시도하는 방식이다.

## 42. persistent repair TTL 잔여 30초 경로 hot override

작성 시각: `2026-06-29 17:05 KST`

### 42.1 배경

- `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8` 반영 후 일반 REG 중복 생략 로그는 `ttl_sec=8.0`으로 정상 전환됐다.
- 그러나 재기동 후 `17:00:55`, `17:01:47`, `17:02:14`, `17:02:22`, `17:03:21`에 persistent repair 등록 제한 로그가 여전히 `ttl_sec=30.0`을 표시했다.
- root cause:
  - 일반 REG 중복 TTL과 persistent repair 자체 TTL은 별도 key다.
  - 기존 effective 값 `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=30`이 persistent repair 재등록을 계속 늦췄다.

### 42.2 조치

- `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - tail override로 `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=8` 추가
  - rollback: `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=30`
- 이 key는 이미 `src/engine/kiwoom_websocket.py`의 WS hot runtime override family에 포함되어 있어 재기동 없이 반영 대상이다.
- 변경 범위:
  - persistent WS repair pacing only
  - BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, watch attach cap, scale-in guard는 변경하지 않았다.

### 42.3 검증 및 관측

- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과
- source readback:
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES=28`
- `17:04:27` 이후 `001530`, `065350`, `093370`, `153890`, `475150`에 대해 실제 REG 전송이 다시 확인됐다.
- `17:05` 보조 diagnostic:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1705_1500_goal.json`
  - `real_submit_symbol_count=1`
  - `falling_real_submitted_count=0`
  - `rising_missed_buy_count=17`
  - `full_eval_delay=0`, `pre_submit_hard_stale=0`, `ws_quote_missing=0`
  - `top_unresolved_stale_eval_symbols=[]`
  - `unresolved_stale_or_delayed_low_ai_or_pressure_events=0`
- 고정 flow report도 같은 diagnostic으로 갱신했다.
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
  - temp CSV는 `/tmp/intraday_entry_flow_2026-06-29_1500_to_1705.csv`로 생성 후 삭제했다.
- `data/report/intraday_entry_flow/`에는 고정 md 1개만 남아 있다.

### 42.4 다음 루프 기준

- stale aggregate count는 15:00 이후 누적 window의 과거 진단 비중이므로 신규 submit hard blocker로 보지 않는다.
- 다음 17:20 loop에서 확인할 항목:
  - fresh window에서도 `scanner_strength_history_or_stale_eval`의 unresolved count가 0인지
  - `ws_snapshot_missing_or_zero`가 특정 종목에 반복되는지
  - watch cap 로그가 구조화 blocker로 상승하는지
  - AI wait/low score가 fresh positive context 없이 threshold 완화 요구로 오인되지 않는지

## 43. WS alternate-route TTL 잔여 30초 경로 hot override

작성 시각: `2026-06-29 17:11 KST`

### 43.1 배경

- persistent repair TTL을 8초로 낮춘 뒤 `persistent repair 등록 제한` 로그는 새로 반복되지 않았다.
- 하지만 `17:07~17:10` 구간에 `alternate route 등록 제한`이 `ttl_sec=30.0`으로 반복됐다.
- 일부 종목은 exchange-aware alternate item(`_AL`) 없이 기본 item으로만 재등록되는 구간이 있었고, 같은 `scanner_strength_history_or_stale_eval` 계열 회복을 늦출 가능성이 있다.

### 43.2 조치

- `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - tail override로 `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC=8` 추가
  - rollback: `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC=30`
- 이 key는 이미 `src/engine/kiwoom_websocket.py`의 WS hot runtime override family에 포함되어 있어 재기동 없이 반영 대상이다.
- 변경 범위:
  - WS alternate-route repair pacing only
  - BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, watch attach cap, scale-in guard는 변경하지 않았다.

### 43.3 검증 및 관측

- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과
- source readback:
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=12`
- `17:10:21` 이후 `001530`, `093370`, `153890`, `475150`에 대해 `_AL` 포함 REG가 다시 전송됐다.
- `17:10:42`에는 `034020`, `161000`, `373220`, `445090`에 대해 `_AL` 포함 REG가 전송됐다.
- `17:11:04`에는 `001530`, `065350`, `093370`, `153890`, `475150`에 대해 `_AL` 포함 REG가 전송됐다.
- KILL/restart는 사용하지 않았다.

### 43.4 다음 루프 기준

- 17:20 diagnostic에서 stale split과 rising missed 구성을 재확인한다.
- alternate-route 제한이 계속 major blocker로 나타나지 않는다면 추가 WS TTL 조정은 중단한다.
- watch cap 로그는 아직 pipeline event의 구조화 blocker로 잡히지 않았으므로, 17:20 결과에서 rising missed blocker로 올라올 때만 root cause로 승격한다.

## 44. persistent WS gap 전체 REG 그룹 재구성 보강

작성 시각: `2026-06-29 17:24 KST`

### 44.1 17:20 loop 판정

- source diagnostic: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1720_1500_goal.json`
- fixed flow report:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
  - temp CSV `/tmp/intraday_entry_flow_2026-06-29_1500_to_1720.csv`는 삭제했다.
- summary:
  - `entry_event_count=25054`
  - `promoted_symbol_count=89`
  - `real_submit_symbol_count=1`
  - `falling_real_submitted_count=0`
  - `rising_missed_buy_count=19`
- stale split:
  - `diagnostic_quote_age_stale=274`
  - `pre_ai_stale_or_history_gap=49`
  - `full_eval_delay=0`
  - `pre_submit_hard_stale=0`
  - `ws_quote_missing=0`
- root priority evidence:
  - `top_unresolved_stale_eval_symbols=[]`
  - `unresolved_stale_or_delayed_low_ai_or_pressure_events=0`
- blocker rollup에서 `scalping_scanner_watching_runtime_skip/ws_snapshot_missing_or_zero=144`가 최상위로 남았다.
- 대표 persistent gap:
  - `153890`, `475150`, `093370`
  - `ws_received_type_count=0`
  - `ws_recovery_outcome=persistent_ws_gap`
  - `ws_recovery_action=ws_repair_cycle_wait` 또는 `ws_reg_reissued_rest_quote_fallback`
  - `ws_repair_batch_min_interval_sec=8.0`
- REG 로그상 base와 `_AL` item을 반복 전송했지만 해당 종목들의 실수신이 회복되지 않았다.

### 44.2 root cause 분해

- 이미 조치한 항목:
  - 일반 REG recent TTL: `8s`
  - persistent repair TTL: `8s`
  - alternate route TTL: `8s`
  - alternate `_AL` 포함 REG 반복
- 남은 원인 후보:
  - 서버/클라이언트 구독 그룹이 이미 등록된 것으로 보이나 실수신이 없는 stuck subscription 상태
  - 단순 `refresh=0` REG add 반복만으로는 그룹 상태가 갱신되지 않는 케이스
- 잘못된 해소 방향:
  - BUY score/threshold 완화
  - stale-submit bypass
  - REST quote만으로 strength/momentum hard freshness를 대체
  - broker/account/order/quantity/cooldown guard 완화

### 44.3 코드 보강

- `src/engine/kiwoom_websocket.py`
  - hot runtime override key 추가:
    - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED`
    - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC`
  - persistent repair 시 override가 켜져 있고 throttle을 통과하면 현재 `subscribed_codes`와 repair target을 합쳐 `refresh=1` REG 그룹 재구성을 한 번 수행한다.
  - 기본값은 OFF라 기존 동작은 변경하지 않는다.
  - 재구성은 persistent repair 경로에만 제한된다.
- `src/tests/test_kiwoom_websocket.py`
  - 기본 OFF 회귀 테스트 추가
  - enabled 시 subscribed set과 repair target merge 및 min-interval throttle 테스트 추가
  - hot override parser가 새 key를 읽는지 테스트 보강

### 44.4 runtime override

- `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED=true`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC=60`
  - rollback:
    - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED=false`
    - `unset KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC`
- 이 변경은 persistent WS subscription freshness 전용이다.
- BUY/submit threshold, order price, stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, watch attach cap, scale-in guard는 변경하지 않았다.

### 44.5 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_websocket.py -k 'persistent_repair_rebuild_targets or ws_repair_budget_hot_reloads_operator_override_file or persistent_repair_filter or recent_reg_filter or alternate_route_filter or send_reg_applies_alternate'`
  - `12 passed, 24 deselected`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_kiwoom_websocket.py src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'persistent_repair_rebuild_targets or ws_repair_budget_hot_reloads_operator_override_file or persistent_repair_filter or recent_reg_filter or alternate_route_filter or send_reg_applies_alternate or persistent_repair_passes_repair_cycle or subscription_recheck_snapshot_is_applied_before_heavy_eval_recheck_skip'`
  - `14 passed, 178 deselected, 1 warning`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py`
  - 통과
- `git diff --check`
  - 통과
- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과

### 44.6 runtime 반영 계획

- `src/engine/kiwoom_websocket.py` 코드 변경이므로 봇 재기동이 필요하다.
- review-gate 결과 결함 없음이면 `restart.flag` 기반 우아한 재기동을 사용한다.
- KILL은 사용하지 않는다.

### 44.7 runtime 반영 결과

- `restart.flag` 기반 우아한 재기동을 수행했다.
- old bot PID: `181081`
- new bot PID: `190109`
- `restart.flag`는 재기동 후 제거된 상태로 확인했다.
- wrapper는 이전 PID 종료 대기 timeout 문구를 출력했지만, 독립 확인 결과 실제 bot 프로세스는 `190109` 하나만 남아 있었다. KILL은 사용하지 않았다.
- new bot `/proc/190109/environ` readback:
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED=true`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC=60`
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=8`
  - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC=8`
- 재기동 후 WS 연결/로그인/주문체결통보 등록이 정상 완료됐다.
- `17:27:09~17:27:35` 첫 실시간 데이터 수신 확인:
  - `006400`, `161000`, `347850`, `183190`, `065350`, `034020`, `226950`, `010120`, `373220`, `004980`, `376900`, `028050`, `445090`
- `17:29:01` persistent repair 전체 REG 그룹 재구성 실행 확인:
  - `repair_targets=['001530', '086520', '093370', '153890', '475150']`
  - `rebuild_targets=['001530', '004980', '006400', '010120', '028050', '034020', '065350', '086520', '093370', '153890', '161000', '183190', '226950', '347850', '373220', '376900', '445090', '475150']`
  - `min_interval_sec=60.0`
- 재구성 직후 `086520`은 첫 실시간 데이터 수신이 확인됐다.
- 다만 17:30 관측 기준 대표 persistent gap인 `093370`, `153890`, `475150`은 아직 첫 실시간 수신 로그가 없다. 다음 17:40 loop에서 fixed flow와 diagnostic으로 blocker rollup 감소 여부를 확인한다.
- `17:27:19~17:27:22` `ka10001` 429 1회 재시도 실패가 있었다. 현재는 REST 조회 rate-limit 경고로 기록만 하고, 반복될 때 별도 root cause로 승격한다.

## 45. 17:40 loop fixed flow 갱신, WS alternate-route coverage relief, 올릭스 청산 분석

작성 시각: `2026-06-29 17:43 KST`

### 45.1 17:40 loop 판정

- source diagnostic: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1740_1500_goal.json`
- fixed flow report:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
  - temp CSV `/tmp/intraday_entry_flow_2026-06-29_1500_to_1740.csv`는 삭제했다.
- summary:
  - `entry_event_count=27261`
  - `promoted_symbol_count=91`
  - `real_submit_symbol_count=1`
  - `falling_real_submitted_count=0`
  - `rising_missed_buy_count=19`
  - `repeated_zero_strength_history_workorder_count=10`
  - `rising_missed_repeated_zero_strength_history_workorder_count=5`
- stale split:
  - `diagnostic_quote_age_stale=305`
  - `pre_ai_stale_or_history_gap=51`
  - `full_eval_delay=0`
  - `pre_submit_hard_stale=0`
  - `ws_quote_missing=0`
- relief blocker rollup:
  - rising missed: `scalping_scanner_watching_runtime_skip/ws_snapshot_missing_or_zero=25`
  - rising missed: `scalping_scanner_watching_runtime_skip/entry_cooldown_active=5`
  - non-rising promoted: `scalping_scanner_watching_runtime_skip/ws_snapshot_missing_or_zero=115`
  - non-rising promoted: `scanner_full_eval_loop_budget_deferred=33`
- fixed flow summary:
  - `rising_missed_symbol_count_in_report=9`
  - `rising_stale_eval_symbol_count=7`
  - `rising_fresh_only_symbol_count=3`
  - `stale_refresh_recovered_symbol_count=12`
- major blocker는 여전히 `ws_snapshot_missing_or_zero`/strength-history source freshness다.

### 45.2 반복 blocker root cause 추가 분해

- 17:29 이후 persistent repair group rebuild는 실제 실행됐다.
- 그러나 17:40 전까지 `153890`, `475150`은 계속 repair target에 남았고 first realtime tick이 확인되지 않았다.
- 로그상 rebuild packet에서 `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=12` 때문에 일부 repair/rebuild 대상이 `_AL` alternate item 없이 skipped됐다.
- 17:41에는 개별 repair REG로 `153890`, `475150` base+`_AL`이 들어갔지만, 전체 rebuild에서는 still skipped가 남았다.
- 단순 TTL 추가 완화는 중단한다. 남은 hypothesis는:
  - alternate-route coverage 부족
  - 특정 종목 서버-side 실수신 stuck
  - 실시간 해지/재등록 계약 부재
- 해지/재등록은 Kiwoom WS 계약 확인 전에는 구현하지 않는다.

### 45.3 hot runtime relief

- `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=28`
  - rollback:
    - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=12`
- scope:
  - WS alternate-route repair coverage only
  - hot-reload key
- safety:
  - BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity/cooldown guard, provider route, hard/protect/emergency stop, watch attach cap, scale-in guard는 변경하지 않았다.
- validation:
  - `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
    - 통과
  - source readback:
    - `ALT_MAX=28`
    - `ALT_TTL=8`
    - `REBUILD=true`
- runtime observation:
  - 17:42 rebuild부터 `alternate route 등록 제한` 로그가 사라졌다.
  - 17:42 rebuild items에 `475150`, `475150_AL`, `153890`, `153890_AL`이 함께 포함됐다.
  - 아직 `153890`, `475150` first realtime tick은 미확인이다. 다음 loop에서 효과를 판정한다.

### 45.4 올릭스(226950) 청산 즉시 분석

- 매수:
  - `16:53:01` `[WS 실제체결] 226950 BUY 8주 @ 166300원 (주문번호: 0059624)`
  - `position_rebased_after_fill` 및 `holding_started` 관측
- 청산:
  - `17:38:06` `[WS 주문상태] 226950 | 주문번호: '0060681' | 상태: '접수' | 구분: '-매도'`
  - `17:38:06` `[WS 주문상태] 226950 | 주문번호: '0060681' | 상태: '체결' | 구분: '-매도'`
  - `17:38:06` `[WS 실제체결] 226950 SELL 8주 @ 168200원 (주문번호: 0060681)`
  - gross price move: `(168200 - 166300) / 166300 = +1.14%`
  - holding events around exit showed profit about `+0.91%~+0.97%` after cost/marking effects.
  - observed peak before exit was about `+0.97%`; sell happened close to observed peak, not a clear immediate missed-upside case yet.
- receipt caveat:
  - `17:39:42` 정기 동기화가 `잔고 없음`을 보고 `COMPLETED` 강제 전환했다.
  - WS 실제체결 로그는 존재하므로 broker fill 자체는 관측됐다. 다만 pipeline sell receipt/COMPLETED event contract가 약해 post-sell JSONL 후보/평가에는 아직 이 건이 없다.
- 6월 비교:
  - clean baseline 이후 6월 scalping post-sell evaluation rows: `63`
  - `scalp_trailing_take_profit`: `22`건, `MISSED_UPSIDE=7`건, missed rate `31.8%`, avg profit `+1.704%`, avg peak `+2.692%`, avg 10m MFE vs buy `+4.886%`
  - `scalp_mfe_protect_exit`: `2`건, missed rate `50.0%`
  - `scalp_soft_stop_pct`: `22`건, missed rate `18.2%`
  - `scalp_hard_stop_pct`: `11`건, missed rate `72.7%`
- 현재 판정:
  - 올릭스는 realized profit close-to-peak로 보이며, 지금 즉시 TP/trailing 완화 대상은 아니다.
  - post-sell candidate/evaluation 누락은 instrumentation gap이다.
  - 다음 post-sell evaluation 생성 후 10m/20m MFE가 sell 대비 유의하게 높으면 trailing missed-upside 표본으로 재분류한다.

## 46. 18:00 loop fixed flow 갱신, kt10003 재확인, alternate-route cap 보완

작성 시각: `2026-06-29 18:04 KST`

### 46.1 18:00 loop 판정

- source diagnostic: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1800_1500_goal.json`
- fixed flow report:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
  - temp CSV `/tmp/intraday_entry_flow_2026-06-29_1500_to_1800.csv`는 삭제했다.
  - `data/report/intraday_entry_flow/`에는 fixed md 1개만 남겼다.
- summary:
  - `entry_event_count=29799`
  - `promoted_symbol_count=91`
  - `real_submit_symbol_count=1`
  - `falling_real_submitted_count=0`
  - `rising_missed_buy_count=19`
  - `repeated_zero_strength_history_workorder_count=10`
  - `rising_missed_repeated_zero_strength_history_workorder_count=5`
- stale split:
  - `diagnostic_quote_age_stale=386`
  - `pre_ai_stale_or_history_gap=55`
  - `full_eval_delay=0`
  - `pre_submit_hard_stale=0`
  - `ws_quote_missing=0`
- relief blocker split:
  - rising missed: `scalping_scanner_watching_runtime_skip/ws_snapshot_missing_or_zero=24`
  - rising missed: `scalping_scanner_watching_runtime_skip/entry_cooldown_active=10`
  - rising missed: `scanner_full_eval_loop_budget_deferred=1`
  - non-rising promoted: `ws_snapshot_missing_or_zero=118`
  - non-rising promoted: `scanner_full_eval_loop_budget_deferred=45`
- post-sell diagnostic:
  - candidate/evaluated `1/1`
  - outcome `NEUTRAL`
  - `missed_upside_count=0`
- scale-in diagnostic:
  - `blocked_count=614`
  - `executed_count=0`
  - top blockers remain `profit_not_enough`, `pnl_out_of_range`, `flow_hold_interval`; guard bypass 없음.

### 46.2 kt10003/kt10002 재확인

- `docs/reference/키움 REST API 문서.xlsx` 확인 결과:
  - `kt10002`: `주식 정정주문`
  - `kt10003`: `주식 취소주문`
- `src/engine/kiwoom_orders.py::send_cancel_order`는 `api-id=kt10003`을 유지한다.
- `src/tests/test_kiwoom_orders.py::test_send_cancel_order_uses_requested_exchange`도 `kt10003`을 기대한다.
- 226950의 과거 취소거절은 `kt10002/kt10003` 혼동이 아니라 `571412` SOR/KRX 원주문 거래소 mismatch로 분리한다.

### 46.3 반복 blocker root cause 추가 조치

- 18:00 이후에도 `475150`, `153890` 등은 `received_type_count=0`, `strength_history_count=0`인 persistent WS gap이 반복됐다.
- 그러나 17:43 hot override `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=28`은 코드 내부 cap `min(value, 20)` 때문에 실제 최대 20으로 잘려 있었다.
- 조치:
  - `src/engine/kiwoom_websocket.py`
    - `_alternate_route_max_codes()` 상한을 `20 -> 32`로 변경한다.
    - scope는 WS alternate-route repair coverage only.
    - BUY score, AI threshold, order price, stale-submit, broker/account/order/quantity/cooldown, hard/protect/emergency stop은 변경하지 않는다.
  - `src/tests/test_kiwoom_websocket.py`
    - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=28`이 실제 `28`로 반영되는 테스트를 추가한다.
- next validation:
  - targeted pytest
  - py_compile
  - `git diff --check`
  - review gate re-read

### 46.4 검증 및 runtime follow-up 판정

- `PYTHONPATH=. .venv/bin/pytest src/tests/test_kiwoom_websocket.py -k 'alternate_route_hot_override_allows_rebuild_group_coverage or persistent_repair_rebuild_targets or ws_repair_budget_hot_reloads_operator_override_file or persistent_repair_filter or recent_reg_filter or alternate_route_filter or send_reg_applies_alternate'`
  - `13 passed, 24 deselected`
- `.venv/bin/python -m py_compile src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py`
  - 통과
- `git diff --check -- src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py docs/code-reviews/2026-06-29-intraday-scanner-watchlist-code-change-list.md data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
  - 통과
- `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - parser 통과, backlog count `22`
- self review:
  - runtime/order/provider/bot/threshold authority leak 없음.
  - stale quote, broker/account/order/quantity/cooldown, hard/protect/emergency stop guard 우회 없음.
  - 코드 cap 변경은 WS alternate route repair coverage만 반영한다.
- runtime follow-up:
  - 실행 중인 봇 프로세스는 이전 코드 cap `20`을 계속 사용하므로, `restart.flag` 방식 우아한 재기동으로 cap `32` 코드와 hot override `28`을 반영한다.

### 46.5 runtime 반영 결과

- `restart.flag` 기반 우아한 재기동을 수행했다.
- old bot PID: `190109`
- new bot PID: `204253`
- `restart.flag`는 재기동 후 제거된 상태로 확인했다.
- runtime env handoff verification:
  - `passed=true`
  - `pid_passed=true`
  - `pid_mismatches=[]`
- new bot `/proc/204253/environ` readback:
  - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=28`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED=true`
  - `KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC=8`
  - `KORSTOCKSCAN_SCALPING_BUY_WINDOWS=08:03:00-08:40:00,09:03:00-15:20:00,16:00:00-19:45:00`
- 재기동 후 WS 연결/로그인/주문체결통보 등록 정상 완료.
- `18:08:06` persistent repair 전체 REG 그룹 재구성 확인:
  - `repair_targets=['086520', '153890', '458870', '475150']`
  - `rebuild_targets=['006400', '010120', '028050', '034020', '035420', '065350', '086520', '153890', '161000', '183190', '226950', '347850', '373220', '445680', '458870', '475150']`
  - items include `153890`, `153890_AL`, `475150`, `475150_AL`
  - `alternate route 등록 제한`은 재발하지 않았다.
- `18:08` 관측 시점:
  - `086520` first realtime data recovered.
  - `153890`, `475150` first realtime data는 아직 미확인이다. 다음 18:20 loop에서 blocker 감소 여부를 판정한다.
- incident note:
  - `18:07:05` OpenAI Responses WS timeout 1회가 있었다. 단발이면 기록만 하고, 반복되면 AI transport blocker로 승격한다.

## 47. 18:20 loop fixed flow 갱신, kt10003 재확인, persistent no-tick repair cooldown

### 47.1 18:20 고정 flow 리포트 갱신

- 갱신 대상:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- 입력 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1820_1500_goal.json`
- fixed flow summary:
  - `symbol_count=28`
  - `rising_symbol_count_by_max_delta=10`
  - `rising_missed_buy_count_in_latest_diagnostic=19`
  - `rising_missed_symbol_count_in_report=9`
  - `real_submit_symbol_count_in_latest_diagnostic=1`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
  - `stale_eval_symbol_count=14`
  - `rising_stale_eval_symbol_count=7`
  - `stale_refresh_recovered_symbol_count=12`
- top blocker:
  - 전체: `scalping_scanner_watching_runtime_skip/ws_snapshot_missing_or_zero=6`, `scanner_fast_precheck_stability_pending=4`, `blocked_strength_momentum/below_window_buy_value=4`
  - rising: `ws_snapshot_missing_or_zero`, `scanner_fast_precheck_stability_pending`, strength/overbought/AI WAIT 계열이 1건씩 분산
- latest diagnostic 주요 분해:
  - rising missed rollup: `ws_snapshot_missing_or_zero=24`, `entry_cooldown_active=10`, `scanner_full_eval_loop_budget_deferred=1`
  - stale split: `diagnostic_quote_age_stale=464`, `pre_ai_stale_or_history_gap=57`, `full_eval_delay=0`, `pre_submit_hard_stale=0`, `ws_quote_missing=0`
  - source-quality repeated zero strength-history top: `475150=442`, `153890=169`, `001530=159`, `093370=109`, `445090=86`
  - falling real-submitted count remains `0`
  - post-sell diagnostic: candidate/evaluated `1/1`, outcome `NEUTRAL`, missed_upside `0`
  - scale-in: blocked `688`, executed `0`, top blockers remain `profit_not_enough`, `pnl_out_of_range`, `flow_hold_interval`, `add_judgment_locked`

### 47.2 kt10003/kt10002 재확인

- 사용자 정정에 따라 `docs/reference/키움 REST API 문서.xlsx`를 다시 확인했다.
  - `kt10002`: `주식 정정주문`
  - `kt10003`: `주식 취소주문`
- `src/engine/kiwoom_orders.py::send_cancel_order`는 `api-id=kt10003`을 유지한다.
- `src/tests/test_kiwoom_orders.py::test_send_cancel_order_uses_requested_exchange`는 `kt10003`을 기대한다.
- 따라서 226950 취소거절은 TR-id 혼동이 아니라 `571412` SOR/KRX 원주문 거래소 mismatch 유형으로 계속 분리한다.

### 47.3 반복 blocker root cause 추가 조치

- 18:05 재기동 이후 `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=28` 및 rebuild group이 적용되어 `153890`, `475150`의 base/_AL REG payload는 전송됐다.
- 그럼에도 18:20 이후 pipeline event 기준:
  - `153890`: `received_type_count=0`, `ws_strength_history_count=0`, `rising_rest_quote_recovery_without_realtime_strength` 반복
  - `475150`: `received_type_count=0`, `ws_strength_history_count=0`, `rest_quote_without_realtime_strength` 반복
- 루프 시간은 50초대에서 20~33초대로 내려왔지만, 동일 no-tick 종목 repair가 계속 반복되어 source-quality repair churn 압력이 남았다.
- 조치:
  - `src/engine/kiwoom_websocket.py`
    - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS`
    - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC`
    - 위 hot keys를 추가하고, persistent repair가 N회 REG 후에도 first realtime을 만들지 못한 코드는 짧은 cooldown 동안 repair REG에서 제외한다.
    - 실제 realtime이 들어오면 no-tick attempt/cooldown 상태를 즉시 해제한다.
  - `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
    - provenance/rollback 포함 runtime override 추가:
      - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS=3`
      - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC=240`
- scope:
  - persistent WS repair pressure relief only.
  - BUY score, AI threshold, order price, stale-submit block, broker/account/order/quantity/cooldown, hard/protect/emergency stop, provider route, watch attach cap, scale-in guard는 변경하지 않는다.

### 47.4 검증 및 review gate

- `$korstockscan-review-gate` 기준으로 diff/producer-consumer 계약을 재확인했다.
- targeted validation:
  - `PYTHONPATH=. .venv/bin/pytest src/tests/test_kiwoom_websocket.py -k 'persistent_repair_stuck_cooldown_skips_no_tick_code or persistent_repair_attempts_clear_after_first_realtime or ws_repair_budget_hot_reloads_operator_override_file or persistent_repair_filter or persistent_repair_rebuild_targets or alternate_route_hot_override_allows_rebuild_group_coverage'`
    - `9 passed, 30 deselected`
  - `.venv/bin/python -m py_compile src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py`
    - 통과
  - `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
    - 통과
  - `git diff --check -- src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py data/threshold_cycle/runtime_env/operator_runtime_overrides.env data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md docs/code-reviews/2026-06-29-intraday-scanner-watchlist-code-change-list.md`
    - 통과
  - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
    - parser 통과, backlog count `22`
- runtime follow-up:
  - 실행 중인 bot PID `204253`은 아직 no-tick cooldown 코드가 없으므로, 우아한 재기동 후 hot override 반영 여부와 loop time/rebuild 로그를 확인한다.

### 47.5 runtime 반영 결과

- `restart.flag` 기반 우아한 재기동을 수행했다.
- old bot PID: `204253`
- new bot PID: `210209`
- `restart.flag`는 재기동 후 제거된 상태로 확인했다.
- runtime env readback:
  - `KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=28`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED=true`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS=3`
  - `KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC=240`
  - `KORSTOCKSCAN_SCALPING_BUY_WINDOWS=08:03:00-08:40:00,09:03:00-15:20:00,16:00:00-19:45:00`
- `KILL`은 사용하지 않았다.
- wrapper 출력은 중간 PID를 `new_pid=210161`로 잡았지만, 직접 `pgrep` 확인 기준 실제 실행 bot은 `210209` 하나다.
- next observation:
  - 18:40 loop에서 no-tick cooldown 로그, loop_elapsed, `153890/475150` source-quality count 변화, BUY 후보/pre-submit/submit/fill 흐름을 다시 판정한다.

## 48. 18:40 loop fixed flow 갱신 및 full-eval auto-pressure 추가 감압

### 48.1 18:40 고정 flow 리포트 갱신

- 갱신 대상:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- 입력 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1840_1500_goal.json`
- fixed flow summary:
  - `symbol_count=28`
  - `rising_symbol_count_by_max_delta=10`
  - `rising_missed_buy_count_in_latest_diagnostic=20`
  - `rising_missed_symbol_count_in_report=9`
  - `real_submit_symbol_count_in_latest_diagnostic=1`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
  - `stale_eval_symbol_count=14`
  - `rising_stale_eval_symbol_count=7`
  - `rising_fresh_only_symbol_count=3`
  - `stale_refresh_recovered_symbol_count=12`
- latest diagnostic:
  - `promoted_symbol_count=92`
  - `falling_real_submitted_count=0`
  - rising missed rollup: `ws_snapshot_missing_or_zero=23`, `entry_cooldown_active=12`, `scanner_full_eval_loop_budget_deferred=1`
  - stale split: `diagnostic_quote_age_stale=528`, `pre_ai_stale_or_history_gap=60`, `full_eval_delay=0`, `pre_submit_hard_stale=0`, `ws_quote_missing=0`
  - source-quality repeated zero strength-history top: `475150=500`, `153890=203`, `001530=159`, `093370=109`, `445090=86`
  - post-sell diagnostic remains `candidate/evaluated=1/1`, outcome `NEUTRAL`, missed_upside `0`
  - scale-in remains `blocked=784`, `executed=0`; top blockers are `profit_not_enough`, `pnl_out_of_range`, `flow_hold_interval`
- flow directory cleanup state:
  - `data/report/intraday_entry_flow/` contains only `intraday_entry_flow_2026-06-29_0800_to_1004.md` after each update.

### 48.2 병목 재분해

- 18:40 이후 event analysis:
  - `scalping_scanner_runtime_queue_lag`가 거의 모든 WATCHING scanner 종목에 반복됐다.
  - 18:26:51 이후 runtime queue lag by minute:
    - `18:29=42`, `18:40=34`, `18:31=30`, `18:34=30`, `18:35=30`, `18:37=29`, `18:32=28`, `18:36=28`
  - top queue-lag symbols include `086520`, `183190`, `065350`, `028050`, `006400`, `347850`, `226950`, `153890`, `475150`.
- loop metrics after no-tick cooldown restart:
  - `18:31:42 loop_elapsed_ms=46646.3`
  - `18:32:54 loop_elapsed_ms=31831.5`
  - `18:34:02 loop_elapsed_ms=38510.4`
  - `18:35:13 loop_elapsed_ms=31102.9`
  - `18:36:15 loop_elapsed_ms=32368.9`
  - `18:37:47 loop_elapsed_ms=28173.2`
  - `18:39:47 loop_elapsed_ms=44137.5`
  - `18:41:12 loop_elapsed_ms=40424.6`
- no-tick repair cooldown alone did not sufficiently reduce loop pressure.
- 현재 full-eval governor는 `effective_limit=4/min_limit=4`에 고정되어 더 깊게 감압할 수 없었다.

### 48.3 추가 조치

- 기존 승인된 `SCANNER_FULL_EVAL_AUTO_PRESSURE` hot runtime family 안에서만 감압 범위를 조정한다.
- `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - provenance/rollback 포함 추가:
    - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=2`
    - rollback: `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=4`
- scope:
  - scanner full-eval pacing/pressure governor only.
  - BUY score, AI threshold, order price, stale-submit block, broker/account/order/quantity/cooldown, hard/protect/emergency stop, provider route, watch attach cap, scale-in guard는 변경하지 않는다.
- runtime reflection:
  - `/proc` env는 재기동 시점 값 `4`를 보이나, hot override file reload가 적용되어 `18:41:38` 로그에서 `SCANNER_FULL_EVAL_PRESSURE action=reduce ... effective_limit=2 min_limit=2 reduction=6` 확인.
- validation:
  - `bash -n data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
    - 통과
  - `git diff --check -- data/threshold_cycle/runtime_env/operator_runtime_overrides.env docs/code-reviews/2026-06-29-intraday-scanner-watchlist-code-change-list.md data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md src/engine/kiwoom_websocket.py src/tests/test_kiwoom_websocket.py`
    - 통과
- next observation:
  - 다음 loop에서 `effective_limit=2` 반영 후 loop_elapsed, `scanner_full_eval_loop_budget_deferred`, rising missed count 증가 여부를 함께 판정한다.

### 48.4 runtime 관측 결과

- `effective_limit=2` 적용 직후 loop pressure가 완화됐다.
  - `18:41:38 SCANNER_FULL_EVAL_PRESSURE action=reduce ... effective_limit=2 min_limit=2 reduction=6`
  - `18:41:54 LOOP_METRICS loop_elapsed_ms=15543.2`
  - `18:43:01 LOOP_METRICS loop_elapsed_ms=8966.4`
- 이전 `18:31~18:41` 루프가 대체로 28~46초였던 것과 비교하면 실질적인 runtime pressure relief로 판정한다.
- 19:00 loop에서 상승 미체결, full-eval deferred, runtime_queue_lag 재증가 여부를 재검토한다.

## 49. 19:00 loop fixed flow 갱신 및 sim-only 후보 분리

### 49.1 19:00 고정 flow 리포트 갱신

- 갱신 대상:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- 입력 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1900_1500_goal.json`
- fixed flow summary:
  - `symbol_count=28`
  - `rising_symbol_count_by_max_delta=10`
  - `rising_missed_buy_count_in_latest_diagnostic=21`
  - `rising_missed_symbol_count_in_report=9`
  - `real_submit_symbol_count_in_latest_diagnostic=1`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
  - `stale_eval_symbol_count=14`
  - `rising_stale_eval_symbol_count=7`
  - `rising_fresh_only_symbol_count=3`
  - `stale_refresh_recovered_symbol_count=12`
- latest diagnostic:
  - `promoted_symbol_count=97`
  - `falling_real_submitted_count=0`
  - rising missed rollup: `ws_snapshot_missing_or_zero=27`, `entry_cooldown_active=12`, `scanner_full_eval_loop_budget_deferred=2`
  - stale split: `diagnostic_quote_age_stale=573`, `pre_ai_stale_or_history_gap=68`, `full_eval_delay=0`, `pre_submit_hard_stale=0`, `ws_quote_missing=0`
  - source-quality repeated zero strength-history top: `475150=560`, `153890=242`, `001530=159`, `093370=109`, `445090=86`
  - post-sell diagnostic remains `candidate/evaluated=1/1`, outcome `NEUTRAL`, missed_upside `0`
  - scale-in remains `blocked=826`, `executed=0`; top blockers remain `profit_not_enough`, `pnl_out_of_range`, `flow_hold_interval`

### 49.2 actual submit/fill 판정

- `real_submit_symbol_count=1` 유지.
- 실제 BUY submit/fill은 기존 `올릭스(226950)` 1건뿐이다.
  - `16:40:30` BUY 접수 order `0059624`
  - `16:53:01` BUY 체결 order `0059624`
  - receipt: `ID 13961`, avg `166,300`, qty `8`
- 18:51~18:56 holding 증가처럼 보인 이벤트는 실제 주문이 아니라 scalp-sim 가상 체결이다.
  - `086520` `scalp_sim_buy_order_virtual_pending` / `scalp_sim_buy_order_assumed_filled` / `scalp_sim_holding_started`, `actual_order_submitted=False`
  - `065350` 동일, `actual_order_submitted=False`
  - `247540` 동일, `actual_order_submitted=False`
- sim-only 후보를 실주문으로 전환하는 것은 broker/order guard 문제가 아니라 real-order authority 변경이다. 사용자 승인 없이 변경하지 않는다.

### 49.3 18:40 조치 효과와 부작용

- full-eval auto-pressure min limit `2` 적용 후 loop pressure는 전반적으로 개선됐다.
  - `18:41:54 loop_elapsed_ms=15543.2`
  - `18:43:01 loop_elapsed_ms=8966.4`
  - `18:44:14 loop_elapsed_ms=12720.4`
  - `18:47:09 loop_elapsed_ms=15228.5`
  - `18:50:23 loop_elapsed_ms=11492.8`
  - `18:52:38 loop_elapsed_ms=8913.8`
  - `18:53:57 loop_elapsed_ms=14687.8`
  - intermittent spikes remain: `18:45:59=22747.1`, `18:48:28=28984.8`, `18:51:58=33189.4`, `18:57:40=44529.6`
- side effect:
  - `scanner_full_eval_loop_budget_deferred` increased from `1` to `2`.
  - new deferred rising symbol: `247540(에코프로비엠)` at `18:53:41`, `max_delta=0.95`, `scanner_full_eval_limit=2`, `scanner_rising_full_eval_relief_count=5`.
- 판정:
  - pressure relief is useful but now bounded by occasional watchlist prune/promote churn and a small deferred increase.
  - 즉시 full-eval capacity를 되돌리지는 않는다. 다음 19:20 loop에서 deferred가 더 늘거나 high-delta real candidate가 누락되면 min limit rollback or adaptive exception을 검토한다.

## 50. 19:20 loop fixed flow 갱신, kt10003 재확인, full-eval min-limit rollback

### 50.1 19:20 고정 flow 리포트 갱신

- 갱신 대상:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- 입력 진단:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1920_1500_goal.json`
- fixed flow summary:
  - `symbol_count=34`
  - `rising_missed_buy_count_in_latest_diagnostic=24`
  - `rising_missed_symbol_count_in_report=9`
  - `real_submit_symbol_count_in_latest_diagnostic=1`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
- latest diagnostic:
  - `entry_event_count=41284`
  - `promoted_symbol_count=131`
  - `falling_real_submitted_count=0`
  - `rising_missed_full_eval_budget_deferred_count=11`, `symbol_count=3`
  - stale split: `diagnostic_quote_age_stale=619`, `pre_ai_stale_or_history_gap=74`, `full_eval_delay=0`, `pre_submit_hard_stale=0`, `ws_quote_missing=0`
  - source-quality repeated zero strength-history top: `475150=617`, `153890=276`, `001530=159`, `093370=109`, `445090=86`
  - scale-in remains `blocked=848`, `executed=0`
- flow directory cleanup state:
  - `data/report/intraday_entry_flow/` contains only `intraday_entry_flow_2026-06-29_0800_to_1004.md`; timestamped loop files are deleted after the fixed file is updated.

### 50.2 kt10003/kt10002 재확인

- reference:
  - `docs/reference/키움 REST API 문서.xlsx`
- confirmed TR mapping:
  - `kt10002 = 주식 정정주문`
  - `kt10003 = 주식 취소주문`
- code/test state:
  - `src/engine/kiwoom_orders.py::send_cancel_order` uses `api-id: kt10003`
  - `src/tests/test_kiwoom_orders.py::test_send_cancel_order_uses_requested_exchange` asserts `kt10003`
- conclusion:
  - 226950 cancel reject was not caused by kt10002/kt10003 confusion.
  - observed blocker remains original-order exchange mismatch, with order history snapshot exchange resolution as the corrective path.

### 50.3 full-eval min-limit rollback

- 18:42 relief:
  - `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=2`
  - benefit: loop elapsed temporarily improved from 28-46s range to several 9-15s loops.
  - side effect by 19:20: `scanner_full_eval_loop_budget_deferred` increased from `2` to `11`.
- affected high-delta deferred candidates:
  - `066970(엘앤에프)`: `count=7`, `max_delta=1.93`, latest `19:02:13`
  - `329180(HD현대중공업)`: `count=3`, `max_delta=0.51`
  - `247540(에코프로비엠)`: `count=1`, `max_delta=3.05`, latest `18:53:41`
- corrective action:
  - append hot runtime rollback in `data/threshold_cycle/runtime_env/operator_runtime_overrides.env`
  - restore `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=4`
  - rollback value left as `KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=2`
- safety:
  - no BUY score, AI threshold, order price, stale-submit block, broker/account/order/quantity/cooldown, provider route, hard/protect/emergency stop, watch attach cap, or scale-in guard change.

## 51. blocker taxonomy 분리 적용

### 51.1 수정 의도

- `ws_snapshot_missing_or_zero`는 REST quote/subscription recheck 이후에도 남는 source freshness blocker로 계속 major/actionable로 유지한다.
- `scanner_full_eval_loop_budget_deferred`는 일반 blocker가 아니라 `runtime_backpressure`로 분류하고, 반복 또는 충분한 상승폭이 있는 SLA breach일 때만 major/actionable로 승격한다.
- `entry_cooldown_active`는 기본적으로 `intended_guard`로 분류하고, 반복 및 상승폭 조건이 동시에 있을 때만 cooldown opportunity-loss/wrong-scope 병목으로 승격한다.
- 이 변경은 진단/리포트 taxonomy only이며, runtime threshold, order submit, stale-submit, broker/account/order/quantity/cooldown, hard/protect/emergency stop guard는 변경하지 않는다.

### 51.2 코드 변경

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - `_blocker_taxonomy()` 추가.
  - per-symbol `dominant_actionable_blocker` 추가.
  - `blocker_taxonomy.class_counts`, `actionable_major_blocker_counts`, `suppressed_non_actionable_counts` 추가.
  - `scanner_full_eval_budget_deferred` root priority는 rising-missed 기준 actionable backpressure가 있을 때만 생성되도록 변경.
- `src/engine/monitoring/intraday_entry_flow_report.py`
  - diagnostic의 `dominant_actionable_blocker`를 `BUY전 주 blocker` 우선 source로 사용.
  - `blocker taxonomy`와 `suppressed non-actionable blocker counts` 섹션 추가.
  - top rows에 blocker `class` 컬럼 추가.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 정상 cooldown/single deferred가 major blocker에서 suppressed되는 회귀 테스트 추가.
  - `ws_snapshot_missing_or_zero`가 source freshness major blocker로 유지되는 테스트 추가.

### 51.3 산출물 갱신

- 신규 diagnostic:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1930_taxonomy.json`
- fixed flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- latest fixed flow taxonomy:
  - `runtime_backpressure=581`
  - `source_freshness_blocker=511`
  - `strategy_reject=457`
  - `intended_guard=10`
  - suppressed non-actionable:
    - `runtime_backpressure/scanner_full_eval_loop_budget_deferred=10`
    - `intended_guard/entry_cooldown_active=5`
- rising-missed root priority still keeps actionable full-eval SLA breach:
  - actionable backpressure count `11`, symbol count `3`
  - `066970` count `7`, max delta `1.93`
  - `329180` count `3`, max delta `0.51`
  - `247540` count `1`, max delta `3.05`

### 51.4 검증

- `PYTHONPATH=. .venv/bin/pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `32 passed`
- `.venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과

## 52. source freshness/watch budget 재분류 및 full-eval governor 병목 제외 보완

### 52.1 수정 의도

- 51번 변경 후 사용자 재판정에 따라 `ws_snapshot_missing_or_zero`를 BUY 제출 병목이 아니라 source freshness 회복/제외/예산 재배정 상태로 분리한다.
- REST quote/WS REG/subscription recheck 이후에도 no-tick 또는 zero snapshot이 반복되는 종목은 감시대상 유지 병목이 아니라 `source_freshness_evictable`로 표기하고, 다른 종목에 watch budget을 재배정한 이벤트는 `watch_budget_reallocated`로 표기한다.
- `scanner_full_eval_loop_budget_deferred`는 자동 governor/backpressure 관측값으로 두고, blocker taxonomy에서는 더 이상 major blocker로 취급하지 않는다.
- 단, downstream 평가로 회복되지 않은 반복 deferred는 `scanner_full_eval_budget_deferred.status=deferred_never_evaluated`로 남겨 root priority 후보만 유지한다.
- 이 변경은 진단/리포트 taxonomy only이며, runtime threshold, order submit, stale-submit, broker/account/order/quantity/cooldown, hard/protect/emergency stop guard는 변경하지 않는다.

### 52.2 코드 변경

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - `ws_snapshot_missing_or_zero` taxonomy를 `source_freshness_recovering` 또는 `source_freshness_evictable`로 분리하고 `major_blocker=false`로 변경.
  - `scalping_scanner_watch_eviction`을 `watch_budget_reallocated`로 분류하고, `eviction_reason`, `terminal_reason`, `eviction_attempt_count`, `stale_age_sec`를 recent blocker에 노출.
  - `scanner_full_eval_budget_deferred.status`를 `deferred_then_evaluated`, `deferred_never_evaluated`, `not_deferred`로 추가.
  - `scanner_full_eval_loop_budget_deferred` taxonomy route를 `auto_governor_backpressure_observation`으로 변경하고 `major_blocker=false`로 고정.
  - root priority의 full-eval 항목은 `deferred_then_evaluated`를 제외하고, 반복 또는 high-delta인데 아직 평가로 회복되지 않은 후보만 남기도록 축소.
- `src/engine/monitoring/intraday_entry_flow_report.py`
  - `eviction_reason`을 blocker reason 우선순위에 추가.
  - fixed flow MD에 `blocker taxonomy`, `suppressed non-actionable blocker counts`, blocker `class` 컬럼을 유지.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - ws snapshot missing의 recovering/evictable 분리 테스트 추가.
  - watch eviction의 budget reallocated 분류 테스트 추가.
  - full-eval deferred의 `deferred_then_evaluated`/`deferred_never_evaluated` 상태 분리 테스트 추가.

### 52.3 산출물 갱신

- diagnostic:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1930_taxonomy.json`
- fixed flow:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- fixed flow summary:
  - `symbol_count=68`
  - `rising_symbol_count_by_max_delta=10`
  - `rising_missed_buy_count_in_latest_diagnostic=32`
  - `rising_missed_symbol_count_in_report=9`
  - `real_submit_symbol_count_in_latest_diagnostic=1`
  - `buy_signal_or_pre_submit_pass_seen_symbols=0`
  - `rising_fresh_only_symbol_count=3`
  - `rising_stale_eval_symbol_count=7`
- latest taxonomy:
  - `runtime_backpressure=585`
  - `strategy_reject=484`
  - `source_freshness_evictable=277`
  - `watch_budget_reallocated=122`
  - `source_freshness_recovering=121`
  - `source_freshness_blocker=28`
  - `intended_guard=9`
- suppressed non-actionable:
  - `source_freshness_evictable/ws_snapshot_missing_or_zero=277`
  - `source_freshness_recovering/ws_snapshot_missing_or_zero=121`
  - `watch_budget_reallocated/stale_recovery_failed=111`
  - `runtime_backpressure/scanner_full_eval_loop_budget_deferred=10`
  - `intended_guard/entry_cooldown_active=4`
- full-eval deferred status:
  - `deferred_then_evaluated=2`
  - `deferred_never_evaluated=1`
  - root priority actionable residual: `329180(HD현대중공업)` count `3`, max delta `0.51`, status `deferred_never_evaluated`

### 52.4 검증

- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `34 passed`
- `.venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 통과

## 53. 코드리뷰 보완: suppressed non-major taxonomy alias

### 53.1 리뷰 발견사항

- 52번 변경 후 `ws_snapshot_missing_or_zero` 반복은 BUY 제출 major blocker가 아니지만, `source_freshness_evictable`은 감시대상 제외 또는 watch budget 재배정 조치 대상이다.
- 기존 JSON field `suppressed_non_actionable_counts`는 이 상태를 "조치 불필요"로 오해하게 만들 수 있어 진단 의미가 부정확했다.

### 53.2 보완

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - 정확한 의미의 `blocker_taxonomy.suppressed_non_major_counts`를 추가했다.
  - 기존 `suppressed_non_actionable_counts`는 downstream 호환을 위해 같은 값의 alias로 유지했다.
- `src/engine/monitoring/intraday_entry_flow_report.py`
  - MD 섹션명을 `suppressed non-major blocker counts`로 변경했다.
  - 새 key를 우선 사용하고, 구 diagnostic 파일과의 호환을 위해 기존 key fallback을 유지했다.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 새 key와 기존 key의 호환 동등성 테스트를 추가했다.

### 53.3 산출물 갱신 및 검증

- 갱신:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1930_taxonomy.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`
- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `34 passed`
- `.venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 통과

## 54. source freshness/strength history: price-only REST quote 회전

### 54.1 배경

- `rising_rest_quote_recovery_without_realtime_strength`는 REST quote로 가격만 회복했지만 WS 실시간 strength/history가 계속 비어 있는 상태다.
- 이 상태를 계속 `eligible_for_heavy_entry_eval`로만 통과시키면 BUY 후보 판단 전 strength/history 단계에서 반복 차단되거나 full-eval 예산을 소모한다.
- 하드 stale quote/order/broker/quantity/cooldown guard는 변경하지 않고, scanner WATCHING pool 관리 범위에서만 반복 source-quality 미해소 종목을 회전시킨다.

### 54.2 변경

- `src/engine/kiwoom_sniper_v2.py`
  - `rising_rest_quote_recovery_without_realtime_strength`를 watch eviction source-quality reason에 추가했다.
  - 해당 reason은 rising WS gap priority recheck로 무한 유예하지 않고, 표준 stale 반복/age 조건으로 `source_quality_unresolved` eviction 카운트가 쌓이게 했다.
  - fast-precheck가 `eligible_for_heavy_entry_eval`를 반환해도 price-only REST quote + strength/history missing 상태면 full-eval 예산 진입 전에 eviction 카운터를 먼저 갱신한다.
  - eviction event에는 기존 contract route를 유지하고, `source_quality_detail_route=price_only_rest_quote_strength_history_missing`, `rest_quote_price_recovery_only=True`, `scanner_source_quality_reallocation_candidate=True`를 남긴다.
- `src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - price-only REST quote strength gap이 rising priority recheck로 유예되지 않고 3회/90초 조건에서 회전되는지 검증했다.
  - 해당 eviction check가 full-eval budget 처리보다 먼저 실행되는지 run loop 순서를 검증했다.

### 54.3 검증

- `.venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/tests/test_kiwoom_sniper_market_regime_runtime.py`
  - 통과
- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_kiwoom_sniper_market_regime_runtime.py -k 'rest_quote_price_only_strength_gap or source_quality or stale_eviction'`
  - 통과: `7 passed, 151 deselected`
- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_observation_source_quality_audit.py -k 'scalping_scanner_watch_eviction'`
  - 통과: `1 passed, 67 deselected`
- `git diff --check -- src/engine/kiwoom_sniper_v2.py src/tests/test_kiwoom_sniper_market_regime_runtime.py docs/code-reviews/2026-06-29-intraday-scanner-watchlist-code-change-list.md`
  - 통과
- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - parser 통과, backlog count `22`

### 54.4 자체 리뷰 보완

- 1차 리뷰에서 `source_quality_route` contract key에 새 상세 route를 직접 넣으면 observation source-quality audit 계약과 충돌할 수 있는 리스크를 발견했다.
- 2차 리뷰에서 동일 reason에 `ws_recovery_outcome=rest_quote_applied`가 들어오면 기존 stale reset 분기가 먼저 실행될 수 있는 결함을 발견했다.
- 보완:
  - `source_quality_route`는 기존 `runtime_watchlist_eviction_pool_management_only`로 유지했다.
  - 새 상세 분류는 `source_quality_detail_route=price_only_rest_quote_strength_history_missing`로 분리했다.
  - `rising_rest_quote_recovery_without_realtime_strength`는 REST quote 가격 복구 outcome보다 먼저 `source_quality_unresolved_price_only_rest_quote`로 정규화해 stale eviction counter를 리셋하지 않게 했다.
- 재리뷰 결과:
  - threshold/provider/order price/quantity cap 변경 없음.
  - stale quote, broker/account/order/cooldown, hard/protect/emergency stop 우회 없음.
  - runtime effect는 scanner WATCHING pool management에만 한정된다.

## 55. 2026-06-30 10:20-10:40 목표 루프: latency block 진단 분류 보강

작성 시각: `2026-06-30 10:43 KST`

### 55.1 판정

- 10:20 루프에서 `rising_missed_buy_count=2`가 재발했으나, 두 종목 모두 scanner precheck 이후 `latency_block`까지 진행했다.
- 기존 diagnostic은 `latency_block`을 blocker stage로 보지 않아 최신 pre-submit guard를 놓치고, 이전 `scanner_fast_precheck_stability_pending`을 주 blocker로 남겼다.
- 이는 BUY threshold, order price, cancel wait, broker guard 문제가 아니라 관측 producer의 pre-submit blocker 분류 누락이다.
- 10:40 루프에서는 `rising_missed_buy_count=0`, `real_submit_symbol_count=20`으로 일반 BUY 전 actionable major blocker는 실질 잔여 없음으로 회복됐다.

### 55.2 코드수정

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - `latency_block`을 blocker stage에 추가했다.
  - `latency_block` taxonomy를 `pre_submit_quality_guard` / `inspect_latency_danger_or_slippage_without_guard_bypass`로 분류했다.
  - pre-submit quality guard가 scanner skip보다 뒤 단계의 submit 직전 차단으로 보이도록 dominant actionable blocker 우선순위를 추가했다.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - scanner precheck 이후 `latency_block/latency_state_danger`가 최신 blocker와 dominant actionable blocker로 남는 회귀 테스트를 추가했다.

### 55.3 산출물

- 10:20:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1020_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1020.md`
  - `rising_missed_buy_count=2`, 최신 blocker는 `latency_block/latency_state_danger`로 정정.
- 10:30:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1030_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1030.md`
  - `rising_missed_buy_count=1`, 삼화콘덴서 최신 blocker는 `latency_block/caution_slippage_exceeded`.
  - full-eval deferred는 `deferred_then_evaluated`라 submit 병목으로 승격하지 않음.
- 10:40:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1040_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1040.md`
  - `rising_missed_buy_count=0`, `real_submit_symbol_count=20`, `buy_signal_or_pre_submit_pass_seen_symbols=21`.
- 10:50:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1050_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1050.md`
  - `rising_missed_buy_count=0`, `real_submit_symbol_count=21`.
- 11:00:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1100.md`
  - `rising_missed_buy_count=0`, `real_submit_symbol_count=21`, `rising_missed_full_eval_budget_deferred_symbol_count=0`.
- final stabilization:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_final_stabilization.md`
  - 사용자 목표 변경에 맞춰 10:00~11:00 loop 판정으로 갱신.

### 55.4 운영 경계

- `runtime_effect=false`
- forbidden uses: `stale_submit_bypass`, `broker_guard_bypass`, `intraday_threshold_mutation`, `order_price_relaxation_without_operator_override`, `real_order_approval`
- latency DANGER/slippage guard, stale quote guard, broker/account/order/quantity/cooldown, hard/protect/emergency stop은 우회하지 않았다.

## 56. 2026-06-30 11:00-13:00 목표 루프: forced scout residual 관측 분리

작성 시각: `2026-06-30 11:25 KST`
수정 시각: `2026-06-30 11:43 KST`

### 56.1 판정

- 11:20 루프에서 `rising_missed_buy_count=8`로 재발했고, `rising_missed_one_share_entry` forced scout가 발생한 종목도 residual에 남아 있었다.
- 원익IPS는 일반 submit 성공이 아니라 `rising_missed_one_share_entry` forced scout 직후 1주 submit/fill lineage로 확인되어 일반 BUY/submit/fill/holding 성공에서 제외했다.
- 따라서 forced 1주 scout/매수 이벤트 때문에 감시대상 종목 자체가 제외되어 `rising missed=0`처럼 사라지는 상황은 아니다.
- 반복 actionable major blocker는 `latency_block/latency_state_danger`이며, 원본 이벤트상 quote stale이 아니라 약 1%대 `spread_ratio`에 따른 pre-submit 품질가드 차단이다.
- 주문/threshold/cancel wait/provider/broker guard를 변경하지 않고, 리포트 관측에서 forced scout와 일반 residual을 분리한다.

### 56.2 코드수정

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - forced scout row 자체뿐 아니라 같은 종목의 forced scout 직후 180초 안에 이어지는 `latency_pass`, `order_bundle_submitted`, `holding_started`, 1주 fill/submit lineage를 일반 real submit 집계에서 제외했다.
- `src/engine/monitoring/intraday_entry_flow_report.py`
  - 기존처럼 `rising_missed_one_share_entry` forced row는 일반 BUY flow/submit count에서 제외한다.
  - forced scout 직후 180초 안에 이어지는 submit/fill lineage도 일반 BUY flow/submit count에서 제외한다.
  - forced scout 이벤트 수, forced scout 종목 수, forced scout 종목 중 rising missed residual 유지 종목 수를 summary에 추가했다.
  - `latency danger root cause` 섹션을 추가해 종목별 `spread_ratio`, `ws_age_ms`, spread tick, micro bucket, top cause를 출력한다.
  - Markdown에 `forced scout observation` 섹션을 추가해 forced scout 종목과 forced scout 제외 residual 종목을 함께 출력한다.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - 원익IPS형 forced scout 이후 플래그 없는 submit/fill lineage가 일반 `real_submit_count`를 올리지 않는 회귀 테스트를 추가했다.
- `src/tests/test_intraday_entry_flow_report.py`
  - forced broker submit row가 일반 submit count를 올리지 않으면서 forced scout observation에만 집계되는 회귀 테스트를 추가했다.
  - forced scout 이후 플래그 없는 submit row가 일반 flow submit count와 BUY 통과 신호를 올리지 않는 회귀 테스트를 추가했다.
  - `spread_too_wide`, `spread_microstructure_wide`, `latency_provenance_gap` latency root cause 집계 회귀 테스트를 추가했다.

### 56.3 11:20 산출물

- `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1120_1100_goal.json`
- `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1120.md`
- 주요 값:
  - `rising_missed_buy_count_in_latest_diagnostic=8`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - `rising_missed_forced_scout_event_count=22`
  - `rising_missed_forced_scout_symbol_count=3`
  - `rising_missed_forced_scout_residual_symbol_count=3`
  - `rising_missed_residual_excluding_forced_scout_symbol_count=5`
  - forced scout residual: `000500`, `010120`, `240810`
  - forced scout 제외 residual: `001820`, `033100`, `095610`, `153890`, `475150`
- 11:30:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1130_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1130.md`
  - `rising_missed_buy_count_in_latest_diagnostic=8`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - forced scout residual: `000500`, `010120`, `240810`, `475150`
- 11:40:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1140_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1140.md`
  - `rising_missed_buy_count_in_latest_diagnostic=8`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - forced scout residual: `000500`, `010120`, `240810`, `475150`
- 11:50:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1150_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1150.md`
  - `rising_missed_buy_count_in_latest_diagnostic=8`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - root cause: `000500`/`010120`은 `spread_too_wide`, `475150`은 `spread_microstructure_wide`
- 12:00:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1200_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1200.md`
  - `rising_missed_buy_count_in_latest_diagnostic=8`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - root cause: `033100`은 `latency_provenance_gap`, `000500`/`010120`은 `spread_too_wide`, `475150`은 `spread_microstructure_wide`
- 12:10:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1210_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1210.md`
  - `rising_missed_buy_count_in_latest_diagnostic=9`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - root cause: `033100`은 `latency_provenance_gap`, `000500`/`010120`은 `spread_too_wide`, `475150`/`002990`은 `spread_microstructure_wide`
- 12:20:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1220_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1220.md`
  - `rising_missed_buy_count_in_latest_diagnostic=10`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - forced scout 제외 residual: `033100`, `095610`
- 12:30:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1230_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1230.md`
  - `rising_missed_buy_count_in_latest_diagnostic=10`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - forced scout 제외 residual: `033100`, `095610`
- 12:40:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1240_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1240.md`
  - `rising_missed_buy_count_in_latest_diagnostic=11`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - root cause: `080220` quote stale가 latency root cause에 추가
- 12:50:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1250_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1250.md`
  - `rising_missed_buy_count_in_latest_diagnostic=11`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - forced scout residual: 9종목
- 13:00:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1300_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1300.md`
  - `rising_missed_buy_count_in_latest_diagnostic=13`
  - `real_submit_symbol_count_in_latest_diagnostic=0`
  - forced scout residual: `000500`, `001820`, `002990`, `010120`, `025320`, `080220`, `103590`, `153890`, `240810`, `475150`
  - forced scout 제외 residual: `033100`, `095610`, `356680`
  - 최초 root cause: `033100`은 `latency_provenance_gap`, `000500`/`010120`은 `spread_too_wide`, `475150`/`002990`/`080220`/`025320`/`103590`은 `spread_microstructure_wide`
  - 57절 source-quality 보완 후 `033100`은 `spread_microstructure_wide`로 복구됐다.

### 56.4 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `45 passed`
- `.venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과

### 56.5 운영 경계

- `runtime_effect=false`
- forbidden uses: `stale_submit_bypass`, `broker_guard_bypass`, `intraday_threshold_mutation`, `order_price_relaxation_without_operator_override`, `real_order_approval`
- stale quote, latency DANGER/spread guard, broker/account/order/quantity/cooldown, hard/protect/emergency stop은 우회하지 않았다.

## 57. 2026-06-30 latency provenance gap 보완

### 57.1 판정

- `033100` 제룡전기의 `latency_provenance_gap`는 원본 `pipeline_events` 결손이 아니라 intraday diagnostic/event-cache 소비 경로의 source-quality 누락이었다.
- 원본 `ENTRY_PIPELINE latency_block/latency_state_danger` 38건에는 spread/WS age/orderbook microstructure 필드가 있었다.
- 보완 후 13:00 flow report에서 `033100` top cause는 `spread_microstructure_wide`로 복구됐다.

### 57.2 변경

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - 종목별 `latency_danger_root_cause` 요약을 추가했다.
  - `recent_blockers`에 latency state, stale flag, spread ratio, WS age, spread ticks, microstructure bucket, root cause를 보존한다.
- `src/engine/monitoring/intraday_entry_flow_report.py`
  - event cache에 종목 latency row가 없을 때 diagnostic의 `latency_danger_root_cause`를 우선 사용한다.
  - diagnostic에도 provenance가 없을 때만 `latency_provenance_gap`를 남긴다.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`, `src/tests/test_intraday_entry_flow_report.py`
  - diagnostic latency provenance 보존과 event-cache missing fallback 회귀 테스트를 추가했다.

### 57.3 재생성 결과

- 재생성:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1300_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1300.md`
- `033100` root cause:
  - `event_count=38`
  - `top_cause=spread_microstructure_wide`
  - `cause_counts`: `spread_microstructure_wide=19`, `quote_stale=18`, `spread_too_wide=1`
  - `spread_ratio median/max=0.00996/0.011952`
  - `ws_age_ms median/max=646.5/14480.0`
  - `spread_ticks median/max=5.0/9.0`

### 57.4 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `46 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py`
  - 통과

### 57.5 운영 경계

- `runtime_effect=false`
- forbidden uses: `stale_submit_bypass`, `broker_guard_bypass`, `intraday_threshold_mutation`, `order_price_relaxation_without_operator_override`, `real_order_approval`
- 이번 변경은 source-quality/diagnostic 보완이며 latency DANGER, spread, stale quote, broker/account/order/quantity/cooldown, hard/protect/emergency guard를 우회하지 않는다.

## 58. 2026-06-30 spread microstructure latency 후속 handoff 보완

### 58.1 판정

- `033100` 복구 후 남은 핵심 blocker는 단순 spread/slippage가 아니라 orderbook microstructure spread 계열까지 포함한다.
- 기존 BUY Funnel submit-drought root cause는 spread 계열을 `spread_or_slippage_guard`로 합쳐 downstream workorder/daily source bundle에서 microstructure spread를 별도 축으로 보기 어려웠다.
- 보완 후 `spread_microstructure_guard`가 BUY Funnel root cause, code-improvement workorder provenance, daily threshold-cycle source metrics까지 전달된다.

### 58.2 변경

- `src/engine/buy_funnel_sentinel.py`
  - `orderbook_micro_spread_ticks>=5` 또는 `orderbook_micro_*bucket`의 `spread=wide`를 `orderbook_micro_spread_wide` label로 보존한다.
  - 해당 label과 `spread_microstructure_wide`/`quote_fresh_composite_orderbook_micro_block`을 `spread_microstructure_guard` root cause로 분리한다.
- `src/engine/daily_threshold_cycle_report.py`
  - BUY Funnel `submit_drought_root_cause.latency_root_cause_counts`를 source metrics에 보존한다.
  - `latency_spread_microstructure_guard_count`, `latency_spread_or_slippage_guard_count`, `latency_quote_stale_count`를 별도 필드로 노출한다.
- `src/tests/test_buy_funnel_sentinel.py`, `src/tests/test_build_code_improvement_workorder.py`, `src/tests/test_daily_threshold_cycle_report.py`
  - microstructure spread 분리, workorder provenance 보존, daily source bundle 전달 회귀 테스트를 추가했다.

### 58.3 현재 산출물 확인

- `data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-30.json`
  - `primary=PRICE_GUARD_DROUGHT`
  - `matches`: `PRICE_GUARD_DROUGHT`, `LATENCY_DROUGHT`, `UPSTREAM_AI_THRESHOLD`
  - `latency_root_cause_counts.spread_microstructure_guard=411`
  - `unknown_latency_reason_count=0`
- 현재 날짜는 submit-drought primary가 아니라 `entry_submit_drought_contract.critical=false`이며, followup route는 `pre_submit_price_guard_review`다.

### 58.4 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `274 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/buy_funnel_sentinel.py src/engine/build_code_improvement_workorder.py src/engine/daily_threshold_cycle_report.py src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py`
  - 통과

### 58.5 운영 경계

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- 이번 변경은 source taxonomy/handoff 보완이며 spread cap, stale quote, latency DANGER, broker/account/order/quantity/cooldown, hard/protect/emergency guard를 완화하지 않는다.

## 59. 2026-06-30 root cause 해소 기준 보정

### 59.1 판정

- 목표 문구는 불분명하지 않았다. 목표 2번은 반복 actionable blocker에 대해 root cause 분해 뒤 최소 1개 이상의 해소 조치를 요구한다.
- 58절 변경은 `spread_microstructure_guard`를 downstream에 전달했지만, intraday diagnostic taxonomy에서는 `latency_block/latency_state_danger`가 계속 actionable major로 남아 root cause 해소 판정까지 닫지 못했다.
- 이번 보정 후 known latency guard(`quote_stale`, `spread_too_wide`, `spread_microstructure_wide`)는 guard를 유지한 채 non-major `pre_submit_quality_guard`로 내려간다. unknown/other/ws-age latency는 계속 actionable major로 남겨 후속 수정을 요구한다.

### 59.2 변경

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
  - `_blocker_taxonomy`가 `latency_root_cause`를 입력받도록 확장했다.
  - `spread_microstructure_wide`, `spread_too_wide`, `quote_stale`는 `known_*_guard_preserved_no_bypass` route로 suppress한다.
  - dominant actionable blocker와 taxonomy rollup이 latency root cause를 같이 소비하도록 보정했다.
- `src/tests/test_intraday_entry_blocker_diagnostics.py`
  - known latency guard는 suppressed non-major로 닫히고, `other_danger`는 actionable major로 유지되는 회귀 테스트를 추가했다.
  - 같은 종목 안에 known/unknown latency 원인이 섞여도 개별 root cause별로 major/suppressed가 갈라지는 회귀 테스트를 추가했다.

### 59.3 재생성 결과

- 재생성:
  - `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1300_1100_goal.json`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1100_to_1300.md`
- 결과:
  - `pre_submit_quality_guard/latency_block/latency_state_danger=24`가 `suppressed_non_actionable_counts`로 이동했다.
  - `actionable_major_blocker_counts`에는 latency known guard가 남지 않는다.
  - 남은 `actionable_major_blocker_count=157`은 strategy reject, entry cooldown opportunity, source freshness 등 별도 축이다.

### 59.4 검증

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `48 passed`
- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py`
  - 통과: `276 passed`
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/monitoring/intraday_entry_flow_report.py`
  - 통과

### 59.5 운영 경계

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- 이번 변경은 diagnostic taxonomy 해소 보정이며 spread/stale/latency/broker/account/order/quantity/cooldown/hard/protect/emergency guard를 완화하지 않는다.

## 60. 2026-06-30 intraday_entry_flow 중간 스냅샷 정리

### 60.1 판정

- `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_*_to_*.md` timestamp flow report는 사용 후 삭제 가능한 중간 산출물로 정리했다.
- 원천 이벤트와 루프별 진단 JSON은 별도 경로에 보존되며, flow 최종 판단은 고정 갱신 파일과 final stabilization 요약으로 유지한다.

### 60.2 변경

- 유지 파일:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_current.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_final_stabilization.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1300_to_1500_final_stabilization.md`
- 삭제 파일:
  - 2026-06-30 `0800_to_*`, `1100_to_*`, `1300_to_*` 중간 flow md/csv 스냅샷
- 10:00~11:00 final stabilization의 삭제된 flow/csv 참조는 `consolidated_into_final_summary`와 `deleted_after_use`로 정리했다.
- 13:00~15:00 final stabilization은 `source_flow_final`을 `intraday_entry_flow_2026-06-30_current.md`로 연결했다.

### 60.3 검증

- `find data/report/intraday_entry_flow -maxdepth 1 -type f -name 'intraday_entry_flow_2026-06-30*.csv'`
  - 잔여 없음
- `git diff --check`
  - 통과
