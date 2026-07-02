# 2026-07-02 10:30-12:00 KST intraday entry flow final stabilization

- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-02_current.md
- source_diagnostic_final: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-02.json
- event_window_since: 2026-07-02T10:30:00+09:00
- event_window_until: 2026-07-02T12:00:00+09:00
- generated_from_current_at: 2026-07-02T12:00:00+09:00

## Decision

- 10:30-12:00 entry-flow observation is complete.
- Rising missed one-share forced scout rows are excluded from normal BUY bottleneck, submit/fill success, and unresolved rising-missed judgment.
- After excluding forced scout rows, unresolved rising-missed residual is 0 symbols.
- The direct Namkwang E&C scale-in failure class is quote-stale pre-submit price safety. The correction path is REST orderbook refresh before scale-in price guard when the WS quote is stale but otherwise usable; stale-submit and broker/order hard guards remain unchanged.
- The operator-requested WS condition-search path was fully reopened at 2026-07-02 11:58 KST through operator runtime override and graceful restart. This is an operational load observation change, not a BUY threshold or broker guard change.

## Evidence

- symbol_count: 73
- rising_symbol_count_by_max_delta: 7
- rising_missed_buy_count_in_latest_diagnostic: 5
- rising_missed_symbol_count_in_report: 5
- rising_missed_forced_scout_event_count: 159
- rising_missed_forced_scout_symbol_count: 5
- rising_missed_forced_scout_residual_symbol_count: 5
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 32
- stale_eval_symbol_count: 61
- rising_stale_eval_symbol_count: 7
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 46

Forced scout symbols:

- 001260
- 007610
- 267260
- 378340
- 486990

12:00 rising missed class counts:

- source_quality_excluded: 3
- intended_guard_preserved: 2

12:00 root-cause priorities:

- scanner_strength_history_or_stale_eval: fix observation freshness before threshold tuning.
- ai_wait_or_baseline_prior_score_block: do not relax score without fresh positive context and rolling confirmation.
- entry_price_or_submit_price_guard_block: review price resolution quality without stale-submit bypass.
- scale_in_blocked: preserve scale-in safety and separate price/quantity/window guard classes before any scale-in change.

Condition-search reopen evidence:

- pid: 65015
- KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED=true
- WS log observed CNSRLST list reception with 17 condition rows.
- WS log observed real-time PUSH requests for scalp condition rows including scalp_candid_aggressive_01, scalp_candid_normal_01, scalp_open_reclaim_01, scalp_vwap_reclaim_01, scalp_dryup_squeeze_01, scalp_preclose_01, scalp_strong_01, scalp_underpress_01, scalp_shooting_01, scalp_afternoon_01, vcp_shooting_01, vcp_shooting_next_01, and vcp_candid_01.
- Initial CNSRREQ load observed nonzero rows for scalp_vwap_reclaim_01, scalp_preclose_01, and scalp_strong_01.

## Next Action

- Treat forced scout rows as source-quality-only until a non-forced BUY/submit/fill path appears.
- Watch WS load after condition-search reopening: condition match/unmatch volume, WS REG churn, quote_stale ratio, scanner loop lag, and full-eval budget deferral.
- Do not relax BUY score, strength, latency, stale-submit, broker/account/order/quantity/cooldown, hard stop, or scale-in guards based on this intraday window alone.
- If condition-search reopen increases stale_eval or queue lag, close it with a bounded workorder or rollback `KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED=false`.
