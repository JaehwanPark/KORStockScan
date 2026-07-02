# 2026-07-02 18:00~19:30 KST intraday entry flow final stabilization

- generated_at: 2026-07-02T19:30:09+09:00
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-02_current.md
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-02.json
- event_window_since: 2026-07-02T18:00:00+09:00
- event_window_until: 2026-07-02T19:30:00+09:00
- decision_authority: source_quality_and_blocker_observation_only
- runtime_effect: false

## Decision

18:00~19:30 KST goal is closed as final stabilization from the fixed current flow artifact. Normal BUY/submit/fill residual after excluding `rising_missed_one_share_entry` forced scout events is 0.

No intraday threshold mutation, stale submit bypass, broker/account/order/quantity/cooldown guard relaxation, provider change, cap change, or bot restart was performed.

## Evidence

- symbol_count: 138
- rising_symbol_count_by_max_delta: 13
- buy_signal_or_pre_submit_pass_seen_symbols: 13
- real_submit_symbol_count_in_latest_diagnostic: 0
- rising_missed_buy_count_in_latest_diagnostic: 3
- rising_missed_symbol_count_in_report: 3
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 104
- rising_missed_forced_scout_symbol_count: 14
- rising_missed_forced_scout_residual_symbol_count: 3
- rising_missed_class_counts: intended_guard_preserved=3
- rising_missed_full_eval_budget_deferred_symbol_count: 0
- rising_missed_one_share_eligible_symbol_count: 0
- rising_missed_repeated_zero_strength_history_workorder_count: 0
- rising_missed_runtime_attach_identity_mismatch_workorder_count: 0

## Final blocker split

- strategy_reject: 284
- source_freshness_evictable: 119
- source_freshness_recovering: 60
- watch_budget_reallocated: 58
- pre_submit_quality_guard: 10
- intended_guard: 9
- source_freshness_blocker: 3
- runtime_backpressure: 3

Suppressed non-major observations remained separated from normal BUY residual:

- ws_snapshot_missing_or_zero source-freshness evict/recover: 179
- stale_recovery_failed watch_budget_reallocated: 53
- latency_state_danger pre_submit_quality_guard: 10
- entry_cooldown_active intended_guard: 3
- scanner_full_eval_loop_budget_deferred runtime_backpressure: 3

## Rising missed details

The final rising missed residual symbols are `094360`, `378340`, and `486990`, but all are excluded from normal BUY resolution because the residual path is covered by forced-scout observation and/or intended guard classification.

- `094360` 칩스앤미디어: latest blocker `entry_cooldown_active`; prior overbought, liquidity, score, and insufficient-history observations remain strategy/source-quality attribution. Forced scout is not counted as normal BUY/submit/fill.
- `378340` 필에너지: latest blocker `entry_cooldown_active`; latency DANGER root cause was primarily quote stale or spread wide and remains a preserved pre-submit quality guard.
- `486990` 노타: latest blocker `entry_cooldown_active`; earlier latency DANGER and strength/momentum observations remain intended/source-quality attribution.

## Source-quality and workorder routing

Bounded freshness recheck workorders remain source-quality only and have no runtime apply authority:

- `094360`: event_count=125, diagnostic_quote_age_stale=120, pre_ai_stale_or_history_gap=5
- `378340`: event_count=51, diagnostic_quote_age_stale=51
- `486990`: event_count=12, diagnostic_quote_age_stale=10, pre_ai_stale_or_history_gap=2

Whole-window source-quality workorders also include repeated zero strength/history and one runtime attach identity mismatch outside the rising missed residual set. These are producer/source-quality follow-up items, not real-order or threshold authority.

## Closure conditions

- Actionable normal rising missed BUY residual: 0.
- Deferred-never-evaluated high-delta candidate: not observed; rising missed full-eval deferred symbol count is 0.
- Price-only/no-tick/source-quality churn is routed to source-freshness evict/recover or watch_budget_reallocated.
- Stale quote, latency DANGER, spread, broker/account/order/quantity/cooldown, hard/protect/emergency guard boundaries are preserved.
- Forced `rising_missed_one_share_entry` scout rows remain source-quality observation only and are not counted as normal BUY, submit, fill, holding, or rising-missed resolution success.
